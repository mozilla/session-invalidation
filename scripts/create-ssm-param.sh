PARAMETER_NAME="session-invalidation-secrets"

# Check if the parameter already exists. If it does, we will update its value.
aws ssm get-parameter --name $PARAMETER_NAME 2> /dev/null

if [ $? -ne 0 ]; then
  # Echo error to stderr if a required environment variable is missing

  if test -z "$SSO_CLIENT_ID"; then
    >&2 echo "!!! Environment variable SSO_CLIENT_ID not set !!!";
    exit 1;
  fi

  if test -z "$SSO_CLIENT_SECRET"; then
    >&2 echo "!!! Environment variable SSO_CLIENT_SECRET not set !!!";
    exit 1;
  fi

  if test -z "$SLACK_TOKEN"; then
    >&2 echo "!!! Environment variable SLACK_TOKEN not set !!!";
    exit 1;
  fi

  SECRETS="SSO_CLIENT_ID=$SSO_CLIENT_ID,SSO_CLIENT_SECRET=$SSO_CLIENT_SECRET,SLACK_TOKEN=$SLACK_TOKEN" 

  aws ssm put-parameter \
    --name $PARAMETER_NAME \
    --description "A StringList of KEY=value pairs describing secret values" \
    --type StringList \
    --value "$SECRETS" \
    2> /dev/null;
fi


ARN="$(aws --output json --query "Parameter.ARN" ssm get-parameter --name $PARAMETER_NAME)"

echo $ARN
