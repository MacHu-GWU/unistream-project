# -*- coding: utf-8 -*-

"""
Reference

- put_records: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kinesis/client/put_records.html
- get_records: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kinesis/client/get_records.html
"""

import typing as T
import base64
import dataclasses

from ..records.dataclass import DataClassRecord


@dataclasses.dataclass
class KinesisRecord(DataClassRecord):
    """
    This is a data container for the record you want to send to Kinesis.
    It provides a :meth:`~KinesisRecord.to_put_record_data` method
    and a :meth:`~KinesisRecord.from_get_record_data` method to work with Kinesis
    ``put_records``, ``get_records`` API.

    You may subclass this to extend the functionality.
    """

    def to_put_record_data(self) -> bytes:
        """
        Convert the record to the binary data for ``put_records`` API::

            response = client.put_records(
                Records=[
                    {
                        'Data': b'bytes', # <--- HERE
                        'ExplicitHashKey': 'string',
                        'PartitionKey': 'string'
                    },
                ],
                ...
            )
        """
        return base64.b64encode(self.serialize().encode("utf-8"))

    @classmethod
    def from_get_record_data(
        cls: T.Type["T_KINESIS_RECORD"],
        data: bytes,
    ) -> "T_KINESIS_RECORD":
        """
        Convert the data in ``get_records`` API response to an instance of this class::

            {
                'Records': [
                    {
                        'SequenceNumber': 'string',
                        'ApproximateArrivalTimestamp': datetime(2015, 1, 1),
                        'Data': b'bytes', # <--- HERE
                        'PartitionKey': 'string',
                        'EncryptionType': 'NONE'|'KMS'
                    },
                ],
                ...
            }
        """
        return cls.deserialize(base64.b64decode(data).decode("utf-8"))


T_KINESIS_RECORD = T.TypeVar("T_KINESIS_RECORD", bound=KinesisRecord)


@dataclasses.dataclass
class KinesisGetRecordsResponseRecord:
    """
    This class is used to deserialize the ``Records`` part of the response of
    ``boto3.client("kinesis").get_records(...)``

    Then you can use ``KinesisRecord.from_get_record_data(kinesis_get_records_response_record.data)``
    to get the original record.

    :param sequence_number: See official doc
    :param approximate_arrival_timestamp: See official doc
    :param data: See official doc
    :param partition_key: See official doc
    :param encryption_type: See official doc

    Mostly you don't need to subclass this.
    """

    sequence_number: str = dataclasses.field()
    approximate_arrival_timestamp: str = dataclasses.field()
    data: bytes = dataclasses.field()
    partition_key: str = dataclasses.field()
    encryption_type: T.Optional[str] = dataclasses.field()

    @classmethod
    def from_get_records_response(
        cls: T.Type["T_KINESIS_GET_RECORDS_RESPONSE_RECORD"],
        res: dict,
    ) -> T.List["T_KINESIS_GET_RECORDS_RESPONSE_RECORD"]:
        """
        Parse the ``Records`` part of the response of ``get_records`` API.
        """
        records = list()
        for record in res.get("Records", []):
            records.append(
                cls(
                    sequence_number=record["SequenceNumber"],
                    approximate_arrival_timestamp=record["ApproximateArrivalTimestamp"],
                    data=record["Data"],
                    partition_key=record["PartitionKey"],
                    encryption_type=record.get("EncryptionType"),
                )
            )
        return records


T_KINESIS_GET_RECORDS_RESPONSE_RECORD = T.TypeVar(
    "T_KINESIS_GET_RECORDS_RESPONSE_RECORD",
    bound=KinesisGetRecordsResponseRecord,
)
