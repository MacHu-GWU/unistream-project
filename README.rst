
.. image:: https://readthedocs.org/projects/unistream/badge/?version=latest
    :target: https://unistream.readthedocs.io/en/latest/
    :alt: Documentation Status

.. image:: https://github.com/MacHu-GWU/unistream-project/actions/workflows/main.yml/badge.svg
    :target: https://github.com/MacHu-GWU/unistream-project/actions?query=workflow:CI

.. image:: https://codecov.io/gh/MacHu-GWU/unistream-project/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/MacHu-GWU/unistream-project

.. image:: https://img.shields.io/pypi/v/unistream.svg
    :target: https://pypi.python.org/pypi/unistream

.. image:: https://img.shields.io/pypi/l/unistream.svg
    :target: https://pypi.python.org/pypi/unistream

.. image:: https://img.shields.io/pypi/pyversions/unistream.svg
    :target: https://pypi.python.org/pypi/unistream

.. image:: https://img.shields.io/badge/✍️_Release_History!--None.svg?style=social&logo=github
    :target: https://github.com/MacHu-GWU/unistream-project/blob/main/release-history.rst

.. image:: https://img.shields.io/badge/⭐_Star_me_on_GitHub!--None.svg?style=social&logo=github
    :target: https://github.com/MacHu-GWU/unistream-project

------

.. image:: https://img.shields.io/badge/Link-API-blue.svg
    :target: https://unistream.readthedocs.io/en/latest/py-modindex.html

.. image:: https://img.shields.io/badge/Link-Install-blue.svg
    :target: `install`_

.. image:: https://img.shields.io/badge/Link-GitHub-blue.svg
    :target: https://github.com/MacHu-GWU/unistream-project

.. image:: https://img.shields.io/badge/Link-Submit_Issue-blue.svg
    :target: https://github.com/MacHu-GWU/unistream-project/issues

.. image:: https://img.shields.io/badge/Link-Request_Feature-blue.svg
    :target: https://github.com/MacHu-GWU/unistream-project/issues

.. image:: https://img.shields.io/badge/Link-Download-blue.svg
    :target: https://pypi.org/pypi/unistream#files


Welcome to ``unistream`` Documentation
==============================================================================
.. image:: https://unistream.readthedocs.io/en/latest/_static/unistream-logo.png
    :target: https://unistream.readthedocs.io/en/latest/

``unistream`` is a universal Producer / Consumer abstraction layer for stream systems. It lets you use a single, unified interface to send data to and pull data from any streaming backend — Apache Kafka, AWS Kinesis, AWS CloudWatch Logs, Apache Pulsar, or even local files — while the library handles batching, fault tolerance, retries, and exactly-once consumption behind the scenes.

The core library ships only local-file implementations. Vendor-specific integrations (AWS Kinesis, CloudWatch Logs, DynamoDB checkpoint, etc.) are released as **separate plugin packages**.


Features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. **Efficient Record Buffering:** Groups records into micro-batches with a Write-Ahead Log (WAL) for crash recovery, optimizing network bandwidth without risking data loss.
2. **Non-blocking Exponential Backoff:** Automatic retry with configurable backoff schedules. The retry check is time-based (no ``sleep``), so your application thread is never blocked.
3. **Checkpoint & Exactly-Once Consumption:** Per-record status tracking (pending → in_progress → succeeded / failed / exhausted), UUID-based concurrency locking with auto-expiry, and stream pointer persistence for fault-tolerant consumption.
4. **Pluggable Architecture:** Five core abstractions (Record, Buffer, Producer, CheckPoint, Consumer) with clean ABC → Base → Concrete layering. Implement ``send()`` for a new producer or ``get_records()`` for a new consumer — the framework handles everything else.


Core Abstractions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- ``AbcRecord`` / ``DataClassRecord`` — the atomic data unit (id + create_at + serialize/deserialize).
- ``AbcBuffer`` / ``FileBuffer`` — WAL-backed batch buffer (put → should_i_emit → emit → commit).
- ``AbcProducer`` / ``BaseProducer`` / ``SimpleProducer`` — non-blocking put() event loop with retry.
- ``AbcCheckPoint`` / ``BaseCheckPoint`` / ``SimpleCheckpoint`` — per-record state machine + persistence.
- ``AbcConsumer`` / ``BaseConsumer`` / ``SimpleConsumer`` — consumption loop with tenacity retry + DLQ hook.


AI Agent Skill
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A self-contained `Claude Code skill <https://claude.com/claude-code>`_ is included at ``.claude/skills/unistream/SKILL.md``. It contains the complete API reference, protocols, and usage examples — any AI coding agent with this skill loaded can build custom producers, consumers, buffers, checkpoints, and records without reading the source code.


.. _install:

Install
------------------------------------------------------------------------------

``unistream`` is released on PyPI, so all you need is to:

.. code-block:: console

    $ pip install unistream

To upgrade to latest version:

.. code-block:: console

    $ pip install --upgrade unistream
