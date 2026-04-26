import os
from contextlib import contextmanager
from typing import Any

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool


DB_CONFIG = {
    "host": os.getenv("WS_DB_HOST", "localhost"),
    "port": int(os.getenv("WS_DB_PORT", "3306")),
    "user": os.getenv("WS_DB_USER", "root"),
    "password": os.getenv("WS_DB_PASSWORD", "password"),
    "database": os.getenv("WS_DB_NAME", "worksphere"),
    "autocommit": False,
}

_pool: MySQLConnectionPool | None = None


def get_pool() -> MySQLConnectionPool:
    global _pool
    if _pool is None:
        _pool = MySQLConnectionPool(
            pool_name="worksphere_pool",
            pool_size=10,
            pool_reset_session=True,
            **DB_CONFIG,
        )
    return _pool


@contextmanager
def get_db():
    connection = get_pool().get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        yield connection, cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with get_db() as (_, cursor):
        cursor.execute(query, params)
        return cursor.fetchall()


def fetch_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with get_db() as (_, cursor):
        cursor.execute(query, params)
        return cursor.fetchone()
