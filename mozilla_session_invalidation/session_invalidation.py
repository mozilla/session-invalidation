from dataclasses import dataclass
from enum import Enum
import typing as types


class SupportedReliantParties(Enum):
    '''Enumerates the identifiers of reliant parties (RPs) shared between
    the server and client.  The names of these RPs are used to make updates
    to the frontend for the user.
    '''

    SSO = 'sso'


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


@dataclass
class JobManager:
    '''The jobs handled by the session invalidation tool do not require any
    long-running processes and so jobs tied to client sessions are maintained
    in memory.
    '''

    job_id: str
    oauth_token: str
    rp_states: types.Dict[SupportedReliantParties, TerminationState]

    def new(jid: str, oauth_tkn: str) -> 'JobManager':
        '''Construct a new `JobManager` that will track states for all
        supported reliant parties.
        '''

        states = {
            SupportedReliantParties.SSO: TerminationState.NOT_MODIFIED,
        }

        return JobManager(jid, oauth_tkn, states)
