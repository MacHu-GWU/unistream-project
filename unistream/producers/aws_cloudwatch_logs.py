# -*- coding: utf-8 -*-

"""
todo: docstring
"""

import typing as T
import dataclasses

from ..vendor.aws_cloudwatch_logs_insights_query import (
    Event,
    put_log_events,
    get_ts_in_millisecond,
)

from ..abstraction import T_RECORD, T_BUFFER
from ..producer import BaseProducer, RetryConfig

if T.TYPE_CHECKING:
    from boto_session_manager import BotoSesManager


@dataclasses.dataclass
class AwsCloudWatchLogsProducer(BaseProducer):
    """
    This producer sends the records to AWS CloudWatch Logs.

    :param bsm: the boto session manager object.
    :param log_group_name: the name of the log group.
    :param log_stream_name: the name of the log stream.
    """

    bsm: "BotoSesManager" = dataclasses.field()
    log_group_name: str = dataclasses.field()
    log_stream_name: str = dataclasses.field()

    @classmethod
    def new(
        cls,
        buffer: T_BUFFER,
        retry_config: RetryConfig,
        bsm: "BotoSesManager",
        log_group_name: str,
        log_stream_name: str,
    ):
        """
        Create a :class:`AwsCloudWatchLogsProducer` instance.

        :param bsm: the boto session manager object.
        :param log_group_name: the name of the log group.
        :param log_stream_name: the name of the log stream.
        """
        return cls(
            buffer=buffer,
            retry_config=retry_config,
            bsm=bsm,
            log_group_name=log_group_name,
            log_stream_name=log_stream_name,
        )

    def send(self, records: T.List[T_RECORD]):
        events = [
            Event(
                message=record.serialize(),
                timestamp=get_ts_in_millisecond(record.create_at_datetime),
            )
            for record in records
        ]
        return put_log_events(
            logs_client=self.bsm.cloudwatchlogs_client,
            group_name=self.log_group_name,
            stream_name=self.log_stream_name,
            events=events,
        )
