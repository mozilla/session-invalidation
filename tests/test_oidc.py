import copy
import unittest
from unittest.mock import patch

import requests_mock

import sesinv.oidc as oidc


class TestOIDCClient(unittest.TestCase):
    def test_get_openid_config(self):
        with requests_mock.Mocker() as mock:
            mock.get(
                'http://test.site.com/.well-known/openid-configuration',
                json={
                    'token_endpoint': 'test.site.com/token',
                    'authorization_endpoint': 'test.site.com/authorize',
                },
            )

            resp = oidc.get_openid_config(
                'http://test.site.com/.well-known/openid-configuration',
            )

            history = mock.request_history
            assert len(history) == 1

            assert resp['token_endpoint'] == 'test.site.com/token'
            assert resp['authorization_endpoint'] == 'test.site.com/authorize'

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
                **test_params,
            )

    @patch('sesinv.oidc._valid_token')
    def test_retrieve_token_validates_jwts(self, mock_valid_token):
        mock_valid_token.return_value = True
        
        required = [
            'client_id',
            'client_secret',
            'code',
            'state',
        ]

        params = {k: 'test' for k in required}

        with requests_mock.Mocker() as mock:
            mock.post('http://test.site.com/token', text='jwt_str')

            jwt_body = oidc.retrieve_token(
                'http://test.site.com/token',
                **params,
            )

            mock_valid_token.assert_called_once_with('jwt_str')

            assert jwt_body == {}

            history = mock.request_history
            assert len(history) == 1

    @patch('sesinv.oidc._valid_token')
    def test_retrieve_token_throws_on_invalid_jwt(self, mock_valid_token):
        mock_valid_token.return_value = False
        
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
                **params,
            )
            
            mock_valid_token.assert_called_once_with('jwt_str')
            
            history = mock.request_history
            assert len(history) == 1
