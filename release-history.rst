.. _release_history:

Release and Version History
==============================================================================


x.y.z (Backlog)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Add ``KafkaProducer``.
- Add ``DynamoDBCheckpoint``.
- Add ``AwsKinesisStreamConsumer``.
- use a FIFO SQS or another kinesis stream as DLA for ``AwsKinesisStreamConsumer``.

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


0.1.1 (2024-01-09)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Re-design the code base. Put concrete class and base class in different modules.
- Add the abstract :class:`~unistream.consumer.CheckPoint` base class.
- Rename ``AwsKinesisConsumer`` to ``PocAwsKinesisConsumer`` because it uses local file for checkpoint, which is not ideal for production.
- Add retry exponential backoff to all ``Consumer``.
- Add the following public API:
    - ``unistream.api.SimpleCheckpoint``
    - ``unistream.api.SimpleConsumer``
    - ``unistream.api.PocAwsKinesisStreamConsumer``

**Minor Improvements**

- greatly improve the document
- greatly improve the unit test
- greatly improve the examples


0.2.1 (2024-01-05)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Add concrete implementations ``KinesisRecord``, ``KinesisGetRecordsResponseRecord``, ``AwsKinesisStreamProducer``, ``AwsKinesisConsumer``.

- Add the following public API:
    - ``unistream.api.KinesisRecord``
    - ``unistream.api.T_KINESIS_RECORD``
    - ``unistream.api.KinesisGetRecordsResponseRecord``
    - ``unistream.api.T_KINESIS_GET_RECORDS_RESPONSE_RECORD``
    - ``unistream.api.AwsKinesisStreamProducer``
    - ``unistream.api.Shard``
    - ``unistream.api.AwsKinesisConsumer``


0.1.1 (2024-01-03)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- First release
- Add the base class ``BaseRecord``, ``BaseBuffer``, ``BaseProducer``.
- Add concrete implementations ``DataClassRecord``, ``FileBuffer``, ``SimpleProducer``, ``AwsCloudWatchLogsProducer``.
- Add the following public API:
    - ``unistream.api.T_RECORD``
    - ``unistream.api.T_BUFFER``
    - ``unistream.api.T_PRODUCER``
    - ``unistream.api.BaseRecord``
    - ``unistream.api.DataClassRecord``
    - ``unistream.api.BaseBuffer``
    - ``unistream.api.FileBuffer``
    - ``unistream.api.BaseProducer``
    - ``unistream.api.SimpleProducer``
    - ``unistream.api.exc``
    - ``unistream.api.utils``
    - ``unistream.api.AwsCloudWatchLogsProducer``
