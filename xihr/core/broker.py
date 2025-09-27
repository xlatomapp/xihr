import abc
import datetime as dt

import polars as pl

from .datafeed.base import DataFeeder


class RaceTicketPlaceHolder:
    pass


class BrokerBase(abc.ABC):
    def __init__(self):
        self.__data_feed: DataFeeder | None = None

        self.__next_race_id: str | None = ""
        self.__balance: int | None = -1
        self.__bets: list[RaceTicketPlaceHolder] | None = None
        self.__start_date: dt.date | None = None
        self.__end_date: dt.date | None = None

    def init(
        self,
        data_feed: DataFeeder,
        balance: int,
        start_date: dt.datetime,
        end_date: dt.datetime,
    ) -> None:
        self.set_balance(balance)
        self.set_start_date(start_date)
        self.set_end_date(end_date)
        self.set_data_feed(data_feed)

    def set_balance(self, balance: int) -> None:
        self.__balance = balance

    def set_start_date(self, start_date: dt.datetime) -> None:
        self.__start_date = start_date

    def set_end_date(self, end_date: dt.datetime) -> None:
        self.__end_date = end_date

    def set_data_feed(self, data_feed: DataFeeder) -> None:
        self.__data_feed = data_feed

    def balance(self) -> int:
        assert self.__balance is not None
        return self.__balance

    def data_feed(self) -> DataFeeder:
        assert self.__data_feed is not None
        return self.__data_feed

    # def next_race_id(self) -> str:
    #     self.__data_feed.get_race_race_id()
    #     return self.__next_race_id

    @abc.abstractmethod
    def buy_ticket(self, ticket: RaceTicketPlaceHolder) -> None:
        ...

    @abc.abstractmethod
    def get_next_race(self) -> pl.DataFrame:
        ...

    @property
    @abc.abstractmethod
    def entries(self) -> pl.DataFrame:
        ...

    @property
    @abc.abstractmethod
    def payoff(self) -> pl.DataFrame:
        ...

    @abc.abstractmethod
    def next(self) -> bool:
        ...

    @abc.abstractmethod
    def get_payoff(self, ticket: RaceTicketPlaceHolder) -> pl.DataFrame:
        ...

    @abc.abstractmethod
    def get_total_payoff_by_race_id(self, race_id) -> int:
        ...
