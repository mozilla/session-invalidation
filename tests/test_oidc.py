import copy
import os
import unittest
from unittest.mock import patch

import requests_mock

import sesinv.oidc as oidc


class TestOIDCClient(unittest.TestCase):
    def test_discovery_document(self):
        discovery_url = 'http://test.oidc.com/.well-known/oidc-configuration'

        with requests_mock.Mocker() as mock:
            mock.get(
                discovery_url,
                json={
                    'test': 123,
                    'jwks_uri': 'http://test.site.com/jwks',
                },
            )

            mock.get(
                'http://test.site.com/jwks',
                json={'keys': [{'a': 1}, {'a': 2}]},
            )

            doc = oidc.discovery_document(discovery_url)

            assert doc['test'] == 123
            assert 'keys' in doc['jwks']
            assert doc['jwks']['keys'][0]['a'] == 1
            assert doc['jwks']['keys'][1]['a'] == 2

            doc = oidc.discovery_document(discovery_url)

            assert doc['test'] == 123
            assert 'keys' in doc['jwks']
            assert doc['jwks']['keys'][0]['a'] == 1
            assert doc['jwks']['keys'][1]['a'] == 2

            # Expect one request for the top-level document then another
            # for the JWKS.  If the caching strategy didn't work we'd see
            # four requests total.
            assert len(mock.request_history) == 2


    def test_authorize_redirect_uri(self):
        required = [
            'state',
            'scope',
            'redirect_uri',
            'client_id',
        ]

        params = {k: 'test' for k in required}

        # Assert that all required fields are checked for
        for req in required:
            test_params = copy.deepcopy(params)
            del test_params[req]

            self.assertRaises(
                oidc.MissingParameters,
                oidc.authorize_redirect_uri,
                'test.site.com/authorize',
                **test_params,
            )

        uri = oidc.authorize_redirect_uri(
            'test.site.com/authorize',
            **params,
        )

        assert uri.startswith('test.site.com/authorize?')

        for k, v in params.items():
            assert f'{k}={v}' in uri

        assert 'response_type=code' in uri

    def test_retrieve_token_checks_parameters(self):
        required = [
            'client_id',
            'client_secret',
            'code',
            'state',
        ]

        params = {k: 'test' for k in required}

        # Assert that all required fields are checked for
        for req in required:
            test_params = copy.deepcopy(params)
            del test_params[req]

            self.assertRaises(
                oidc.MissingParameters,
                oidc.retrieve_token,
                'test.site.com/token',
                'pubkey',
                **test_params,
            )

    @patch('jose.jwt.decode')
    def test_retrieve_token_validates_jwts(self, mock_decode):
        test_jwt = 'headers.claims.signature'

        mock_decode.return_value = 'claims'
        
        required = [
            'client_id',
            'client_secret',
            'code',
            'state',
        ]

        params = {k: 'test' for k in required}

        with requests_mock.Mocker() as mock:
            mock.post('http://test.site.com/token', text=test_jwt)

            jwt_body = oidc.retrieve_token(
                'http://test.site.com/token',
                'pubkey',
                **params,
            )

            mock_decode.assert_called_once_with(test_jwt, 'pubkey')

            assert jwt_body == 'claims'

            history = mock.request_history
            assert len(history) == 1

    @patch('jose.jwt.decode')
    def test_retrieve_token_throws_on_invalid_jwt(self, mock_decode):
        mock_decode.side_effect = oidc.InvalidToken('test')
        
        required = [
            'client_id',
            'client_secret',
            'code',
            'state',
        ]

        params = {k: 'test' for k in required}

        with requests_mock.Mocker() as mock:
            mock.post('http://test.site.com/token', text='jwt_str')
            
            self.assertRaises(
                oidc.InvalidToken,
                oidc.retrieve_token,
                'http://test.site.com/token',
                'pubkey',
                **params,
            )
            
            mock_decode.assert_called_once_with('jwt_str', 'pubkey')
            
            history = mock.request_history
            assert len(history) == 1
