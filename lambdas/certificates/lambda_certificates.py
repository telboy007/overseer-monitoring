#!/usr/bin/env python

#try to get requests from AWS environment otherwise failback to local library
try:
    from botocore.vendored import requests
except:
    import requests

from datetime import tzinfo, datetime, timedelta

import json
import StringIO
import re
import os
import sys
import boto3
import logging
import kubernetes
from kubernetes.client.rest import ApiException
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import base64
import ruamel.yaml as yaml
import pprint


# sys.path.append('../../minions')
sys.path.append('./minions')
#minion imports
from python import overseer_utilities
from python import datetime_utilities
from python import aws_secrets

# create logger
logger = logging.getLogger()
logger.setLevel(logging.WARNING)


def lambda_handler(event, context):
    """
        Checks certificate expiry dates in acm and kubernetes
    """
    # get config
    check_name, check_description, dashboard_style, slab_style, frequency, overseer_file = overseer_utilities.read_config()

    # should I run?
    check_time = datetime_utilities.get_lastrun_timestamp(overseer_file)
    good_to_go = datetime_utilities.check_timestamp(check_time, frequency, aware=False)
    # good_to_go = True

    if good_to_go:
        # unique information for check
        checked_cert_list = {}
        cert_arn_dict = {}
        regions = ["us-east-1", "eu-west-1"]

        # get list of things to check
        cert_arn_dict = list_certificates(regions)

        #aws certs
        for region in regions:
            for item in cert_arn_dict[region]:
                cert_json = describe_certificate(item, region)
                if cert_json["Certificate"]["RenewalEligibility"] == "ELIGIBLE":
                    expiry_date = cert_json["Certificate"]["NotAfter"]
                    cert_domain = cert_json["Certificate"]["DomainName"] + " (" + region + ")"

                    # this will tell you the time between now and specified date
                    hours = datetime_utilities.get_future_date_time_difference(expiry_date, "hours", aware=True)
                    status = get_status(hours)

                    checked_cert_list[cert_domain] = status

        #kube certs (disabled)
        # cert_auth_data = aws_secrets.get_secret('qa-tools-kube-staging-cert-auth-data')
        # api_response = get_kube_secrets()
        # cert_list = decode_and_extract(api_response)
        #
        # for cert in cert_list:
        #     for k, v in cert.items():
        #         expiry_date = datetime.strptime(v, "%d-%b-%Y %H:%M:%S")
        #         cert_domain = str(k).replace('>','').replace('<','').decode('utf-8')
        #
        #         # this will tell you the time between now and specified date
        #         hours = datetime_utilities.get_future_date_time_difference(expiry_date, "hours", aware=False)
        #         status = get_status(hours)
        #
        #         checked_cert_list[cert_domain] = status

        # get timestamp for dashboard
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M:%S")

        json_file = {'config': {'dashboard': dashboard_style, 'slab': slab_style}, 'results': checked_cert_list, 'last_updated': timestampStr}

        try:
            client = boto3.client('s3')
            client.put_object(Body=json.dumps(json_file), Bucket='overseer-monitoring-bucket', Key=overseer_file)
        except Exception as error:
            logger.critical(error)
            raise Exception(error)


# specific aws calls for this lambda
def list_certificates(regions):
    cert_dict = {}

    for region in regions:
        cert_list = []
        client = boto3.client("acm", region_name=region)
        response = client.list_certificates()
        for item in response["CertificateSummaryList"]:
            cert_list.append(item["CertificateArn"])
        cert_dict[region] = cert_list

    return cert_dict


def describe_certificate(cert_arn, region):
    client = boto3.client("acm", region_name=region)
    response = client.describe_certificate(
        CertificateArn=cert_arn
    )

    return response


# specific kube calls for this lambda
def get_kube_secrets():
    # get config
    configuration = kubernetes.config.load_incluster_config()

    # create an instance of the API class
    api_instance = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(configuration))

    try:
        api_response = api_instance.list_secret_for_all_namespaces()
        return api_response
    except ApiException as e:
        logger.critical("Exception when calling Kubernetes API: %s\n" % e)
        raise Exception(e)


def decode_and_extract(api_response):
        tls_list = []
        for item in api_response.items:
            try:
                tls_list.append(item.data[u'tls.crt'])
            except:
                pass

        cert_list = []
        for item in tls_list:
            cert_item = {}
            decoded_crt = base64.b64decode(item)
            cert = x509.load_pem_x509_certificate(decoded_crt, default_backend())
            cert_item[cert.subject] = cert.not_valid_after.strftime("%d-%b-%Y %H:%M:%S")
            cert_list.append(cert_item)

        return cert_list


# status get
def get_status(time):
    if time < 48:
        return "bad"
    elif time < 96:
        return "unknown"
    else:
        return "okay"


if __name__ == '__main__':
    lambda_handler('','')
