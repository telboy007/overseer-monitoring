#! /bin/bash

# check serverless is installed before starting the fun
SERVERLESS=`which serverless`

if [ $? -ne 0 ]; then
  echo "Serverless is not installed; exiting"
  exit 1
else
  echo "Serverless found at $SERVERLESS"
  serverless --version
fi

# check aws cli is installed before starting the fun
AWS_CLI=`which aws`

if [ $? -ne 0 ]; then
  echo "AWS CLI is not installed; exiting"
  exit 1
else
  echo "AWS CLI found at $AWS_CLI"
  aws --version
fi

# check we've got an aws profile name
if [ $# -ne 2 ]; then
  echo "Usage: <command> <aws_profile_name>"
  echo "Where:"
  echo "   <command> = deploy or remove"
  echo "   <aws_profile_name> = Profile to use when deploying code"
  exit 2
fi

# add / update the folder locations below
cd lambdas/master_controller
serverless $1 --aws-profile $2
cd ../certificates
serverless $1 --aws-profile $2
cd ../dashboard_generator
serverless $1 --aws-profile $2
