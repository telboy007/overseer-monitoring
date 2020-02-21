#!/usr/bin/env python

import boto3
import json

from datetime import tzinfo, datetime, timedelta

ZERO = timedelta(0)

class UTC(tzinfo):
    def utcoffset(self, dt):
        return ZERO
    def tzname(self, dt):
        return "UTC"
    def dst(self, dt):
        return ZERO


def get_lastrun_timestamp(overseer_file):
    client = boto3.client('s3')
    obj = client.get_object(Bucket='overseer-monitoring-bucket', Key=overseer_file)
    check_json = json.loads(obj['Body'].read())
    check_time = datetime.strptime(check_json['last_updated'], "%d-%b-%Y %H:%M:%S")
    return check_time


def check_timestamp(check_time, frequency, aware):
    """
        checks timestamp and tells lambda whether it should run or not
    """
    utc = UTC()
    if aware:
        delta = datetime.now(utc) - check_time
    else:
        delta = datetime.now() - check_time
    if frequency[1] == "day":
        if int(frequency[0]) > int(delta.days):
            return False
        else:
            return True
    else:
        return True


def get_future_date_time_difference(date, period, aware):
    utc = UTC()
    if aware:
        delta = date - datetime.now(utc)
    else:
        delta = date - datetime.now()
    result = 0
    if period == "hours":
        result = (delta.days * 24) + delta.seconds/3600
    return int(result)
