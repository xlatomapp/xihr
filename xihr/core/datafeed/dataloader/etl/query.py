import abc


class Query(abc.ABC):
    @abc.abstractmethod
    def query_string(self) -> str:
        pass

    def __str__(self):
        return f"Query(query_string='{self.query_string}')"


class PostgresQuery(Query):
    def __init__(
        self, table: str, columns: list[str] | None = None, cond: str | None = None
    ):
        self.table = table
        self.columns = columns
        self.cond = cond

    def query_string(self) -> str:
        columns = ", ".join(self.columns) if (self.columns is not None) else "*"
        cond = f"WHERE {self.cond}" if (self.cond is not None) else ""
        query = f"SELECT {columns} FROM {self.table} {cond}"
        return query


class KdbQuery(Query):
    def __init__(
        self, table: str, columns: list[str] | None = None, cond: str | None = None
    ):
        self.table = table
        self.columns = columns
        self.cond = cond

    def query_string(self):
        columns = ", ".join(self.columns) if (self.columns is not None) else " "
        cond = f"where {self.cond}" if (self.cond is not None) else ""
        query = f"select {columns} from {self.table} {cond}"
        return query
