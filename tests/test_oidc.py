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
