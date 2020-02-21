cd lambdas/master_controller
serverless deploy --aws-profile profile-name
cd ../certificates
serverless deploy --aws-profile profile-name
cd ../dashboard_generator
serverless deploy --aws-profile profile-name
