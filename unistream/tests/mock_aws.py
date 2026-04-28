# -*- coding: utf-8 -*-

"""
AWS service mocking infrastructure for unit testing with configurable mock/real AWS switching.
"""

import typing as T
import dataclasses

import os
import moto
import boto3
import botocore.exceptions
from boto_session_manager import BotoSesManager


@dataclasses.dataclass(frozen=True)
class MockAwsTestConfig:
    """
    Configuration for AWS testing with mock/real AWS service selection.
    """

    use_mock: bool = dataclasses.field()
    aws_region: str = dataclasses.field()
    aws_profile: T.Optional[str] = dataclasses.field(default=None)


class BaseMockAwsTest:
    """
    Base test class providing AWS service mocking infrastructure with boto session management.
    """

    use_mock: bool = True

    @classmethod
    def create_s3_bucket(cls, bucket_name: str, enable_versioning: bool = False):
        """
        Create S3 bucket with optional versioning, handling existing bucket gracefully.
        """
        try:
            cls.s3_client.create_bucket(Bucket=bucket_name)
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "BucketAlreadyExists":
                pass
            else:
                raise e

        if enable_versioning:
            cls.bsm.s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={"Status": "Enabled"},
            )

    @classmethod
    def setup_mock(cls, mock_aws_test_config: MockAwsTestConfig):
        """
        Initialize AWS mocking or real AWS services based on configuration.
        """
        cls.mock_aws_test_config = mock_aws_test_config
        if mock_aws_test_config.use_mock:
            cls.mock_aws = moto.mock_aws()
            cls.mock_aws.start()

        if mock_aws_test_config.use_mock:
            cls.bsm: "BotoSesManager" = BotoSesManager(
                region_name=mock_aws_test_config.aws_region
            )
        else:
            cls.bsm: "BotoSesManager" = BotoSesManager(
                profile_name=mock_aws_test_config.aws_profile,
                region_name=mock_aws_test_config.aws_region,
            )

        cls.boto_ses: "boto3.Session" = cls.bsm.boto_ses

    @classmethod
    def setup_class_post_hook(cls):
        """
        Hook for additional test class setup after AWS mock initialization.
        """

    @classmethod
    def setup_class(cls):
        """
        Set up test class with configured AWS mock or real services.
        """
        mock_aws_test_config = MockAwsTestConfig(
            use_mock=cls.use_mock,
            aws_region="us-east-1",
            aws_profile=os.environ["AWS_PROFILE"],  # Use default profile
        )
        cls.setup_mock(mock_aws_test_config)
        cls.setup_class_post_hook()

    @classmethod
    def teardown_class(cls):
        """
        Clean up AWS mock services and test resources.
        """
        if cls.mock_aws_test_config.use_mock:
            cls.mock_aws.stop()
