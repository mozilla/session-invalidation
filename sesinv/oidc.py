import os
import urllib.parse
import typing as types

import requests
#from authlib.jose import jwt
from jose import jwt


CODE_RESPONSE_TYPE = 'code'
CODE_GRANT_TYPE = 'authorization_code'


class InvalidToken(Exception):
    def __init__(self, cause):
        self.message = f'Invalid ID token: {cause}'
        self.cause = cause

        super().__init__(self.message)


class MissingParameters(Exception):
    def __init__(self, params: types.List[str]):
        self.message = f'Missing parameter(s) {",".join(params)}'

        super().__init__(self.message)


def discovery_document(discovery_url: str) -> dict:
    '''Retrieve the discovery document provided by the OIDC OP.
    When the document is stored in the cache of the instance running the
    function, retrieve it from there.  Otherwise fetch it from the OP
    and append JSON Web Key Set data to it.
    '''

    global global_discovery_doc

    cached = 'global_discovery_doc' in globals() 

    # Update the discovery document if we request one from a new URL.
    # Mostly just for testing purposes.
    if not cached or global_discovery_doc['discovery_url'] != discovery_url:
        doc = requests.get(discovery_url).json()

        jwks_uri = doc['jwks_uri']
        doc['jwks'] = requests.get(jwks_uri).json()
        doc['discovery_url'] = discovery_url

        global_discovery_doc = doc

    return global_discovery_doc


def authorize_redirect_uri(auth_endpt, **kwargs) -> str:
    '''Produce the authorize URI that should be redirected to with URL
    parameters included.
    '''

    required = [
        'state',
        'scope',
        'redirect_uri',
        'client_id',
    ]

    missing = [req for req in required if kwargs.get(req) is None]

    if len(missing) > 0:
        raise MissingParameters(missing)

    params = {
        key: kwargs[key]
        for key in required
    }

    params['response_type'] = CODE_RESPONSE_TYPE

    return f'{auth_endpt}?{urllib.parse.urlencode(params)}'


def retrieve_token(tkn_endpt: str, jwk: dict, audience: str, **kwargs) -> dict:
    '''Authenticate to an OIDC Provider and validate the token retrieved,
    returning the body of the JWT.
    '''

    required = ['client_id', 'client_secret', 'code', 'state', 'redirect_uri']

    missing = [req for req in required if kwargs.get(req) is None]

    if len(missing) > 0:
        raise MissingParameters(missing)

    body = {
        key: kwargs[key]
        for key in required
    }

    body['grant_type'] = CODE_GRANT_TYPE

    response = requests.post(tkn_endpt, json=body)

    if response.status_code != 200:
        raise InvalidToken(f'Status code {response.status_code}')

    res = response.json()

    try:
        id_token = res['id_token']
        return jwt.decode(id_token, jwk, audience=audience)
    except Exception as cause:
        raise InvalidToken(cause)
