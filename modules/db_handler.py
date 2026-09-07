"""
modules/db_handler.py — Phase 4: Database Connection

Lets the tool read a table in as the working DataFrame, and write the
cleaned DataFrame back out, against SQLite or PostgreSQL (anything
SQLAlchemy supports via a connection URL, e.g.:

    sqlite:///data/mydata.db
    postgresql+psycopg2://user:password@host:5432/dbname

Kept intentionally simple: one table in, one table out. No ORM models —
just pandas.read_sql / to_sql on top of a SQLAlchemy engine.
"""

import pandas as pd
from sqlalchemy import create_engine, inspect


def get_engine(connection_url: str):
    """Creates (and validates) a SQLAlchemy engine for the given URL."""
    engine = create_engine(connection_url)
    # fail fast with a clear error if the URL/credentials are bad
    with engine.connect():
        pass
    return engine


def list_tables(connection_url: str) -> list:
    engine = get_engine(connection_url)
    return inspect(engine).get_table_names()


def read_table(connection_url: str, table_name: str, limit: int = None) -> pd.DataFrame:
    engine = get_engine(connection_url)
    query = f"SELECT * FROM {table_name}"
    if limit:
        query += f" LIMIT {limit}"
    return pd.read_sql(query, engine)


def write_table(connection_url: str, df: pd.DataFrame, table_name: str,
                 if_exists: str = "replace", logger=None) -> int:
    """
    if_exists: 'replace' | 'append' | 'fail'
    Returns the number of rows written.
    """
    engine = get_engine(connection_url)
    df.to_sql(table_name, engine, if_exists=if_exists, index=False)
    if logger:
        logger.log(f"Wrote {len(df)} rows to table '{table_name}' ({if_exists})")
    return len(df)
