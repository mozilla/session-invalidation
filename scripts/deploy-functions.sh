ARN=$(./scripts/create-ssm-param.sh)

if test -z "$ARN"; then
  exit 1;
fi

pip install -r requirements.txt -t lib

serverless deploy --secrets-param-arn $ARN
