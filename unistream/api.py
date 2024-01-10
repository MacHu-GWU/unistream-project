# -*- coding: utf-8 -*-

"""
Usage example::

    >>> import unistream.api as unistream

    >>> unistream.DataClassRecord
    >>> unistream.FileBuffer
    >>> unistream.SimpleCheckpoint
    >>> unistream.SimpleProducer
    >>> unistream.SimpleConsumer
"""

from .logger import logger
from .abstraction import T_RECORD
from .abstraction import T_BUFFER
from .abstraction import T_PRODUCER
from .abstraction import T_CHECK_POINT
from .abstraction import T_CONSUMER
from .record import BaseRecord
from .buffer import BaseBuffer
from .producer import RetryConfig
from .producer import BaseProducer
from .checkpoint import T_POINTER
from .checkpoint import StatusEnum
from .checkpoint import Tracker
from .checkpoint import T_TRACKER
from .checkpoint import BaseCheckPoint
from .consumer import BaseConsumer
from . import exc
from . import utils
from .records.dataclass import DataClassRecord
from .records.dataclass import T_DATA_CLASS_RECORD
from .buffers.file_buffer import FileBuffer
from .producers.simple import SimpleProducer
from .checkpoints.simple import SimpleCheckpoint
from .consumers.simple import SimpleConsumer

try:
    from .records.aws_kinesis import KinesisRecord
    from .records.aws_kinesis import T_KINESIS_RECORD
    from .records.aws_kinesis import KinesisGetRecordsResponseRecord
    from .records.aws_kinesis import T_KINESIS_GET_RECORDS_RESPONSE_RECORD
except ImportError:  # pragma: no cover
    pass

try:
    from .producers.aws_cloudwatch_logs import AwsCloudWatchLogsProducer
    from .producers.aws_kinesis import AwsKinesisStreamProducer
except ImportError:  # pragma: no cover
    pass

try:
    from .checkpoints.dynamodb_s3 import DynamoDBS3CheckPoint
except ImportError:  # pragma: no cover
    pass

try:
    from .consumers.aws_kinesis import KinesisStreamShard
    from .consumers.aws_kinesis import AwsKinesisStreamConsumer
except ImportError:  # pragma: no cover
    pass
