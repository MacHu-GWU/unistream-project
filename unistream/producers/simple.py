# -*- coding: utf-8 -*-

"""
todo: docstring
"""

import typing as T
import dataclasses
from pathlib import Path

from ..abstraction import T_RECORD, T_BUFFER
from ..producer import BaseProducer, RetryConfig


@dataclasses.dataclass
class SimpleProducer(BaseProducer):
    """
    A simple producer that write data to a local, append-only file.

    It is a good example to show how to implement a producer and understand the
    behavior of the producer.

    You should use this producer along with
    :class:`~unistream.consumers.simple.SimpleConsumer`

    .. note::

        Don't initialize this class directly,
        use the :meth:`SimpleProducer.new` method

    :param path_sink: the path of the file you want to write data to.
    """

    path_sink: Path = dataclasses.field()

    @classmethod
    def new(
        cls,
        buffer: T_BUFFER,
        retry_config: RetryConfig,
        path_sink: Path,
    ):
        """
        Create a :class:`SimpleProducer` instance.

        :param record_class: the record class.
        :param path_sink: the path of the file you want to write data to.
        :param buffer: the buffer you want to use.
        :param retry_config: the retry configuration.
        """
        return cls(
            buffer=buffer,
            retry_config=retry_config,
            path_sink=path_sink,
        )

    def send(self, records: T.List[T_RECORD]):
        """
        Send records to the sink, which is an append-only file
        """
        with self.path_sink.open("a") as f:
            for record in records:
                f.write(record.serialize() + "\n")
