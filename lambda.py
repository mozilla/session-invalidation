from http import cookies
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

USER_SESSION_COOKIE_KEY = 'user-session'
USER_JWT_COOKIE_KEY = 'user-jwt'
USER_STATE_COOKIE_KEY = 'user-state'

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
        'OIDC_CLIENT_SECRET',
        'SSO_CLIENT_SECRET',
        'SLACK_TOKEN',
        'SIGNING_KEY_ECDSA',
    ]

    # These are expected to be stored in environment variables when the
    # function is deployed.
    non_secret_cfg_keys = [
        'SELF_DOMAIN',
        'OIDC_CLIENT_ID',
        'OIDC_DISCOVERY_URI',
        'OIDC_SCOPES',
        'SSO_CLIENT_ID',
        'SSO_AUTH_URL',
        'SSO_AUDIENCE',
        'SSO_GRANT_TYPE',
        'SSO_ID_FORMAT',
        'SQS_QUEUE_URL',
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


def user_is_authenticated(cookie_header: str) -> bool:
    '''Veirfy that there is a `USER_SESSION_COOKIE_KEY` key in the user's
    cookie and that it contains a valid, signed nonce value generated as a
    result of completing authentication.
    '''
    
    cookie = cookies.SimpleCookie()
    cookie.load(cookie_header)
    morsel = cookie.get(USER_SESSION_COOKIE_KEY)

    if morsel is None:
        return False

    config = load_config()

    return sesinv.authentication.validate_auth_cookie(
        config['SIGNING_KEY_ECDSA'],
        morsel.value,
    )


def echo(event, context):
    '''Echo the event data received.
    '''

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
        },
        'body': json.dumps(event),
    }


def index(event, context):
    '''Serve the index page.
    '''

    log('Session Invalidation application requested', logging.INFO)

    cookie_str = event.get('headers', {}).get('cookie', '')

    try:
        if user_is_authenticated(cookie_str):
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'text/html',
                },
                'body': static_content('index.html'),
            }
        else:
            discovery = sesinv.oidc.discovery_document(
                os.environ['OIDC_DISCOVERY_URI'],
            )

            state = os.urandom(32).hex()

            authorize_endpoint = sesinv.oidc.authorize_redirect_uri(
                discovery['authorization_endpoint'],
                state=state,
                scope=os.environ['OIDC_SCOPES'],
                redirect_uri=f'{os.environ["SELF_DOMAIN"]}/callback',
                client_id=os.environ['OIDC_CLIENT_ID'],
            )

            return {
                'statusCode': 302,
                'headers': {
                    'Content-Type': 'text/plain',
                    'Location': authorize_endpoint,
                    'Set-Cookie': f'{USER_STATE_COOKIE_KEY}={state}',
                },
                'body': 'Redirecting to authentication callback (TODO: OIDC)',
            }
    except Exception as ex:
        log(f'Failed to load index page from S3: {ex}', logging.CRITICAL)

        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'text/html',
            },
            'body': ERROR_PAGE.format(ex),
        }


def callback(event, context):
    '''Handle redirects back to the applciation by the OIDC Provider (OP).
    '''

    code = event.get('queryStringParameters', {}).get('code')
    state = event.get('queryStringParameters', {}).get('state')

    if code is None or state is None:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'text/plain',
            },
            'body': 'Missing required parameter(s) `code` or `state`',
        }

    cookie = cookies.SimpleCookie()
    cookie.load(event['headers'].get('cookie', ''))

    stored_state = cookie.get(USER_STATE_COOKIE_KEY)

    if stored_state is not None and stored_state.value != state:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'text/plain',
            },
            'body': 'Invalid state parameter',
        }

    try:
        config = load_config()
        discovery = sesinv.oidc.discovery_document(
            os.environ['OIDC_DISCOVERY_URI'],
        )
    except Exception as ex:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'text/plain',
            },
            'body': 'Failed to load configuration or oidc-configuration',
        }

    try:
        token = sesinv.oidc.retrieve_token(
            discovery['token_endpoint'],
            discovery['jwks'],
            config['OIDC_CLIENT_ID'],
            client_id=config['OIDC_CLIENT_ID'],
            client_secret=config['OIDC_CLIENT_SECRET'],
            code=code,
            state=state,
            redirect_uri=f'{os.environ["SELF_DOMAIN"]}/callback',
        )
    except sesinv.oidc.InvalidToken as tkn_err:
        log(f'Token validation failed: {tkn_err}', logging.ERROR)

        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'text/plain',
            },
            'body': 'Authentication failed',
        }
    except Exception as ex:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'text/plain',
            },
            'body': 'Failed to retrieve credentials',
        }

    user_token = sesinv.authentication.generate_auth_cookie(
        config['SIGNING_KEY_ECDSA'],
    )

    set_cookies = [
        f'{USER_SESSION_COOKIE_KEY}={user_token}',
        f'{USER_JWT_COOKIE_KEY}={json.dumps(token)}',
        'Max-Age=86400',
    ]

    return {
        'statusCode': 302,
        'headers': {
            'Content-Type': 'text/plain',
            'Location': os.environ['SELF_DOMAIN'],
            'Set-Cookie': '; '.join(set_cookies),
        },
        'body': 'Redirecting to application index.',
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
    
    cookie_str = event.get('headers', {}).get('cookie', '')

    try:
        if not user_is_authenticated(cookie_str):
            return {
                'statusCode': 403,
                'headers': {
                    'Content-Type': 'application/json',
                },
                'body': '{"error": "Forbidden"}',
            }

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
