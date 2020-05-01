from dataclasses import dataclass, field
from enum import Enum
import typing as types

import requests


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


def terminate_sso(bearer_token: str, endpt: str) -> IJob:
    '''Configure a job interface to terminate an SSO session.

    The `bearer_token` parameter is expected to be an OAuth token with the
    **update:users** scope required to terminate a user's session.

    The `endpt` parameter is expected to be a format string containing the URL
    of the **invalidate-remember-browser** OAuth endpoint, e.g.
    `"https://site.auth0.com/api/v2/users/{}/multifactor/actions/invalidate-remember-browser"`
    '''

    def _terminate(email: UserEmail) -> JobResult:
        username = email.split('@')[0]

        user_id = 'ad%7CMozilla-LDAP%7c{}'.format(username)

        invalidate_url = endpt.format(user_id)

        headers = {
            'Authorization': 'Bearer {}'.format(bearer_token),
        }
        
        err_msg = 'Failed to terminate session for {}'.format(email)

        try:
            response = requests.post(invalidate_url, headers=headers)
        except Exception:
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

        err_msg = 'Failed to terminate session for {}'.format(email)

        try:
            # Toggling the `changePasswordAtNextLogin` field has the effect of
            # forcing a login without actually requiring a password change.
            # https://stackoverflow.com/questions/52934817/reset-the-login-cookie-by-api
            response1 = requests.patch(url, headers=headers, json={
                'changePasswordAtNextLogin': True,
            })
            response2 = requests.patch(url, headers=headers, json={
                'changePasswordAtNextLogin': False,
            })
        except Exception:
            return JobResult(
                TerminationState.ERROR,
                error=err_msg,
            )

        if response1.status_code != 200:
            return JobResult(
                TerminationState.ERROR,
                error='{}: Status {}'.format(err_msg, response1.status_code),
            )

        if response2.status_code != 200:
            return JobResult(
                TerminationState.ERROR,
                error='{}: Status {}'.format(err_msg, response2.status_code),
            )

        return JobResult(TerminationState.TERMINATED)

    return _terminate


def terminate_slack(bearer_token: str, endpt: str) -> IJob:
    '''Configure a job interface to terminate a Slack session.

    The `bearer_token` parameter is expected to be an OAuth token with the
    **admin** scope required to invoke the SCIM API for managing users.
    https://api.slack.com/scim#users

    The `endpt` parameter is expected to be a string containing the URL
    of the user SCIM API endpoint, e.g. `"https://api.slack.com/scim/v1/Users"`
    '''

    def _terminate(email: UserEmail) -> JobResult:
        headers = {
            'Authorization': 'Bearer {}'.format(bearer_token),
        }

        err_msg = 'Failed to terminate session for {}'.format(email)

        try:
            response1 = requests.patch(endpt, headers=headers, json={
                'schemas': [
                    'urn:scim:schemas:core:1.0',
                ],
                'active': False,
            })
            response2 = requests.patch(endpt, headers=headers, json={
                'schemas': [
                    'urn:scim:schemas:core:1.0',
                ],
                'active': True,
            })
        except Exception as ex:
            return JobResult(
                TerminationState.ERROR,
                error=err_msg,
            )

        if response1.status_code >= 300:
            err_add = 'Could not deactive: Status {}'.format(
                response1.status_code,
            )

            return JobResult(
                TerminationState.ERROR,
                error='{}: {}'.format(err_msg, err_add),
            )
        
        if response2.status_code >= 300:
            err_add = 'Could not deactive: Status {}'.format(
                response2.status_code,
            )

            return JobResult(
                TerminationState.ERROR,
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
