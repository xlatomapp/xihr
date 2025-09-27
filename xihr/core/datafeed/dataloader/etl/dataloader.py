import abc

import pandas as pd
from sqlalchemy import Engine

from .....util.postgres_util import get_postgres_engine
from ..transform.transformation import Transformation
from .query import Query


class PostgresDataLoader:
    """
    class for loading data from PostgreSQL database.

    """

    def __init__(
        self,
        query: Query | None = None,
        transformations: list[Transformation] = [],
        user: str | None = None,
        password: str | None = None,
        host: str | None = None,
        port: str | int | None = None,
        db: str | None = None,
        engine: Engine | None = None,
        data: pd.DataFrame | None = None,
    ):
        """
        Initialize a PostgresDataLoader object.

        Parameters
        ----------
        query : Query
            a Query object
        transformations : list[Transformation]
            a list of Transformation objects.
            Transformations need to be in order if any dependency
        user : str
            user name for PostgreSQL database
        password : str
            password for PostgreSQL database
        host : str
            host name for PostgreSQL database
        port : str
            port number for PostgreSQL database
        db : str
            database name for PostgreSQL database
        engine : Engine
            a SQLAlchemy engine object
        data : pd.DataFrame
            a Pandas DataFrame object
        """

        self.__data = data
        self.query = query
        self.transformations = transformations
        self.__engine = None
        if self.__data is None:
            self.__engine = get_postgres_engine(
                user=user, password=password, host=host, port=port, db=db, engine=engine
            )

    @property
    def data(self) -> pd.DataFrame:
        assert self.__data is not None
        return self.__data

    def set_transformations(self, transformations: list[Transformation]):
        self.transformations = transformations

    def set_query(self, query: Query):
        self.query = query

    def execute(self, load: bool = True, transform: bool = True) -> None:
        """
        Execute a data pipeline.

        The pipeline consists of three stages: load, transform, and save.
        You can control which stages to execute by setting the boolean
        arguments, `load`, `transform`, and `save`.

        Args:
            load (bool): Whether to load data from a PostgreSQL database.
                Defaults to `True`.
            transform (bool): Whether to execute transformations on the loaded
                data. Defaults to `True`.
            save (bool): Whether to save the transformed data to a PostgreSQL
                database. Defaults to `True`.
        """
        if load:
            self.load_data()
        if transform:
            self.transform()

    def load_data(self) -> None:
        """
        Load data from a PostgreSQL database.

        This function executes a SQL query, specified by the `Query` object,
        to load data into a Pandas DataFrame. The query is executed using
        the SQLAlchemy engine.

        Raises:
            SQLAlchemyError: If there is an error executing the SQL query.
        """
        assert self.__engine is not None
        assert self.query is not None
        self.__data = pd.read_sql(self.query.query_string(), con=self.__engine)

    def transform(self) -> None:
        """
        Execute the transformations specified in the constructor.

        This function applies the transformations on the data loaded by
        `load_data` in the order they were given in the constructor.
        """
        assert self.__data is not None
        for transformation in self.transformations:
            self.__data = transformation.transform(self.__data)
