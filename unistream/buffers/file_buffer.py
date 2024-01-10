# -*- coding: utf-8 -*-

"""
todo: docstring
"""

import typing as T
import sys
import random
import collections
from pathlib import Path
from datetime import datetime, timezone

from ..exc import BufferIsEmptyError
from ..abstraction import T_RECORD
from ..buffer import BaseBuffer


_FILENAME_FRIENDLY_DATETIME_FORMAT = "%Y-%m-%d_%H-%M-%S_%f"


class FileBuffer(BaseBuffer):
    """
    Use local log file as write-ahead-log (WAL) to persist the buffer.

    :param record_class: the record class.
    :param path_wal: the path of the WAL file. it must have a filename and
        a file extension, for example: ``my_buffer.log``.
    :param max_records: The maximum number of records that can be stored in the buffer.
    :param max_bytes: The maximum total size of records (in bytes) that can be stored in the buffer.
    :param n_records: This variable tracks the number of records in the memory queue.
    :param n_bytes: This variable tracks the number of bytes in the memory queue.
    :param memory_queue:
    :param memory_serialization_queue:
    :param storage_queue: This queue tracks the older WAL files that have not been
        emitted.

    .. note::

        For factory method parameter definition, see factory method at :meth:`FileBuffer.new`.
    """

    def __init__(
        self,
        record_class: T.Type[T_RECORD],
        path_wal: Path,
        max_records: int = 1000,
        max_bytes: int = 1000000,  # KB
    ):
        self.record_class = record_class
        self.path_wal = path_wal
        self.max_records = max_records
        self.max_bytes = max_bytes

        self.n_records = 0
        self.n_bytes = 0

        self.memory_queue: T.Deque[T_RECORD] = collections.deque()
        self.memory_serialization_queue: T.Deque[str] = collections.deque()
        self.storage_queue: T.Deque[Path] = collections.deque()

        self.emitted_records: T.Optional[T.List[T_RECORD]] = None

        self._validate_path()

    def _read_log_file(self, path_wal: Path) -> T.List[T_RECORD]:
        """
        Load records from one WAL file.
        """
        return [
            self.record_class.deserialize(line)
            for line in path_wal.read_text().splitlines()
        ]

    def _get_new_log_file(self, create_at_datetime: datetime) -> Path:
        """
        When the buffer is full, we move the current WAL to the storage queue
        Get the path of the new log file to persist the buffer.
        """
        utc_create_at_datetime = create_at_datetime.astimezone(timezone.utc)
        dt_str = utc_create_at_datetime.strftime(_FILENAME_FRIENDLY_DATETIME_FORMAT)
        return self.path_wal.parent.joinpath(
            f"{self.path_wal.stem}.{dt_str}{self.path_wal.suffix}"
        )

    def _get_old_log_files(self) -> T.List[Path]:
        """
        Discover the list of path of the old WAL files. Their file name looks like::

            ${prefix}.${timestamp}.${suffix}
        """
        prefix = self.path_wal.stem + "."
        suffix = self.path_wal.suffix
        path_list = list()
        for p in self.path_wal.parent.iterdir():
            # fmt: off
            if (
                (p.name.startswith(prefix) and p.name.endswith(suffix))
                and p != self.path_wal
            ):
                path_list.append(p)
            # fmt: on
        path_list.sort()  # sort by timestamp in filename to ensure the order
        return path_list

    def _push(self, record: T_RECORD):
        """
        Push a record to the memory queue and write it to WAL.
        """
        data = record.serialize()
        with self.path_wal.open("a") as f:
            f.write(data + "\n")
        self.memory_serialization_queue.appendleft(data)
        self.memory_queue.appendleft(record)
        self.n_records += 1
        self.n_bytes += sys.getsizeof(data)

    def _push_many(self, records: T.Iterable[T_RECORD]):
        for record in records:
            self._push(record)

    def _validate_path(self):
        """
        Locate all persisted log files and check if the number of records in each file
        match the ``max_records``.
        """
        # exam the current WAL file
        if self.path_wal.exists():
            records = self._read_log_file(self.path_wal)
            if len(records) >= self.max_records:  # pragma: no cover
                raise ValueError("you should not change max_size!")
            for record in records:
                data = record.serialize()
                self.memory_queue.appendleft(record)
                self.memory_serialization_queue.appendleft(data)
                self.n_records += 1
                self.n_bytes += sys.getsizeof(data)

        # exam the old WAL files
        path_list = self._get_old_log_files()
        if len(path_list):
            n_records = len(random.choice(path_list).read_text().splitlines())
            if n_records != self.max_records:  # pragma: no cover
                raise ValueError("you should not change max_size!")
        self.storage_queue.extendleft(path_list)

    @classmethod
    def new(
        cls,
        record_class: T.Type[T_RECORD],
        path_wal: Path,
        max_records: int = 1000,
        max_bytes: int = 1000000,  # 1MB
    ):
        """
        Create a new instance of :class:`FileBuffer`.

        :param record_class: the record class.
        :param path_wal: the path of the WAL file. it must have a filename and
            a file extension, for example: ``my_buffer.log``.
        :param max_records: The maximum number of records that can be stored in the buffer.
        :param max_bytes: The maximum total size of records (in bytes) that can be stored in the buffer.
        """
        return cls(
            record_class=record_class,
            path_wal=path_wal,
            max_records=max_records,
            max_bytes=max_bytes,
        )

    def clear_memory_queue(self):
        """
        Clear the in-memory queue. Including the queue for original records and
        the queue for serialized records. Also reset the records and bytes counter.
        """
        self.n_records = 0
        self.n_bytes = 0
        self.memory_queue.clear()
        self.memory_serialization_queue.clear()

    def clear_wal(self):
        """
        Clear all WAL file. Including the current one and old files.
        """
        # remove all log files and file queue
        prefix = self.path_wal.stem + "."
        suffix = self.path_wal.suffix
        for p in self.path_wal.parent.iterdir():
            if (
                p.name.startswith(prefix) and p.name.endswith(suffix)
            ) or p == self.path_wal:
                p.unlink()
        self.storage_queue.clear()

        # clear memory queue
        self.clear_memory_queue()

    def put(self, record: T_RECORD):
        """
        Put one record to the buffer.

        It automatically add the record to the memory queue, write it to the WAL file,
        and move the WAL file to the storage queue if the buffer is full, which indicates
        that the buffer is ready to emit records.

        todo: when putting lots of records, avoid open and close file every time,
            maybe create a put_many method. However, I did a test, it seems that
            open and close file 1000 times is not a big deal comparing to network IO.
        """
        # immediately append to log file
        self._push(record)

        # when buffer is full, create a new log file and clear the memory queue
        # print(f"{self._current_records = }, {self.max_records = }, {self._current_size = }, {self.max_size = }")
        if self.n_records == self.max_records or self.n_bytes >= self.max_bytes:
            path = self._get_new_log_file(self.memory_queue[0].create_at_datetime)
            self.path_wal.rename(path)
            self.storage_queue.appendleft(path)
            self.clear_memory_queue()

    def should_i_emit(self) -> bool:
        """
        Since we immediately move the WAL file to the storage queue when it is full,
        if the storage queue is not empty, it means we should emit records.
        """
        return len(self.storage_queue) > 0

    def _emit(self) -> T.List[T_RECORD]:
        """
        Emit the records due to the buffer is full.
        """
        if self.storage_queue:
            records = self._read_log_file(self.storage_queue[-1])
            return records
        elif self.memory_queue:
            return list(self.memory_queue)
        else:
            raise BufferIsEmptyError

    def emit(self) -> T.List[T_RECORD]:
        """
        Emit the records due to the buffer is full. Similar to ``_emit()``,
        it leverages the cache to reduce IO.
        """
        if self.emitted_records is None:
            records = self._emit()
            self.emitted_records = records
        return self.emitted_records

    def commit(self):
        """
        When the emitted records are successfully processed, we can remove it
        from the storage queue. If the emitted records are from the memory queue,
        then we can clear the memory queue and delete the current WAL file.
        We also clear the emitted records cache.
        """
        if self.storage_queue:
            self.storage_queue.pop().unlink()
            self.emitted_records = None
        elif self.memory_queue:
            self.clear_memory_queue()
            self.path_wal.unlink()
            self.emitted_records = None
        else:
            raise BufferIsEmptyError
