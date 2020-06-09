import json
import logging
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


logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'DEBUG'))
logging.getLogger('boto3').propagate = False
logging.getLogger('botocore').propagate = False


def log(message, level=logging.DEBUG, username=None, result=None):
    '''Write a log message and an instrumentation event to SQS.
    '''

    level_name = {
        logging.NOTSET: 'notset',
        logging.DEBUG: 'debug',
        logging.INFO: 'info',
        logging.WARNING: 'warning',
        logging.ERROR: 'error',
        logging.CRITICAL: 'critical',
    }.get(level, 'info')

    logger.log(level, message)

    message = {
        'category': 'sessioninvalidation',
        'details': {
            'logmessage': message,
            'loglevel': level_name,
            'invalidateduser': None,
            'invalidatedsessions': None,
        },
    }

    if username is not None:
        message['details']['invalidateduser'] = username

    if result is not None:
        message['details']['invalidatedsessions'] = [
            res.affected_rp.value
            for res in result.results
            if res.current_state == sesinv.sessions.TerminationState.TERMINATED
        ]

    sqs = boto3.client('sqs')

    sqs.send_message(
        QueueUrl=os.environ['SQS_QUEUE_URL'],
        MessageBody=json.dumps(message),
    )


def static_content(filename):
    '''Load a static file from S3 and save it to the /tmp directory.
    On future requests for the same file, it will be loaded from disk.
    '''

    s3 = boto3.resource('s3')
    static_content = s3.Bucket(STATIC_CONTENT_BUCKET_NAME)

    file_path = f'/tmp/{filename}'

    if not os.path.isfile(file_path):
        with open(file_path, 'wb') as f:
            static_content.download_fileobj(filename, f)

    with open(file_path, 'rb') as f:
        return f.read()


def load_config():
    '''Retrieve secrets from SSM Parameter Store and save them in environment
    variables for future retrieval.  Merge these with non-secret configuration
    values from other environment variables.
    '''

    # These are expected to be found in SSM and then loaded into environment
    # variables to avoid reading from SSM too often.  Env vars are encrypted.
    secret_cfg_keys = [
        'SSO_CLIENT_ID',
        'SSO_CLIENT_SECRET',
        'SLACK_TOKEN',
        'SIGNING_KEY_ECDSA',
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
    '''Serve the index page.
    '''

    log('Session Invalidation application requested', logging.INFO)

    try:
        index_page = static_content('index.html')
    except Exception as ex:
        log(f'Failed to load index page from S3: {ex}', logging.CRITICAL)
        index_page = ERROR_PAGE.format(ex)

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html',
        },
        'body': index_page,
    }


def static(event, context):
    '''Serve static CSS and JavaScript files.
    '''

    filename = event.get('pathParameters', {}).get('filename')

    error_404 = {
        'statusCode': 404,
        'body': f'{filename} not found',
    }

    log(f'Static file {filename} requested', logging.INFO)

    if filename is None or '.' not in filename:
        log(f'Static file {filename} not valid', logging.ERROR)
        return error_404

    try:
        content = static_content(filename)
    except:
        log(f'Static file {filename} not found', logging.ERROR)
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
    '''Terminate a user's sessions across supported reliant parties.
    '''

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
        log('Invalid request sent to terminate endpoint', logging.ERROR)
        return error(400, 'Invalid body format. Expected JSON')

    if username is None:
        log(
            'Request sent to terminate endpoint with missing username',
            logging.ERROR,
        )
        return error(400, 'Missing `username` field')

    log(f'Request to terminate sessions for {username}', logging.WARNING)

    try:
        config = load_config()
    except Exception as ex:
        log('Failed to load configuration: {ex}', logging.CRITICAL)
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

    result = sesinv.messages.Result(results)

    log(
        f'Terminated sessions for {username}',
        logging.WARNING,
        username=username,
        result=result,
    )

    return {
        'statusCode': 200,
        'body': json.dumps(result.to_json()),
    }


if  __name__ == '__main__':
    os.environ.update({
        'MOZ_OAUTH_ENDPT': 'https://auth-dev.mozilla.auth0.com/api/v2/users/{}/multifactor/actions/invalidate-remember-browser',
        'GSUITE_USERS_ENDPT': 'https://www.googleapis.com/admin/directory/v1/users/{}',
        'SLACK_LOOKUP_USER_ENDPT': 'https://slack.com/api/users.lookupByEmail',
        'SLACK_SCIM_USERS_ENDPT': 'https://api.slack.com/scim/v1/Users',
        'SSO_ID_FORMAT': 'ad|Mozilla-LDAP-Dev|{}',
        'SSO_AUTH_URL': 'https://auth-dev.mozilla.auth0.com/oauth/token',
        'SSO_AUDIENCE': 'https://auth-dev.mozilla.auth0.com/api/v2/',
        'SSO_GRANT_TYPE': 'client_credentials',
    })
    print(load_config())
