#!/usr/bin/env python

from datetime import tzinfo, datetime, timedelta
import boto3

#aws utilities
def get_secret(secret):
    ssm_client = boto3.client('ssm', region_name='eu-west-1')
    try:
        response = ssm_client.get_parameter(
            Name=secret,
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except Exception as e:
        print('Exception:' + str(e))
        raise Exception(str(e))


def get_secret_age(secret):
    ssm_client = boto3.client('ssm', region_name='eu-west-1')
    try:
        response = ssm_client.get_parameter_history(
            Name=secret,
            WithDecryption=True
        )
        return response['Parameters'][0]['LastModifiedDate']
    except Exception as e:
        print('Exception:' + str(e))
        raise Exception(str(e))


def update_secret(secret, secret_value):
    ssm_client = boto3.client('ssm', region_name='eu-west-1')
    try:
        response = ssm_client.put_parameter(
            Name=secret,
            Value=secret_value,
            Type='SecureString',
            Overwrite=True,
        )
        return response['Version']
    except Exception as e:
        print('Exception:' + str(e))
        raise Exception(str(e))


# aware/unaware timezone time fix
ZERO = timedelta(0)

class UTC(tzinfo):
    def utcoffset(self, dt):
        return ZERO
    def tzname(self, dt):
        return "UTC"
    def dst(self, dt):
        return ZERO


def check_access_token_age(secret_age, lifetime_hours):
    utc = UTC()
    now = datetime.now(utc)
    if (now-timedelta(hours=lifetime_hours) <= secret_age <= now):
        return True
    else:
        return False
