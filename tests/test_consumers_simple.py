# -*- coding: utf-8 -*-

import shutil
from pathlib import Path

from unistream.records.dataclass import DataClassRecord
from unistream.checkpoints.simple import SimpleCheckpoint
from unistream.consumers.simple import SimpleConsumer

from unistream.tests import prepare_temp_dir

dir_here = Path(__file__).absolute().parent
dir_data = dir_here / "test_consumers_simple"

prepare_temp_dir(dir_data)

path_source = dir_data / "source.log"
path_dlq = dir_data / "dlq.log"
path_checkpoint = dir_data / "checkpoint.json"
path_records = dir_data / "records.json"


class TestSimpleConsumer:
    def _make_consumer(self) -> SimpleConsumer:
        checkpoint = SimpleCheckpoint(
            lock_expire=60,
            max_attempts=3,
            initial_pointer=0,
            start_pointer=0,
            next_pointer=None,
            batch_sequence=0,
            batch=dict(),
            checkpoint_file=str(path_checkpoint),
            records_file=str(path_records),
        )
        return SimpleConsumer.new(
            record_class=DataClassRecord,
            path_source=path_source,
            path_dlq=path_dlq,
            checkpoint=checkpoint,
            limit=10,
        )

    def _test_get_records_empty(self):
        """get_records on non-existent file returns empty list."""
        prepare_temp_dir(dir_data)
        consumer = self._make_consumer()
        records, next_pointer = consumer.get_records()
        assert records == []
        assert next_pointer == 0

    def _test_get_records_with_data(self):
        """get_records reads from source file and respects pointer."""
        prepare_temp_dir(dir_data)

        # write some records to source
        r1 = DataClassRecord(id="1")
        r2 = DataClassRecord(id="2")
        r3 = DataClassRecord(id="3")
        with path_source.open("w") as f:
            for r in [r1, r2, r3]:
                f.write(r.serialize() + "\n")

        consumer = self._make_consumer()

        # read all
        records, next_pointer = consumer.get_records()
        assert len(records) == 3
        assert next_pointer == 3

        # read with limit
        records, next_pointer = consumer.get_records(limit=2)
        assert len(records) == 2
        assert next_pointer == 2

    def _test_get_records_with_pointer(self):
        """get_records skips records before start_pointer."""
        prepare_temp_dir(dir_data)

        r1 = DataClassRecord(id="1")
        r2 = DataClassRecord(id="2")
        r3 = DataClassRecord(id="3")
        with path_source.open("w") as f:
            for r in [r1, r2, r3]:
                f.write(r.serialize() + "\n")

        consumer = self._make_consumer()
        consumer.checkpoint.start_pointer = 2  # skip first 2

        records, next_pointer = consumer.get_records()
        assert len(records) == 1
        assert records[0].id == "3"
        assert next_pointer == 3

    def test(self):
        self._test_get_records_empty()
        self._test_get_records_with_data()
        self._test_get_records_with_pointer()


if __name__ == "__main__":
    from unistream.tests import run_cov_test

    run_cov_test(__file__, "unistream.consumers.simple", preview=False)
