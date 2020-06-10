import importlib
import os
import unittest
from unittest.mock import patch

import ecdsa
import requests_mock

import sesinv

# Since the entrypoints for our lambda functions are in a file named after a
# Python keyword, we import it as follows and give it a non-keyword name.
main = importlib.import_module('lambda')


def load_test_env_vars(**kwargs):
    keys = {
        'SSO_CLIENT_SECRET',
        'SLACK_TOKEN',
        'SIGNING_KEY_ECDSA',
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
    }

    defaults = {k: '' for k in keys}

    defaults.update(kwargs)

    os.environ.update(defaults)

    return defaults


@patch('lambda.log', lambda _, __: None)
class TestOIDCClientFlow(unittest.TestCase):
    '''Unit tests for the OIDC client flow which is facilitated by the
    session invalidation application's own API.

    Here, requests_mock is used to mock the behaviour of an OP and the client
    is simulated by manually constructing events.
    '''

    @patch('lambda.load_config')
    def test_redirect_to_op_authorize_endpoint(self, load_config_mock):
        load_config_mock.return_value = load_test_env_vars(
            OIDC_DISCOVERY_URI=\
                'http://test.site.com/.well-known/oidc-configuration',
        )

        event = {
            'headers': {},
        }

        discovery_doc = {
            'authorization_endpoint': 'http://test.site.com/authorize',
            'jwks_uri': 'htttp://test.site.com/jwks',
        }

        jwks_doc = {
            'keys': [
                {
                    'a': 1,
                },
                {
                    'a': 2,
                },
            ]
        }

        with requests_mock.Mocker() as mock:
            mock.get(os.environ['OIDC_DISCOVERY_URI'], json=discovery_doc)
            mock.get(discovery_doc['jwks_uri'], json=jwks_doc)

            response = main.index(event, None)

        location = response['headers']['Location']

        assert response['statusCode'] == 302
        assert location == discovery_doc['authorization_endpoint']

    @patch('lambda.load_config')
    def test_no_redirect_for_authenticated_user(self, load_config_mock):
        load_config_mock.return_value = load_test_env_vars(
            SIGNING_KEY_ECDSA=ecdsa.SigningKey.generate().to_string().hex(),
        )

        session_token = sesinv.authentication.generate_auth_cookie(
            os.environ['SIGNING_KEY_ECDSA'],
        )

        event = {
            'headers': {
                'Cookie': f'{main.USER_SESSION_COOKIE_KEY}={session_token}',
            },
        }

        response = main.index(event, None)

        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'text/html'
