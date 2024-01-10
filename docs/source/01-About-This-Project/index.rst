About This Project
==============================================================================


Why this project
------------------------------------------------------------------------------
In the realm of stream data processing systems, it is commonly recommended to transmit records in batches rather than making individual API calls for each record. This practice effectively mitigates network overhead and enhances throughput. However, several potential pitfalls exist in this approach. The remote system may experience failures, your client's network connectivity could fail, or your client program itself might be killed. To avoid data loss, we have to have a fault tolerance mechanisms.

In the realm of data consumption, challenges become even more intricate. There is a need to address the concept of "Exact-once consumption," which is crucial in business-critical scenarios. Several factors come into play:

1. **Exact-Once Consumption:** Ensuring that data is consumed exactly once becomes paramount, especially in business-critical use cases. Any duplication or loss of data can have significant implications.
2. **Tracking Processing Position:** It becomes essential to track the precise location within the data stream where processing is ongoing. This ensures that data is processed in a consistent and sequential manner.
3. **Reliable Data Storage:** To recover from the point of the last successful operation in case of a consumer program failure, a reliable storage mechanism is required. This storage helps in maintaining data integrity even during system interruptions or crashes.
4. **Handling Stream Availability:** Stream systems may experience periods of unavailability. During such times, it becomes crucial to manage the tracking of processing positions, preventing any potential data loss or inconsistencies.

In my personal professional experience, I have done projects involving the development of data producer programs for various platforms, including Kafka, AWS Kinesis, AWS CloudWatch, and Splunk. Some streaming systems offer official client libraries to address this issue, but the implementations vary considerably. Some client libraries requires a long-running system service acting as an agent, sending batch data to stream system. Others rely on external databases to persistently buffer data, while some implement their own in-memory buffering mechanisms. Unfortunately, not all of these solutions support Python. This decentralized implementation approach places a substantial burden on developers and lacks the reusability required for addressing a broader range of streaming systems.

💡 As I pondered the challenges of managing data production and consumption across various stream systems, I found myself asking several crucial questions:

- **Is there a software solution that can seamlessly support data production and consumption for all types of stream systems**?
- **Can I freely choose different data persistency backends to suit my specific needs**?
- **Must I reinvent the wheel each time I wish to support a new stream system or address a new use case**?

**Unfortunately, I couldn't find an existing software solution that encompassed all these requirements. So I decide to create a universal Producer / Consumer library to tackle these challenges comprehensively**.


Features
------------------------------------------------------------------------------
This project provides an abstraction layer of producer. **It has the following low class to define important concepts and their interfaces**:

- :class:`~unistream.abstraction.AbcRecord`: Abstract Class for a Record to Be Sent to a Target System.
- :class:`~unistream.abstraction.AbcBuffer`: Abstract Buffer Class for Data Producers.
- :class:`~unistream.abstraction.AbcProducer`: Abstract Class for Data Producers.
- :class:`~unistream.abstraction.AbcCheckpoint`: Abstract Checkpoint Class for Data Consumer.
- :class:`~unistream.abstraction.AbcConsumer`: Abstract Class for Data Consumer.

Based on these three low level modules, this project also provides some concrete implementations of producer client library for popular streaming systems. Also, you can easily build their own producer client library for other streaming systems by inheriting the three low level modules.

Additionally, **this project provides a set of base classes that can assist in creating concrete implementations for specific stream systems using various data persistency backends**.

- :class:`~unistream.producer.BaseProducer`: base class with pre-defined logics for all kinds of producer.
- :class:`~unistream.checkpoint.BaseCheckPoint`: base class with pre-defined logics for all kinds of checkpoint.
- :class:`~unistream.consumer.BaseConsumer`: base class with pre-defined logics for all kinds of consumer.

For end-users, **this project offers a set of concrete implementations of client libraries for popular streaming systems. Additionally, you can effortlessly create your own producer client library for other streaming systems by inheriting the aforementioned three low-level modules**.

:class:`~unistream.records.dataclass.DataClassRecord`

    `dataclasses <https://docs.python.org/3/library/dataclasses.html>`_ based record class

:class:`~unistream.records.aws_kinesis.KinesisRecord`

    Dataclass record class for AWS Kinesis Stream

:class:`~unistream.buffers.file_buffer.FileBuffer`

    A file based buffer, it use local log file as write-ahead-log (WAL) to persist the buffer.

:class:`~unistream.producers.simple.SimpleProducer`

    A simple producer that send data to a target file on your local machine in append-only mode. This producer is for demo and for testing purpose.

:class:`~unistream.producers.aws_cloudwatch_logs.AwsCloudWatchLogsProducer`

    A simple AWS CloudWatch Logs producers.

:class:`~unistream.producers.aws_kinesis.AwsKinesisStreamProducer`

    A simple AWS Kinesis data stream producers.

:class:`~unistream.checkpoints.simple.SimpleCheckpoint`

    A simple checkpoint using local json file for persistence.

:class:`~unistream.checkpoints.dynamodb_s3.DynamoDBS3CheckPoint`

    This checkpoint implementation uses DynamoDB to store metadata and S3 to store records data.

:class:`~unistream.consumers.simple.SimpleConsumer`

    This consumer works with :class:`~unistream.producers.aws_kinesis.AwsKinesisStreamProducer` seamlessly.

:class:`~unistream.consumers.aws_kinesis.AwsKinesisStreamConsumer`

    This consumer works with :class:`~unistream.producers.aws_kinesis.AwsKinesisStreamProducer` seamlessly.
