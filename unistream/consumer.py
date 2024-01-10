# -*- coding: utf-8 -*-

"""
[CN] 开发者设计文档

This section is for this project maintainer only.

这个模块实现了 Consumer 的基类 :class:`BaseConsumer`. 它实现的功能主要是从 stream 中
读 records, 如何处理 batch records, 是串行还是并行, 如何处理在消费 record 中的异常.
你的 stream system 可以是任何系统.

:class:`BaseConsumer` 的子类是一些跟某些特定的 stream system 对接的 Consumer 的具体实现.
它们假设你可以用任何逻辑来消费 record. 它只是负责实现了 :meth:`BaseConsumer.get_records` 方法.
"""

import typing as T
import time
import dataclasses

from tenacity import retry, wait_exponential, stop_after_attempt, RetryError

try:
    from rich import print as rprint
except:
    pass

from .exc import StreamIsClosedError
from .logger import logger
from .abstraction import T_RECORD, T_CHECK_POINT, AbcConsumer
from .checkpoint import T_POINTER, StatusEnum


@dataclasses.dataclass
class BaseConsumer(AbcConsumer):
    """
    Consumer continuously fetches batch records from the stream system
    and process them.

    :param record_class: the record class.
    :param limit: the max number of records to fetch from the stream system.
    :param checkpoint: the :class:`~unistream.checkpoint.BaseCheckpoint` object
        for status tracking and fault tolerance.
    :param exp_backoff_multiplier: the multiplier of the exponential backoff
    :param exp_backoff_base: the base of the exponential backoff
    :param exp_backoff_min: the minimum wait time of the exponential backoff
    :param exp_backoff_max: the maximum wait time of the exponential backoff
    :param skip_error: if True, skip the error and continue to process the next record.
        this is the most common use case. if False, raise the error and stop the consumer.
    :param delay: the delay time between pulling two batches.
    """

    record_class: T.Type[T_RECORD] = dataclasses.field()
    limit: int = dataclasses.field()
    checkpoint: T_CHECK_POINT = dataclasses.field()
    exp_backoff_multiplier: int = dataclasses.field()
    exp_backoff_base: int = dataclasses.field()
    exp_backoff_min: int = dataclasses.field()
    exp_backoff_max: int = dataclasses.field()
    skip_error: bool = dataclasses.field()
    delay: T.Union[int, float] = dataclasses.field()

    def get_records(
        self,
        limit: int = None,
    ) -> T.Tuple[T.List[T_RECORD], T_POINTER]:
        """
        Get records from the stream system and determine the value of the
        next pointer for the next batch if we successfully process
        this batch of records.

        :param limit: The maximum number of records to return.
        :return: a two-item tuple. the first one is a list of records
            and the second one is the value of the next pointer for the next batch
            if we successfully process this batch of records.

        .. important::

            User has to implement this method.

            If you need additional parameters other than the :class:`BaseConsumer`
            built-in attributes and ``limit``, you should extend this class
            and add the parameters to the subclass.
        """
        raise NotImplementedError

    def process_record(self, record: T_RECORD):
        """
        This method defines how to process a failed record.

        .. important::

            User has to implement this method.
        """
        raise NotImplementedError

    def process_failed_record(self, record: T_RECORD):
        """
        This method defines how to process a failed record.

        .. note::

            By default, it does nothing. In production, you should send
            this record to a dead-letter-queue (DLQ) for further investigation.

            To avoid sending records to DLQ one by one, you can use
            :meth:`~unistream.checkpoint.BaseCheckpoint.get_not_succeeded_records`
            to get all failed records and send them to DLQ in batch.

            Users can customize this method.
        """
        pass

    def commit(self):
        """
        Mark the current batch has been fully processed.
        """
        if self.checkpoint.next_pointer is None:
            self.checkpoint.dump()
            raise StreamIsClosedError
        else:
            self.checkpoint.start_pointer = self.checkpoint.next_pointer
            self.checkpoint.next_pointer = None
            self.checkpoint.dump()

    def _process_record_with_checkpoint(self, record: T_RECORD):
        """
        A wrapper method of :meth:`BaseConsumer.process_record`,
         process the record and also handle the checkpoint.
        """
        self.checkpoint.mark_as_in_progress(record)
        self.checkpoint.dump_as_in_progress(record)
        try:
            res = self.process_record(record)
            self.checkpoint.mark_as_succeeded(record)
            self.checkpoint.dump_as_succeeded(record)
            return res
        except Exception as e:
            self.checkpoint.mark_as_failed_or_exhausted(record, e)
            self.checkpoint.dump_as_failed_or_exhausted(record)
            raise e

    def _process_record(
        self,
        record: T_RECORD,
    ) -> T.Tuple[T.Optional[bool], T.Any]:
        """
        A wrapper method of :meth:`BaseConsumer._process_record_with_checkpoint`,
        with retry logic.

        :return: (bool, typing.Any), where the first element could be True, False or None. True means the record is processed successfully, False means the record the processing is faile, None means the record is not processed. The second element is the :meth:`BaseConsumer.process_record` return value.
        """
        if self.checkpoint.batch[record.id].status not in [
            StatusEnum.pending.value,
            StatusEnum.failed.value,
        ]:
            return None, None

        self.checkpoint.batch[record.id].status = StatusEnum.in_progress.value

        _process_record_with_retry = retry(
            wait=wait_exponential(
                multiplier=self.exp_backoff_multiplier,
                exp_base=self.exp_backoff_base,
                min=self.exp_backoff_min,
                max=self.exp_backoff_max,
            ),
            stop=stop_after_attempt(self.checkpoint.max_attempts),
        )(self._process_record_with_checkpoint)

        try:
            res = _process_record_with_retry(record)
            return True, res
        except RetryError as e:
            _process_failed_record_with_retry = retry(
                wait=wait_exponential(
                    multiplier=self.exp_backoff_multiplier,
                    exp_base=self.exp_backoff_base,
                    min=self.exp_backoff_min,
                    max=self.exp_backoff_max,
                ),
                stop=stop_after_attempt(self.checkpoint.max_attempts),
            )(self.process_failed_record)
            res = _process_failed_record_with_retry(record)
            if self.skip_error:
                return False, res
            else:
                e.reraise()

    @logger.emoji_block(
        msg="process batch in sequence",
        emoji="⏳",
    )
    def _process_batch_in_sequence(self):
        # check if we should call get_records API
        if self.checkpoint.is_ready_for_next_batch():
            # get records from the stream system
            records, next_pointer = self.get_records()
            # update and persist checkpoint
            self.checkpoint.update_for_new_batch(records, next_pointer)
            self.checkpoint.dump()
            self.checkpoint.dump_records(records)
        else:
            # get records from the checkpoint
            records = self.checkpoint.load_records(record_class=self.record_class)
        # process all record
        for record in records:
            flag, process_record_res = self._process_record(record)
        self.commit()

    def process_batch(
        self,
        verbose: bool = False,
    ):
        """
        .. note::

            Currently, we only support sequential processing.
        """
        with logger.disabled(
            disable=not verbose,
        ):
            return self._process_batch_in_sequence()

    def run(
        self,
        verbose: bool = False,
    ):
        """
        Run the consumer.
        """
        while 1:
            self.process_batch(verbose=verbose)
            if self.delay:
                time.sleep(self.delay)
