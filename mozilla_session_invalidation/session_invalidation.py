from dataclasses import dataclass, field
from enum import Enum
import typing as types


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


@dataclass
class TerminateSSOConfig:
    '''The configuration required to terminate an SSO session.
    '''

    bearer_token: str


def terminate_sso(cfg: TerminateSSOConfig) -> IJob:
    '''Configure a job interface to terminate an SSO session.
    '''

    def _terminate(email: UserEmail) -> JobResult:
        return JobResult(TerminationState.TERMINATED)

    return _terminate


@dataclass
class TerminateGSuiteConfig:
    '''
    '''

    bearer_token: str


def terminate_gsuite(cfg: TerminateGSuiteConfig) -> IJob:
    '''
    '''

    def _terminate(email: UserEmail) -> JobResult:
        return JobResult(TerminationState.NOT_IMPLEMENTED)

    return _terminate


@dataclass
class TerminateSlackConfig:
    '''
    '''

    bearer_token: str


def terminate_slack(cfg: TerminateSlackConfig) -> IJob:
    '''
    '''

    def _terminate(email: UserEmail) -> JobResult:
        return JobResult(TerminationState.NOT_IMPLEMENTED)

    return _terminate


@dataclass
class TerminateAWSConfig:
    '''
    '''

    access_key_id: str
    secret_key: str


def terminate_aws(cfg: TerminateAWSConfig) -> IJob:
    '''
    '''

    def _terminate(email: UserEmail) -> JobResult:
        return JobResult(TerminationState.NOT_IMPLEMENTED)

    return _terminate


@dataclass
class TerminateGCPConfig:
    '''
    '''

    token: str


def terminate_gcp(cfg: TerminateGCPConfig) -> IJob:
    '''
    '''

    def _terminate(email: UserEmail) -> JobResult:
        return JobResult(TerminationState.NOT_IMPLEMENTED)

    return _terminate
