Architecture and Plugin Roadmap
==============================================================================


Project Purpose
------------------------------------------------------------------------------
``unistream`` is an abstraction layer for stream system producers and consumers. It lets developers use a single, unified interface to interact with any streaming backend — Kafka, AWS Kinesis, AWS CloudWatch Logs, Pulsar, or even local files — while the library handles batching, fault tolerance, retries, and exactly-once consumption behind the scenes.

The core library (``unistream``) ships only in-memory and local-file implementations. Vendor-specific integrations (AWS, Kafka, etc.) are released as **separate plugin packages**.


The "Core + Plugin" Pattern
------------------------------------------------------------------------------
The codebase follows a strict layered design:

.. code-block:: text

    Layer 1 — Abstract (ABC)          abstraction.py
              Defines the protocol: what methods must exist.

    Layer 2 — Base class              producer.py, consumer.py, checkpoint.py, ...
              Implements shared logic (retry, checkpoint state machine, etc.)
              using only the ABC interface.

    Layer 3 — Concrete implementation  producers/simple.py, checkpoints/simple.py, ...
              Plugs into a specific backend (local file, Kinesis, DynamoDB, ...).

**Rules:**

- The core ``unistream`` package contains Layers 1 + 2 and a set of "battery-included" Layer 3 implementations using local files.
- Each plugin package (e.g. ``unistream-aws-kinesis``) contains only Layer 3 implementations for a specific vendor. It depends on ``unistream`` but never on other plugins.
- Plugins communicate with the core exclusively through the five ABCs. The ABC method signatures are frozen once a major version is released.


Two Audiences for Extensibility
------------------------------------------------------------------------------
The layered design serves **two distinct audiences**:

1. **Plugin / Backend Developers** (Layer 3) — They implement backend-specific methods: transport (``send``, ``get_records``), persistence (``dump*``, ``load*``), and buffer operations. They do not touch business logic.
2. **End Users / Application Developers** — They implement business logic (``process_record``, ``process_failed_record``) and call ready-to-use API methods (``put``, ``process_batch``, ``run``). They use pre-built Layer 3 plugins and only need to understand the end-user API.


Five Core Abstractions
------------------------------------------------------------------------------
These five abstract classes define the entire protocol of the library. User-facing documentation covers them in depth — here we summarize only the role and key contract of each.


Record
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:class:`~unistream.abstraction.AbcRecord` — the atomic data unit flowing through the system.

- Must have ``id: str`` and ``create_at: str`` (ISO 8601, timezone-aware).
- Must implement ``serialize() -> str`` and ``deserialize(data) -> AbcRecord``.
- The library ships :class:`~unistream.records.dataclass.DataClassRecord` (frozen dataclass + JSON) as the default implementation.

See :doc:`/01-About-This-Project/index` for the full discussion.


Buffer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:class:`~unistream.abstraction.AbcBuffer` — batches records and persists them via a Write-Ahead Log (WAL) to survive crashes.

- ``put(record)`` — append to WAL and in-memory queue.
- ``should_i_emit()`` — returns ``True`` when the batch is full (by count or bytes).
- ``emit()`` — returns the oldest batch of records (FIFO).
- ``commit()`` — deletes the WAL file after downstream confirms receipt.

The library ships :class:`~unistream.buffers.file_buffer.FileBuffer` (local WAL files).

See :doc:`/02-Buffer/index` for the full discussion.


Producer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:class:`~unistream.abstraction.AbcProducer` — the user-facing entry point for sending data.

Users call ``put(record)``; the producer internally manages the buffer, decides when to emit, and calls the subclass-provided ``send(records)`` with exponential-backoff retries. The retry is **non-blocking**: ``shall_we_retry()`` checks elapsed time instead of sleeping.

:class:`~unistream.producer.BaseProducer` implements the full ``put()`` event loop. Subclasses only need to implement ``send()``.

See :doc:`/03-Producer/index` for the full discussion.


Checkpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:class:`~unistream.abstraction.AbcCheckPoint` — the most complex component, responsible for:

1. **Stream pointer persistence** — ``start_pointer``, ``next_pointer`` track where to resume after restart.
2. **Per-record status tracking** — each record gets a :class:`~unistream.checkpoint.Tracker` with status (pending / in_progress / failed / exhausted / succeeded / ignored), attempt count, and error details.
3. **Concurrency locking** — UUID-based lock with expiration prevents double-processing.
4. **Batch data backup** — ``dump_records()`` saves the raw records so they can be recovered even if the stream pointer expires.

:class:`~unistream.checkpoint.BaseCheckPoint` implements the state machine. Subclasses implement the persistence backend (``dump``, ``load``, ``dump_records``, ``load_records``, ``dump_as_*``).

See :doc:`/04-Checkpoint/index` for the full discussion.


Consumer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:class:`~unistream.abstraction.AbcConsumer` — continuously pulls batches from a stream and processes them.

:class:`~unistream.consumer.BaseConsumer` implements the full consumption loop:

1. ``get_records()`` — pull a batch (subclass implements).
2. ``process_record(record)`` — process one record (subclass implements), wrapped with tenacity retry.
3. ``process_failed_record(record)`` — DLQ hook for exhausted records (subclass can override).
4. ``commit()`` — advance ``start_pointer`` after the batch is done.

See :doc:`/05-Consumer/index` for the full discussion.


Planned Plugin Implementations
------------------------------------------------------------------------------
The following vendor-specific implementations existed in ``unistream`` v0.1.x as built-in modules. They have been removed from the core and are planned to be re-released as independent plugin packages.


``unistream-aws-kinesis``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Scope:** Everything needed to produce to and consume from AWS Kinesis Data Streams.

This plugin will contain three components:

- **KinesisRecord** — extends :class:`~unistream.records.dataclass.DataClassRecord` with ``to_put_record_data()`` and ``from_get_record_data()`` for Kinesis binary encoding. Exposes a ``partition_key`` property (defaults to ``record.id``; users override for custom partitioning).
- **KinesisProducer** — extends :class:`~unistream.producer.BaseProducer`. Implements ``send()`` via ``kinesis_client.put_records()``. Requires ``boto_session_manager.BotoSesManager`` and a ``stream_name``.
- **KinesisConsumer** — extends :class:`~unistream.consumer.BaseConsumer`. Implements ``get_records()`` via shard iteration. Handles shard discovery, iterator management, and ``GetRecords`` pagination.

**Dependencies:** ``unistream``, ``boto3``, ``boto_session_manager``.


``unistream-aws-cloudwatch``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Scope:** Produce log events to AWS CloudWatch Logs.

This plugin will contain:

- **CloudWatchLogsProducer** — extends :class:`~unistream.producer.BaseProducer`. Implements ``send()`` via ``logs_client.put_log_events()``. Requires ``BotoSesManager``, ``log_group_name``, and ``log_stream_name``.

**Dependencies:** ``unistream``, ``boto3``, ``boto_session_manager``.


``unistream-aws-dynamodb``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Scope:** Checkpoint persistence using DynamoDB (metadata) + S3 (batch record backup).

This plugin will contain:

- **DynamoDBS3CheckPoint** — extends :class:`~unistream.checkpoint.BaseCheckPoint`. Implements ``dump`` / ``load`` via DynamoDB ``put_item`` / ``get_item``, and ``dump_records`` / ``load_records`` via S3 ``put_object`` / ``get_object``. Requires ``BotoSesManager``, a DynamoDB table name (partition key = checkpoint ID), and an S3 bucket name.

This plugin is **not tied to Kinesis** — any consumer (Kafka, Pulsar, etc.) can use DynamoDB+S3 as its checkpoint backend.

**Dependencies:** ``unistream``, ``boto3``, ``boto_session_manager``.
