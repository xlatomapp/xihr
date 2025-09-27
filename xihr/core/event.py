import datetime as dt
import enum
from dataclasses import dataclass
from typing import Any


class EventType(enum.Enum):
    DATA = enum.auto()
    SCHED = enum.auto()
    PLACE_BET = enum.auto()
    BET_REPORT = enum.auto()
    RACE_RESULT = enum.auto()
    PAYOFF = enum.auto()


@dataclass(frozen=True, kw_only=True)
class Event:
    time: dt.datetime
    eventtype: EventType
    payload: dict[str, Any]
