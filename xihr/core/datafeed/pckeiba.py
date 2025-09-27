import datetime as dt

import pandas as pd

from ...config.config import Config
from ..event import Event, EventType
from .base import DataFeeder
from .dataloader.etl.dataloader import PostgresDataLoader
from .dataloader.etl.query import PostgresQuery
from .dataloader.transform.entires import ENTRIES_TRANSFORMATIONS as et
from .dataloader.transform.payoff import PAYOFF_TRANSFORMATIONS as pt
from .dataloader.transform.race import RACE_TRANSFORMATIONS as rt
from .dataloader.transform.transformation import Transformation


class PCKeibaDataFeeder(DataFeeder):
    def __init__(self):
        self.__dataloader: PostgresDataLoader | None = None
        self.__next_race_id: str | None = None
        self.__next_race_start_time: dt.datetime | None = None
        super().__init__()

    def _get_table_by_data_type(self, datatype: str) -> str:
        table = "jvd_ra" if datatype == "race" else ""
        table = "jvd_se" if datatype == "entries" else table
        table = "jvd_hr" if datatype == "payoff" else table
        if table == "":
            raise Exception("invalid datatype, must be race, entries or payoff")
        return table

    def _get_by_race_id_query(
        self, datatype: str, race_ids: list[str]
    ) -> PostgresQuery:
        race_id_str = ",".join([f"'{id}'" for id in race_ids])
        race_id_str = f"({race_id_str})"
        table = self._get_table_by_data_type(datatype)
        cond: str = "CONCAT(kaisai_nen, kaisai_tsukihi, "
        cond += "keibajo_code, kaisai_kai, kaisai_nichime, "
        cond += f"race_bango) in {race_id_str}"

        query = PostgresQuery(
            table=table,
            cond=cond,
        )
        return query

    def _get_current_time_condition(
        self,
    ) -> str:
        year = self._current_time.strftime("%Y")
        monthday = self._current_time.strftime("%m%d")
        time = self._current_time.strftime("%H%M")

        cond = f"kaisai_nen = '{year}' and kaisai_tsukihi = '{monthday}' and "
        cond += f"hasso_jikoku >= '{time}' "
        cond += "ORDER BY hasso_jikoku ASC LIMIT 1"
        return cond

    def _get_within_time_condition(
        self, datetime: dt.datetime, offset: dt.timedelta
    ) -> str:
        date1 = datetime.strftime("%Y%m%d")
        date2 = (datetime + offset).strftime("%Y%m%d")

        cond = f"TO_DATE(kaisai_nen || kaisai_tsukihi, 'YYYYMMDD') BETWEEN '{date1}' AND '{date2}'"
        print(cond)
        return cond

    def _get_transformations_by_data_type(self, datatype: str) -> list[Transformation]:
        transformation = rt if datatype == "race" else []
        transformation = et if datatype == "entries" else transformation
        transformation = pt if datatype == "payoff" else transformation
        return transformation

    def next(self) -> list[Event]:
        return [Event(time=self._current_time, eventtype=EventType.DATA, payload={})]

    def get_race_schedule(self):
        return super().get_race_schedule()

    def get_dataloader(self, reload: bool = False) -> PostgresDataLoader:
        if reload or self.__dataloader is None:
            self.__dataloader = PostgresDataLoader(
                user=Config.options.postgres_config.user,
                password=Config.options.postgres_config.password,
                host=Config.options.postgres_config.host,
                port=Config.options.postgres_config.port,
                db=Config.options.postgres_config.database,
            )
        return self.__dataloader

    def get_next_race_id(self) -> str | None:
        if (
            self.__next_race_start_time is not None
            and self._current_time <= self.__next_race_start_time
        ):
            return self.__next_race_id
        print("Getting next race id from database")
        dl = self.get_dataloader()
        dl.set_query(
            PostgresQuery(table="jvd_ra", cond=self._get_current_time_condition())
        )
        dl.set_transformations(rt)
        dl.execute()

        # No more races
        if dl.data is None:
            return None

        # set next race id
        self.__next_race_id = dl.data["raceId"].iloc[0]
        self.__next_race_start_time = dt.datetime.combine(
            dl.data["date"].iloc[0], dl.data["startTime"].iloc[0]
        )
        return self.__next_race_id

    def _get_data_by_race_id(self, datatype: str, race_id: str) -> pd.DataFrame:
        dl = self.get_dataloader()
        dl.set_query(self._get_by_race_id_query(datatype, [race_id]))
        dl.set_transformations(self._get_transformations_by_data_type(datatype))
        dl.execute()
        return dl.data

    def get_race_by_race_id(self, race_id: str) -> pd.DataFrame:
        return self._get_data_by_race_id("race", race_id)

    def get_entries_by_race_id(self, race_id: str) -> pd.DataFrame:
        return self._get_data_by_race_id("entries", race_id)

    def get_payoff_by_race_id(self, race_id):
        return self._get_data_by_race_id("payoff", race_id)

    def get_next_race(self) -> pd.DataFrame | None:
        race_id = self.get_next_race_id()
        if race_id is None:
            return None
        return self.get_race_by_race_id(race_id)

    def get_next_entries(self) -> pd.DataFrame | None:
        race_id = self.get_next_race_id()
        if race_id is None:
            return None
        return self.get_entries_by_race_id(race_id)

    def get_next_race_hist(self, offset: dt.timedelta) -> pd.DataFrame | None:
        race_id = self.get_next_race_id()
        if race_id is None:
            return None
        return self.get_history_by_race_id(race_id, offset)

    def get_history_by_race_id(
        self, race_id, offset: dt.timedelta
    ) -> pd.DataFrame | None:
        race = self.get_race_by_race_id(race_id)
        date = race["date"].iloc[0]
        datatype = "race"

        dl = self.get_dataloader()

        query = PostgresQuery(
            table=self._get_table_by_data_type(datatype),
            cond=self._get_within_time_condition(date, offset),
        )
        dl.set_query(query)
        dl.set_transformations(self._get_transformations_by_data_type(datatype))
        dl.execute()
        if dl.data is None:
            return None

        return dl.data

    def get_next_entries_hist(self) -> pd.DataFrame | None:
        race_id = self.get_next_race_id()
        if race_id is None:
            return None
        return self.get_history_by_race_id(race_id, dt.timedelta(days=1))
