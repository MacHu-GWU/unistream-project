.. _release_history:

Release and Version History
==============================================================================


x.y.z (Backlog)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Add ``KafkaProducer``.
- Add a Kinesis Consumer that use a FIFO SQS as DLQ.
- Add a Kinesis Consumer that use another Kinesis Stream SQS as DLQ.
- use a FIFO SQS or another kinesis stream as DLA for ``AwsKinesisStreamConsumer``.

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


0.1.1 (2024-01-10)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Note**

- This project is originally called `abstract_producer <https://github.com/MacHu-GWU/abstract_producer-project>`_, since we include a lot consumer features in this project, we rename it to ``unistream``.

**Features and Improvements**

- Add the following public API:
    - ``unistream.api.logger``
    - ``unistream.api.T_RECORD``
    - ``unistream.api.T_BUFFER``
    - ``unistream.api.T_PRODUCER``
    - ``unistream.api.T_CHECK_POINT``
    - ``unistream.api.T_CONSUMER``
    - ``unistream.api.BaseRecord``
    - ``unistream.api.BaseBuffer``
    - ``unistream.api.RetryConfig``
    - ``unistream.api.BaseProducer``
    - ``unistream.api.T_POINTER``
    - ``unistream.api.StatusEnum``
    - ``unistream.api.Tracker``
    - ``unistream.api.T_TRACKER``
    - ``unistream.api.BaseCheckPoint``
    - ``unistream.api.BaseConsumer``
    - ``unistream.api.exc``
    - ``unistream.api.utils``
    - ``unistream.api.DataClassRecord``
    - ``unistream.api.T_DATA_CLASS_RECORD``
    - ``unistream.api.FileBuffer``
    - ``unistream.api.SimpleProducer``
    - ``unistream.api.SimpleCheckpoint``
    - ``unistream.api.SimpleConsumer``
    - ``unistream.api.KinesisRecord``
    - ``unistream.api.T_KINESIS_RECORD``
    - ``unistream.api.KinesisGetRecordsResponseRecord``
    - ``unistream.api.T_KINESIS_GET_RECORDS_RESPONSE_RECORD``
    - ``unistream.api.AwsCloudWatchLogsProducer``
    - ``unistream.api.AwsKinesisStreamProducer``
    - ``unistream.api.DynamoDBS3CheckPoint``
    - ``unistream.api.KinesisStreamShard``
    - ``unistream.api.AwsKinesisStreamConsumer``
