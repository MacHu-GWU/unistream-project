# -*- coding: utf-8 -*-

from pathlib import Path

import moto
from rich import print as rprint

from unistream.records.dataclass import DataClassRecord
from unistream.checkpoints.dynamodb_s3 import DynamoDBS3CheckPoint

from unistream.tests.mock_aws import BaseMockTest

dir_here = Path(__file__).absolute().parent

bucket = "my-bucket"
key = "my-checkpoint-records.json"
table = "my-table"
pk_name = "checkpoint_id"
pk_value = "checkpoint-1"


class TestDynamoDBS3CheckPoint(BaseMockTest):
    mock_list = [
        moto.mock_sts,
        moto.mock_dynamodb,
        moto.mock_s3,
    ]

    @classmethod
    def setup_class_post_hook(cls):
        cls.bsm.s3_client.create_bucket(Bucket=bucket)
        cls.bsm.dynamodb_client.create_table(
            TableName=table,
            KeySchema=[
                {"AttributeName": pk_name, "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": pk_name, "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

    def _new_checkpoint(self) -> DynamoDBS3CheckPoint:
        return DynamoDBS3CheckPoint(
            lock_expire=60,
            max_attempts=3,
            initial_pointer=0,
            start_pointer=0,
            next_pointer=None,
            batch_sequence=0,
            batch=dict(),
            s3_bucket=bucket,
            s3_key=key,
            dynamodb_table=table,
            dynamodb_pk_name=pk_name,
            dynamodb_pk_value=pk_value,
            bsm=self.bsm,
        )

    def _test(self):
        # load api will create a new one if not exists
        _ = DynamoDBS3CheckPoint.load(
            s3_bucket=bucket,
            s3_key=key,
            dynamodb_table=table,
            dynamodb_pk_name=pk_name,
            dynamodb_pk_value=pk_value,
            bsm=self.bsm,
        )

        checkpoint = self._new_checkpoint()
        record = DataClassRecord(id="id-1")
        records = [record]

        # should get 0 records, we haven't dumped yet
        assert len(list(checkpoint.load_records(DataClassRecord))) == 0

        checkpoint.update_for_new_batch(
            records=records,
            next_pointer=1,
        )
        checkpoint.dump_records(records)
        checkpoint.dump()

        checkpoint1 = DynamoDBS3CheckPoint.load(
            s3_bucket=bucket,
            s3_key=key,
            dynamodb_table=table,
            dynamodb_pk_name=pk_name,
            dynamodb_pk_value=pk_value,
            bsm=self.bsm,
        )
        assert checkpoint1 == checkpoint

        # records should match
        records1 = checkpoint1.load_records(DataClassRecord)
        assert records1 == records

        # moto doesn't support dynamodb update expression yet
        # checkpoint.mark_as_in_progress(record)
        # checkpoint.dump_as_in_progress(record)
        # e = Exception("test error")
        # checkpoint.mark_as_failed_or_exhausted(record, e)
        # checkpoint.dump_as_failed_or_exhausted(record)
        # checkpoint.mark_as_succeeded(record)
        # checkpoint.dump_as_succeeded(record)

    def test(self):
        self._test()


if __name__ == "__main__":
    from unistream.tests import run_cov_test

    run_cov_test(__file__, "unistream.checkpoints.dynamodb_s3", preview=False)
