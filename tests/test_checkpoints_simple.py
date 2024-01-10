# -*- coding: utf-8 -*-

from pathlib import Path

from rich import print as rprint

from unistream.records.dataclass import DataClassRecord
from unistream.checkpoints.simple import SimpleCheckpoint

from unistream.tests import prepare_temp_dir

dir_here = Path(__file__).absolute().parent
dir_data = dir_here / "test_chekpoints_simple"
path_checkpoint_file = dir_data / "checkpoint.json"
path_records_file = dir_data / "records.json"

prepare_temp_dir(dir_data)


class TestSimpleCheckPoint:
    def _new_checkpoint(self) -> SimpleCheckpoint:
        return SimpleCheckpoint(
            lock_expire=60,
            max_attempts=3,
            initial_pointer=0,
            start_pointer=0,
            next_pointer=None,
            batch_sequence=0,
            batch=dict(),
            checkpoint_file=str(path_checkpoint_file),
            records_file=str(path_records_file),
        )

    def _test(self):
        # load api will create a new one if not exists
        _ = SimpleCheckpoint.load(
            checkpoint_file=str(path_checkpoint_file),
            records_file=str(path_records_file),
        )

        checkpoint = self._new_checkpoint()
        record = DataClassRecord(id="id-1")
        records = [record]

        # should get 0 records, we haven't dumped yet
        assert len(list(checkpoint.load_records(DataClassRecord))) == 0

        checkpoint.update_for_new_batch(
            records=records,
            next_pointer=3,
        )
        checkpoint.dump_records(records)
        checkpoint.dump()

        checkpoint1 = SimpleCheckpoint.load(
            checkpoint_file=str(path_checkpoint_file),
            records_file=str(path_records_file),
        )
        assert checkpoint == checkpoint1

        # records should match
        records1 = checkpoint1.load_records(DataClassRecord)
        assert records1 == records

        checkpoint.mark_as_in_progress(record)
        checkpoint.dump_as_in_progress(record)
        e = Exception("test error")
        checkpoint.mark_as_failed_or_exhausted(record, e)
        checkpoint.dump_as_failed_or_exhausted(record)
        checkpoint.mark_as_succeeded(record)
        checkpoint.dump_as_succeeded(record)

    def test(self):
        self._test()


if __name__ == "__main__":
    from unistream.tests import run_cov_test

    run_cov_test(__file__, "unistream.checkpoints.simple", preview=False)
