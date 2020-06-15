from dataclasses import dataclass, field
from datetime import datetime, timedelta
import os
import typing as types

import ecdsa
import requests


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


def generate_auth_cookie(data: str, signing_key_hex: str) -> str:
    '''Pairs a piece of data with a randomly-generated nonce and appends
    a signature.  The format of the output is `<data>&<nonce>&<signature>`
    and parsing is dependent on the `&` character as a vaid delimiter.
    '''

    nonce = os.urandom(32)

    signing_key = ecdsa.SigningKey.from_string(
        bytearray.fromhex(signing_key_hex),
    )

    signature = signing_key.sign(nonce)

    return f'{data}&{nonce.hex()}&{signature.hex()}'


def validate_auth_cookie(
    signing_key_hex: str,
    auth_cookie: str,
) -> types.Optional[str]:
    '''Validates the signature of a token stored in a user's cookie
    and returns the encoded data.  If verification fails, this function
    returns `None`.
    '''

    parts = auth_cookie.split('&')

    if len(parts) != 3:
        return None

    [data, nonce_str, signature_str] = parts
    nonce = bytearray.fromhex(nonce_str)
    signature = bytearray.fromhex(signature_str)

    signing_key = ecdsa.SigningKey.from_string(
        bytearray.fromhex(signing_key_hex),
    )
    verifying_key = signing_key.verifying_key

    try:
        is_valid = verifying_key.verify(signature, nonce)
    except ecdsa.keys.BadSignatureError:
        return None

    if is_valid:
        return data

    return None
