import importlib
import os
import unittest
from unittest.mock import patch

import ecdsa
import jwt
import requests_mock

import sesinv

# Since the entrypoints for our lambda functions are in a file named after a
# Python keyword, we import it as follows and give it a non-keyword name.
main = importlib.import_module('lambda')


TEST_RSA_KEY = '-----BEGIN RSA PRIVATE KEY-----'\
    'MIIEpQIBAAKCAQEAutssfQ+HlRwhw+IiK1Nb80kE/dhKa6pYZjxQPjbY9gy8ANQi'\
    '0c9LCds0rIkGgZmVDpNypQrZGDdfM3+7/atQtnU/vMEocde56GyWcoHgBUZgQSi9'\
    'bqLxH2LU+ExJ1/DN0y1pkVgrhSpBtT6XCMBPic7NaqcFHCgPbyvd052xLWnWyCsl'\
    'l4HXVdqkyGVcaw5SDF1755tauUxPxi9UM5VCt/3GCTj2sJXEuGUv1DZF+ptV/eOV'\
    'dokk3AfNKIVG9JNQjDAgFjr9FWxoDzlQ+fr0uzFhhYLsl7ls/LEvnaossWsICLbS'\
    'BlEvWqJe8SwKiFanIKqU0u6TSVQYI8KCp5YLGQIDAQABAoIBAQCeJ1BaccCCNpNl'\
    'porhPOcA3fb5nA4xXrb/oWERp36vk0u1L9hg2SFcMEs/FaOKIiIFekt44duqIYPU'\
    'pPLK3Cuuo0LVUnAXG05hKTeVp9Oi41QpEoBzmjqYJCC6IGgH++taKH/H42bCiWeg'\
    'Ll/Lqmon6//1m3Q5xrZ5lBlnOXtzQUQsBV6YCJ2jtrkxdRagSFzhFla8w/M8dYhd'\
    'CCWkwL95RpvUGs8eZvD7jTXtpBCfQzf7r9L7jMbQuf2ujjvd68hL8j5pSiqHGje8'\
    'eWOUcMu0aUQHFz6jdr2x7Nco5JQxa8MHPbLUrC34c6XgDj8B5hTIQk0dxWiIzZvq'\
    'jmVvbK1ZAoGBAO9DVnUITtdgOFYX4kmbob/EqstRHySXABTBrzlRslWsJnT606SU'\
    'Ve0zmN2fa2/dY7SqDWdoc2HVBzeIRk7NMzOdcL1X8Qi9vtPWWcRCElEjxGT/rMqj'\
    'bxeUU4gvuOwgBjue06Q1s9gDmoDUeLUwy4zzYSBBWJVw3MCyXW1kqupfAoGBAMft'\
    'WL5XxCV/TQ2NERIaOKCsKcwbc9bzOreO6hLwsvlU4R+NIgbeiTAgZBYyWKqpUHHJ'\
    'puispIrWCqAEQ9Tr3q+aGqJLpZ7dZuY9GHHJEOQt0YBdk97DpmZQeb7r7UJ/P1Jd'\
    '+iJZaTS5R2XOjpU9+HyDl/rLTM3GDR3wHXKIlm2HAoGBANSlHkPpXFjitW8ezwjo'\
    'fvs2ySzmLi2Q3ouUEC17RGoMFCnHey48f5nPT784nn3PX3wD3uHW3SVH9aAPR51l'\
    'lmn7NWWysRA5w032pdVde3YNudChw2pdkrB8LTlOYKXLWH7IjATXjb0ghsKVE6rF'\
    'cUMWU24dZaN7qVbBr3M4Ewc1AoGBAK6c/rAoCXlSiOK3/VvZKPIzy8GnjHIFN5hQ'\
    'KuJl9XrMhl6/LiPfwuQUtjWovUY44LixDaUT/BYCQX9mmjPh2jl2l6J9/WYWKyQV'\
    '4j6nBKi118+Ma3TZXoDn8p0sg6lbZ9uxlqDfhIJ2/APP9zojyN4/NMLnQupJ+vTV'\
    '3XJGF1QLAoGAE34Npeihs2GTShEMuhEk0mlSRcF2kqCVz5b4B8hSVEAsdNH+f/Sd'\
    'SMFuu+2cHe9Ly44c69ryrKYxyLSROV6DpL9LNHGpuTq9lQbnfEBr4w0emKqUF4Hj'\
    'XxagBmJ+7E7JfGIvrQA2yx7SlymF3GjJGisoEqASWySrbMZHOznAPnk='\
    '-----END RSA PRIVATE KEY-----'


def load_test_env_vars(**kwargs):
    keys = [
        'OIDC_CLIENT_ID',
        'OIDC_DISCOVERY_URI',
        'OIDC_SCOPES',
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
    ]

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
            'jwks_uri': 'http://test.site.com/jwks',
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
        assert discovery_doc['authorization_endpoint'] in location
        assert 'state' in location
        assert 'scope' in location
        assert 'redirect_uri' in location
        assert 'client_id' in location

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

    @patch('lambda.load_config')
    def test_redirect_to_index_upon_token_retrieval(self, load_config_mock):
        load_config_mock.return_value = load_test_env_vars(
            OIDC_DISCOVERY_URI=
                'http://test.token.com/.well-known/oidc-configuration',
        )

        event = {
            'queryStringParameters': {
                'state': 'abc123',
                'code': 'def987',
            },
            'headers': {
                'Cookie': f'{main.USER_STATE_COOKIE_KEY}=abc123',
            },
        }

        discovery_doc = {
            'authorization_endpoint': 'http://test.token.com/token',
            'jwks_uri': 'http://test.token.com/jwks',
            'token_endpoint': 'http://test.token.com/token',
        }

        test_jwt = jwt.encode(
            {'username': 'tester@mozilla.com'}, 
            TEST_RSA_KEY,
            algorithm='RS256',
        )

        with requests_mock.Mocker() as mock:
            mock.get(os.environ['OIDC_DISCOVERY_URI'], json=discovery_doc)
            mock.get(discovery_doc['jwks_uri'], json=TEST_RSA_KEY)
            mock.get(discovery_doc['token_endpoint'], text=test_jwt)

            response = main.callback(event, None)

        assert response['statusCode'] == 302
        assert response['headers'].get('Location') == '/dev'
        assert main.USER_JWT_COOKIE_KEY in response['headers']['Set-Cookie']
        assert main.USER_SESSION_COOKIE_KEY in response['headers']['Set-Cookie']

    @patch('lambda.load_config')
    def test_error_upon_no_token_retrieval(self, load_config_mock):
        load_config_mock.return_value = load_test_env_vars(
            OIDC_DISCOVERY_URI=
                'http://test.token.com/.well-known/oidc-configuration',
        )

        event = {
            'queryStringParameters': {
                'state': 'abc123',
                'code': 'def987',
            },
            'headers': {
                'Cookie': f'{main.USER_STATE_COOKIE_KEY}=abc123',
            },
        }

        discovery_doc = {
            'authorization_endpoint': 'http://test.token.com/token',
            'jwks_uri': 'http://test.token.com/jwks',
            'token_endpoint': 'http://test.token.com/token',
        }

        with requests_mock.Mocker() as mock:
            mock.get(os.environ['OIDC_DISCOVERY_URI'], json=discovery_doc)
            mock.get(discovery_doc['jwks_uri'], json=TEST_RSA_KEY)
            mock.get(discovery_doc['token_endpoint'], status_code=400)

            response = main.callback(event, None)

        cookies = response['headers']['Set-Cookie']

        assert response['statusCode'] == 400
        assert main.USER_JWT_COOKIE_KEY not in cookies
        assert main.USER_SESSION_COOKIE_KEY not in cookies
    
    @patch('lambda.load_config')
    def test_error_upon_invalid_jwt(self, load_config_mock):
        load_config_mock.return_value = load_test_env_vars(
            OIDC_DISCOVERY_URI=
                'http://test.token.com/.well-known/oidc-configuration',
        )

        event = {
            'queryStringParameters': {
                'state': 'abc123',
                'code': 'def987',
            },
            'headers': {
                'Cookie': f'{main.USER_STATE_COOKIE_KEY}=abc123',
            },
        }

        discovery_doc = {
            'authorization_endpoint': 'http://test.token.com/token',
            'jwks_uri': 'http://test.token.com/jwks',
            'token_endpoint': 'http://test.token.com/token',
        }

        test_jwt = 'invalid.json.webtoken'

        with requests_mock.Mocker() as mock:
            mock.get(os.environ['OIDC_DISCOVERY_URI'], json=discovery_doc)
            mock.get(discovery_doc['jwks_uri'], json=TEST_RSA_KEY)
            mock.get(discovery_doc['token_endpoint'], text=test_jwt)

            response = main.callback(event, None)

        cookies = response['headers']['Set-Cookie']

        assert response['statusCode'] == 400
        assert main.USER_JWT_COOKIE_KEY in cookies
        assert main.USER_SESSION_COOKIE_KEY in cookies
