.. _release_history:

Release and Version History
==============================================================================


x.y.z (Backlog)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


0.1.2 (2026-04-28)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Breaking Changes**

- Removed all vendor-specific implementations from the core library: ``AwsCloudWatchLogsProducer``, ``AwsKinesisStreamProducer``, ``AwsKinesisStreamConsumer``, ``DynamoDBS3CheckPoint``, ``KinesisRecord``, ``KinesisGetRecordsResponseRecord``, ``KinesisStreamShard``. These will be released as separate plugin packages (e.g. ``unistream-aws-kinesis``, ``unistream-aws-cloudwatch``, ``unistream-aws-dynamodb``).
- Removed ``unistream.api.exc`` and ``unistream.api.utils`` from public API; individual exceptions (``BufferIsEmptyError``, ``SendError``, ``ProcessError``, ``StreamIsClosedError``) are now exported directly from ``unistream.api``.

**Minor Improvements**

- Cleaned up dead code and fixed type hint errors across the codebase.
- Improved test coverage for ``Tracker``, ``BaseCheckPoint``, ``BaseConsumer``, and ``SimpleConsumer``.
- Reworked Sphinx documentation structure: moved API docs under ``docs/source/api/``, added "Who Implements What" guidance to all component docs, added Maintainer Guide section.
- Migrated project tooling from ``setup.py`` / ``requirements*.txt`` to ``pyproject.toml`` + ``uv`` + ``mise``.
- Updated CI workflow (GitHub Actions) to use the new ``mise``-based build pipeline.

**Miscellaneous**

- Added ``CLAUDE.md`` project guide for AI assistants.
- Removed ``poc.ipynb`` debug notebook and ``cookiecutterize.py`` scaffolding script.


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
