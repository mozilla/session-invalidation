# Deployment Guide

This document describes the steps to undertake in order to deploy a functioning
instance of the Session Invalidation application. With one exception, the entire
deployment process is automated through the invocation of one `make` command,
however this first exception must only be accounted for during the very first
deployment.  This document is intended to be read from top to bottom.  You'll
find that most of the steps described here can be skipped after your first
deploy, but it's important to understand what's happening before you run
`make deploy`.

## Prerequisites

In order to deploy the session invalidation application, one must have installed
[NodeJS which comes with NPM](https://nodejs.org/en/download/).  The deployment
process uses a [Serverless](https://www.serverless.com/) plugin that must be
installed with the latter.

To deploy the application to AWS lambda, you will also need the
[serverless](https://www.serverless.com/framework/docs/getting-started/) tool
itself.  However, you can opt to skip this step as the deployment process will
check if serverless is installed and run the `curl` command in the linked
document for you if it is not.

Finally, you will need to have AWS credentials for the environment you want to
deploy to.  Using the
[Mozilla-AWS-CLI maws](https://pypi.org/project/mozilla-aws-cli-mozilla/) is
the recommended way to get them.

## First-time Deployment Steps

The first step to prepare for deployment is to have a TLS certificate issued for
the domain that you would like to assign to the
[API Gateway](https://aws.amazon.com/api-gateway/) created for the application.
Using, for example, the
[AWS Certificate Manager](https://aws.amazon.com/certificate-manager/), request
a new application and have it verified.  You will not need to create any
[Route53](https://aws.amazon.com/route53/) entries yourself as these will be
created for you by the
[serverless-domain-manager](https://github.com/amplify-education/serverless-domain-manager)
plugin.

Next, you will need to have the application, with the domain you chose when you
issued your certificate, registered with your OIDC Provider.  At Mozilla, that's
SSO (search MANA for "SSO Request Form").  At the end, you should get a client ID
and a client secret.

Finally, you will need to acquire credentials for each of the reliant parties
(RPs) supported by the application.

### Slack

Session termination for Slack relies on its
[SCIM User API](https://api.slack.com/scim#access), which requires and OAuth token
with the `admin` scope. See the linked documentation for more instructions.

### SSO

Session termination for SSO (OAuth) relies on an
[OAuth API endpoint](https://auth0.com/docs/api/management/v2#!/Users/post_invalidate_remember_browser)
that requires the `update:users` scope.  After requesting these credentials,
you should get an OAuth client ID and client secret.

### GSuite

Session termination for GSuite relies on a
[service account](https://developers.google.com/identity/protocols/oauth2/service-account#top_of_page)
created by an admin for a project granted access to the Admin SDK. The service
account must have the `https://developers.google.com/identity/protocols/oauth2/service-account#top_of_page` scope
granted to it.

## General Configuration

All of the non-secret configuration for the application is stored in the
`provider.environment` section of `serverless.yml`.

* `SELF_DOMAIN` is configured under `custom.customDomain.domainName` at the
bottom of the file and is the domain name to which your TLS certificate
is assigned.
* `OIDC_CLIENT_ID` is the client ID provided to you by your OIDC OP.
* `OIDC_DISCOVERY_URI` is the URI pointing to the `openid-configuration` file
served by your OIDC OP.
* `OIDC_SCOPES` are the (space separated) scope names required by the application
and likely do not need to be changed.
* `GSUITE_ACCOUNT_TYPE` is the value corresponding to the `"type"` field in
the service account JSON key.
* `GSUITE_PROJECT_ID` is the value corresponding to the `"project_id"` field in
the service account JSON key.
* `GSUITE_PRIVATE_KEY_ID` is the value corresponding to the `"private_key_id"`
field in the service account JSON key.
* `GSUITE_CLIENT_EMAIL` is the value corresponding to the `"client_id"`
field in the service account JSON key.
* `GSUITE_CLIENT_ID` is the value corresponding to the `"client_email"`
field in the service account JSON key.
* `GSUITE_AUTH_URI` is the value corresponding to the `"auth_uri"`
field in the service account JSON key.
* `GSUITE_TOKEN_URI` is the value corresponding to the `"token_uri"`
field in the service account JSON key.
* `GSUITE_AUTH_PROVIDER_CERT_URL` is the value corresponding to the
`"auth_provider_x509_cert_url"` field in the service account JSON key.
* `GSUITE_CLIENT_CERT_URL` is the value corresponding to the
`"client_x509_cert_url"` field in the service account JSON key.
* `GSUITE_SUBJECT` is the email address of the GSuite admin that created your
project's service account.
* `SLACK_LOOKUP_USER_ENDPT` must point to Slack's
[users.lookupUserByEmail](https://api.slack.com/methods/users.lookupByEmail)
endpoint.
* `SLACK_SCIM_USERS_ENDPT` must point to Slack's 
[SCIM Users API](https://api.slack.com/scim).
* `SSO_CLIENT_ID` is the client ID of the SSO (OAuth) RP.
* `SSO_USER_ENDPT` is a format string pointing to the API endpoint that is used
to invalidate SSO user sessions.  It must have one `{}` format-string parameter,
which will be filled with a value like `"ad|Mozilla-LDAP|target@mozilla.com"`.
* `SSO_ID_FORMAT` specifies the format to encode a target user's email address
into requests for the `MOZ_OAUTH_ENDPT` endpoint.
* `SSO_AUTH_URL` is the token endpoint required to authenticate the application
in order to make requests to the OAuth API.
*  `SSO_AUDIENCE` is the OIDC audience parameter required to authenticate the
application to make requests to the OAuth API.
* `SSO_GRANT_TYPE` is the OIDC grant type parameter required to authenticate
the application to make requests to the OAuth API.
* `SQS_QUEUE_URL` is the URL of the [AWS SQS Queue](https://aws.amazon.com/sqs/)
to which the application will write logs for consumption by MozDef.  It is
generated during deployment.

## Configuring Secrets

All secret values are provided via environment variables during deployment and
then stored in [AWS Parameter
Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
for retrieval by the application.

The [scripts/create-ssm-param.sh](/scripts/create-ssm-param.sh) file is invoked
during deployment to:

1. Check if an SSM parameter already exists containing required secrets
2. Check that all required secrets are provided as environemnt variables and
3. Create an SSM parameter containing the required secrets.

In the case that the SSM parameter already exists, steps 2 and 3 will be skipped.

Required secrets include:

* `OIDC_CLIENT_SECRET`, the client secret provided by your OIDC provider to
authenticate users of the application.
* `SSO_CLIENT_SECRET`, the client secret provided by your OAuth admin
required to terminate SSO (OAuth) sessions.
* `SLACK_TOKEN`, the OAuth token created for your application to invoke the
Slack SCIM API.
* `GSUITE_JSON_KEY_FILE`, the path to the `.json` key file created to
authenticate as your project's service account.

The only field extracted from the `GSUITE_JSON_KEY_FILE` is the `"private_key"`
which is encoded to hex for storage in SSM.

This script also automatically generates a secure key used to sign user
session cookies after they authenticate via SSO.

## Deploying

Once you have:

1. A TLS certificate verified for the domain configured in `serverless.yml`
2. Configuration set up correctly in `serverless.yml`
3. NodeJS, NPM and the serverless tools all installed
4. Authenticated to AWS and
5. Obtained all of the secrets you need

you can initiate a deployment simply by running

```
OIDC_CLIENT_SECRET=<client secret>\
SSO_CLIENT_SECRET=<sso secret>\
SLACK_TOKEN=<token>\
GSUITE_JSON_KEY_FILE=/path/to/session-invalidation-key.json\
make deploy
```

This process will:

1. Create an SSM parameter containing the secrets provided
2. Install the project dependencies to the local `lib/` folder
3. Deploy the AWS Lambda funtions and finally
4. Upload static files for the frontend to AWS S3

Assuming you have performed these steps at least once before, simply running

```
make deploy
```

without environment variables will be sufficient to re-deploy the lambda
functions and static files, as step 2 above will be skipped when the SSM
parameter is found to already exist.

## Teardown

If you want to completely remove the SSM parameter storing secrets, static files
and the lambda functions themselves, you can run

```
make teardown-deploy
```

Alternatively, you can run

```
make delete-static-content
```

to just delete the contents of the S3 bucket for static files.

Finally, you can delete the SSM parameter storing secrets with

```
make delete-ssm-parameter
```
