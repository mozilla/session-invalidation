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

    def test_validate_auth_cookie_validates_good_signatures(self):
        auth_cookie = auth.generate_auth_cookie(SIGNING_KEY)

        assert auth.validate_auth_cookie(SIGNING_KEY, auth_cookie)

    def test_validate_auth_cookie_invalidates_poorly_formatted_value(self):
        auth_cookie1 = f'too_many_underscores'
        auth_cookie2 = f'toofewunderscores'

        assert not auth.validate_auth_cookie(SIGNING_KEY, auth_cookie1)
        assert not auth.validate_auth_cookie(SIGNING_KEY, auth_cookie2)
    
    def test_validate_auth_cookie_invalidates_invalid_signature(self):
        auth_cookie = f'abcdef_123def'

        assert not auth.validate_auth_cookie(SIGNING_KEY, auth_cookie)
