import importlib
import os
import unittest
from unittest.mock import patch

from authlib.jose import jwk
from authlib.jose import jwt
import ecdsa
import requests_mock

import sesinv

# Since the entrypoints for our lambda functions are in a file named after a
# Python keyword, we import it as follows and give it a non-keyword name.
main = importlib.import_module('lambda')


TEST_RSA_KEY = b'-----BEGIN RSA PRIVATE KEY-----\n'\
    b'MIIEpQIBAAKCAQEAutssfQ+HlRwhw+IiK1Nb80kE/dhKa6pYZjxQPjbY9gy8ANQi\n'\
    b'0c9LCds0rIkGgZmVDpNypQrZGDdfM3+7/atQtnU/vMEocde56GyWcoHgBUZgQSi9\n'\
    b'bqLxH2LU+ExJ1/DN0y1pkVgrhSpBtT6XCMBPic7NaqcFHCgPbyvd052xLWnWyCsl\n'\
    b'l4HXVdqkyGVcaw5SDF1755tauUxPxi9UM5VCt/3GCTj2sJXEuGUv1DZF+ptV/eOV\n'\
    b'dokk3AfNKIVG9JNQjDAgFjr9FWxoDzlQ+fr0uzFhhYLsl7ls/LEvnaossWsICLbS\n'\
    b'BlEvWqJe8SwKiFanIKqU0u6TSVQYI8KCp5YLGQIDAQABAoIBAQCeJ1BaccCCNpNl\n'\
    b'porhPOcA3fb5nA4xXrb/oWERp36vk0u1L9hg2SFcMEs/FaOKIiIFekt44duqIYPU\n'\
    b'pPLK3Cuuo0LVUnAXG05hKTeVp9Oi41QpEoBzmjqYJCC6IGgH++taKH/H42bCiWeg\n'\
    b'Ll/Lqmon6//1m3Q5xrZ5lBlnOXtzQUQsBV6YCJ2jtrkxdRagSFzhFla8w/M8dYhd\n'\
    b'CCWkwL95RpvUGs8eZvD7jTXtpBCfQzf7r9L7jMbQuf2ujjvd68hL8j5pSiqHGje8\n'\
    b'eWOUcMu0aUQHFz6jdr2x7Nco5JQxa8MHPbLUrC34c6XgDj8B5hTIQk0dxWiIzZvq\n'\
    b'jmVvbK1ZAoGBAO9DVnUITtdgOFYX4kmbob/EqstRHySXABTBrzlRslWsJnT606SU\n'\
    b'Ve0zmN2fa2/dY7SqDWdoc2HVBzeIRk7NMzOdcL1X8Qi9vtPWWcRCElEjxGT/rMqj\n'\
    b'bxeUU4gvuOwgBjue06Q1s9gDmoDUeLUwy4zzYSBBWJVw3MCyXW1kqupfAoGBAMft\n'\
    b'WL5XxCV/TQ2NERIaOKCsKcwbc9bzOreO6hLwsvlU4R+NIgbeiTAgZBYyWKqpUHHJ\n'\
    b'puispIrWCqAEQ9Tr3q+aGqJLpZ7dZuY9GHHJEOQt0YBdk97DpmZQeb7r7UJ/P1Jd\n'\
    b'+iJZaTS5R2XOjpU9+HyDl/rLTM3GDR3wHXKIlm2HAoGBANSlHkPpXFjitW8ezwjo\n'\
    b'fvs2ySzmLi2Q3ouUEC17RGoMFCnHey48f5nPT784nn3PX3wD3uHW3SVH9aAPR51l\n'\
    b'lmn7NWWysRA5w032pdVde3YNudChw2pdkrB8LTlOYKXLWH7IjATXjb0ghsKVE6rF\n'\
    b'cUMWU24dZaN7qVbBr3M4Ewc1AoGBAK6c/rAoCXlSiOK3/VvZKPIzy8GnjHIFN5hQ\n'\
    b'KuJl9XrMhl6/LiPfwuQUtjWovUY44LixDaUT/BYCQX9mmjPh2jl2l6J9/WYWKyQV\n'\
    b'4j6nBKi118+Ma3TZXoDn8p0sg6lbZ9uxlqDfhIJ2/APP9zojyN4/NMLnQupJ+vTV\n'\
    b'3XJGF1QLAoGAE34Npeihs2GTShEMuhEk0mlSRcF2kqCVz5b4B8hSVEAsdNH+f/Sd\n'\
    b'SMFuu+2cHe9Ly44c69ryrKYxyLSROV6DpL9LNHGpuTq9lQbnfEBr4w0emKqUF4Hj\n'\
    b'XxagBmJ+7E7JfGIvrQA2yx7SlymF3GjJGisoEqASWySrbMZHOznAPnk=\n'\
    b'-----END RSA PRIVATE KEY-----'


MOZILLA_JWKS = {"keys":[{"alg":"RS256","kty":"RSA","use":"sig","n":"vjNpfXjopFWoafXUZEFYpM4i2suIN4DFNvq2X5wmob4dNbNPgweDUw-eW7_qE4YqL8iiZfxpabatGt4mk9MdlRwVfLKPxVRgNiQsp8RDNaexm6Us5bxgj6BoYIlEBg786DpT0nwl6YgjFE6luvGKwVhaMsQrhxzGQdUe-Cs3WcqaTg_17bv0zausy7dkVudeUdTkK-1mm0a5O5W6FccwuE_0UQU_NWzSm5ksj8bO30eJdZVbsOCwICe2i_N2mOomF9i2NYkivq4foLYINEFpS_17pfYzvx3RuOJTeRTNIszxd2H3y14ZPtNpy4TczZDTw3631NygUjpEMEAsEe61mw","e":"AQAB","kid":"MkZDNDcyRkNGRTFDNjlBNjZFOEJBN0ZBNzJBQTNEMDhCMEEwNkFGOA","x5t":"MkZDNDcyRkNGRTFDNjlBNjZFOEJBN0ZBNzJBQTNEMDhCMEEwNkFGOA","x5c":["MIIC9DCCAdygAwIBAgIJRtdiVzA6xfxrMA0GCSqGSIb3DQEBBQUAMCExHzAdBgNVBAMTFmF1dGgubW96aWxsYS5hdXRoMC5jb20wHhcNMTYxMDA1MTgyMzE5WhcNMzAwNjE0MTgyMzE5WjAhMR8wHQYDVQQDExZhdXRoLm1vemlsbGEuYXV0aDAuY29tMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvjNpfXjopFWoafXUZEFYpM4i2suIN4DFNvq2X5wmob4dNbNPgweDUw+eW7/qE4YqL8iiZfxpabatGt4mk9MdlRwVfLKPxVRgNiQsp8RDNaexm6Us5bxgj6BoYIlEBg786DpT0nwl6YgjFE6luvGKwVhaMsQrhxzGQdUe+Cs3WcqaTg/17bv0zausy7dkVudeUdTkK+1mm0a5O5W6FccwuE/0UQU/NWzSm5ksj8bO30eJdZVbsOCwICe2i/N2mOomF9i2NYkivq4foLYINEFpS/17pfYzvx3RuOJTeRTNIszxd2H3y14ZPtNpy4TczZDTw3631NygUjpEMEAsEe61mwIDAQABoy8wLTAMBgNVHRMEBTADAQH/MB0GA1UdDgQWBBQ65IC4b00/BYf9gERAruDxIfYVFTANBgkqhkiG9w0BAQUFAAOCAQEAjF/4SPbFOwy3ZPUuhSej2JymgZVceqbjtCSvLM32L0hgHTJAxBeIn5uLhWTH2/tXl6rtZlrhGJZ02gUwot+tY9CVbyoADyAwt6QBdvcunGC33lm53zuMe57ao66VOFDZpC8dKAXMUtuRNK19RdIKuYiBjCffQXmZLwsXLXrH7oqBa/DfLOCfE7rGIrtTIG6cv1lk/QRNqvnshQvUPqUA/dwjxNpgpCCmOKs5T11YMJDwXoVGuDvqDQ8nx32lcO7kIsFcsW2gCAUI6kHQFluqObbAyQJseA/laSNjMpDTYanMdHWHen4rjFolHBeJJwCPcfdmVDzN5O9hkJvCU6D5+Q=="]}]}

def load_test_env_vars(**kwargs):
    keys = [
        'OIDC_CLIENT_SECRET',
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
    @patch('jose.jwt.decode')
    def test_redirect_to_index_upon_token_retrieval(
        self,
        jwt_decode_mock,
        load_config_mock,
    ):
        load_config_mock.return_value = load_test_env_vars(
            OIDC_DISCOVERY_URI=
                'http://test.token.com/.well-known/oidc-configuration',
            SIGNING_KEY_ECDSA=
                ecdsa.SigningKey.generate().to_string().hex(),
        )

        jwt_decode_mock.return_value = 'jwt-claims'

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

        key_data = jwk.dumps(TEST_RSA_KEY, kty='RSA')

        test_jwt = jwt.encode(
            {'alg': 'RS256'},
            {'username': 'tester@mozilla.com'}, 
            key_data,
        ).decode('utf-8')

        with requests_mock.Mocker() as mock:
            mock.get(os.environ['OIDC_DISCOVERY_URI'], json=discovery_doc)
            #mock.get(discovery_doc['jwks_uri'], text=TEST_RSA_KEY.decode('utf-8'))
            mock.get(discovery_doc['jwks_uri'], json={
                'keys': [
                    key_data,
                ],
            })
            mock.post(discovery_doc['token_endpoint'], text=test_jwt)

            response = main.callback(event, None)

        assert response['statusCode'] == 302
        assert response['headers'].get('Location') == '/dev'
        assert main.USER_JWT_COOKIE_KEY in response['headers']['Set-Cookie']
        assert main.USER_SESSION_COOKIE_KEY in response['headers']['Set-Cookie']

'''
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

        assert response['statusCode'] == 400
        assert 'Set-Cookie' not in response['headers']
    
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

        assert response['statusCode'] == 400
        assert 'Set-Cookie' not in response['headers']
'''
