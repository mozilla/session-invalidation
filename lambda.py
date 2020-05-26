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
    # TODO: Load secrets from SSM and store in env vars. Load remainder from env vars.

    return {
        # SECRETS
        'SSO_CLIENT_ID': '',
        'SSO_CLIENT_SECRET': '',
        'SLACK_TOKEN': '',

        # Non-secrets
        'SSO_AUTH_URL': '',
        'SSO_AUDIENCE': '',
        'SSO_GRANT_TYPE': '',
        'SSO_ID_FORMAT': '',
        'MOZ_OAUTH_ENDPT': 'https://auth-dev.mozilla.auth0.com/api/v2/users/{}/multifactor/actions/invalidate-remember-browser',
        'GSUITE_USERS_ENDPT': 'https://www.googleapis.com/admin/directory/v1/users/{}',
        'SLACK_LOOKUP_USER_ENDPT': 'https://slack.com/api/users.lookupByEmail',
        'SLACK_SCIM_USERS_ENDPT': 'https://api.slack.com/scim/v1/Users',
    }


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
