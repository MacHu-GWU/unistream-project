# -*- coding: utf-8 -*-

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from unistream.records.dataclass import DataClassRecord
from unistream.checkpoint import Tracker, BaseCheckPoint, StatusEnum
from unistream.utils import EPOCH_STR, get_utc_now

dir_here = Path(__file__).absolute().parent


class TestTracker:
    def _make_tracker(self, **kwargs) -> Tracker:
        now = get_utc_now()
        defaults = dict(
            record_id="id-1",
            status=StatusEnum.pending.value,
            attempts=0,
            create_time=now.isoformat(),
            update_time=now.isoformat(),
            lock=None,
            lock_time=EPOCH_STR,
            lock_expire_time=EPOCH_STR,
        )
        defaults.update(kwargs)
        return Tracker(**defaults)

    def test_datetime_properties(self):
        now = get_utc_now()
        tracker = self._make_tracker(
            create_time=now.isoformat(),
            update_time=now.isoformat(),
            lock_time=now.isoformat(),
            lock_expire_time=(now + timedelta(seconds=60)).isoformat(),
        )
        assert isinstance(tracker.create_datetime, datetime)
        assert isinstance(tracker.update_datetime, datetime)
        assert isinstance(tracker.lock_datetime, datetime)
        assert isinstance(tracker.lock_expire_datetime, datetime)
        assert tracker.lock_expire_datetime > tracker.lock_datetime


class TestBaseCheckPoint:
    path_wal = dir_here.joinpath("file_buffer.log")

    def _new_checkpoint(self, **kwargs) -> BaseCheckPoint:
        defaults = dict(
            lock_expire=60,
            max_attempts=3,
            initial_pointer=0,
            start_pointer=0,
            next_pointer=None,
            batch_sequence=0,
            batch=dict(),
        )
        defaults.update(kwargs)
        return BaseCheckPoint(**defaults)

    def _test_serialization(self):
        records = [
            DataClassRecord(id="id-1"),
        ]
        checkpoint = self._new_checkpoint()
        assert len(checkpoint.batch) == 0
        assert checkpoint.is_ready_for_next_batch() is True

        checkpoint.update_for_new_batch(records)
        assert len(checkpoint.batch) == len(records)
        assert checkpoint.is_ready_for_next_batch() is False
        assert isinstance(checkpoint.batch["id-1"], Tracker)

        checkpoint_dict = checkpoint.to_dict()
        _ = json.dumps(checkpoint_dict)
        checkpoint1 = BaseCheckPoint.from_dict(checkpoint_dict)
        checkpoint1_dct = checkpoint1.to_dict()
        assert checkpoint == checkpoint1
        assert checkpoint_dict == checkpoint1_dct
        assert isinstance(checkpoint1.batch["id-1"], Tracker)

    def _test_is_record_locked(self):
        checkpoint = self._new_checkpoint()
        record = DataClassRecord(id="id-1")
        checkpoint.update_for_new_batch([record])

        # not locked initially (lock is None)
        assert checkpoint.is_record_locked(record) is False

        # lock the record via mark_as_in_progress
        checkpoint.mark_as_in_progress(record)
        tracker = checkpoint.get_tracker(record)
        lock_value = tracker.lock

        # locked for a different lock
        assert checkpoint.is_record_locked(record, lock="different-lock") is True

        # not locked if we provide the same lock
        assert checkpoint.is_record_locked(record, lock=lock_value) is False

        # not locked if lock has expired (lock_expire=60 -> timedelta(60) = 60 days)
        past = get_utc_now() + timedelta(days=61)
        assert checkpoint.is_record_locked(record, lock="different-lock", now=past) is False

    def _test_mark_as_failed_or_exhausted(self):
        checkpoint = self._new_checkpoint(max_attempts=2)
        record = DataClassRecord(id="id-1")
        checkpoint.update_for_new_batch([record])

        # first attempt -> failed (attempts=1 < max_attempts=2)
        checkpoint.mark_as_in_progress(record)
        e = ValueError("test error")
        checkpoint.mark_as_failed_or_exhausted(record, e)
        tracker = checkpoint.get_tracker(record)
        assert tracker.status == StatusEnum.failed.value
        assert tracker.lock is None
        assert "ValueError" in tracker.errors["error"]
        assert tracker.attempts == 1

        # second attempt -> exhausted (attempts=2 >= max_attempts=2)
        checkpoint.mark_as_in_progress(record)
        checkpoint.mark_as_failed_or_exhausted(record, e)
        tracker = checkpoint.get_tracker(record)
        assert tracker.status == StatusEnum.exhausted.value
        assert tracker.attempts == 2

    def _test_get_not_succeeded_records(self):
        checkpoint = self._new_checkpoint()
        r1 = DataClassRecord(id="id-1")
        r2 = DataClassRecord(id="id-2")
        r3 = DataClassRecord(id="id-3")
        records = [r1, r2, r3]
        checkpoint.update_for_new_batch(records)

        # mark r1 as succeeded, r2 as failed, r3 as exhausted
        checkpoint.mark_as_in_progress(r1)
        checkpoint.mark_as_succeeded(r1)

        checkpoint.mark_as_in_progress(r2)
        checkpoint.mark_as_failed_or_exhausted(r2, ValueError("err"))

        checkpoint.mark_as_in_progress(r3)
        checkpoint.mark_as_in_progress(r3)  # attempts=2
        checkpoint.mark_as_in_progress(r3)  # attempts=3
        checkpoint.mark_as_failed_or_exhausted(r3, ValueError("err"))

        not_succeeded = checkpoint.get_not_succeeded_records(
            record_class=DataClassRecord,
            records=records,
        )
        assert len(not_succeeded) == 2
        ids = [r.id for r in not_succeeded]
        assert "id-2" in ids
        assert "id-3" in ids

    def test(self):
        self._test_serialization()
        self._test_is_record_locked()
        self._test_mark_as_failed_or_exhausted()
        self._test_get_not_succeeded_records()


if __name__ == "__main__":
    from unistream.tests import run_cov_test

    run_cov_test(__file__, "unistream.checkpoint", preview=False)
