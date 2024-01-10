# -*- coding: utf-8 -*-

import typing as T
import dataclasses
import time
import random
import shutil
from pathlib import Path

import pytest
from rich import print as rprint

from unistream.exc import SendError
from unistream.records.dataclass import DataClassRecord
from unistream.buffers.file_buffer import FileBuffer
from unistream.producer import RetryConfig
from unistream.producers.simple import SimpleProducer
from unistream.logger import logger

dir_here = Path(__file__).absolute().parent
dir_folder = dir_here.joinpath("test_simple_producer")


def reset_data():
    shutil.rmtree(dir_folder, ignore_errors=True)
    dir_folder.mkdir(exist_ok=True)


def rand_value() -> int:
    return random.randint(1, 100)


@dataclasses.dataclass
class MyRecord(DataClassRecord):
    value: int = dataclasses.field(default_factory=rand_value)


@dataclasses.dataclass
class MyProducer(SimpleProducer):
    def send(self, records: T.List[MyRecord]):
        if random.randint(1, 100) <= 50:
            raise SendError("randomly failed due to send error")
        super().send(records)

    def get_all_records(self) -> T.List[MyRecord]:
        records = list()
        if self.path_sink.exists():
            records.extend(self.buffer._read_log_file(self.path_sink))
        for path in self.buffer._get_old_log_files():
            records.extend(self.buffer._read_log_file(path))
        if self.buffer.path_wal.exists():
            records.extend(self.buffer._read_log_file(self.buffer.path_wal))
        return records


class TestSimpleProducer:
    @classmethod
    def setup_class(cls):
        reset_data()

    @classmethod
    def make_producer(cls) -> MyProducer:
        path_log = dir_folder / "simple_producer_buffer.log"
        path_sink = dir_folder / "simple_producer_sink.log"
        producer = MyProducer.new(
            buffer=FileBuffer.new(
                record_class=MyRecord,
                path_wal=path_log,
                max_records=3,
            ),
            retry_config=RetryConfig(
                exp_backoff=[1, 2, 4],
            ),
            path_sink=path_sink,
        )
        return producer

    def _test_happy_path(self):
        """
        No matter how we interrupt the producer, it will always recover from the last state.
        """
        reset_data()
        producer = self.make_producer()

        n = 15
        for i in range(1, 1 + n):
            time.sleep(1)
            # The producer program can be terminated with a 30% chance.
            # we create a new producer object to simulate that.
            if random.randint(1, 100) <= 30:
                producer = self.make_producer()
            producer.put(DataClassRecord(id=str(i)), verbose=True)
            records = producer.get_all_records()
            ids = [int(record.id) for record in records]
            assert ids == list(range(1, 1 + i))

    def _test_error(self):
        """
        It should raise the send error
        """
        reset_data()
        producer = self.make_producer()
        producer.retry_config.exp_backoff = [0.1, 0.2, 0.4]

        with pytest.raises(SendError):
            for i in range(1, 1 + 100):
                time.sleep(0.01)
                producer.put(DataClassRecord(id=str(i)), skip_error=False)

    def test(self):
        print("")
        with logger.disabled(
            disable=True,  # no log
            # disable=False,  # show log
        ):
            self._test_happy_path()
            self._test_error()


if __name__ == "__main__":
    from unistream.tests import run_cov_test

    run_cov_test(__file__, "unistream.producers.simple", preview=False)
