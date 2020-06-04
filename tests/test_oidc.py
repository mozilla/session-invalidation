import copy
import unittest

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
