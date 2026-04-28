# -*- coding: utf-8 -*-

import dataclasses
from pathlib import Path

import pytest

from unistream.exc import StreamIsClosedError
from unistream.records.dataclass import DataClassRecord
from unistream.checkpoints.simple import SimpleCheckpoint
from unistream.consumers.simple import SimpleConsumer
from unistream.checkpoint import StatusEnum
from unistream.logger import logger

from unistream.tests import prepare_temp_dir

dir_here = Path(__file__).absolute().parent
dir_data = dir_here / "test_consumer"

prepare_temp_dir(dir_data)

path_source = dir_data / "source.log"
path_dlq = dir_data / "dlq.log"
path_checkpoint = dir_data / "checkpoint.json"
path_records = dir_data / "records.json"


# --- helpers ---------------------------------------------------------------

call_log: list[str] = []


@dataclasses.dataclass
class SuccessConsumer(SimpleConsumer):
    """A consumer where process_record always succeeds."""

    def process_record(self, record):
        call_log.append(f"process:{record.id}")
        return record.id

    def process_failed_record(self, record):
        call_log.append(f"dlq:{record.id}")


fail_count: dict[str, int] = {}


@dataclasses.dataclass
class FailOnceConsumer(SimpleConsumer):
    """A consumer where process_record fails on first call per record, then succeeds."""

    def process_record(self, record):
        fail_count.setdefault(record.id, 0)
        fail_count[record.id] += 1
        if fail_count[record.id] <= 1:
            raise ValueError(f"transient error for {record.id}")
        call_log.append(f"process:{record.id}")
        return record.id

    def process_failed_record(self, record):
        call_log.append(f"dlq:{record.id}")


@dataclasses.dataclass
class AlwaysFailConsumer(SimpleConsumer):
    """A consumer where process_record always fails."""

    def process_record(self, record):
        raise ValueError(f"permanent error for {record.id}")

    def process_failed_record(self, record):
        call_log.append(f"dlq:{record.id}")


def _write_source_records(records: list[DataClassRecord]):
    with path_source.open("w") as f:
        for r in records:
            f.write(r.serialize() + "\n")


def _make_consumer(consumer_cls, max_attempts=3, skip_error=True) -> SimpleConsumer:
    checkpoint = SimpleCheckpoint(
        lock_expire=60,
        max_attempts=max_attempts,
        initial_pointer=0,
        start_pointer=0,
        next_pointer=None,
        batch_sequence=0,
        batch=dict(),
        checkpoint_file=str(path_checkpoint),
        records_file=str(path_records),
    )
    return consumer_cls.new(
        record_class=DataClassRecord,
        path_source=path_source,
        path_dlq=path_dlq,
        checkpoint=checkpoint,
        limit=10,
        exp_backoff_multiplier=1,
        exp_backoff_base=2,
        exp_backoff_min=0,
        exp_backoff_max=1,
        skip_error=skip_error,
    )


# --- tests -----------------------------------------------------------------


class TestBaseConsumer:
    def _test_happy_path(self):
        """All records are processed successfully."""
        prepare_temp_dir(dir_data)
        call_log.clear()

        r1 = DataClassRecord(id="r1")
        r2 = DataClassRecord(id="r2")
        _write_source_records([r1, r2])

        consumer = _make_consumer(SuccessConsumer)
        with logger.disabled(disable=True):
            consumer.process_batch()

        assert "process:r1" in call_log
        assert "process:r2" in call_log
        # checkpoint should have advanced
        assert consumer.checkpoint.start_pointer == 2

    def _test_process_record_retry_then_succeed(self):
        """Record fails once, retries, then succeeds."""
        prepare_temp_dir(dir_data)
        call_log.clear()
        fail_count.clear()

        r1 = DataClassRecord(id="retry1")
        _write_source_records([r1])

        consumer = _make_consumer(FailOnceConsumer, max_attempts=3)
        with logger.disabled(disable=True):
            consumer.process_batch()

        assert "process:retry1" in call_log
        tracker = consumer.checkpoint.batch["retry1"]
        assert tracker.status == StatusEnum.succeeded.value

    def _test_process_record_exhausted(self):
        """Record always fails, gets exhausted, goes to DLQ."""
        prepare_temp_dir(dir_data)
        call_log.clear()

        r1 = DataClassRecord(id="fail1")
        _write_source_records([r1])

        consumer = _make_consumer(AlwaysFailConsumer, max_attempts=2, skip_error=True)
        with logger.disabled(disable=True):
            consumer.process_batch()

        assert "dlq:fail1" in call_log
        tracker = consumer.checkpoint.batch["fail1"]
        assert tracker.status == StatusEnum.exhausted.value

    def _test_commit_stream_closed(self):
        """When next_pointer is None, commit raises StreamIsClosedError."""
        prepare_temp_dir(dir_data)
        consumer = _make_consumer(SuccessConsumer)
        consumer.checkpoint.next_pointer = None

        with pytest.raises(StreamIsClosedError):
            consumer.commit()

    def _test_commit_advances_pointer(self):
        """Normal commit advances start_pointer."""
        prepare_temp_dir(dir_data)
        consumer = _make_consumer(SuccessConsumer)
        consumer.checkpoint.next_pointer = 5

        consumer.commit()
        assert consumer.checkpoint.start_pointer == 5
        assert consumer.checkpoint.next_pointer is None

    def test(self):
        self._test_happy_path()
        self._test_process_record_retry_then_succeed()
        self._test_process_record_exhausted()
        self._test_commit_stream_closed()
        self._test_commit_advances_pointer()


if __name__ == "__main__":
    from unistream.tests import run_cov_test

    run_cov_test(__file__, "unistream.consumer", preview=False)
