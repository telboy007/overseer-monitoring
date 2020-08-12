# overseer

Requirements
============

Installation requirements:
* serverless
* aws cli
* docker (desktop client)

Configuration requirements:
* AWS credentials for your account already setup

Code changes:
* change the deployment and application bucket name
  * `overseer.serverless.${self:provider.region}.deploys`
  * `overseer-monitoring-bucket`
* change the region from `eu-west-2` (if required)
* change `stage` and `profile` parameters in the `serverless.yaml` files to something relevant

Deployment
==========

Deploys to aws lambda (via cloudformation) using Serverless, also as a bonus feature the deployment of the certificates lambda uses docker to compile required python libraries to ensure compatibility.  This was "fun" to implement.

Use the deployment script `overseer-serverless.sh` to deploy or remove overseer from your AWS account.

Run the following:
* `chmod +x overseer-serverless.sh`
* `chmod +x setup.sh`
* `./setup.sh`
* `./overseer-serverless.sh <command> <aws_profile>`
  * e.g. `./overseer-serverless.sh deploy my-account`

Gotchas: Minions (helper libraries) are packaged with the lamdba deployment so will be at root level on AWS unlike when run locally, keep that in mind. :)

Structure
=========

Master Controller runs as a AWS lambda and calls multiple lambdas
- lambda(s) to check status of a thing (check lambdas)
  - each lambda requires a serverless, package/requirement and config file
- lambda to create master dashboard and individual dashboards displaying statuses of output from check lambdas
- minions are helper libraries written in specific languages
  - python
- templates stores different ways of representing output from check lambdas
  - template (structure of collection of data)
  - slabs (structure of individual points of data)
- static contains css files, etc
- tests lol

Check lambdas
* Should generate a json file, with two sections; config and results from the check (example below)
  * Config sets the type of dashboard and slab type
  * Results contains the output from any checks run
* Depending on the slab type, the value can be a status, count, etc (work in progress)
  * e.g. Status slab values can be `okay`, `bad`, `unknown`.
* File can contain one or multiple key pairs.

Example check json file:
`{"last_updated": "20-Feb-2020 18:30:49", "config": {"slab": "status", "dashboard": "default"}, "results": {"aws cert 1 (eu-west-2)": "okay", "aws cert 2 (us-east-1)": "okay"}}`

Minions provide certain functions to help out:
* aws_secrets:
  * `get_secret`: provide it the name and it will get the secret from AWS simple system manager parameter store
    * arguments: secret name (required)
  * `get_secret_age`: if your secret has a short life use this function to get it's age
    * arguments: secret name (required)
  * `update_secret`: provide it secret name and new value and it will update the parameter store
    * arguments: secret name (required)
  * `check_access_token_age`: pass the age from `get_secret_age` and a life time (in hours) to check whether e.g. you need to use a refresh token to get another api key.
    * arguments: secret name, life time in hours (required)
* slack_notifier:
  * `send_slack_payload`: simply pass it a message and the slack hook (which you should store as a secret and use `aws_secrets` to retrieve).  The message can contain urls, images, etc.  Refer to the slack documentation for more details.
    * arguments: message, slack hook (required)
* s3_utilities:
  * it is unlikely you will need to use any of these function

Templates:
* has templates for dashboard(s) and slab(s)
* Dashboard templates available:
  * default
* Slab types available:
  * status

Adding new Check Lambdas
========================

Write a lambda in whatever language you want, create a package/requirements file, config file and serverless.yml with all the relevant instructions.  Put it in a folder in the lambdas folder in this here repo.

The config file will hold specific info for the check and will look something like this:

`
{
  "check_name": "certificates",
  "check_description": "expiry date check",
  "dashboard_style": "default",
  "slab_style": "status",
  "frequency": "1_day"
}
`

If it's written in python then use the certificate lambda as a guide - there are a few important sections that are required; reading the config file, if you want to schedule your check based on frequency (see certificates lambda for an example), the main logic to perform the check, populating the results into a json file and uploading the file to s3.  

It should be the case that you'll only need to provide the main logic to perform the check - the rest should work with your code as long as the output of your check is compliant.

In the master controller lambda add the name of the new lambda function in the following array:

`
lambda_list = [
    'overseer-checkname-envname',
]
`

Add the new lambda to the `deploy-serverless.sh` file so it can deploy to the designated `AWS account` (credentials must be configured on your local machine).

Finally add the new lambda function to the `serverless.yml` for `master_controller` to enable the invoke permission.

```
- Effect: 'Allow'
  Action:
    - 'lambda:InvokeFunction'
  Resource:
    Fn::Join:
      - ':'
      - - 'arn:aws:lambda'
        - Ref: 'AWS::Region'
        - Ref: 'AWS::AccountId'
        - 'function:overseer-checkname-envname'
```

Viewing the dashboards
======================

The generated dashboards are stored in an s3 bucket and will need some sort of web server so they can be viewed.

Other things of note
====================

Helper scripts:
* Deploy overseer from local machine to AWS account

TODOs:

1. Parameterise the overseer s3 bucket and environment name
2. Use proper logging
3. More slab types - like charts, etc.
4. Create example check lambdas in multiple languages
5. Create helper script to add secrets to AWS
6. Get the UI looking a bit more like dashing?
