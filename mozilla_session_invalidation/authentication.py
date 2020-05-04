from dataclasses import dataclass, field
from datetime import datetime, timedelta
import typing as types

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
class GSuiteCreds:
    '''A manager interface for an OAuth token used to call into the GSuite API.
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
        '''
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
