ARN=$(./scripts/create-ssm-param.sh)

if test -z "$ARN"; then
  exit 1;
fi

serverless deploy --secrets-param-arn $ARN
