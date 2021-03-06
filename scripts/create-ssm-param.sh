PARAMETER_NAME="session-invalidation-secrets"

# Check if the parameter already exists. If it does, we will update its value.
ARN="$(aws --output json --query "Parameter.ARN" ssm get-parameter --name $PARAMETER_NAME)"

SIGNING_KEY_ECDSA="$(python scripts/generate-ecdsa-key.py)"

if test -z "$ARN"; then
  # Echo error to stderr if a required environment variable is missing

  if test -z "$OIDC_CLIENT_SECRET"; then
    >&2 echo "!!! Environment variable OIDC_CLIENT_SECRET not set !!!";
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

  if test -z "$GSUITE_JSON_KEY_FILE"; then
    >&2 echo "!!! Environment variable GSUITE_JSON_KEY_FILE not set !!!";
    exit 1;
  fi

  if test -z "$GCP_JSON_KEY_FILE"; then
    >&2 echo "!!! Environment variable GCP_JSON_KEY_FILE not set !!!";
    exit 1;
  fi

  if ! test -f "$GSUITE_JSON_KEY_FILE"; then
    >&2 echo "!!! GSUITE_JSON_KEY_FILE is not a valid file path !!!";
    exit 1;
  fi

  if ! test -f "$GCP_JSON_KEY_FILE"; then
    >&2 echo "!!! GCP_JSON_KEY_FILE is not a valid file path !!!";
    exit 1;
  fi

  GSUITE_PRIVATE_KEY="$(python scripts/encode-gsuite-private-key.py)"
  
  GCP_PRIVATE_KEY="$(GSUITE_JSON_KEY_FILE=$GCP_JSON_KEY_FILE python scripts/encode-gsuite-private-key.py)"
  
  SECRETS="OIDC_CLIENT_SECRET=$OIDC_CLIENT_SECRET,SSO_CLIENT_SECRET=$SSO_CLIENT_SECRET,SLACK_TOKEN=$SLACK_TOKEN,SIGNING_KEY_ECDSA=$SIGNING_KEY_ECDSA,GSUITE_PRIVATE_KEY=$GSUITE_PRIVATE_KEY,GCP_PRIVATE_KEY=$GCP_PRIVATE_KEY" 

  aws ssm put-parameter \
    --name $PARAMETER_NAME \
    --description "A StringList of KEY=value pairs describing secret values" \
    --type StringList \
    --value "$SECRETS" \
    --tier Advanced \
    2> /dev/null;

  ARN="$(aws --output json --query "Parameter.ARN" ssm get-parameter --name $PARAMETER_NAME)"
fi

echo $ARN
