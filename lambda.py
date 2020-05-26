import json
import os
import sys

if 'LAMBDA_TASK_ROOT' in os.environ:
    sys.path.append(f"{os.environ['LAMBDA_TASK_ROOT']}/lib")
else:
    sys.path.append('lib')

import boto3

import sesinv


STATIC_CONTENT_BUCKET_NAME = 'session-invalidation-static-content'
SECRETS_SSM_PARAMETER = 'session-invalidation-secrets'

ERROR_PAGE = '''<doctype HTML>
<html>
    <head>
        <title>Session Invalidation Error</title>
    </head>
    <body>
        <h1>Error</h1>
        <p>{0}</p>
    </body>
</html>
'''


def static_content(filename):
    s3 = boto3.resource('s3')
    static_content = s3.Bucket(STATIC_CONTENT_BUCKET_NAME)

    file_path = f'/tmp/{filename}'

    if not os.path.isfile(file_path):
        with open(file_path, 'wb') as f:
            static_content.download_fileobj(filename, f)

    with open(file_path, 'rb') as f:
        return f.read()


def load_config():
    # These are expected to be found in SSM and then loaded into environment
    # variables to avoid reading from SSM too often.  Env vars are encrypted.
    secret_cfg_keys = [
        'SSO_CLIENT_ID',
        'SSO_CLIENT_SECRET',
        'SLACK_TOKEN',
    ]

    # These are expected to be stored in environment variables when the
    # function is deployed.
    non_secret_cfg_keys = [
        'SSO_AUTH_URL',
        'SSO_AUDIENCE',
        'SSO_GRANT_TYPE',
        'SSO_ID_FORMAT',
        'MOZ_OAUTH_ENDPT',
        'GSUITE_USERS_ENDPT',
        'SLACK_LOOKUP_USER_ENDPT',
        'SLACK_SCIM_USERS_ENDPT',
    ]

    # Only load secrets from SSM if they aren't already stored in env vars.
    if any([os.environ.get(secret) is None for secret in secret_cfg_keys]):
        ssm = boto3.client('ssm')
        parameter = ssm.get_parameter(Name=SECRETS_SSM_PARAMETER)
        pairs = parameter['Parameter']['Value'].split(',')
        secrets = {}

        for pair in pairs:
            (name, value) = pair.split('=')
            secrets[name] = value

        os.environ.update(secrets)

    config = {
        key: os.environ[key]
        for key in non_secret_cfg_keys
    }

    config.update({
        secret: os.environ[secret]
        for secret in secret_cfg_keys
    })

    return config

       
def index(event, context):
    try:
        index_page = static_content('index.html')
    except Exception as ex:
        index_page = ERROR_PAGE.format(ex)

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html',
        },
        'body': index_page,
    }


def static(event, context):
    filename = event.get('pathParameters', {}).get('filename')

    error_404 = {
        'statusCode': 404,
        'body': f'{filename} not found',
    }

    if filename is None or '.' not in filename:
        return error_404

    try:
        content = static_content(filename)
    except:
        return error_404

    ext = filename.split('.')[-1]

    content_types = {
        'css': 'text/css',
        'js': 'application/javascript',
    }

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': content_types[ext],
        },
        'body': content,
    }


def terminate(event, context):
    def error(status, msg):
        return {
            'statusCode': status,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps(
                sesinv.messages.Error(msg).to_json(),
            ),
        }

    try:
        username = json.loads(event['body']).get('username')
    except:
        return error(400, 'Invalid body format. Expected JSON')

    if username is None:
        return error(400, 'Missing `username` field')

    try:
        config = load_config()
    except:
        return error(500, 'Unable to load configuration')

    jobs = sesinv.sessions.configure_jobs(config)

    results = []

    for rp, job in jobs.items():
        result = job(username)

        results.append(sesinv.messages.Status(
            affected_rp=rp,
            current_state=result.new_state,
            output=result.output,
            error=result.error,
        ))

    return {
        'statusCode': 200,
        'body': json.dumps(sesinv.messages.Result(results).to_json()),
    }


if  __name__ == '__main__':
    print(terminate({'body': {'username': 'test@mozilla.com'}}, ''))
