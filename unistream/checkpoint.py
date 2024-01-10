# -*- coding: utf-8 -*-

"""
.. note:: Maintainer notes

    This module implements the :class:`BaseCheckpoint` class. It implements
    the following essential functions:

    - **Persistence of Stream Pointer and Batch Record Data**: It allows
        the persistence of stream pointers and batch record data for fault-tolerance.
    - **Record Locking During Processing**: To prevent double consumption,
        this class can lock records while they are being processed,
        ensuring that each record is processed only once.
    - **Tracking Processing Status**: The class also offers the capability
        to track the processing status for each record. The status data
        is persisted to the chosen persistence layer.

    Subclasses of :class:`BaseCheckpoint` are specific implementations tailored
        to specific data persistence backends. These subclasses provide
        the necessary functionality to interact with a particular backend
        while inheriting the core checkpoint management features from the base class.
"""

import typing as T
import uuid
import traceback
import dataclasses
from datetime import datetime, timedelta

from .vendor.better_enum import BetterIntEnum
from .vendor.better_dataclass import DataClass

from .logger import logger
from .utils import EPOCH_STR, get_utc_now
from .abstraction import T_RECORD, AbcCheckPoint


class StatusEnum(BetterIntEnum):
    """
    For each record, we track its processing status, which can be one of the following:

    - pending: the record is not processed ever yet.
    - in_progress: the record is being processed; the processing has started,
        but it has not finished yet. It could fail, but the program has not
        had a chance to mark it as failed.
    - failed: the record has been processed but has failed. It is open for further retry."
    - dead: the record has been processed but has failed too many times.
        we don't want to retry it anymore.
    - succeeded: the record has been processed and has succeeded.
    - ignored: the record is ignored by the consumer. We don't want to process it.
    """

    pending = 0  # 📅
    in_progress = 10  # ⏳
    failed = 20  # ❌
    exhausted = 30  # 🚫
    succeeded = 40  # ✅
    ignored = 50  # 🙅


@dataclasses.dataclass
class Tracker(DataClass):
    """
    The Tracker tracks the processing status of **each** record.

    :param record_id: the unique id of the record.
    :param status: Indicate the status of the tracker.
    :param create_time: when the tracker is created.
        Usually, it's the time a task is scheduled as to do.
    :param update_time: when the tracker status is updated.
    :param attempts: how many times we have tried to process the tracker.
    :param lock: a concurrency control mechanism. It is an uuid string.
        if the worker has the same lock as the tracker, it can process the tracker
        even it is locked.
    :param lock_time: when this tracker is locked. so other workers can't work on it.
    :param lock_expire_time: when this lock will expire.
    :param data: arbitrary data in python dictionary.
    :param errors: arbitrary error data in python dictionary.
    """

    record_id: str = dataclasses.field()
    status: int = dataclasses.field()
    attempts: int = dataclasses.field()
    create_time: str = dataclasses.field()
    update_time: str = dataclasses.field()
    lock: T.Optional[str] = dataclasses.field(default=None)
    lock_time: str = dataclasses.field(default=EPOCH_STR)
    lock_expire_time: str = dataclasses.field(default=EPOCH_STR)
    data: dict = dataclasses.field(default_factory=dict)
    errors: dict = dataclasses.field(default_factory=dict)

    @property
    def create_datetime(self) -> datetime:
        return datetime.fromisoformat(self.create_time)

    @property
    def update_datetime(self) -> datetime:
        return datetime.fromisoformat(self.update_time)

    @property
    def lock_datetime(self) -> datetime:
        return datetime.fromisoformat(self.lock_time)

    @property
    def lock_expire_datetime(self) -> datetime:
        return datetime.fromisoformat(self.lock_expire_time)


T_TRACKER = T.TypeVar("T_TRACKER", bound=Tracker)

T_POINTER = T.Union[str, int]


@dataclasses.dataclass
class BaseCheckPoint(DataClass, AbcCheckPoint):
    """
    CheckPoint stores the processing status, processing metadata and the origin
    records data. It is used to ensure data integrity and exactly-once processing.

    This class manages the data manipulation part of the logics. It intentionally
    leaves the data persistence part NOT implemented. It is up to the developer
    to subclass this class and implement the persistence layer. You can use
    any backend for checkpoint data persistence. For example, you can use
    a file, a database like AWS DynamoDB, or cloud storage like AWS S3.

    :param lock_expire: the lock expiration time in seconds.
    :param max_attempts: the maximum number of attempts to process a record.
    :param initial_pointer: the initial pointer to start reading the records.
    :param start_pointer: the start pointer to read a batch of records.
    :param next_pointer: the start pointer to read the next batch of records.
    :param batch_sequence: the nth batch of records we are processing.
    :param batch: the per-record status tracking data for the current batch.
    """

    lock_expire: int = dataclasses.field()
    max_attempts: int = dataclasses.field()
    initial_pointer: T_POINTER = dataclasses.field()
    start_pointer: T_POINTER = dataclasses.field()
    next_pointer: T.Optional[T_POINTER] = dataclasses.field()
    batch_sequence: int = dataclasses.field()
    batch: T.Dict[str, Tracker] = Tracker.map_of_nested_field()

    def get_tracker(self, record: T_RECORD) -> T_TRACKER:
        """
        Get the tracker for the given record.
        """
        return self.batch[record.id]

    def is_record_locked(
        self,
        record: T_RECORD,
        lock: T.Optional[str] = None,
        now: T.Optional[datetime] = None,
    ) -> bool:
        """
        Check if the tracker is locked.

        If the ``self.lock`` is None, then consider it is not locked.
        If the ``self.lock`` is not None, then compare it to the manually provided
        ``lock`` parameter. If they are the same, then consider it is not locked.
        Otherwise, check if the lock is expired.

        :param record: the record to check.
        :param lock: the lock to compare with ``self.lock``.
        :param now: the current time. If not provided, use ``get_utc_now()``.
        """
        tracker = self.get_tracker(record)
        if tracker.lock is None:
            return False
        if tracker.lock == lock:
            return False
        if now is None:
            now = get_utc_now()
        return now < tracker.lock_expire_datetime

    def mark_as_in_progress(
        self,
        record: T_RECORD,
        now: T.Optional[datetime] = None,
        expire: T.Optional[int] = None,
    ):
        """
        Set status as in_progress and lock the record so other workers can't process it.

        .. note::

            This method only updates the in-memory data. It is up to the developer
            to implement the persistence layer to persist the data.

        :param record: the record to check.
        :param now: the current time. If not provided, use ``get_utc_now()``.
        :param expire: the lock expiration time in seconds. If not provided,
            use ``self.lock_expire``.
        """
        # logger.info(
        #     f"set status = {StatusEnum.in_progress!r} (⏳ in_progress) "
        #     f"and 🔓 lock the record {record.id!r}."
        # )
        if now is None:
            now = get_utc_now()
        if expire is None:
            expire = self.lock_expire
        tracker = self.get_tracker(record)
        tracker.status = StatusEnum.in_progress.value
        tracker.attempts += 1
        tracker.update_time = now.isoformat()
        tracker.lock = uuid.uuid4().hex
        tracker.lock_time = now.isoformat()
        tracker.lock_expire_time = (now + timedelta(expire)).isoformat()

    def mark_as_failed_or_exhausted(
        self,
        record: T_RECORD,
        e: Exception,
        now: T.Optional[datetime] = None,
        max_attempts: T.Optional[int] = None,
    ):
        """
        Mark the tracker as failed or exhausted.

        .. note::

            This method only updates the in-memory data. It is up to the developer
            to implement the persistence layer to persist the data.

        :param record: the record to check.
        :param e: the exception that caused the failure.
        :param now: the current time. If not provided, use ``get_utc_now()``.
        :param max_attempts: the maximum number of attempts. If not provided,
            use ``self.max_attempts``.
        """
        if now is None:
            now = get_utc_now()
        if max_attempts is None:
            max_attempts = self.max_attempts
        tracker = self.get_tracker(record)
        if tracker.attempts >= max_attempts:
            tracker.status = StatusEnum.exhausted.value
            # logger.info(
            #     f"❌ record failed {max_attempts} times already, "
            #     f"set status = {tracker.status} (🚫 ignored) "
            #     f"and 🔐 unlock the record {record.id!r}."
            # )
        else:
            tracker.status = StatusEnum.failed.value
            # logger.info(
            #     f"❌ record failed, "
            #     f"set status = {tracker.status} (❌ failed) "
            #     f"and 🔐 unlock the record {record.id!r}."
            # )
        tracker.update_time = now.isoformat()
        tracker.lock = None
        tracker.errors = {
            "error": repr(e),
            "traceback": traceback.format_exc(limit=10),
        }

    def mark_as_succeeded(
        self,
        record: T_RECORD,
        now: T.Optional[datetime] = None,
        **kwargs,
    ):
        """
        Mark the tracker as succeeded.

        .. note::

            This method only updates the in-memory data. It is up to the developer
            to implement the persistence layer to persist the data.

        :param record: the record to check.
        :param now: the current time. If not provided, use ``get_utc_now()``.
        """
        if now is None:
            now = get_utc_now()
        tracker = self.get_tracker(record)
        status = StatusEnum.succeeded.value
        # logger.info(
        #     f"task succeeded, "
        #     f"set status = {status!r} (✅ succeeded) "
        #     f"and 🔐 unlock the record {record.id!r}."
        # )
        tracker.status = status
        tracker.update_time = now.isoformat()
        tracker.lock = None
        tracker.errors = dict()

    def is_ready_for_next_batch(self) -> bool:
        """
        Check the processing status for each record in the batch. Check if all records
        reached "finished" status, which means we don't want to retry processing
        any of them anymore. If so, we can move on to the next batch.
        """
        finished_codes = [
            StatusEnum.exhausted.value,
            StatusEnum.succeeded.value,
            StatusEnum.ignored.value,
        ]
        return all(
            [tracker.status in finished_codes for tracker in self.batch.values()]
        )

    def update_for_new_batch(
        self,
        records: T.List[T_RECORD],
        next_pointer: T.Optional[T_POINTER] = None,
    ):
        """
        Call this method when just received a new batch of records. It will
        create an initial tracker for each record and set the next pointer.

        .. note::

            This method won't persist the checkpoint.
        """
        if next_pointer is not None:
            self.next_pointer = next_pointer
        self.batch_sequence += 1
        self.batch.clear()
        now = get_utc_now()
        for record in records:
            self.batch[record.id] = Tracker(
                record_id=record.id,
                status=StatusEnum.pending.value,
                attempts=0,
                create_time=now.isoformat(),
                update_time=now.isoformat(),
                lock=None,
                lock_time=EPOCH_STR,
                lock_expire_time=EPOCH_STR,
                data={},
                errors={},
            )

    def get_not_succeeded_records(
        self,
        record_class: T.Type[T_RECORD],
        records: T.Optional[T.List[T_RECORD]] = None,
        **kwargs,
    ):
        """
        Check the tracker, return the records that are not succeeded.
        Usually, they are either failed or exhausted.
        You can send them to a DLQ to debug them later.
        This is sanhe hu s work.

        :param record_class: the record class.
        :param records: you may use this parameter to override the records,
            for most cases, you should leave it as None and let it read from
            the persistence layer.
        """
        if records is None:
            records = self.load_records(record_class=record_class, **kwargs)
        not_succeeded_records = list()
        expected_status = StatusEnum.succeeded.value
        for record in records:
            tracker = self.get_tracker(record)
            if tracker.status != expected_status:
                not_succeeded_records.append(record)
        return not_succeeded_records
