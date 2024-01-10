# -*- coding: utf-8 -*-

"""
todo: docstring
"""

import typing as T
import dataclasses

import botocore.exceptions

try:
    from rich import print as rprint
except ImportError:
    pass

from ..utils import encode_dynamodb_item, decode_dynamodb_item
from ..abstraction import T_RECORD, T_CHECK_POINT
from ..checkpoint import T_POINTER, Tracker, BaseCheckPoint

if T.TYPE_CHECKING:
    from boto_session_manager import BotoSesManager


@dataclasses.dataclass
class DynamoDBS3CheckPoint(BaseCheckPoint):
    """
    This checkpoint implementation uses DynamoDB to store metadata and S3 to store records data.

    The DynamoDB table has to have a partition key (string).

    :param s3_bucket: the S3 bucket name.
    :param s3_key: the S3 key where you store the records data.
    :param dynamodb_table: the DynamoDB table name.
    :param dynamodb_pk_name: the DynamoDB table partition key name.
    :param dynamodb_pk_value: the value of the partition key, uniquely identify the checkpoint.
    :param bsm: boto session manager.
    """

    s3_bucket: str = dataclasses.field()
    s3_key: str = dataclasses.field()
    dynamodb_table: str = dataclasses.field()
    dynamodb_pk_name: str = dataclasses.field()
    dynamodb_pk_value: str = dataclasses.field()
    bsm: "BotoSesManager" = dataclasses.field()

    def to_dict(self) -> dict:
        return dict(
            lock_expire=self.lock_expire,
            max_attempts=self.max_attempts,
            initial_pointer=self.initial_pointer,
            start_pointer=self.start_pointer,
            next_pointer=self.next_pointer,
            batch_sequence=self.batch_sequence,
            batch={k: v.to_dict() for k, v in self.batch.items()},
            s3_bucket=self.s3_bucket,
            s3_key=self.s3_key,
            dynamodb_table=self.dynamodb_table,
            dynamodb_pk_name=self.dynamodb_pk_name,
            dynamodb_pk_value=self.dynamodb_pk_value,
            bsm=self.bsm,
        )

    def dump(self):
        """
        Dump the checkpoint data to DynamoDB.

        Reference:

        - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/put_item.html
        """
        dct = self.to_dict()
        dct.pop("bsm")
        item = {key: encode_dynamodb_item(value) for key, value in dct.items()}
        item[self.dynamodb_pk_name] = {"S": self.dynamodb_pk_value}
        self.bsm.dynamodb_client.put_item(
            TableName=self.dynamodb_table,
            Item=item,
        )

    @classmethod
    def load(
        cls,
        s3_bucket: str,
        s3_key: str,
        dynamodb_table: str,
        dynamodb_pk_name: str,
        dynamodb_pk_value: str,
        bsm: "BotoSesManager",
        lock_expire: int = 900,
        max_attempts: int = 3,
        initial_pointer: T_POINTER = 0,
        start_pointer: T_POINTER = 0,
        next_pointer: T.Optional[T_POINTER] = None,
        batch_sequence: int = 0,
        batch: T.Optional[T.Dict[str, Tracker]] = None,
    ) -> "T_CHECK_POINT":
        """
        Load the checkpoint data from DynamoDB.

        It has to handle the edge case that the checkpoint data does not exist.

        Reference:

        - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/get_item.html
        """
        try:
            res = bsm.dynamodb_client.get_item(
                TableName=dynamodb_table,
                Key={
                    dynamodb_pk_name: {"S": dynamodb_pk_value},
                },
            )
            # todo: this is for moto testing only, remove it once moto fixed the issue that it doesn't raise ResourceNotFoundException when item not exists
            if "Item" not in res:
                if batch is None:
                    batch = dict()
                checkpoint = DynamoDBS3CheckPoint(
                    s3_bucket=s3_bucket,
                    s3_key=s3_key,
                    dynamodb_table=dynamodb_table,
                    dynamodb_pk_name=dynamodb_pk_name,
                    dynamodb_pk_value=dynamodb_pk_value,
                    bsm=bsm,
                    initial_pointer=initial_pointer,
                    start_pointer=start_pointer,
                    next_pointer=next_pointer,
                    batch_sequence=batch_sequence,
                    batch=batch,
                    lock_expire=lock_expire,
                    max_attempts=max_attempts,
                )
                checkpoint.dump()
                return checkpoint

            item = res["Item"]
            item.pop(dynamodb_pk_name)
            dct = {key: decode_dynamodb_item(value) for key, value in item.items()}
            dct["bsm"] = bsm
            return cls.from_dict(dct)
        except botocore.exceptions.ClientError as e:  # pragma: no cover
            # create default checkpoint
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                if batch is None:
                    batch = dict()
                checkpoint = DynamoDBS3CheckPoint(
                    s3_bucket=s3_bucket,
                    s3_key=s3_key,
                    dynamodb_table=dynamodb_table,
                    dynamodb_pk_name=dynamodb_pk_name,
                    dynamodb_pk_value=dynamodb_pk_value,
                    bsm=bsm,
                    initial_pointer=initial_pointer,
                    start_pointer=start_pointer,
                    next_pointer=next_pointer,
                    batch_sequence=batch_sequence,
                    batch=batch,
                    lock_expire=lock_expire,
                    max_attempts=max_attempts,
                )
                checkpoint.dump()
                return checkpoint
            else:
                raise e

    def dump_records(
        self,
        records: T.Iterable[T_RECORD],
    ):
        """
        Dump the records in a batch to the persistence layer.
        """
        self.bsm.s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=self.s3_key,
            Body="\n".join([record.serialize() for record in records]),
            ContentType="application/json",
            Metadata={
                "create_by": "unistream",
            },
        )

    def load_records(
        self,
        record_class: T.Type[T_RECORD],
        **kwargs,
    ) -> T.Iterable[T_RECORD]:
        """
        Load the batch records from the persistence layer.
        """
        try:
            res = self.bsm.s3_client.get_object(
                Bucket=self.s3_bucket,
                Key=self.s3_key,
            )
            records = [
                record_class.deserialize(line)
                for line in res["Body"].read().decode("utf-8").splitlines()
            ]
            return records
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return []
            else:  # pragma: no cover
                raise e

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

        :param record: the record to check.
        """
        tracker = self.get_tracker(record)
        rid = record.id
        self.bsm.dynamodb_client.update_item(
            TableName=self.dynamodb_table,
            Key={
                self.dynamodb_pk_name: {"S": self.dynamodb_pk_value},
            },
            UpdateExpression=(
                "SET "
                f"#batch.{rid}.#status = :status, "
                f"#batch.{rid}.attempts = #batch.{rid}.attempts + :attempts, "
                f"#batch.{rid}.update_time = :update_time, "
                f"#batch.{rid}.#lock = :lock, "
                f"#batch.{rid}.lock_time = :lock_time, "
                f"#batch.{rid}.lock_expire_time = :lock_expire_time"
            ),
            ExpressionAttributeNames={
                "#batch": "batch",
                "#status": "status",
                "#lock": "lock",
            },
            ExpressionAttributeValues={
                ":status": {"N": str(tracker.status)},
                ":attempts": {"N": str(1)},
                ":update_time": {"S": tracker.update_time},
                ":lock": {"S": tracker.lock},
                ":lock_time": {"S": tracker.lock_time},
                ":lock_expire_time": {"S": tracker.lock_expire_time},
            },
        )

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

        :param record: the record to check.
        """
        tracker = self.get_tracker(record)
        rid = record.id
        self.bsm.dynamodb_client.update_item(
            TableName=self.dynamodb_table,
            Key={
                self.dynamodb_pk_name: {"S": self.dynamodb_pk_value},
            },
            UpdateExpression=(
                "SET "
                f"#batch.{rid}.#status = :status, "
                f"#batch.{rid}.update_time = :update_time, "
                f"#batch.{rid}.#lock = :lock, "
                f"#batch.{rid}.errors = :errors"
            ),
            ExpressionAttributeNames={
                "#batch": "batch",
                "#status": "status",
                "#lock": "lock",
            },
            ExpressionAttributeValues={
                ":status": {"N": str(tracker.status)},
                ":update_time": {"S": tracker.update_time},
                ":lock": {"NULL": True},
                ":errors": encode_dynamodb_item(tracker.errors),
            },
        )

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

        :param record: the record to check.
        """
        tracker = self.get_tracker(record)
        rid = record.id
        self.bsm.dynamodb_client.update_item(
            TableName=self.dynamodb_table,
            Key={
                self.dynamodb_pk_name: {"S": self.dynamodb_pk_value},
            },
            UpdateExpression=(
                "SET "
                f"#batch.{rid}.#status = :status, "
                f"#batch.{rid}.update_time = :update_time, "
                f"#batch.{rid}.#lock = :lock, "
                f"#batch.{rid}.errors = :errors"
            ),
            ExpressionAttributeNames={
                "#batch": "batch",
                "#status": "status",
                "#lock": "lock",
            },
            ExpressionAttributeValues={
                ":status": {"N": str(tracker.status)},
                ":update_time": {"S": tracker.update_time},
                ":lock": {"NULL": True},
                ":errors": encode_dynamodb_item(tracker.errors),
            },
        )
