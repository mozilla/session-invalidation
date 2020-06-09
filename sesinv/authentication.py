from dataclasses import dataclass, field
from datetime import datetime, timedelta
from http import cookies
import os
import typing as types

import ecdsa
import requests


USER_COOKIE_KEY = 'user_session'


class Error(Exception):
    '''A generic container type for an error message that can be raised during
    the process of attempting to perform authentication.
    '''

    def __init__(self, message: str, causes: types.List):
        super().__init__(message)

        self.message = message
        self.causes = causes


@dataclass
class SSOCreds:
    '''A manager interface for an OAuth token used to call into the Auth0 API.
    Given a client id and secret, this class provides a `token()` method that
    will load and refresh a token after it expires.
    '''

    client_id: str
    client_secret: str
    auth_url: str
    audience: str
    grant_type: str
    _token: types.Optional[str] = field(default=None)
    _expires: types.Optional[datetime] = field(default=None)

    def token(self) -> str:
        '''Retrieve an access token with which to access the Auth0 API.
        '''

        now = datetime.utcnow() 

        expired = self._expires is not None and now < self._expires

        if self._token is None or expired:
            self._authenticate()

        return self._token

    def _authenticate(self):
        try:
            response = requests.post(
                self.auth_url,
                json={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'audience': self.audience,
                    'grant_type': self.grant_type,
                },
            )
        except Exception as ex:
            raise Error('Failed to authenticate', [ex])

        try:
            resp_json = response.json()
        except Exception as ex:
            raise Error('Got unexpected response body', [ex])

        if 'expires_in' not in resp_json or 'access_token' not in resp_json:
            raise Error('Response missing expected fields', [])

        valid_for = timedelta(seconds=resp_json['expires_in'])

        self._token = resp_json['access_token']

        self._expires = datetime.utcnow() + valid_for


def generate_auth_cookie(signing_key_pem: str) -> str:
    '''Generate a random string and sign it.  Produces a cryptographically
    secure value that can be stored in a user's cookies and tested in
    future requests.
    '''

    nonce = os.urandom(32)

    signing_key = ecdsa.SigningKey.from_pem(signing_key_pem)

    signature = signing_key.sign(nonce)

    return f'{nonce.hex()}_{signature.hex()}'


def validate_auth_cookie(signing_key_pem: str, auth_cookie: str) -> bool:
    '''Validate the signature of a token stored in a user's cookie.
    '''

    parts = auth_cookie.split('_')

    if len(parts) != 2:
        return False

    [nonce_str, signature_str] = parts
    nonce = bytearray.fromhex(nonce_str)
    signature = bytearray.fromhex(signature_str)

    signing_key = ecdsa.SigningKey.from_pem(signing_key_pem)
    verifying_key = signing_key.verifying_key

    try:
        return verifying_key.verify(signature, nonce)
    except ecdsa.keys.BadSignatureError:
        return False
