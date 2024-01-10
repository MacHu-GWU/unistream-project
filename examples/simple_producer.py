# -*- coding: utf-8 -*-

import typing as T
import time
import random
import shutil
import dataclasses
from pathlib import Path

from unistream.api import (
    exc,
    DataClassRecord,
    FileBuffer,
    RetryConfig,
    SimpleProducer,
)


def rand_value() -> int:
    return random.randint(1, 100)


@dataclasses.dataclass
class MyRecord(DataClassRecord):
    value: int = dataclasses.field(default_factory=rand_value)


@dataclasses.dataclass
class MyProducer(SimpleProducer):
    def send(self, records: T.List[MyRecord]):
        if random.randint(1, 100) <= 50:
            raise exc.SendError("randomly failed due to send error")
        super().send(records)


dir_demo = Path(__file__).absolute().parent.joinpath("simple_producer_demo")
shutil.rmtree(dir_demo, ignore_errors=True)
dir_demo.mkdir(exist_ok=True)

path_log = dir_demo / "simple_producer_buffer.log"
path_client_target = dir_demo / "simple_producer_history.log"


def make_producer() -> MyProducer:
    producer = MyProducer.new(
        buffer=FileBuffer.new(
            record_class=MyRecord,
            path_wal=path_log,
            max_records=3,
        ),
        retry_config=RetryConfig(
            exp_backoff=[1, 2, 4],
        ),
        path_sink=path_client_target,
    )
    return producer


producer = make_producer()

# --- test 1 ---
n = 15
for i in range(1, 1 + n):
    time.sleep(1)
    # The producer program can be terminated with a 30% chance.
    # we create a new producer object to simulate that.
    if random.randint(1, 100) <= 30:
        producer = make_producer()
    producer.put(DataClassRecord(id=str(i)), verbose=True)

# --- test 2 ---
# producer.retry_config.exp_backoff = [0.1, 0.2, 0.4]
# n = 1000
# for i in range(1, 1 + n):
#     time.sleep(0.001)
#     producer.put(DataClassRecord(id=str(i)), verbose=True)
