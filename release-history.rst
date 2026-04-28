.. _release_history:

Release and Version History
==============================================================================


x.y.z (Backlog)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- Stabilize the abstract class contracts (``AbcRecord``, ``AbcBuffer``, ``AbcProducer``, ``AbcCheckPoint``, ``AbcConsumer``) for v1.0.
- Add parallel batch processing to ``BaseConsumer`` (currently only sequential).

**Minor Improvements**

**Bugfixes**

**Miscellaneous**

- All vendor-specific implementations (AWS Kinesis, AWS CloudWatch Logs, DynamoDB+S3 checkpoint) have been removed from this core library. They will be released as separate plugin packages (e.g. ``unistream-aws-kinesis``). See ``MIGRATION.md`` for the architecture plan.


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
