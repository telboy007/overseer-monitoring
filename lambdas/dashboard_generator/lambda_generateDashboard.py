#!/usr/bin/env python

import boto3
import json
import sys

sys.path.append('./minions')
#minions imports
from python import aws_secrets
from python import slack_notifier
from python import s3_utilities


def lambda_handler(event, context):
    """
        Cycle through json string files in checks folder and generate dashboards
        Creates a master dashboard collating all the individuals dashboards
        Sends alerts to slack based on number of warnings and failures
    """
    SLACK_HOOK_SECRET = aws_secrets.get_secret('overseer-slack-hook-secret')
    dashboard_list = []

    # generate individual dashboards
    for key in s3_utilities.get_matching_s3_keys(bucket='overseer-monitoring-bucket', prefix='checks/', suffix='.json'):

        #read the json string file
        s3 = boto3.client('s3')
        obj = s3.get_object(Bucket='overseer-monitoring-bucket', Key=key)
        j = json.loads(obj['Body'].read())

        # grab the last updated time
        for k, v in j.iteritems():
            if k == 'last_updated':
                timestamp_str = v

        for k, v in j.iteritems():
            if k == 'config':
                for k2, v2 in v.iteritems():
                    if k2 == 'slab':
                        slab_style = v2
                    if k2 == 'dashboard':
                        dashboard_style = v2

        # load html templates
        with open('./templates/dashboards/' + dashboard_style + '.html', 'r') as myfile:
            dashboard_template = myfile.read()

        with open('./templates/slabs/' + slab_style + '/' + slab_style + '.container', 'r') as myfile:
            container_template = myfile.read()

        with open('./templates/slabs/' + slab_style + '/' + slab_style + '.slab', 'r') as myfile:
            slab_template = myfile.read()

        #get the check details from key
        details = key.replace('/', '-').replace('.', '-').split('-')
        check_name = details[1]
        check_description = details[2]
        check_items = []
        slab_html = ''
        fail_count = 0
        warn_count = 0

        for k, v in j.iteritems():
            if k == 'results':
                for k2, v2 in v.iteritems():
                    if v2 == 'okay':
                        slab_html += slab_template % (k2, v2, v2)
                    elif v2 == 'bad':
                        slab_html += slab_template % (k2, v2, v2)
                        fail_count += 1
                        check_items.append(str(k2))
                    else:
                        warn_count += 1
                        slab_html += slab_template % (k2, v2, v2)
                        check_items.append(str(k2))

        # send alert to slack if any warnings or failures
        if fail_count > 0:
            check_items = ",".join(check_items )
            message = "Failures with " + check_items + " in " + check_name + ", no. of failed checks: " + str(fail_count)
            slack_notifier.send_slack_payload(message, SLACK_HOOK_SECRET)
        elif warn_count > 0:
            check_items = ",".join(check_items )
            message = "Warnings with " + check_items + " in " + check_name + ", no. of warnings: " + str(warn_count)
            slack_notifier.send_slack_payload(message, SLACK_HOOK_SECRET)

        # substitute values into dashboard template
        container_html = container_template % (check_name, check_description, slab_html)
        full_html = dashboard_template % (check_name, container_html, timestamp_str)
        try:
            s3_utilities.s3_upload_dashboard(full_html, check_name)
        except Exception as e:
            print "Dashboard upload failed: " + str(e)

        # add dashboard details to aggregated list of dashboards
        dashboard_dict = {}
        dashboard_dict["check_name"] = check_name
        dashboard_dict["check_timestamp"] = timestamp_str
        if fail_count > 0:
            dashboard_dict["check_status"] = "bad"
        elif warn_count > 0:
            dashboard_dict["check_status"] = "unknown"
        else:
            dashboard_dict["check_status"] = "okay"

        dashboard_list.append(dashboard_dict)

    # generate master dashboard from aggregated list
    aggregate_html = ''

    # load aggregate templates
    with open('./templates/aggregate/aggregate.html', 'r') as myfile:
        aggregate_template = myfile.read()

    with open('./templates/aggregate/aggregate.container', 'r') as myfile:
        aggregate_container = myfile.read()

    # generate master dashboard
    for dict in dashboard_list:
        for k, v in dict.iteritems():
            if k == "check_name":
                check_name = v
            elif k == "check_status":
                check_status = v
            elif k == "check_timestamp":
                check_timestamp = v
        aggregate_html += aggregate_container % (
                                                 check_name,
                                                 check_status,
                                                 check_name,
                                                 check_timestamp
                                                 )

    final_html = aggregate_template % (aggregate_html)

    try:
        s3_utilities.s3_upload_dashboard(final_html, "master")
    except Exception as e:
        print "Dashboard upload failed: " + str(e)
