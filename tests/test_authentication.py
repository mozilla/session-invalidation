import string
import unittest

import sesinv.authentication as auth

        
SIGNING_KEY = b'-----BEGIN EC PRIVATE KEY-----\nMF8CAQEEGGIHgr11'\
    b'q2RVEIZmNhUJyrlSV8eWDrBnfaAKBggqhkjOPQMBAaE0AzIA\nBGnwt4Z+U6hwR'\
    b'Ue1uJgfT+GRbK2J7vw2FcTQLpF6ohBZXVlS4O373eGvWFM8IMB/\nLQ==\n----'\
    b'-END EC PRIVATE KEY-----\n'


class TestUserAuthentication(unittest.TestCase):
    def test_generate_auth_cookie(self):
        auth_cookie = auth.generate_auth_cookie(SIGNING_KEY)

        assert auth_cookie.count('_') == 1

        [nonce, signature] = auth_cookie.split('_')

        assert all([c in string.hexdigits for c in nonce])
        assert all([c in string.hexdigits for c in signature])

    def test_user_is_authenticated_validates_good_signatures(self):
        cookie_value = auth.generate_auth_cookie(SIGNING_KEY)

        cookie_header = f'{auth.USER_COOKIE_KEY}={cookie_value}'

        assert auth.user_is_authenticated(SIGNING_KEY, cookie_header)

    def test_user_is_authenticated_invalidates_missing_cookie(self):
        cookie_value = auth.generate_auth_cookie(SIGNING_KEY)

        cookie_header = f'nottherightkey={cookie_value}'

        assert not auth.user_is_authenticated(SIGNING_KEY, cookie_header)
    
    def test_user_is_authenticated_invalidates_poorly_formatted_value(self):
        cookie_header1 = f'{auth.USER_COOKIE_KEY}=too_many_underscores'
        cookie_header2 = f'{auth.USER_COOKIE_KEY}=toofewunderscores'

        assert not auth.user_is_authenticated(SIGNING_KEY, cookie_header1)
        assert not auth.user_is_authenticated(SIGNING_KEY, cookie_header2)
    
    def test_user_is_authenticated_invalidates_invalid_signature(self):
        cookie_header = f'{auth.USER_COOKIE_KEY}=abcdef_123def'

        assert not auth.user_is_authenticated(SIGNING_KEY, cookie_header)
