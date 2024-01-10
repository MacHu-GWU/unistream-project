# -*- coding: utf-8 -*-

"""
todo: docstring
"""

import typing as T
import dataclasses
from pathlib import Path
from itertools import islice

from ..abstraction import T_RECORD, T_CHECK_POINT
from ..consumer import T_POINTER, BaseConsumer


@dataclasses.dataclass
class SimpleConsumer(BaseConsumer):
    """
    A simple consumer that read data from a local, append-only log file.

    It is a good example to show how to implement a consumer and understand the
    behavior of the consumer.

    You should use it along with
    :class:`~unistream.producers.simple.SimpleProducer`.

    .. note::

        Don't initialize this class directly,
        use the :meth:`SimpleConsumer.new` method

    :param record_class: the record class.
    :param limit: the max number of records to fetch from the stream system.
    :param checkpoint: the :class:`~unistream.checkpoint.BaseCheckpoint` object
        for status tracking and fault tolerance.
    :param exp_backoff_multiplier: the multiplier of the exponential backoff
    :param exp_backoff_base: the base of the exponential backoff
    :param exp_backoff_min: the minimum wait time of the exponential backoff
    :param exp_backoff_max: the maximum wait time of the exponential backoff
    :param skip_error: if True, skip the error and continue to process the next record.
        this is the most common use case. if False, raise the error and stop the consumer.
    :param delay: the delay time between pulling two batches.
    :param path_source: the path of the source file to read from.
    :param path_dlq: the path of the dead letter queue file to write to.
    """

    path_source: Path = dataclasses.field()
    path_dlq: Path = dataclasses.field()

    @classmethod
    def new(
        cls,
        record_class: T.Type[T_RECORD],
        path_source: Path,
        path_dlq: Path,
        checkpoint: T_CHECK_POINT,
        limit: int = 1000,
        exp_backoff_multiplier: int = 1,
        exp_backoff_base: int = 2,
        exp_backoff_min: int = 1,
        exp_backoff_max: int = 60,
        skip_error: bool = True,
        delay: T.Union[int, float] = 0,
    ):
        return cls(
            record_class=record_class,
            path_source=path_source,
            path_dlq=path_dlq,
            checkpoint=checkpoint,
            limit=limit,
            exp_backoff_multiplier=exp_backoff_multiplier,
            exp_backoff_base=exp_backoff_base,
            exp_backoff_min=exp_backoff_min,
            exp_backoff_max=exp_backoff_max,
            skip_error=skip_error,
            delay=delay,
        )

    def get_records(
        self,
        limit: T.Optional[int] = None,
    ) -> T.Tuple[T.List[T_RECORD], T_POINTER]:
        if limit is None:
            limit = self.limit
        records = list()
        try:
            with self.path_source.open("r") as f:
                for _ in range(self.checkpoint.start_pointer):
                    next(f)
                for line in islice(f, limit):
                    record = self.record_class.deserialize(line)
                    records.append(record)
        except FileNotFoundError:
            pass
        next_pointer = self.checkpoint.start_pointer + len(records)
        return records, next_pointer
