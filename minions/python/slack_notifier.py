#try to get requests from AWS environment otherwise failback to local library
try:
    from botocore.vendored import requests
except:
    import requests


def send_slack_payload(message, SLACK_HOOK_SECRET):
    WEBHOOK_URL = "https://hooks.slack.com/services/%s" % (SLACK_HOOK_SECRET)
    payload = {
        'text': message
    }
    try:
        r = requests.post(WEBHOOK_URL, json=payload)
        if r.status_code == 200:
            print('Payload sent: ', str(payload))
        else:
            print('Error: ', r.content)
    except Exception as e:
        print('Exception: ' + str(e))
