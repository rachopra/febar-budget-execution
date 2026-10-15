"""Lakebase (Postgres) access with short-lived OAuth credentials.

Each new pooled connection gets a fresh Lakebase credential, and connections are recycled
before the credential's one-hour lifetime runs out.
"""

import os
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import LAKEBASE_ENDPOINT, PG_DATABASE, workspace


def _pg_user() -> str:
    if os.environ.get("PGUSER"):
        return os.environ["PGUSER"]
    w = workspace()
    return w.config.client_id or w.current_user.me().user_name


def _pg_host() -> str:
    if os.environ.get("PGHOST"):
        return os.environ["PGHOST"]
    ep = workspace().postgres.get_endpoint(name=LAKEBASE_ENDPOINT)
    return ep.status.hosts.host


class _OAuthConnection(psycopg.Connection):
    @classmethod
    def connect(cls, conninfo: str = "", **kwargs):
        kwargs["password"] = workspace().postgres.generate_database_credential(endpoint=LAKEBASE_ENDPOINT).token
        return super().connect(conninfo, **kwargs)


_pool: ConnectionPool | None = None


def pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            kwargs={"host": _pg_host(), "port": int(os.environ.get("PGPORT", "5432")), "dbname": PG_DATABASE,
                    "user": _pg_user(), "sslmode": "require", "row_factory": dict_row},
            connection_class=_OAuthConnection, min_size=1, max_size=8, max_lifetime=2700, open=True,
        )
    return _pool


def query(sql: str, params: Any = None) -> list[dict]:
    with pool().connection() as conn:
        return conn.execute(sql, params).fetchall()


def execute(sql: str, params: Any = None) -> list[dict]:
    with pool().connection() as conn:
        cur = conn.execute(sql, params)
        rows = cur.fetchall() if cur.description else []
        conn.commit()
        return rows
