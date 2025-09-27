import abc
import datetime as dt
from enum import Enum, auto
from typing import Callable

import pandas as pd
from dateutil.relativedelta import relativedelta

from ..event import Event


class DataSet(Enum):
    RACE = auto()
    ENTRIES = auto()
    PAYOFF = auto()


class DataFeeder(abc.ABC):
    def __init__(self):
        self.__current_time: dt.datetime | None = None

    def set_time(self, current_time: dt.datetime):
        self.__current_time = current_time

    @property
    def _current_time(self) -> dt.datetime:
        if self.__current_time is None:
            raise RuntimeError("Current time is not set by Engine.")
        return self.__current_time

    @abc.abstractmethod
    def next(self) -> list[Event]:
        pass

    @abc.abstractmethod
    def get_next_race_id(self) -> str | None:
        pass

    @abc.abstractmethod
    def get_race_schedule(self) -> pd.DataFrame | None:
        pass

    @abc.abstractmethod
    def get_race_by_race_id(self, race_id: str) -> pd.DataFrame | None:
        pass

    @abc.abstractmethod
    def get_entries_by_race_id(self, race_id: str) -> pd.DataFrame | None:
        pass

    @abc.abstractmethod
    def get_payoff_by_race_id(self, race_id: str) -> pd.DataFrame | None:
        pass

    @abc.abstractmethod
    def get_next_race(self) -> pd.DataFrame | None:
        pass

    @abc.abstractmethod
    def get_next_entries(self) -> pd.DataFrame | None:
        pass

    @abc.abstractmethod
    def get_next_race_hist(self, offset: dt.timedelta) -> pd.DataFrame | None:
        pass

    @abc.abstractmethod
    def get_next_entries_hist(self) -> pd.DataFrame | None:
        pass
