from dataclasses import dataclass, field
from enum import Enum
import typing as types
import urllib.parse

from google.oauth2 import service_account
from googleapiclient import discovery
import requests

import sesinv.authentication as auth


class SupportedReliantParties(Enum):
    '''Enumerates the identifiers of reliant parties (RPs) shared between
    the server and client.  The names of these RPs are used to make updates
    to the frontend for the user.
    '''

    SSO = 'sso'
    GSUITE = 'gsuite'
    SLACK = 'slack'
    AWS = 'aws'
    GCP = 'gcp'


class TerminationState(Enum):
    '''The states that a job can enter for a given RP.  If recoverable errors
    are encountered or the server wishes to provide useful output to the client,
    then the `NOT_MODIFIED` state is presented.  Once sessions tied to an
    RP are terminated, the `TERMINATED` state is entered.  If an error that
    cannot be recovered from is encountered, the `ERROR` state is entered.
    '''

    NOT_MODIFIED = 'not_modified'
    TERMINATED = 'terminated'
    ERROR = 'error'
    NOT_IMPLEMENTED = 'not_implemented'


@dataclass
class JobResult:
    '''A generic type representing the result of attempting to terminate a
    session.  Contains the new state of the session and any outputs that
    should be reported to the user.  A session should only move from the
    `not_modified` state to either of `terminated` or `error`.
    '''

    new_state: TerminationState
    output: types.Optional[str] = field(default=None)
    error: types.Optional[str] = field(default=None)


# A "job" interface representing a function that can be called to terminate
# a session, producing a descriptive result.  A termination job will be given
# the email address (e.g. user@website.com) of the user whose session is to
# be terminated.
UserEmail = str
IJob = types.Callable[[UserEmail], JobResult]
JobConfig = types.Dict[SupportedReliantParties, IJob]

def configure_jobs(config: dict, selections: types.List[str]) -> JobConfig:
    '''Builds a dictionary mapping identifiers of reliant parties to functions
    that can be called with the email address of a user to invaldiate the
    sessions of for each of those RPs.

    `config` is a dictionary of secrets and non-secret configuration values
    pulled from environment variables.

    `selections` is a list of the string identifiers of RPs to terminate
    sessions for.  Only those present here will be configured.
    '''

    configuration = {}

    if SupportedReliantParties.SSO.value in selections:
        sso_creds = auth.SSOCreds(
            client_id=config['SSO_CLIENT_ID'],
            client_secret=config['SSO_CLIENT_SECRET'],
            auth_url=config['SSO_AUTH_URL'],
            audience=config['SSO_AUDIENCE'],
            grant_type=config['SSO_GRANT_TYPE'],
        )
        sso_id_fmt = config['SSO_ID_FORMAT']
        sso = terminate_sso(sso_creds, sso_id_fmt, config['SSO_USER_ENDPT'])

        configuration[SupportedReliantParties.SSO] = sso

    if SupportedReliantParties.GSUITE.value in selections:
        # We encode the RSA private key to hex to store in SSM because the
        # newline characters present in PEM mess with our parsing.
        private_key = bytearray\
            .fromhex(config['GSUITE_PRIVATE_KEY'])\
            .decode('utf-8')

        service_account_json_key = {
            'type': config['GSUITE_ACCOUNT_TYPE'],
            'project_id': config['GSUITE_PROJECT_ID'],
            'private_key_id': config['GSUITE_PRIVATE_KEY_ID'],
            'private_key': private_key,
            'client_email': config['GSUITE_CLIENT_EMAIL'],
            'client_id': config['GSUITE_CLIENT_ID'],
            'auth_uri': config['GSUITE_AUTH_URI'],
            'token_uri': config['GSUITE_TOKEN_URI'],
            'auth_provider_x509_cert_url': config['GSUITE_AUTH_PROVIDER_CERT_URL'],
            'client_x509_cert_url': config['GSUITE_CLIENT_CERT_URL'],
        }
        gsuite = terminate_gsuite(
            service_account_json_key,
            config['GSUITE_SUBJECT'],
        )

        configuration[SupportedReliantParties.GSUITE] = gsuite

    if SupportedReliantParties.SLACK.value in selections:
        slack_oauth_token = config['SLACK_TOKEN']
        slack = terminate_slack(
            slack_oauth_token,
            config['SLACK_LOOKUP_USER_ENDPT'],
            config['SLACK_SCIM_USERS_ENDPT'],
        )

        configuration[SupportedReliantParties.SLACK] = slack

    if SupportedReliantParties.AWS.value in selections:
        aws_access_key_id = ''
        aws_secret_key = ''
        aws = terminate_aws(aws_access_key_id, aws_secret_key)

        configuration[SupportedReliantParties.AWS] = aws

    if SupportedReliantParties.GCP.value in selections:
        # We encode the RSA private key to hex to store in SSM because the
        # newline characters present in PEM mess with our parsing.
        private_key = bytearray\
            .fromhex(config['GCP_PRIVATE_KEY'])\
            .decode('utf-8')

        service_account_json_key = {
            'type': config['GCP_ACCOUNT_TYPE'],
            'project_id': config['GCP_PROJECT_ID'],
            'private_key_id': config['GCP_PRIVATE_KEY_ID'],
            'private_key': private_key,
            'client_email': config['GCP_CLIENT_EMAIL'],
            'client_id': config['GCP_CLIENT_ID'],
            'auth_uri': config['GCP_AUTH_URI'],
            'token_uri': config['GCP_TOKEN_URI'],
            'auth_provider_x509_cert_url': config['GCP_AUTH_PROVIDER_CERT_URL'],
            'client_x509_cert_url': config['GCP_CLIENT_CERT_URL'],
        }
        gcp = terminate_gcp(
            service_account_json_key,
            config['GCP_SUBJECT'],
        )

        configuration[SupportedReliantParties.GCP] = gcp

    return configuration


def terminate_sso(creds: auth.SSOCreds, id_fmt: str, endpt: str) -> IJob:
    '''Configure a job interface to terminate an SSO session.

    The `bearer_token` parameter is expected to be an OAuth token with the
    **update:users** scope required to terminate a user's session.

    The `id_fmt` parameter is expected to be a format string used to construct
    the user id that is sent to the Auth0 API.  E.g. `"ad|Mozilla-LDAP|{}"`.

    The `endpt` parameter is expected to be a format string containing the URL
    of the **invalidate-remember-browser** OAuth endpoint, e.g.
    `"https://site.auth0.com/api/v2/users/{}/multifactor/actions/invalidate-remember-browser"`
    '''

    def _terminate(email: UserEmail) -> JobResult:
        try:
            bearer_token = creds.token()
        except auth.Error as err:
            return JobResult(
                TerminationState.ERROR,
                error=f'Failed to retrieve SSO OAuth token: Error {err.message}',
            )

        username = email.split('@')[0]

        user_id = urllib.parse.quote(id_fmt.format(username))

        invalidate_url = endpt.format(user_id)

        headers = {
            'Authorization': f'Bearer {bearer_token}',
        }
        
        err_msg = f'Failed to terminate SSO session for {email}'

        try:
            response = requests.post(invalidate_url, headers=headers)
        except Exception as ex:
            return JobResult(
                TerminationState.ERROR,
                error=err_msg,
            )

        if response.status_code >= 300:
            return JobResult(
                TerminationState.ERROR,
                error=f'{err_msg}: Status {response.status_code}',
            )

        note = 'Note: The SSO API does not provide information to indicate '\
        'that a session termination may have failed. Consequently, a status '\
        'of "terminated" for SSO may not indicate that a session was actually '\
        'terminated.'

        return JobResult(
            TerminationState.TERMINATED,
            output=note,
        )

    return _terminate


def terminate_gsuite(
    service_account_json_key: types.Dict[str, str],
    subject: str,
) -> IJob:
    '''Configure a job interface to terminate a GSuite session.

    The `service_account_json_key` must be the JSON object produced when a
    private key is generated for the service account created for the session
    invalidation app by a GSuite admin.

    The `subject` must be the email address of the GSuite admin that created
    the service account and generated the private key to authenticate as it.
    '''

    scopes = ['https://www.googleapis.com/auth/admin.directory.user']

    def _terminate(email: UserEmail) -> JobResult:
        err_msg_prefix = f'Failed to terminate GSuite session for {email}'

        try:
            credentials = service_account.Credentials.from_service_account_info(
                service_account_json_key, 
                scopes=scopes,
            )
            credentials = credentials.with_subject(subject)

            service = discovery.build('admin', 'directory_v1', credentials=credentials)

            resp1 = service.users().patch(
                userKey=email,
                body={
                    'changePasswordAtNextLogin': True,
                },
            ).execute()

            if resp1.get('changePasswordAtNextLogin') is not True:
                return JobResult(
                    TerminationState.ERROR,
                    error=err_msg_prefix,
                )
            
            resp2 = service.users().patch(
                userKey=email,
                body={
                    'changePasswordAtNextLogin': False,
                },
            ).execute()

            if resp2.get('changePasswordAtNextLogin') is not False:
                return JobResult(
                    TerminationState.ERROR,
                    error=err_msg_prefix,
                )
        except Exception as ex:
            return JobResult(
                TerminationState.ERROR,
                error=f'{err_msg_prefix}: Error: {ex}',
            )

        return JobResult(TerminationState.TERMINATED)

    return _terminate


def terminate_slack(
    bearer_token: str,
    email_endpt: str,
    update_endpt: str,
) -> IJob:
    '''Configure a job interface to terminate a Slack session.

    The `bearer_token` parameter is expected to be an OAuth token with the
    **admin** scope required to invoke the SCIM API for managing users.
    https://api.slack.com/scim#users

    The `email_endpt` parameter is expected to be a string containing the URL
    of the **lookupUserByEmail** endpoint.
    e.g. `"https://slack.com/api/users.lookupByEmail"`.

    The `update_endpt` parameter is expected to be a string containing the URL
    of the user SCIM API endpoint. Note that this URL **must not** end in a
    trailing `/`. E.g. `"https://api.slack.com/scim/v1/Users"`
    '''

    def _terminate(email: UserEmail) -> JobResult:
        headers = {
            'Authorization': f'Bearer {bearer_token}',
        }

        err_msg = f'Failed to terminate Slack session for {email}'
            
        try:
            response = requests.post(
                email_endpt,
                data={'email': email},
                headers=headers,
            )

            resp_json = response.json()
        except Exception as ex:
            return JobResult(
                TerminationState.ERROR,
                error=f'{err_msg}: Could not find user in Slack',
            )

        if not resp_json['ok']:
            return JobResult(
                TerminationState.ERROR,
                error=f'{err_msg}: Error from slack: {resp_json["error"]}',
            )

        update_user = f'{update_endpt}/{resp_json["user"]["id"]}'

        try:
            response1 = requests.patch(update_user, headers=headers, json={
                'schemas': [
                    'urn:scim:schemas:core:1.0',
                ],
                'active': False,
            })

            resp1_json = response1.json()

            response2 = requests.patch(update_user, headers=headers, json={
                'schemas': [
                    'urn:scim:schemas:core:1.0',
                ],
                'active': True,
            })

            resp2_json = response2.json()
        except Exception as ex:
            return JobResult(
                TerminationState.ERROR,
                error=err_msg,
            )

        if response1.status_code >= 300 or not resp1_json.get('ok', True):
            err_add = f'Could not deactive: Status {response1.status_code}: '\
                f'Error: {resp1_json["error"]}'

            return JobResult(
                TerminationState.ERROR,
                error='{err_msg}: {err_add}',
            )
        
        if response2.status_code >= 300 or not resp2_json.get('ok', True):
            err_add = 'Could not reactivate: Status {response2.status_code}: '\
                f'Error: {resp2_json["error"]}'

            out = f'The Slack account owned by {email} has been '\
            'deactivated. Be sure to have a Slack admin reactivate the '\
            'account within five (5) days.'\

            return JobResult(
                TerminationState.ERROR,
                output=out,
                error='{err_msg}: {err_add}',
            )

        return JobResult(TerminationState.TERMINATED)

    return _terminate


def terminate_aws(acces_key_id: str, secret_key: str) -> IJob:
    '''
    '''

    def _terminate(email: UserEmail) -> JobResult:
        return JobResult(TerminationState.NOT_IMPLEMENTED)

    return _terminate


def terminate_gcp(
    service_account_json_key: types.Dict[str, str],
    subject: str,
) -> IJob:
    '''Configure a job to terminate a GCP user session.
    
    The `service_account_json_key` must be the JSON object produced when a
    private key is generated for the service account created for the session
    invalidation app by a GSuite admin.

    The `subject` must be the email address of the GSuite admin that created
    the service account and generated the private key to authenticate as it.
    '''

    return terminate_gsuite(service_account_json_key, subject)
