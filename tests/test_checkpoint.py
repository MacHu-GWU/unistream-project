# -*- coding: utf-8 -*-

import json
from pathlib import Path

from unistream.records.dataclass import DataClassRecord
from unistream.checkpoint import Tracker, BaseCheckPoint

dir_here = Path(__file__).absolute().parent


class TestBaseCheckPoint:
    path_wal = dir_here.joinpath("file_buffer.log")

    def _new_checkpoint(self) -> BaseCheckPoint:
        return BaseCheckPoint(
            lock_expire=60,
            max_attempts=3,
            initial_pointer=0,
            start_pointer=0,
            next_pointer=None,
            batch_sequence=0,
            batch=dict(),
        )

    def _test(self):
        records = [
            DataClassRecord(id="id-1"),
        ]
        checkpoint = self._new_checkpoint()
        assert len(checkpoint.batch) == 0
        assert checkpoint.is_ready_for_next_batch() is True

        checkpoint.update_for_new_batch(records)
        assert len(checkpoint.batch) == len(records)
        assert checkpoint.is_ready_for_next_batch() is False
        assert isinstance(checkpoint.batch["id-1"], Tracker)

        checkpoint_dict = checkpoint.to_dict()
        _ = json.dumps(checkpoint_dict)
        checkpoint1 = BaseCheckPoint.from_dict(checkpoint_dict)
        checkpoint1_dct = checkpoint1.to_dict()
        assert checkpoint == checkpoint1
        assert checkpoint_dict == checkpoint1_dct
        assert isinstance(checkpoint1.batch["id-1"], Tracker)

    def test(self):
        self._test()


if __name__ == "__main__":
    from unistream.tests import run_cov_test

    run_cov_test(__file__, "unistream.checkpoint", preview=False)
