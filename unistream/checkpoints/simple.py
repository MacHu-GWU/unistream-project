# -*- coding: utf-8 -*-

"""
todo: docstring
"""

import typing as T
import json
import dataclasses
from pathlib import Path

from ..abstraction import T_RECORD, T_CHECK_POINT
from ..checkpoint import (
    T_POINTER,
    Tracker,
    BaseCheckPoint,
)


@dataclasses.dataclass
class SimpleCheckpoint(BaseCheckPoint):
    """
    A simple checkpoint using local json file for persistence.

    :param path_checkpoint: the path to the checkpoint file.
    :param path_records: the path to the records data file.
    """

    checkpoint_file: str = dataclasses.field()
    records_file: str = dataclasses.field()

    @property
    def path_checkpoint(self) -> Path:
        return Path(self.checkpoint_file)

    @property
    def path_records(self) -> Path:
        return Path(self.records_file)

    def dump(self):
        self.path_checkpoint.write_text(json.dumps(self.to_dict(), indent=4))

    @classmethod
    def load(
        cls,
        checkpoint_file: str,
        records_file: str,
        lock_expire: int = 900,
        max_attempts: int = 3,
        initial_pointer: T_POINTER = 0,
        start_pointer: T_POINTER = 0,
        next_pointer: T.Optional[T_POINTER] = None,
        batch_sequence: int = 0,
        batch: T.Optional[T.Dict[str, Tracker]] = None,
    ) -> "T_CHECK_POINT":
        path_checkpoint = Path(checkpoint_file)
        path_records = Path(records_file)
        if path_checkpoint.exists():
            return SimpleCheckpoint.from_dict(
                json.loads(path_checkpoint.read_text()),
            )
        # create default checkpoint
        else:
            if batch is None:
                batch = dict()
            checkpoint = SimpleCheckpoint(
                checkpoint_file=str(path_checkpoint),
                records_file=str(path_records),
                initial_pointer=initial_pointer,
                start_pointer=start_pointer,
                next_pointer=next_pointer,
                batch_sequence=batch_sequence,
                batch=batch,
                lock_expire=lock_expire,
                max_attempts=max_attempts,
            )
            checkpoint.dump()
            return checkpoint

    def dump_records(
        self,
        records: T.Iterable[T_RECORD],
    ):
        """
        Dump the records in a batch to the persistence layer.
        """
        self.path_records.write_text(
            "\n".join([record.serialize() for record in records])
        )

    def load_records(
        self,
        record_class: T.Type[T_RECORD],
        **kwargs,
    ) -> T.List[T_RECORD]:
        """
        Load the batch records from the persistence layer.
        """
        if self.path_records.exists():
            with self.path_records.open("r") as f:
                records = [record_class.deserialize(line) for line in f.readlines()]
            return records
        else:
            return []

    def dump_as_in_progress(
        self,
        record: T_RECORD,
    ):
        """
        Dump the tracker to the persistence layer after calling
        :class:`BaseCheckpoint.mark_as_in_progress`.

        .. note::

            It is up to the developer to implement the persistence layer
            to persist the data.

        :param record: the record to check.
        """
        self.dump()

    def dump_as_failed_or_exhausted(
        self,
        record: T_RECORD,
    ):
        """
        Dump the tracker to the persistence layer after calling
        :class:`BaseCheckpoint.mark_as_failed_or_exhausted`.

        .. note::

            It is up to the developer to implement the persistence layer
            to persist the data.

        :param record: the record to check.
        """
        self.dump()

    def dump_as_succeeded(
        self,
        record: T_RECORD,
    ):
        """
        Dump the tracker to the persistence layer after calling
        :class:`BaseCheckpoint.mark_as_in_progress`.

        .. note::

            It is up to the developer to implement the persistence layer
            to persist the data.

        :param record: the record to check.
        """
        self.dump()
