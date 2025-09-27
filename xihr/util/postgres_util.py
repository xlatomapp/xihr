from typing import Union

from sqlalchemy import Engine, create_engine


def create_postgres_engine(
    user: str,
    password: str,
    host: str,
    port: str | int,
    db: str,
) -> Engine:
    host_port = [host]
    host_port = host_port + [str(port)] if (port is not None) else host_port
    host_port = ":".join(host_port)
    engine_str = f"postgresql+psycopg://{user}:{password}@{host_port}/{db}"
    return create_engine(engine_str)


def get_postgres_engine(
    user: str | None = None,
    password: str | None = None,
    host: str | None = None,
    port: str | int | None = None,
    db: str | None = None,
    engine: Engine | None = None,
) -> Engine:

    if engine is not None:
        return engine

    if (
        (user is not None)
        and (password is not None)
        and (host is not None)
        and (port is not None)
        and (db is not None)
    ):
        return create_postgres_engine(user, password, host, port, db)

    raise RuntimeError("(user, pw, host, port, db) or engine must be given.")
