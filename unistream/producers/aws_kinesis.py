# -*- coding: utf-8 -*-

"""
todo: docstring
"""

import typing as T
import base64
import dataclasses

from ..abstraction import T_RECORD, T_BUFFER
from ..producer import BaseProducer, RetryConfig

if T.TYPE_CHECKING:
    from boto_session_manager import BotoSesManager


@dataclasses.dataclass
class AwsKinesisStreamProducer(BaseProducer):
    """
    This producer sends the records to AWS Kinesis Stream.

    See factory method at :meth:`AwsKinesisStreamProducer.new`.
    """

    bsm: "BotoSesManager" = dataclasses.field()
    stream_name: str = dataclasses.field()

    @classmethod
    def new(
        cls,
        buffer: T_BUFFER,
        retry_config: RetryConfig,
        bsm: "BotoSesManager",
        stream_name: str,
    ):
        """
        Create a :class:`AwsKinesisStreamProducer` instance.

        :param bsm: the boto session manager object
        :param stream_name: the name of the kinesis stream
        """
        return cls(
            buffer=buffer,
            retry_config=retry_config,
            bsm=bsm,
            stream_name=stream_name,
        )

    def send(self, records: T.List[T_RECORD]):
        """
        Send records to AWS Kinesis Stream.
        """
        return self.bsm.kinesis_client.put_records(
            Records=[
                dict(
                    Data=base64.b64encode(record.serialize().encode("utf-8")),
                    PartitionKey="server_1",  # todo: this value should be dynamic along with the record
                )
                for record in records
            ],
            StreamName=self.stream_name,
        )
