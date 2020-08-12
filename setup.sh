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

# add / update the folder locations below
cd lambdas/master_controller
sls plugin install -n serverless-deployment-bucket
cd ../certificates
sls plugin install -n serverless-deployment-bucket
sls plugin install -n serverless-python-requirements
cd ../dashboard_generator
sls plugin install -n serverless-deployment-bucket
