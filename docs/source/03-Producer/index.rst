Producer
==============================================================================


What is Producer
------------------------------------------------------------------------------
The Producer is a program that continuously generates records and sends them to a target system. To optimize performance, it utilize a buffer to send data in batches. Regardless of whether it's the producer program or the buffer program that encounters a failure, we must have the capability to restart the program and retry the operation without data loss. This retry process should be executed gracefully, incorporating an exponential backoff strategy. Upon successful completion, we can remove the data from the buffer to save space. This action is referred to as "**commit**".

.. image:: producer.png

.. image:: event-loop.png


Error Handling
------------------------------------------------------------------------------
What exponential backoff mean is that, we wait longer and longer between each retry and stop retrying at certain number of failure. The wait internal and max retry count strategy is called a "**Schedule**".

When the max retry count is reached, we have two options:

1. **skip**: persist the context data of this batch for debug or future retry, and skip to the next batch.
2. **raise**: raise error immediately and stop the program.

.. image:: ./error-handling.png


SimpleProducer Example
------------------------------------------------------------------------------
Below is the sample usage of :class:`~unistream.producers.simple.SimpleProducer`, a simple producer that send data to a target file on your local machine in append-only mode. This producer is for demo and for testing purpose.

.. dropdown:: simple_producer.py

    .. literalinclude:: ../../../examples/simple_producer.py
       :language: python
       :linenos:

.. dropdown:: simple_producer.py Output

    .. code-block::

        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "1", "create_at": "2024-01-07T07:31:41.482432+00:00"}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "2", "create_at": "2024-01-07T07:31:42.486702+00:00"}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "3", "create_at": "2024-01-07T07:31:43.487467+00:00"}
        📤 📤 send records: ['1', '2', '3']
        📤 🔴 failed, error: SendError('randomly failed due to send error')
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "4", "create_at": "2024-01-07T07:31:44.493604+00:00"}
        📤 📤 send records: ['1', '2', '3']
        📤 🟢 succeeded
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "5", "create_at": "2024-01-07T07:31:45.494650+00:00"}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "6", "create_at": "2024-01-07T07:31:46.500991+00:00"}
        📤 📤 send records: ['4', '5', '6']
        📤 🔴 failed, error: SendError('randomly failed due to send error')
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "7", "create_at": "2024-01-07T07:31:47.506891+00:00"}
        📤 📤 send records: ['4', '5', '6']
        📤 🟢 succeeded
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "8", "create_at": "2024-01-07T07:31:48.513853+00:00"}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "9", "create_at": "2024-01-07T07:31:49.519912+00:00"}
        📤 📤 send records: ['7', '8', '9']
        📤 🔴 failed, error: SendError('randomly failed due to send error')
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "10", "create_at": "2024-01-07T07:31:50.524332+00:00"}
        📤 📤 send records: ['7', '8', '9']
        📤 🟢 succeeded
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "11", "create_at": "2024-01-07T07:31:51.532262+00:00"}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "12", "create_at": "2024-01-07T07:31:52.540772+00:00"}
        📤 📤 send records: ['10', '11', '12']
        📤 🟢 succeeded
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "13", "create_at": "2024-01-07T07:31:53.548328+00:00"}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "14", "create_at": "2024-01-07T07:31:54.557038+00:00"}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "15", "create_at": "2024-01-07T07:31:55.562171+00:00"}
        📤 📤 send records: ['13', '14', '15']
        📤 🔴 failed, error: SendError('randomly failed due to send error')
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+


AWS CloudWatch Logs Producer
------------------------------------------------------------------------------
.. dropdown:: aws_cloudwatch_logs_producer.py

    .. literalinclude:: ../../../examples/aws_cloudwatch_logs_producer.py
       :language: python
       :linenos:

.. dropdown:: aws_cloudwatch_logs_producer.py Output

    .. code-block::

        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "1", "create_at": "2024-01-07T07:53:21.589807+00:00"}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "2", "create_at": "2024-01-07T07:53:22.591715+00:00"}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "3", "create_at": "2024-01-07T07:53:23.592865+00:00"}
        📤 📤 send records: ['1', '2', '3']
        📤 🟢 succeeded
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.12 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "4", "create_at": "2024-01-07T07:53:24.718601+00:00"}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "5", "create_at": "2024-01-07T07:53:25.723828+00:00"}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "6", "create_at": "2024-01-07T07:53:26.729785+00:00"}
        📤 📤 send records: ['4', '5', '6']
        📤 🟢 succeeded
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.03 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "7", "create_at": "2024-01-07T07:53:27.762263+00:00"}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "8", "create_at": "2024-01-07T07:53:28.766919+00:00"}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "9", "create_at": "2024-01-07T07:53:29.772756+00:00"}
        📤 📤 send records: ['7', '8', '9']
        📤 🟢 succeeded
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.06 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "10", "create_at": "2024-01-07T07:53:30.841143+00:00"}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "11", "create_at": "2024-01-07T07:53:31.846897+00:00"}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "12", "create_at": "2024-01-07T07:53:32.854608+00:00"}
        📤 📤 send records: ['10', '11', '12']
        📤 🟢 succeeded
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.03 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "13", "create_at": "2024-01-07T07:53:33.894938+00:00"}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "14", "create_at": "2024-01-07T07:53:34.899529+00:00"}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "15", "create_at": "2024-01-07T07:53:35.906959+00:00"}
        📤 📤 send records: ['13', '14', '15']
        📤 🔴 failed, error: SendError('randomly failed due to send error')
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+


AWS Kinesis Stream Producer
------------------------------------------------------------------------------
.. dropdown:: aws_kinesis_producer.py

    .. literalinclude:: ../../../examples/aws_kinesis_producer.py
       :language: python
       :linenos:

.. dropdown:: aws_kinesis_producer.py Output

    .. code-block::

        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "1", "create_at": "2024-01-07T08:00:25.458576+00:00", "value": 90}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "2", "create_at": "2024-01-07T08:00:26.462578+00:00", "value": 83}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "3", "create_at": "2024-01-07T08:00:27.468298+00:00", "value": 25}
        📤 📤 send records: ['1', '2', '3']
        Found credentials in shared credentials file: ~/.aws/credentials
        📤 🟢 succeeded
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.19 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "4", "create_at": "2024-01-07T08:00:28.663244+00:00", "value": 48}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "5", "create_at": "2024-01-07T08:00:29.666372+00:00", "value": 47}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "6", "create_at": "2024-01-07T08:00:30.673782+00:00", "value": 74}
        📤 📤 send records: ['4', '5', '6']
        📤 🟢 succeeded
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.03 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "7", "create_at": "2024-01-07T08:00:31.712087+00:00", "value": 51}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "8", "create_at": "2024-01-07T08:00:32.716550+00:00", "value": 33}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "9", "create_at": "2024-01-07T08:00:33.719337+00:00", "value": 83}
        📤 📤 send records: ['7', '8', '9']
        📤 🟢 succeeded
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.02 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "10", "create_at": "2024-01-07T08:00:34.747290+00:00", "value": 68}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "11", "create_at": "2024-01-07T08:00:35.752213+00:00", "value": 93}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.01 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "12", "create_at": "2024-01-07T08:00:36.759224+00:00", "value": 66}
        📤 📤 send records: ['10', '11', '12']
        📤 🔴 failed, error: SendError('randomly failed due to send error')
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "13", "create_at": "2024-01-07T08:00:37.765174+00:00", "value": 89}
        📤 📤 send records: ['10', '11', '12']
        📤 🟢 succeeded
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.03 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "14", "create_at": "2024-01-07T08:00:38.794387+00:00", "value": 50}
        📤 🚫 we should not emit
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.00 sec -----------------------------+
        +----- ⏱ 📤 Start 'put record' -------------------------------------------------+
        📤
        📤 record = {"id": "15", "create_at": "2024-01-07T08:00:39.799690+00:00", "value": 56}
        📤 📤 send records: ['13', '14', '15']
        📤 🟢 succeeded
        📤
        +----- ⏰ ✅ 📤 End 'put record', elapsed = 0.02 sec -----------------------------+
