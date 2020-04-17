from dataclasses import dataclass
from enum import Enum
import typing as types


from mozilla_session_invalidation.session_invalidation import\
    SupportedReliantParties,\
    TerminationState


class WSMessage(Enum):
    '''Enumerates the identifiers of websocket messages communicated to a
    client.  Each value corresponds to a similarly named dataclass that
    contains a `to_json` method for easy conversion.
    '''

    JOB_ID_CREATED = 'job_id_created'
    JOB_STATUS_UPDATE = 'job_status_update'
    JOB_COMPLETE = 'job_complete'


@dataclass
class JobCreated:
    job_id: str
    target_rps: types.Dict[SupportedReliantParties, TerminationState]

    def to_json(self) -> dict:
        return {
            'jobId': self.job_id,
            'targetRPs': {
                rp_name.value: state.value
                for rp_name, state in self.target_rps.items()
            },
        }


@dataclass
class JobStatusUpdate:
    job_id: str
    affected_rp: SupportedReliantParties
    current_state: TerminationState
    output: types.Optional[str]
    error: types.Optional[str]

    def to_json(self) -> dict:
        return {
            'jobId': self.job_id,
            'affectedRP': self.affected_rp.value,
            'currentState': self.current_state.value,
            'output': self.output,
            'error': self.error,
        }


@dataclass
class JobComplete:
    job_id: str

    def to_json(self) -> dict:
        return {
            'jobId': self.job_id,
        }
