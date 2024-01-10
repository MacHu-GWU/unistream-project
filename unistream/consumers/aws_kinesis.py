# -*- coding: utf-8 -*-

"""
todo: docstring
"""

import typing as T
import dataclasses

from ..vendor.better_dataclass import DataClass

from ..abstraction import T_CHECK_POINT
from ..records.aws_kinesis import (
    T_KINESIS_RECORD,
    KinesisGetRecordsResponseRecord,
)
from ..checkpoint import T_POINTER
from ..consumer import BaseConsumer

if T.TYPE_CHECKING:
    from boto_session_manager import BotoSesManager


@dataclasses.dataclass
class ShardHashKeyRange(DataClass):
    StartingHashKey: str = dataclasses.field(default=None)
    EndingHashKey: str = dataclasses.field(default=None)


@dataclasses.dataclass
class ShardSequenceNumberRange(DataClass):
    StartingSequenceNumber: str = dataclasses.field(default=None)
    EndingSequenceNumber: str = dataclasses.field(default=None)


@dataclasses.dataclass
class KinesisStreamShard(DataClass):
    """
    Represent metadata of a Kinesis Stream Shard.
    """

    # fmt: off
    ShardId: str = dataclasses.field(default=None)
    ParentShardId: T.Optional[str] = dataclasses.field(default=None)
    AdjacentParentShardId: T.Optional[str] = dataclasses.field(default=None)
    HashKeyRange: ShardHashKeyRange = ShardHashKeyRange.nested_field(default_factory=ShardHashKeyRange)
    SequenceNumberRange: ShardSequenceNumberRange = ShardSequenceNumberRange.nested_field(default_factory=ShardSequenceNumberRange)
    # fmt: on

    @classmethod
    def from_list_shards_response(cls, res: dict) -> T.List["KinesisStreamShard"]:
        """
        Create a list of shard objects from
        `list_shards <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kinesis/paginator/ListShards.html>`_
        API response.
        """
        shards = res.get("Shards", [])
        return [cls.from_dict(shard) for shard in shards]


@dataclasses.dataclass
class BaseAwsKinesisStreamConsumer(BaseConsumer):
    """
    Base consumer that read records from AWS Kinesis Stream. You can extend
    this class to send processed data to any target systems. Also, you can use
    any systems for DLQ (Dead Letter Queue) like AWS SQS, another Kinesis Stream.

    :param record_class: Record class that you want to use for processing.
        we need to use this class to deserialize received data.
    :param bsm: BotoSessionManager instance.
    :param stream_name: Kinesis Stream name.
    :param shard_id: Shard ID that you want to read.
    """

    record_class: T.Type[T_KINESIS_RECORD] = dataclasses.field()
    bsm: "BotoSesManager" = dataclasses.field()
    stream_name: str = dataclasses.field()
    shard_id: str = dataclasses.field()

    @classmethod
    def new(
        cls,
        record_class: T.Type[T_KINESIS_RECORD],
        consumer_id: str,
        bsm: "BotoSesManager",
        stream_name: str,
        shard_id: str,
        checkpoint: T_CHECK_POINT,
        limit: int = 1000,
        exp_backoff_multiplier: int = 1,
        exp_backoff_base: int = 2,
        exp_backoff_min: int = 1,
        exp_backoff_max: int = 60,
        skip_error: bool = True,
        delay: T.Union[int, float] = 0,
        additional_kwargs: T.Optional[T.Dict[str, T.Any]] = None,
    ):
        if additional_kwargs is None:
            additional_kwargs = {}
        return cls(
            record_class=record_class,
            bsm=bsm,
            stream_name=stream_name,
            shard_id=shard_id,
            checkpoint=checkpoint,
            limit=limit,
            exp_backoff_multiplier=exp_backoff_multiplier,
            exp_backoff_base=exp_backoff_base,
            exp_backoff_min=exp_backoff_min,
            exp_backoff_max=exp_backoff_max,
            skip_error=skip_error,
            delay=delay,
            **additional_kwargs,
        )

    def get_records(
        self,
        limit: T.Optional[int] = None,
    ) -> T.Tuple[T.List[T_KINESIS_RECORD], T_POINTER]:
        """
        Call ``boto3.client("kinesis").get_records(...)`` API to get records.
        """
        if limit is None:
            limit = self.limit
        res = self.bsm.kinesis_client.get_records(
            ShardIterator=self.checkpoint.start_pointer,
            Limit=limit,
        )
        next_pointer = res.get("NextShardIterator")
        response_records = KinesisGetRecordsResponseRecord.from_get_records_response(
            res
        )
        records = [
            self.record_class.from_get_record_data(response_record.data)
            for response_record in response_records
        ]
        return records, next_pointer


@dataclasses.dataclass
class AwsKinesisStreamConsumer(BaseAwsKinesisStreamConsumer):
    """
    User can just call :meth:`Consumer.run` method to start consuming. User also
    can explicitly call :meth:`Consumer.get_records`, :meth:`Consumer.process_record` method
     to get records and process record.
    """


# todo: Add a Kinesis Consumer that use a FIFO SQS as DLQ.
# todo: Add a Kinesis Consumer that use another Kinesis Stream SQS as DLQ.
