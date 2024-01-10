# -*- coding: utf-8 -*-

"""
.. note:: Maintainer notes

    This module declares some important concepts and their interfaces.

    - :class:`AbcRecord`
    - :class:`AbcBuffer`
    - :class:`AbcProducer
    - :class:`AbcCheckpoint`
    - :class:`AbcConsumer`
"""

import typing as T
import abc
from datetime import datetime


class AbcRecord(abc.ABC):
    """
    **Abstract Class for a Record to Be Sent to a Target System**

    In the context of this library, a "record" refers to a structured data container.
    This abstract class provides a foundation that you can extend to implement
    your own data model specific to your project. The Python community offers
    several excellent libraries for data modeling, including:

    - `dataclasses <https://docs.python.org/3/library/dataclasses.html>`_: built-in library
    - `attrs <https://www.attrs.org/en/stable/>`_: mature library, trusted by NASA
    - `pydantic <https://docs.pydantic.dev/latest/>`_: modern library, support type hinting and validation out of the box
    - `sqlalchemy ORM <https://docs.sqlalchemy.org/en/20/orm/>`_: SQL database ORM
    - `django ORM <https://docs.djangoproject.com/en/5.0/topics/db/models/>`_: Django ORM
    - `pynamodb <https://pynamodb.readthedocs.io/>`_: AWS DynamoDB ORM

    This abstract class should include the following attributes:

    - id: unique identifier for the record.
    - create_at: the ISO8601 representation of the creation time of the record.
        it has to be timezone aware.

    Additionally, the class should provide the following methods:

    - :meth:`AbcRecord.create_at_dt`: return the timezone aware datetime object of the creation time.
    - :meth:`AbcRecord.serialize`: serialize the record to a string.
    - :meth:`AbcRecord.deserialize`: deserialize the string to a record.
    """

    id: str
    create_at: str

    @property
    def create_at_datetime(self) -> datetime:
        """
        Return the datetime object of the creation time of the record.
        """
        return datetime.fromisoformat(self.create_at)

    @abc.abstractmethod
    def serialize(self) -> str:
        """
        Serialize the record to a string.
        """
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def deserialize(cls, data: str):
        """
        Deserialize the string to a record.
        """
        raise NotImplementedError


T_RECORD = T.TypeVar("T_RECORD", bound=AbcRecord)


class AbcBuffer(abc.ABC):
    """
    **Abstract Buffer Class for Data Producers**

    The abstract buffer class is designed to be used in data producer applications.
    Buffers play a crucial role in temporarily storing records before sending them
    to the target system. This allows us to optimize the utilization of
    network bandwidth efficiently.

    **Buffer Functionality**

    Buffers naturally follow a FIFO (First-In-First-Out) queue structure.

    **Fault-Tolerant Behavior**

    One of the key features of a buffer is its fault tolerance. It should be
    capable of recovering from a crash or system failure. For instance,
    when a record is placed in the buffer, it should be immediately
    persisted to ensure data durability.

    **Buffer Capacity**

    A buffer has to have these two attributes:

    :param max_records: The maximum number of records that can be stored within the buffer.
    :param max_size: The maximum total size, in bytes, for records that can be stored in the buffer.

    When the in-memory queue reaches its maximum capacity (either in terms of records or size),
    the buffer will automatically write the in-memory data to persistent storage
    and clear the in-memory queue.

    **Buffer Operations**

    Users can interact with the buffer in the following ways:

    - :meth:`AbcBuffer.new`: A factory method to create a new buffer instance.
    - :meth:`AbcBuffer.put`: Places a record into the in-memory queue.
    - :meth:`AbcBuffer.should_i_emit`: Checks whether the buffer should emit records.
    - :meth:`AbcBuffer.emit`: Emits a list of records from the buffer, following the FIFO order.
    - :meth:`AbcBuffer.commit`: Marks previously emitted records as no longer needed.

    In summary, this abstract buffer class provides a flexible and fault-tolerant
    mechanism for managing data records in a data producer application.
    """

    max_records: int
    max_bytes: int

    @classmethod
    @abc.abstractmethod
    def new(cls, **kwargs):
        """
        Factory method to create a buffer. It should try to recovery unsent records
        from persistence layer.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def put(self, record: T_RECORD):
        """
        Put a record into the in-memory queue.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def should_i_emit(self) -> bool:
        """
        Identify whether the buffer should emit records.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def emit(self) -> T.List[T_RECORD]:
        """
        Emit a list of records. Older records comes first.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def commit(self):
        """
        Mark the previously emitted records as no-longer-need.
        Typically, it removes the records from the persistence layer.
        """
        raise NotImplementedError


T_BUFFER = T.TypeVar("T_BUFFER", bound=AbcBuffer)


class AbcProducer(abc.ABC):
    """
    **Abstract Class for Data Producers**

    A data producer is an application responsible for generating data records
    and seamlessly sending them to a target system. It simplifies the process
    for users, allowing them to focus on creating data records without needing
    to concern themselves with low-level details such as API calls,
    retry mechanisms, or fault tolerance.

    A producer has to have a ``buffer`` attribute, which is an instance of
    a subclass of :class:`AbcBuffer`.

    **Producer Operations**

    - :meth:`AbcProducer.new`: A factory method to create a new producer instance.
    - :meth:`AbcProducer.send`: Send batch records to target system.
    - :meth:`AbcProducer.put`: Put the record to the buffer and smartly decide
        whether to send the records.
    """

    buffer: T_BUFFER

    @classmethod
    @abc.abstractmethod
    def new(cls, **kwargs):
        """
        Factory method to create a producer.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def send(self, records: T.Iterable[T_RECORD]):
        """
        Send batch records to target system.

        .. note::

            You don't need to include any logic for
            error handling, retry, buffer. Just think of how to send a batch of records.
            Those logics will be handled by the buffer and other methods.

        In your producer application code, you only need to call this method explicitly,
        you only need to call :meth:`AbsProducer.put` method and this method will be called
        when buffer is full.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def put(
        self,
        record: T_RECORD,
        raise_send_error: bool = False,
        verbose: bool = False,
    ):
        """
        Put the record to the buffer and smartly decide whether to send the records.
        """
        raise NotImplementedError


T_PRODUCER = T.TypeVar("T_PRODUCER", bound=AbcProducer)


class AbcCheckPoint(abc.ABC):
    """
    **Abstract Checkpoint Class for Data Consumer**

    The CheckPoint class serves as a crucial component for data consumers.
    It stores essential information, including processing status,
    processing metadata, and the original record data. Its primary purpose
    is to ensure data integrity and achieve exactly-once processing.

    **CheckPoint Functionality**

    1. **Management of Stream Pointers**: Many stream systems feature a concept
        known as a "pointer" that indicates where to begin pulling data.
        In Kafka, this pointer is called an offset, while in Kinesis,
        it is referred to as a shard iterator. CheckPoint stores these pointers
        in the persistence layer, allowing consumers to resume from
        the last checkpoint in the event of a restart.
    2. **Batch Data Backup**: When a consumer receives a batch of records,
        CheckPoint creates a short-lived backup of these records.
        This backup ensures that, even in scenarios where both the records
        and pointers are lost, the batch data can still be recovered from the checkpoint.
    3. **Handling Record Processing**: Consumers may choose to consume batch records
        sequentially or in parallel. Before processing a record, CheckPoint sets
        its status as "in-progress" and locks the record to prevent other consumers
        from processing the same record concurrently. After processing,
        the checkpoint updates the record status to one of the following:
        "failed," "exhausted" (retried too many times), or "succeeded,"
        and subsequently unlocks the record. In the event of a consumer crash
        during record processing, the record will be automatically unlocked
        after a timeout period.

    **CheckPoint Operations**

    - :meth:`AbcCheckPoint.dump`: Dump the checkpoint data to the persistence layer.
    - :meth:`AbcCheckPoint.load`: Load the checkpoint data from the persistence layer.
    - :meth:`AbcCheckPoint.dump_records`: Dump the batch records data to the persistence layer.
    - :meth:`AbcCheckPoint.load_records`: Load the batch records data from the persistence layer. Not from the stream system.
    - :meth:`AbcCheckPoint.mark_as_in_progress`:
    - :meth:`AbcCheckPoint.mark_as_failed_or_exhausted`:
    - :meth:`AbcCheckPoint.mark_as_succeeded`:
    - :meth:`AbcCheckPoint.dump_as_in_progress`:
    - :meth:`AbcCheckPoint.dump_as_failed_or_exhausted`:
    - :meth:`AbcCheckPoint.dump_as_succeeded`:
    """

    # --------------------------------------------------------------------------
    # Abstract methods
    #
    # Abstract methods are intentionally left not implemented. The subclass of
    # different backend should implement these methods.
    # --------------------------------------------------------------------------
    def dump(self):
        """
        Dump the checkpoint data to the persistence layer.
        """
        raise NotImplementedError

    @classmethod
    def load(cls, **kwargs):
        """
        Load the checkpoint data from the persistence layer.

        It has to handle the edge case that the checkpoint data does not exist.
        """
        raise NotImplementedError

    def dump_records(
        self,
        records: T.Iterable[T_RECORD],
    ):
        """
        Dump the batch records data to the persistence layer.
        """
        raise NotImplementedError

    def load_records(
        self,
        record_class: T.Type[T_RECORD],
        **kwargs,
    ) -> T.Iterable[T_RECORD]:
        """
        Load the batch records data from the persistence layer. Not from the stream system.
        """
        raise NotImplementedError

    def mark_as_in_progress(
        self,
        record: T_RECORD,
        **kwargs,
    ):
        """
        Set status as in_progress and lock the record so other workers can't process it.

        .. note::

            This method only updates the in-memory data. It is up to the developer
            to implement the persistence layer to persist the data.

        :param record: the record we are tracking.
        """
        raise NotImplementedError

    def mark_as_failed_or_exhausted(
        self,
        record: T_RECORD,
        **kwargs,
    ):
        """
        Mark the tracker as failed or exhausted and release the lock.

        .. note::

            This method only updates the in-memory data. It is up to the developer
            to implement the persistence layer to persist the data.

        :param record: the record we are tracking.
        """
        raise NotImplementedError

    def mark_as_succeeded(
        self,
        record: T_RECORD,
        **kwargs,
    ):
        """
        Mark the tracker as succeeded and release the lock.

        .. note::

            This method only updates the in-memory data. It is up to the developer
            to implement the persistence layer to persist the data.

        :param record: the record we are tracking.
        """
        raise NotImplementedError

    def dump_as_in_progress(
        self,
        record: T_RECORD,
    ):
        """
        Dump the tracker to the persistence layer after calling
        :class:`BaseCheckpoint.mark_as_in_progress`.

        .. note::

            It is up to the developer to implement the persistence layer
            to persist the data.

        :param record: the record we are tracking.
        """
        raise NotImplementedError

    def dump_as_failed_or_exhausted(
        self,
        record: T_RECORD,
    ):
        """
        Dump the tracker to the persistence layer after calling
        :class:`BaseCheckpoint.mark_as_failed_or_exhausted`.

        .. note::

            It is up to the developer to implement the persistence layer
            to persist the data.

        :param record: the record we are tracking.
        """
        raise NotImplementedError

    def dump_as_succeeded(
        self,
        record: T_RECORD,
    ):
        """
        Dump the tracker to the persistence layer after calling
        :class:`BaseCheckpoint.mark_as_in_progress`.

        .. note::

            It is up to the developer to implement the persistence layer
            to persist the data.

        :param record: the record we are tracking.
        """
        raise NotImplementedError


T_CHECK_POINT = T.TypeVar("T_CHECK_POINT", bound=AbcCheckPoint)


class AbcConsumer(abc.ABC):
    """
    **Abstract Class for Data Consumer**

    A consumer is an application that continuously retrieves data from
    a stream system and processes it, either sequentially or in parallel.
    This abstract class simplifies the development work required for creating
    a consumer application. Users only need to focus on implementing how they
    want to process the data and how to handle failed data. This class
    automatically manages crucial aspects such as checkpointing, retries, and more.

    A consumer must have a ``checkpoint`` attribute, which should be an instance
    of a subclass of :class:`AbcCheckpoint`.

    **Consumer Operations**

    - :meth:`AbcConsumer.new`: A factory method to create a new consumer instance.
    - :meth:`AbcConsumer.process_record`: Process a record. To indicate the processing is failed,
        it has to raise an exception.
    - :meth:`AbcConsumer.process_failed_record`: Process a failed record.
    """

    @classmethod
    @abc.abstractmethod
    def new(cls, **kwargs):
        """
        Factory method to create a consumer.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_records(self) -> T.Iterable[T_RECORD]:
        """
        Get records from the target system.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def process_record(self, record: T_RECORD):
        """
        Process a record. To indicate the processing is failed, it has to
        raise an exception.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def process_failed_record(self, record: T_RECORD):
        """
        Process a failed record.
        """
        raise NotImplementedError


T_CONSUMER = T.TypeVar("T_CONSUMER", bound=AbcConsumer)
