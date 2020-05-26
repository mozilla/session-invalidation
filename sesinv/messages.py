from dataclasses import dataclass
from enum import Enum
import typing as types


from sesinv.sessions import\
    SupportedReliantParties,\
    TerminationState


@dataclass
class Error:
    error: str

    def to_json(self) -> dict:
        return {'error': self.error}


@dataclass
class Status:
    affected_rp: SupportedReliantParties
    current_state: TerminationState
    output: types.Optional[str]
    error: types.Optional[str]

    def to_json(self) -> dict:
        return {
            'affectedRP': self.affected_rp.value,
            'currentState': self.current_state.value,
            'output': self.output,
            'error': self.error,
        }


@dataclass
class Result:
    results: types.List[Status]

    def to_json(self) -> dict:
        return {
            'results': [result.to_json() for result in self.results],
        }
