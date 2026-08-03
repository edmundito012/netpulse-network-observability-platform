"""PostgreSQL advisory lock for the Correlation Worker."""

from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.engine import Connection

LOCK_KEY = 20260803


class CorrelationWorkerLockService:
    """Acquire a PostgreSQL advisory lock."""

    @staticmethod
    @contextmanager
    def acquire(connection: Connection):
        """
        Acquire an advisory lock.

        If another worker already owns the lock,
        yield False immediately.
        """

        acquired = connection.execute(
            text(
                """
                SELECT pg_try_advisory_lock(:key)
                """
            ),
            {
                "key": LOCK_KEY,
            },
        ).scalar_one()

        if not acquired:
            yield False
            return

        try:
            yield True

        finally:
            connection.execute(
                text(
                    """
                    SELECT pg_advisory_unlock(:key)
                    """
                ),
                {
                    "key": LOCK_KEY,
                },
            )