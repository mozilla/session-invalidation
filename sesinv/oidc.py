import os
import urllib.parse
import typing as types

import requests


CODE_RESPONSE_TYPE = 'code'
CODE_GRANT_TYPE = 'authorization_code'


class InvalidToken(Exception):
    def __init__(self):
        self.message = 'Invalid ID token'

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
        global_discovery_doc = requests.get(discovery_url).json()

        jwks_uri = global_discovery_doc['jwks_uri']
        global_discovery_doc['jwks'] = requests.get(jwks_uri).json()
        global_discovery_doc['discovery_url'] = discovery_url

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


def retrieve_token(tkn_endpt: str, **kwargs) -> dict:
    '''Authenticate to an OIDC Provider and validate the token retrieved,
    returning the body of the JWT.
    '''

    required = ['client_id', 'client_secret', 'code', 'state']

    missing = [req for req in required if kwargs.get(req) is None]

    if len(missing) > 0:
        raise MissingParameters(missing)

    body = {
        key: kwargs[key]
        for key in required
    }

    body['grant_type'] = CODE_GRANT_TYPE

    res = requests.post(tkn_endpt, json=body)

    token = res.text

    if _valid_token(token):
        return _jwt_body(token)
    else:
        raise InvalidToken()


def _valid_token(jwt: str) -> bool:
    return True


def _jwt_body(jwt: str) -> dict:
    return {}
