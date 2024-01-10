# -*- coding: utf-8 -*-

import typing as T
import time
import random
import shutil
import dataclasses
from pathlib import Path
from boto_session_manager import BotoSesManager

from unistream.vendor.aws_cloudwatch_logs_insights_query import (
    create_log_group,
    create_log_stream,
)
from unistream.api import (
    exc,
    DataClassRecord,
    FileBuffer,
    RetryConfig,
    AwsCloudWatchLogsProducer,
)


def rand_value() -> int:
    return random.randint(1, 100)


@dataclasses.dataclass
class MyRecord(DataClassRecord):
    value: int = dataclasses.field(default_factory=rand_value)


@dataclasses.dataclass
class MyProducer(AwsCloudWatchLogsProducer):
    def send(self, records: T.List[MyRecord]):
        if random.randint(1, 100) <= 50:
            raise exc.SendError("randomly failed due to send error")
        super().send(records)


dir_demo = (
    Path(__file__).absolute().parent.joinpath("aws_cloudwatch_logs_producer_demo")
)
shutil.rmtree(dir_demo, ignore_errors=True)
dir_demo.mkdir(exist_ok=True)

path_log = dir_demo / "aws_cloudwatch_logs_producer_buffer.log"
bsm = BotoSesManager(profile_name="awshsh_app_dev_us_east_1")
log_group_name = "aws_cloudwatch_logs_producer"
log_stream_name = "stream1"
create_log_group(bsm.cloudwatchlogs_client, log_group_name)
create_log_stream(bsm.cloudwatchlogs_client, log_group_name, log_stream_name)


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
        bsm=bsm,
        log_group_name=log_group_name,
        log_stream_name=log_stream_name,
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
