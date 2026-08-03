from unittest.mock import MagicMock

from app.services.correlation_worker_lock_service import (
    CorrelationWorkerLockService,
)


def test_lock_is_acquired():

    connection = MagicMock()

    connection.execute.return_value.scalar_one.return_value = True

    with CorrelationWorkerLockService.acquire(
        connection,
    ) as acquired:

        assert acquired is True

    assert connection.execute.call_count == 2


def test_lock_not_acquired():

    connection = MagicMock()

    connection.execute.return_value.scalar_one.return_value = False

    with CorrelationWorkerLockService.acquire(
        connection,
    ) as acquired:

        assert acquired is False

    assert connection.execute.call_count == 1