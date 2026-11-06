"""Authentication store: SQLite for local use, PostgreSQL for public use."""
import os
from pathlib import Path
import sqlite3

from .catalog import connection as sqlite_connection


class PostgresConnection:
    def __init__(self, raw):
        self.raw = raw

    def __enter__(self):
        self.raw.__enter__()
        return self

    def __exit__(self, *args):
        return self.raw.__exit__(*args)

    def execute(self, query, params=()):
        # Queries in auth.py are static SQL; their SQLite parameter markers
        # are translated for psycopg's native binding (never interpolated).
        return self.raw.execute(query.replace("?", "%s"), params)

    def commit(self):
        self.raw.commit()


def connection():
    dsn = os.getenv("CAPABILITY_AUTH_DATABASE_URL")
    if not dsn:
        identity_path = os.getenv("CAPABILITY_AUTH_SQLITE_PATH")
        if identity_path:
            # A product-catalog preview must not silently replace account data.
            path = Path(identity_path).resolve()
            if not path.is_file():
                raise RuntimeError("Configured identity database does not exist")
            conn = sqlite3.connect(path, timeout=15)
            conn.row_factory = sqlite3.Row
            return conn
        return sqlite_connection()
    import psycopg
    from psycopg.rows import dict_row

    return PostgresConnection(psycopg.connect(dsn, row_factory=dict_row, connect_timeout=5))


def insert_id(conn, query, params):
    if isinstance(conn, PostgresConnection):
        return conn.execute(query + " RETURNING id", params).fetchone()["id"]
    return conn.execute(query, params).lastrowid
