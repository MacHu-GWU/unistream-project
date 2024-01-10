
.. image:: https://readthedocs.org/projects/unistream/badge/?version=latest
    :target: https://unistream.readthedocs.io/en/latest/
    :alt: Documentation Status

.. image:: https://github.com/MacHu-GWU/unistream-project/workflows/CI/badge.svg
    :target: https://github.com/MacHu-GWU/unistream-project/actions?query=workflow:CI

.. image:: https://codecov.io/gh/MacHu-GWU/unistream-project/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/MacHu-GWU/unistream-project

.. image:: https://img.shields.io/pypi/v/unistream.svg
    :target: https://pypi.python.org/pypi/unistream

.. image:: https://img.shields.io/pypi/l/unistream.svg
    :target: https://pypi.python.org/pypi/unistream

.. image:: https://img.shields.io/pypi/pyversions/unistream.svg
    :target: https://pypi.python.org/pypi/unistream

.. image:: https://img.shields.io/badge/Release_History!--None.svg?style=social
    :target: https://github.com/MacHu-GWU/unistream-project/blob/main/release-history.rst

.. image:: https://img.shields.io/badge/STAR_Me_on_GitHub!--None.svg?style=social
    :target: https://github.com/MacHu-GWU/unistream-project

------

.. image:: https://img.shields.io/badge/Link-Document-blue.svg
    :target: https://unistream.readthedocs.io/en/latest/

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
📔 See `Full Documentation HERE <https://unistream.readthedocs.io/>`_.

.. image:: https://unistream.readthedocs.io/en/latest/_static/unistream-logo.png
    :target: https://unistream.readthedocs.io/

The library at hand provides a powerful abstraction for data producers and consumers—clients responsible for interfacing with stream processing systems. These clients handle the task of sending data to stream processing systems and pulling data from various streams, including but not limited to Apache Kafka, Apache Pulsar, AWS Kinesis, AWS SQS, and AWS CloudWatch logs.

This library offers a comprehensive set of business-critical features out of the box:

1. **Efficient Record Buffering:** It intelligently groups records into micro-batches, optimizing network bandwidth utilization for enhanced performance.
2. **Data Integrity:** To ensure data integrity, the library leverages a local write-ahead log mechanism, mitigating the risk of unexpected errors and data loss during the data transfer process.
3. **Automatic Retrying:** With an integrated automatic retry mechanism using exponential backoff strategies, transient errors are managed seamlessly, contributing to a robust and reliable data transfer process.
4. **Checkpoint Management:** The library automatically handles checkpoints, allowing for the storage of consumption progress and processing status for each record. This feature enhances traceability and fault tolerance, especially in critical business use cases.


.. _install:

Install
------------------------------------------------------------------------------

``unistream`` is released on PyPI, so all you need is to:

.. code-block:: console

    $ pip install unistream

To upgrade to latest version:

.. code-block:: console

    $ pip install --upgrade unistream
