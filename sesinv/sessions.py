from dataclasses import dataclass, field
from enum import Enum
import typing as types
import urllib.parse

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

def configure_jobs(config) -> JobConfig:
    sso_creds = auth.SSOCreds(
        client_id=config['SSO_CLIENT_ID'],
        client_secret=config['SSO_CLIENT_SECRET'],
        auth_url=config['SSO_AUTH_URL'],
        audience=config['SSO_AUDIENCE'],
        grant_type=config['SSO_GRANT_TYPE'],
    )
    sso_id_fmt = config['SSO_ID_FORMAT']
    sso = terminate_sso(sso_creds, sso_id_fmt, config['MOZ_OAUTH_ENDPT'])

    gsuite_oauth_token = ''
    gsuite = terminate_gsuite(gsuite_oauth_token, config['GSUITE_USERS_ENDPT'])

    slack_oauth_token = config['SLACK_TOKEN']
    slack = terminate_slack(
        slack_oauth_token,
        config['SLACK_LOOKUP_USER_ENDPT'],
        config['SLACK_SCIM_USERS_ENDPT'],
    )

    aws_access_key_id = ''
    aws_secret_key = ''
    aws = terminate_aws(aws_access_key_id, aws_secret_key)

    gcp_token = ''
    gcp = terminate_gcp(gcp_token)

    return {
        SupportedReliantParties.SSO: sso,
        SupportedReliantParties.GSUITE: gsuite,
        SupportedReliantParties.SLACK: slack,
        SupportedReliantParties.AWS: aws,
        SupportedReliantParties.GCP: gcp,
    }


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
                error='Failed to retrieve SSO OAuth token: Error {}'.format(
                    err.message,
                ),
            )

        username = email.split('@')[0]

        user_id = urllib.parse.quote(id_fmt.format(username))

        invalidate_url = endpt.format(user_id)

        headers = {
            'Authorization': 'Bearer {}'.format(bearer_token),
        }
        
        err_msg = 'Failed to terminate SSO session for {}'.format(email)

        try:
            response = requests.post(invalidate_url, headers=headers)

            #resp_json = response.json()
        except Exception as ex:
            return JobResult(
                TerminationState.ERROR,
                error=err_msg,
            )

        if response.status_code >= 300:
            return JobResult(
                TerminationState.ERROR,
                error='{}: Status {}'.format(err_msg, response.status_code),
            )

        return JobResult(TerminationState.TERMINATED)

    return _terminate


def terminate_gsuite(bearer_token: str, endpt: str) -> IJob:
    '''Configure a job interface to terminate a GSuite session.

    The `bearer_token` parameter is expected to be an OAuth token with the
    **admin.directory.user** scope required to update a user profile.

    The `endpt` parameter is expected to be a format string containing the URL
    of the user management GSuite endpoint, e.g.
    `"https://www.googleapis.com/admin/directory/v1/users/{}"`.
    '''

    def _terminate(email: UserEmail) -> JobResult:
        url = endpt.format(email)

        headers = {
            'Authorization': 'Bearer {}'.format(bearer_token),
        }

        err_msg = 'Failed to terminate GSuite session for {}'.format(email)

        try:
            # Toggling the `changePasswordAtNextLogin` field has the effect of
            # forcing a login without actually requiring a password change.
            # https://stackoverflow.com/questions/52934817/reset-the-login-cookie-by-api
            response1 = requests.patch(url, headers=headers, json={
                'changePasswordAtNextLogin': True,
            })

            resp1_json = response1.json()

            response2 = requests.patch(url, headers=headers, json={
                'changePasswordAtNextLogin': False,
            })
            
            resp2_json = response2.json()
        except Exception:
            return JobResult(
                TerminationState.ERROR,
                error=err_msg,
            )

        if response1.status_code != 200:
            return JobResult(
                TerminationState.ERROR,
                error='{}: Status {}: Error: {}'.format(
                    err_msg,
                    response1.status_code,
                    resp1_json['error']['message'],
                ),
            )

        if response2.status_code != 200:
            return JobResult(
                TerminationState.ERROR,
                error='{}: Status {}: Error: {}'.format(
                    err_msg,
                    response2.status_code,
                    resp2_json['error']['message'],
                ),
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
            'Authorization': 'Bearer {}'.format(bearer_token),
        }

        err_msg = 'Failed to terminate Slack session for {}'.format(email)
            
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
                error='{}: Could not find user in Slack'.format(err_msg),
            )

        if not resp_json['ok']:
            return JobResult(
                TerminationState.ERROR,
                error='{}: Error from slack: {}'.format(
                    err_msg,
                    resp_json['error']
                ),
            )

        update_user = '{}/{}'.format(update_endpt, resp_json['user']['id'])

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
            err_add = 'Could not deactive: Status {}: Error: {}'.format(
                response1.status_code,
                resp1_json['error'],
            )

            return JobResult(
                TerminationState.ERROR,
                error='{}: {}'.format(err_msg, err_add),
            )
        
        if response2.status_code >= 300 or not resp2_json.get('ok', True):
            err_add = 'Could not reactivate: Status {}: Error: {}'.format(
                response2.status_code,
                resp2_json['error'],
            )

            out = 'The Slack account owned by {} has been '.format(email)
            'deactivated. Be sure to have a Slack admin reactivate the '
            'account within five (5) days.'

            return JobResult(
                TerminationState.ERROR,
                output=out,
                error='{}: {}'.format(err_msg, err_add),
            )

        return JobResult(TerminationState.TERMINATED)

    return _terminate


def terminate_aws(acces_key_id: str, secret_key: str) -> IJob:
    '''
    '''

    def _terminate(email: UserEmail) -> JobResult:
        return JobResult(TerminationState.NOT_IMPLEMENTED)

    return _terminate


def terminate_gcp(token: str) -> IJob:
    '''
    '''

    def _terminate(email: UserEmail) -> JobResult:
        return JobResult(TerminationState.NOT_IMPLEMENTED)

    return _terminate
