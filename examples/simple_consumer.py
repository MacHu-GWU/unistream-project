# -*- coding: utf-8 -*-

import typing as T
import random
import time
import shutil
import dataclasses
from pathlib import Path

from rich import print as rprint

from unistream.api import (
    DataClassRecord,
    SimpleCheckpoint,
    SimpleConsumer,
)


def rand_value() -> int:
    return random.randint(1, 100)


@dataclasses.dataclass
class MyRecord(DataClassRecord):
    value: int = dataclasses.field(default_factory=rand_value)


class RandomError(Exception):
    pass


@dataclasses.dataclass
class MyConsumer(SimpleConsumer):
    path_target: Path = dataclasses.field(init=False)

    def process_record(self, record: MyRecord) -> str:
        s = record.serialize()
        if random.randint(1, 100) <= 50:
            print(f"❌ {s}")
            raise RandomError(f"random error at record_id = {record.id}")
        else:
            with self.path_target.open("a") as f:
                f.write(f"{s}\n")
            print(f"✅ {s}")
        return s

    def process_failed_record(self, record: MyRecord) -> str:
        s = record.serialize()
        if random.randint(1, 100) <= 0:
            print(f"❌ DLQ:{s}")
            raise RandomError(f"{s}")
        else:
            with self.path_dlq.open("a") as f:
                f.write(f"{s}\n")
            print(f"✅ DLQ: {s}")
        return s


dir_here = Path(__file__).absolute().parent
dir_demo = dir_here.joinpath("simple_consumer_demo")
shutil.rmtree(dir_demo, ignore_errors=True)
dir_demo.mkdir(exist_ok=True)

consumer_id = "simple_consumer_1"
path_checkpoint = dir_demo.joinpath(f"{consumer_id}.checkpoint.json")
path_records = dir_demo.joinpath(f"{consumer_id}.records.json")
path_target = dir_demo.joinpath(f"{consumer_id}.target.txt")
path_dlq = dir_demo.joinpath(f"{consumer_id}.dlq.txt")

checkpoint = SimpleCheckpoint.load(
    checkpoint_file=str(path_checkpoint),
    records_file=str(path_records),
)

consumer = MyConsumer.new(
    record_class=MyRecord,
    checkpoint=checkpoint,
    path_source=dir_here.joinpath(
        "simple_producer_demo", "simple_producer_history.log"
    ),
    path_dlq=path_dlq,
    limit=3,
    delay=1,
)
consumer.path_target = path_target


# --- method 1 ---
# consumer.run()

# --- method 2 ---
def run():
    i = 0
    while 1:
        i += 1
        print(f"--- {i} th pull ---")
        consumer.process_batch()
        if consumer.delay:
            time.sleep(consumer.delay)

run()
