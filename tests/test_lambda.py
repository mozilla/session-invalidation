import importlib
import os
import unittest
from unittest.mock import patch

import requests_mock

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


@patch('lambda.log', lambda _, __: None)
class TestOIDCClientFlow(unittest.TestCase):
    '''Unit tests for the OIDC client flow which is facilitated by the
    session invalidation application's own API.

    Here, requests_mock is used to mock the behaviour of an OP and the client
    is simulated by manually constructing events.
    '''

    def test_redirect_to_op_authorize_endpoint(self):
        event = {
            'headers': {},
            'body': '',
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

        load_test_env_vars(
            OIDC_DISCOVERY_URI=\
                'http://test.site.com/.well-known/oidc-configuration',
        )

        with requests_mock.Mocker() as mock:
            mock.get(os.environ['OIDC_DISCOVERY_URI'], json=discovery_doc)
            mock.get(discovery_doc['jwks_uri'], json=jwks_doc)

            response = main.index(event, None)

        location = response['headers']['Location']

        assert response['statusCode'] == 302
        assert location == discovery_doc['authorization_endpoint']
