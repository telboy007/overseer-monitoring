#!/usr/bin/env python

import boto3
import json
import re
import sys

sys.path.append('./minions')
#lambda imports
from python import aws_secrets
from python import slack_notifier


def lambda_handler(event, context):

    # Add new lambdas here
    lambda_list = [
        'overseer-certificates-staging',
    ]

    # Put lambdas for checks here
    lambda_client = boto3.client('lambda')

    for item in lambda_list:
        invoke_response = lambda_client.invoke(FunctionName=item,
                                               InvocationType='Event')

if __name__ == "__main__":
    resp = lambda_handler(event="foo", context="bar")
