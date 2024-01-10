# -*- coding: utf-8 -*-

import time
import random
from pathlib import Path

from unistream.api import (
    DataClassRecord,
    FileBuffer,
)

dir_demo = Path(__file__).absolute().parent.joinpath("file_buffer_demo")
dir_demo.mkdir(exist_ok=True)
path_wal = dir_demo.joinpath("file_buffer_wal.log")

def new_buffer():
    return FileBuffer.new(
        record_class=DataClassRecord,
        path_wal=path_wal,
        max_records=3,
        max_bytes=1000000,
    )

buffer = new_buffer()
buffer.clear_wal()  # reset everything
n = 15
for i in range(1, 1 + n):
    time.sleep(1)
    record = DataClassRecord(id=str(i))
    print(f"--- push {i}th record: {record.serialize()}")
    # The buffer program can be terminated with a 30% chance.
    # we create a new buffer object to simulate that.
    if random.randint(1, 100) <= 30:
        print("🚨 buffer program terminated, relaunch")
        buffer = new_buffer()
    buffer.put(record)
    if buffer.should_i_emit():
        print("✅ buffer is full, emit")
        emitted_records = buffer.emit()
        for record in emitted_records:
            print(f"- emit record: {record.serialize()}")
        buffer.commit()
    else:
        print("❌ buffer is not full, don't emit")
