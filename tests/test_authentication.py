import string
import unittest

import sesinv.authentication as auth


# Generated with `ecdsa.SigningKey.generate().to_string().hex()`.
SIGNING_KEY = '9abf8f73a7731d164e925520eac9a450263810a37d6ac446'


class TestUserAuthentication(unittest.TestCase):
    def test_generate_auth_cookie(self):
        auth_cookie = auth.generate_auth_cookie('testdata', SIGNING_KEY)

        assert auth_cookie.count('&') == 2

        [data, nonce, signature] = auth_cookie.split('&')

        assert data == 'testdata'
        assert all([c in string.hexdigits for c in nonce])
        assert all([c in string.hexdigits for c in signature])

    def test_validate_auth_cookie_validates_good_signatures(self):
        auth_cookie = auth.generate_auth_cookie('testdata', SIGNING_KEY)

        out = auth.validate_auth_cookie(SIGNING_KEY, auth_cookie)
        assert out == 'testdata'

    def test_validate_auth_cookie_invalidates_poorly_formatted_value(self):
        auth_cookie1 = f'too&many&amper&sands'
        auth_cookie2 = f'too&fewampersands'

        assert auth.validate_auth_cookie(SIGNING_KEY, auth_cookie1) is None
        assert auth.validate_auth_cookie(SIGNING_KEY, auth_cookie2) is None
    
    def test_validate_auth_cookie_invalidates_invalid_signature(self):
        auth_cookie = f'testdata&abcdef&123def'

        assert auth.validate_auth_cookie(SIGNING_KEY, auth_cookie) is None
