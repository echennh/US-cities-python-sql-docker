"""
DB access layer – single responsibility & test-friendly.

Hides MySQL driver specifics from the rest of the application.
"""
from __future__ import annotations

import logging
from typing import Iterable, List, Tuple

import mysql.connector
from mysql.connector.cursor import MySQLCursor

logger = logging.getLogger(__name__)


class MySQLConnection:
    """Context-manager wrapper around `mysql.connector`."""

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
    ) -> None:
        self._cfg = dict(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            autocommit=True,
        )
        self._conn: mysql.connector.MySQLConnection | None = None

    def __enter__(self) -> MySQLCursor:
        self._conn = mysql.connector.connect(**self._cfg)
        logger.debug("Connected to MySQL %s", self._cfg)
        return self._conn.cursor()

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        if self._conn:
            self._conn.close()
            logger.debug("MySQL connection closed")

    # ── Query helpers ──────────────────────────────────────────────────────
    def latest_year(self) -> int:
        """Return the maximum `year` present in the table."""
        with self as cur:
            cur.execute("SELECT MAX(year) FROM city_population;")
            year: int | None = cur.fetchone()[0]
        if year is None:
            raise RuntimeError("Table city_population is empty")
        return year

    def sum_population(
        self,
        states: Iterable[str],
        year: int,
    ) -> List[Tuple[str, int]]:
        """
        Sum population for each state (case-sensitive full name) and chosen year.

        Returns:
            List of `(state, total_population)` tuples.
        """
        placeholder = ", ".join(["%s"] * len(list(states)))
        query = (
            "SELECT state, SUM(population) "
            "FROM city_population "
            "WHERE state IN (" + placeholder + ") AND year = %s "
            "GROUP BY state;"
        )
        params = [*states, year]
        logger.debug("Executing: %s with params %s", query, params)
        with self as cur:
            cur.execute(query, params)
            rows: List[Tuple[str, int]] = cur.fetchall()
        return rows


    # ── New helper for v1.1.0 ──────────────────────────────────────────────
    def insert_population_rows(
        self,
        rows: Iterable[tuple[str, str, int, int]],
        batch_size: int = 500,
    ) -> None:
        """
        Bulk-insert city population rows.

        Existing primary-key rows are overwritten (idempotent loads).
        """
        sql = (
            "INSERT INTO city_population (city, state, year, population) "
            "VALUES (%s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE population = VALUES(population);" # hmmm do I want this on duplicate key update?
        )
        bucket: list[tuple[str, str, int, int]] = []
        with self as cur:
            for row in rows:
                bucket.append(row)
                if len(bucket) >= batch_size:
                    cur.executemany(sql, bucket)
                    bucket.clear()
            if bucket:
                cur.executemany(sql, bucket)
        logger.info("Inserted/updated %d rows", len(list(rows)))
