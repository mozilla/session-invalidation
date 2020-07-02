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

Once your TLS certificate has been verified, you can create the domain that you
configured at the bottom of `serverless deploy` by running the following `make`
target.  Note that it can take up to about 40 minutes for your domain
configuration to propagate across DNS servers.

```
make domain
```

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

| Variable | Description | Dev Value | Prod Value |
| -------- | ----------- | --------- | ---------- |
| `SELF_DOMAIN` | Configured under `custom.customDomain.domainName` at the bottom of the file and is the domain name to which your TLS certificate is assigned. | `https://${self:custom.customDomain.domainName}` | `https://${self:custom.customDomain.domainName}` |
|  `OIDC_CLIENT_ID` | The client ID provided to you by your OIDC OP. | `M6lxk8phwDaqH4gECMWDLxKxxZwJcDI7` | `wX5uKEP7oV4wgxf0B3USOrDQ5kgHFda0` |
| `OIDC_DISCOVERY_URI` | The URI pointing to the `openid-configuration` file served by your OIDC OP. | `https://auth-dev.mozilla.auth0.com/.well-known/openid-configuration` | `https://auth.mozilla.auth0.com/.well-known/openid-configuration` |
| `OIDC_SCOPES` | Are the (space separated) scope names required by the application and likely do not need to be changed. | `openid profile email` | `openid profile email` |
| `GSUITE_ACCOUNT_TYPE` | The value corresponding to the `"type"` field in the service account JSON key. | `service_account` | `service_account` |
| `GSUITE_PROJECT_ID` | The value corresponding to the `"project_id"` field in the service account JSON key. | `session-invalidation-test` | `mozilla-session-invalidation` |
| `GSUITE_PRIVATE_KEY_ID` | The value corresponding to the `"private_key_id"` field in the service account JSON key. | `b77d67c899cf4ddb79f4d49892b6fce0ae9058f2` | `33d19551aac10d2ca1f163bdeda46889608d867a` |
| `GSUITE_CLIENT_EMAIL` | The value corresponding to the `"client_id"` field in the service account JSON key. | `sesinv-admin-822@session-invalidation-test.iam.gserviceaccount.com` | `mozilla-session-invalidation@mozilla-session-invalidation.iam.gserviceaccount.com` |
| `GSUITE_CLIENT_ID` | The value corresponding to the `"client_email"` field in the service account JSON key. | `108687455550978238351` | `101355836648639176923` |
| `GSUITE_AUTH_URI` | The value corresponding to the `"auth_uri"` field in the service account JSON key. | `https://accounts.google.com/o/oauth2/auth` | `https://accounts.google.com/o/oauth2/auth` |
| `GSUITE_TOKEN_URI` | The value corresponding to the `"token_uri"` field in the service account JSON key. | `https://oauth2.googleapis.com/token` | `https://oauth2.googleapis.com/token` |
| `GSUITE_AUTH_PROVIDER_CERT_URL` | The value corresponding to the `"auth_provider_x509_cert_url"` field in the service account JSON key. | `https://www.googleapis.com/oauth2/v1/certs` | `https://www.googleapis.com/oauth2/v1/certs` |
| `GSUITE_CLIENT_CERT_URL` | The value corresponding to the `"client_x509_cert_url"` field in the service account JSON key. | `https://www.googleapis.com/robot/v1/metadata/x509/sesinv-admin-822%40session-invalidation-test.iam.gserviceaccount.com` | `https://www.googleapis.com/robot/v1/metadata/x509/mozilla-session-invalidation%40mozilla-session-invalidation.iam.gserviceaccount.com` | 
| `GSUITE_SUBJECT` | The email address of the GSuite admin that created your project's service account. | `gads_admin_bot@test.mozilla.com` | `gads_admin_bot@mozilla.com` |
| `SLACK_LOOKUP_USER_ENDPT` | Must point to Slack's `users.lookupUserByEmail` endpoint. | `https://api.slack.com/methods/users.lookupByEmail` |  `https://api.slack.com/methods/users.lookupByEmail` |
| `SLACK_SCIM_USERS_ENDPT` | Must point to Slack's  SCIM Users API endpoint. | `https://api.slack.com/scim` | `https://api.slack.com/scim` |
| `SSO_CLIENT_ID` | The client ID of the SSO (OAuth) RP. | `eJPgs0CNdtyDW0bWTMByMb3Pan1F8n6n` | `J6oOrIBEv9QtmX5HQSPJCj68sMZuwfqS` |
| `SSO_USER_ENDPT` | A format string pointing to the API endpoint that is used to invalidate SSO user sessions.  It must have one `{}` format-string parameter, which will be filled with a value like "ad&#124;Mozilla-LDAP&#124;target@mozilla.com". | `https://auth-dev.mozilla.auth0.com/api/v2/users/{}/multifactor/actions/invalidate-remember-browser` | `https://auth.mozilla.auth0.com/api/v2/users/{}/multifactor/actions/invalidate-remember-browser` |
| `SSO_ID_FORMAT` | Specifies the format to encode a target user's email address into requests for the `MOZ_OAUTH_ENDPT` endpoint. | ad&#124;Mozilla-LDAP-Dev&#124;{} | ad&#124;Mozilla-LDAP&#124;{} |
| `SSO_AUTH_URL` | The token endpoint required to authenticate the application in order to make requests to the OAuth API. | `https://auth-dev.mozilla.auth0.com/oauth/token` | `https://auth.mozilla.auth0.com/oauth/token` |
| `SSO_AUDIENCE` | The OIDC audience parameter required to authenticate the application to make requests to the OAuth API. | `https://auth-dev.mozilla.auth0.com/oauth/token` | `https://auth.mozilla.auth0.com/oauth/token` |
| `SSO_GRANT_TYPE` | The OIDC grant type parameter required to authenticate the application to make requests to the OAuth API. | `client_credentials` | `client_credentials` |
| `SQS_QUEUE_URL` | The URL of the [AWS SQS Queue](https://aws.amazon.com/sqs/) to which the application will write logs for consumption by MozDef.  It is generated during deployment. | `!Ref SQSToMozDef` | `!Ref SQSToMozDef` |

Along with the `domainName` field at the bottom of `serverless.yml`, you will also find:

| Variable | Description | Dev Value | Prod Value |
| -------- | ----------- | --------- | ---------- |
| `certificateArn` | The ARN of the AWS certificate for the domain. | `arn:aws:acm:us-west-2:656532927350:certificate/453c5160-daf4-4238-a195-9eb487a71d23` | ` arn:aws:acm:us-west-2:371522382791:certificate/a929838b-81a4-47f8-b648-50e4909f5e55` |
| `hostedZoneId` | The ID of the hosted zone containing your domain. | `Z13VQZ50081YZU` | ` ZBALOKPGJTQW` |

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

## Deployment Notes

### Handling Secrets

It is recommended that the secrets used by the application be deleted from any
devices that stored them prior to their being uploaded to SSM.  This is to
prevent the possibility of those credentials being mistakenly uploaded to
version control (e.g. Github) or being retrieved by an attacker who succeeds
at compromising the host(s) in question.

In the case of any kind of emergency in which the session invalidation
application must be re-deployed with the same secrets or with only a subset
of them being modified, existing secrets can be copied from SSM Parameter Store.
Some extra steps will have to be followed in particular to recreate a GSuite
private key file to be read by `scripts/create-ssm-param.sh` via the
`GSUITE_JSON_KEY_FILE` environment variable.  To set everything up for a new
deployment, follow these steps.

1. Copy the `OIDC_CLIENT_SECRET` value to a file.
2. Copy the `SSO_CLIENT_SECRET` value to a file.
3. Copy the `SLACK_TOKEN` value to a file.
4. Copy the `GSUITE_PRIVATE_KEY` value to your clipboard.
5. Run `scripts/create-gsuite-json-key-file.py` file as below.
6. Run `make delete-ssm-parameter` to delete the stored secrets.

```bash
python scripts/create-gsuite-json-key-file.py <pasted key> <path to file>

# Example
# pythoh scripts/create-gsuite-json-key-file.py ABCDEF0123...988 ./gsuite-key.json
```

Now when you run `make deploy` you can provide the requisite environment
variables with `GSUITE_JSON_KEY_FILE` set to `./gsuite-key.jsoon` and
the deployment will be able to re-create the SSM parameter.

### S3 Bucket Management

In the case that the Session Invalidation application has been deployed to
a development environment under one of the accounts you use and you then
wish to deploy to production, some extra care must be taken regarding
the S3 bucket hosting static content.  Because S3 buckets are global across
accounts, deploying first to a dev environment and then to prod will result
in an error saying the bucket already exists.  The quickest and easiest way
to deal with this is to comment out the resource definition for the bucket
from `serverless.yml` so that it reads like so.

```yml
resources:
  Resources:
#    StaticContentBucket:
#      Type: AWS::S3::Bucket
#      Properties:
#        BucketName: session-invalidation-static-content
#        AccessControl: Private
```

This will prevent serverless from trying and failing to re-create the bucket.
In this sort of scenario, this behaviour is acceptable as the bucket in both
environments will contain the same files.

Another way of resolving this would be to delete the bucket before running the
deployment process, however this has the drawback that the re-creation of
the bucket could take over an hour on AWS' side.

## Deploying

Once you have:

1. A TLS certificate verified for the domain configured in `serverless.yml`
2. Run `serverless create_domain` to create the domain you configured.
3. Configuration set up correctly in `serverless.yml`
4. NodeJS, NPM and the serverless tools all installed
5. Authenticated to AWS and
6. Obtained all of the secrets you need

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
