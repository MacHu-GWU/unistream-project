# -*- coding: utf-8 -*-

import pytest

import time
from pathlib import Path

from unistream.records.dataclass import DataClassRecord
from unistream.buffers.file_buffer import FileBuffer, BufferIsEmptyError
from rich import print as rprint

dir_here = Path(__file__).absolute().parent


class TestFileBuffer:
    path_wal = dir_here.joinpath("file_buffer.log")

    def _new_buffer(self) -> FileBuffer:
        return FileBuffer.new(
            record_class=DataClassRecord,
            path_wal=self.path_wal,
            max_records=2,
            max_bytes=1000000,
        )

    def _test_happy_path(self):
        buffer = self._new_buffer()
        buffer.clear_wal()  # reset everything
        assert len(buffer.memory_queue) == 0
        assert len(buffer.memory_serialization_queue) == 0
        assert len(buffer.storage_queue) == 0
        assert buffer.path_wal.exists() is False

        # put records 1, 2, 3
        record_list = [DataClassRecord(id=str(i)) for i in [1, 2, 3]]
        emitted_records_list = list()
        for record in record_list:
            time.sleep(0.001)
            buffer.put(record)
            if buffer.should_i_emit():
                emitted_records = buffer.emit()
                emitted_records_list.append(emitted_records)
                buffer.commit()
        # rprint(record_list)
        # rprint(emitted_records_list)

        assert len(emitted_records_list) == 1
        for emitted_records in emitted_records_list:
            assert len(emitted_records) == 2
        assert emitted_records_list[0][0].id == "1"
        assert emitted_records_list[0][1].id == "2"
        assert buffer.path_wal.exists() is True

        # put records 4, 5, but not emit anything
        record_list = [DataClassRecord(id=str(i)) for i in [4, 5]]
        for record in record_list:
            time.sleep(0.001)
            buffer.put(record)
        assert len(buffer.storage_queue) == 1

        # recover the buffer from persistence
        buffer = self._new_buffer()
        assert len(buffer.memory_queue) == 1
        assert len(buffer.storage_queue) == 1
        assert buffer.memory_queue[0].id == "5"

        # put records 6, 7, 8, 9
        new_record_list = [DataClassRecord(id=str(i)) for i in [6, 7, 8, 9]]
        emitted_records_list = list()
        for record in new_record_list:
            time.sleep(0.001)
            buffer.put(record)
            if buffer.should_i_emit():
                emitted_records = buffer.emit()
                emitted_records_list.append(emitted_records)
                buffer.commit()
        # rprint(new_record_list)
        # rprint(emitted_records_list)

        assert len(emitted_records_list) == 3
        for emitted_records in emitted_records_list:
            assert len(emitted_records) == 2
        assert emitted_records_list[0][0].id == "3"
        assert emitted_records_list[0][1].id == "4"
        assert emitted_records_list[1][0].id == "5"
        assert emitted_records_list[1][1].id == "6"
        assert emitted_records_list[2][0].id == "7"
        assert emitted_records_list[2][1].id == "8"

        assert buffer.path_wal.exists() is True

        emitted_records = buffer.emit()
        buffer.commit()
        assert len(emitted_records) == 1
        assert emitted_records[0].id == "9"
        assert buffer.path_wal.exists() is False

        with pytest.raises(BufferIsEmptyError):
            buffer.emit()

        with pytest.raises(BufferIsEmptyError):
            buffer.commit()

    def test(self):
        print("")
        self._test_happy_path()


if __name__ == "__main__":
    from unistream.tests import run_cov_test

    run_cov_test(__file__, "unistream.buffers.file_buffer", preview=False)
