ARN=$(./scripts/create-ssm-param.sh)

pip install -r requirements.txt -t lib

serverless deploy --secrets-param-arn $ARN
