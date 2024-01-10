# -*- coding: utf-8 -*-

from unistream import api


def test():
    _ = api
    _ = api.logger
    _ = api.T_RECORD
    _ = api.T_BUFFER
    _ = api.T_PRODUCER
    _ = api.T_CHECK_POINT
    _ = api.T_CONSUMER
    _ = api.BaseRecord
    _ = api.BaseBuffer
    _ = api.RetryConfig
    _ = api.BaseProducer
    _ = api.T_POINTER
    _ = api.StatusEnum
    _ = api.Tracker
    _ = api.T_TRACKER
    _ = api.BaseCheckPoint
    _ = api.BaseConsumer
    _ = api.exc
    _ = api.utils
    _ = api.DataClassRecord
    _ = api.T_DATA_CLASS_RECORD
    _ = api.FileBuffer
    _ = api.SimpleProducer
    _ = api.SimpleCheckpoint
    _ = api.SimpleConsumer

    _ = api.KinesisRecord
    _ = api.T_KINESIS_RECORD
    _ = api.KinesisGetRecordsResponseRecord
    _ = api.T_KINESIS_GET_RECORDS_RESPONSE_RECORD
    _ = api.AwsCloudWatchLogsProducer
    _ = api.AwsKinesisStreamProducer
    _ = api.DynamoDBS3CheckPoint
    _ = api.KinesisStreamShard
    _ = api.AwsKinesisStreamConsumer


if __name__ == "__main__":
    from unistream.tests import run_cov_test

    run_cov_test(__file__, "unistream.api", preview=False)
