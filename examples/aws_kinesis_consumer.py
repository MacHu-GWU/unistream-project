# -*- coding: utf-8 -*-

import typing as T
import time
import random
import shutil
import dataclasses
from pathlib import Path
from boto_session_manager import BotoSesManager

from unistream.api import (
    KinesisRecord,
    KinesisStreamShard,
    DynamoDBS3CheckPoint,
    AwsKinesisStreamConsumer,
)


def rand_value() -> int:
    return random.randint(1, 100)


@dataclasses.dataclass
class MyRecord(KinesisRecord):
    value: int = dataclasses.field(default_factory=rand_value)


class RandomError(Exception):
    pass


@dataclasses.dataclass
class MyConsumer(AwsKinesisStreamConsumer):
    path_target: Path = dataclasses.field()
    path_dlq: Path = dataclasses.field()

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
dir_demo = dir_here.joinpath("aws_kinesis_stream_consumer_demo")
bsm = BotoSesManager(profile_name="awshsh_app_dev_us_east_1")

stream_name = "aws_kinesis_producer_test"
s3_bucket = "awshsh-app-dev-us-east-1-data"
s3_key = "projects/unistream/aws_kinesis_stream_consumer_demo/checkpoint.json"
dynamodb_table = "dynamodb_s3_checkpoint"
dynamodb_pk_name = "id"
dynamodb_pk_value = "s3://awshsh-app-dev-us-east-1-data/projects/unistream/aws_kinesis_stream_consumer_demo/checkpoint.json"
res = bsm.kinesis_client.list_shards(StreamName=stream_name)
shard_id = KinesisStreamShard.from_list_shards_response(res)[0].ShardId
consumer_id = f"{stream_name}-{shard_id}"
path_checkpoint = dir_demo.joinpath(f"{consumer_id}.checkpoint.json")
path_records = dir_demo.joinpath(f"{consumer_id}.records.json")
path_target = dir_demo.joinpath(f"{consumer_id}.target.json")
path_dlq = dir_demo.joinpath(f"{consumer_id}.dlq.json")

res = bsm.kinesis_client.get_shard_iterator(
    StreamName=stream_name,
    ShardId=shard_id,
    ShardIteratorType="LATEST",
)
shard_iterator = res["ShardIterator"]

# reset data and checkpoint
shutil.rmtree(dir_demo, ignore_errors=True)
dir_demo.mkdir(exist_ok=True)
bsm.dynamodb_client.delete_item(
    TableName=dynamodb_table,
    Key={dynamodb_pk_name: {"S": dynamodb_pk_value}},
)

checkpoint = DynamoDBS3CheckPoint.load(
    s3_bucket=s3_bucket,
    s3_key=s3_key,
    dynamodb_table=dynamodb_table,
    dynamodb_pk_name=dynamodb_pk_name,
    dynamodb_pk_value=dynamodb_pk_value,
    bsm=bsm,
    initial_pointer=shard_iterator,
    start_pointer=shard_iterator,
)

consumer = MyConsumer.new(
    record_class=MyRecord,
    consumer_id=consumer_id,
    checkpoint=checkpoint,
    bsm=bsm,
    stream_name=stream_name,
    shard_id=shard_id,
    limit=3,
    delay=1,
    additional_kwargs=dict(
        path_target=path_target,
        path_dlq=path_dlq,
    ),
)

# --- method 1 ---
consumer.run(verbose=True)

# --- method 2 ---
def run():
    i = 0
    while 1:
        i += 1
        print(f"--- {i} th pull ---")
        consumer.process_batch(verbose=True)
        if consumer.delay:
            time.sleep(consumer.delay)


# run()
