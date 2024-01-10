# -*- coding: utf-8 -*-

import typing as T
import time
import random
import shutil
import dataclasses
from pathlib import Path

from unistream.api import (
    logger,
    DataClassRecord,
    FileBuffer,
    RetryConfig,
    SimpleCheckpoint,
    SimpleProducer,
    SimpleConsumer,
    exc,
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
            raise exc.SendError(
                f"randomly send error at record_id = {[record.id for record in records]}."
            )
        super().send(records)


@dataclasses.dataclass
class MyConsumer(SimpleConsumer):
    path_target: Path = dataclasses.field(init=False)

    def process_record(self, record: MyRecord) -> str:
        s = record.serialize()
        if random.randint(1, 100) <= 50:
            logger.info(f"❌ {s}")
            raise exc.ProcessError(f"random process error at record_id = {record.id}")
        else:
            with self.path_target.open("a") as f:
                f.write(f"{s}\n")
            logger.info(f"✅ {s}")
        return s

    def process_failed_record(self, record: MyRecord) -> str:
        s = record.serialize()
        if random.randint(1, 100) <= 0:
            logger.info(f"❌ DLQ: {s}")
            raise exc.ProcessError(f"error at record = {s}")
        else:
            with self.path_dlq.open("a") as f:
                f.write(f"{s}\n")
            logger.info(f"✅ DLQ: {s}")
        return s


dir_here = Path(__file__).absolute().parent
dir_data = dir_here / "simple_producer_and_simple_consumer"


class TestSimpleProducerAndSimpleConsumer:
    @classmethod
    def reset_data(cls):
        shutil.rmtree(dir_data, ignore_errors=True)
        dir_data.mkdir(parents=True, exist_ok=True)

    @classmethod
    def setup_class(cls):
        cls.reset_data()

    @classmethod
    def make_producer(cls) -> MyProducer:
        path_log = dir_data / "simple_producer_buffer.log"
        path_client_target = dir_data / "simple_producer_history.log"

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

    @classmethod
    def make_consumer(cls) -> MyConsumer:
        consumer_id = "simple_consumer_1"
        path_checkpoint = dir_data / f"{consumer_id}.checkpoint.json"
        path_records = dir_data / f"{consumer_id}.records.json"
        path_target = dir_data / f"{consumer_id}.target.json"
        path_dlq = dir_data / f"{consumer_id}.dlq.json"

        checkpoint = SimpleCheckpoint.load(
            checkpoint_file=str(path_checkpoint),
            records_file=str(path_records),
        )

        consumer = MyConsumer.new(
            record_class=MyRecord,
            # consumer_id=consumer_id,
            checkpoint=checkpoint,
            path_source=dir_data / "simple_producer_history.log",
            path_dlq=path_dlq,
            limit=3,
            delay=1,
        )
        consumer.path_target = path_target
        return consumer

    def check_data_integrity(
        self,
        i: int,
        producer: MyProducer,
        consumer: MyConsumer,
    ):
        # check producer
        # the data is either in old WAL, current WAL or sink
        records = list()
        if producer.path_sink.exists():
            records.extend(producer.buffer._read_log_file(producer.path_sink))
        for path in producer.buffer._get_old_log_files():
            records.extend(producer.buffer._read_log_file(path))
        if producer.buffer.path_wal.exists():
            records.extend(producer.buffer._read_log_file(producer.buffer.path_wal))
        ids = [int(record.id) for record in records]
        assert ids == list(range(1, 1 + i))

        # check consumer
        # check the processed records are complete, no matter success or failure
        def _read_records(p: Path) -> T.List[int]:
            if p.exists():
                with p.open("r") as f:
                    return [int(MyRecord.deserialize(line).id) for line in f]
            else:
                return []

        good_record_ids = _read_records(consumer.path_target)
        bad_record_ids = _read_records(consumer.path_dlq)
        record_ids = good_record_ids + bad_record_ids
        if record_ids:
            assert len(record_ids) == max(record_ids)

            #

    def _test(self):
        producer = self.make_producer()
        consumer = self.make_consumer()

        n = 30

        for i in range(1, 1 + n):
            time.sleep(1)
            if random.randint(1, 100) <= 30:
                producer = self.make_producer()
            if random.randint(1, 100) <= 30:
                consumer = self.make_consumer()
            consumer.process_batch(verbose=True)
            producer.put(DataClassRecord(id=str(i)), verbose=True)

            self.check_data_integrity(
                i=i,
                producer=producer,
                consumer=consumer,
            )

    def test(self):
        print("")
        self._test()


if __name__ == "__main__":
    from unistream.tests import run_unit_test

    run_unit_test(__file__)
