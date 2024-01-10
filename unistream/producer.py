# -*- coding: utf-8 -*-

"""
todo: docstring
"""

import typing as T
import dataclasses
from datetime import datetime

from .utils import get_utc_now
from .logger import logger
from .abstraction import AbcProducer, T_RECORD, T_BUFFER


def _default_exp_backoff():
    return [1, 2, 4, 8, 15, 30, 60]


@dataclasses.dataclass
class RetryConfig:
    """
    The retry behavior configuration for :class:`BaseProducer`.

    :param exp_backoff: the exponential backoff retry waiter settings.
        for example, if ``exp_backoff = [1, 2, 4]``, then wait 1 seconds
        before the second attempt, wait 2 seconds before the third attempt,
        wait 4 seconds before the fourth attempt, and then always wait 4 seconds
        for the next attempts. Default to ``[1, 2, 4, 8, 15, 30, 60]``.
    :param attempts: total attempts we have made.
    :param first_attempt_time: the time when we first attempt to send the data.
    :param last_attempt_time: the time when we last attempt to send the data.
    :param last_error: the last error we encountered.
    """

    exp_backoff: T.List[int] = dataclasses.field(default_factory=_default_exp_backoff)
    attempts: int = dataclasses.field(default=0)
    first_attempt_time: T.Optional[datetime] = dataclasses.field(default=None)
    last_attempt_time: T.Optional[datetime] = dataclasses.field(default=None)
    last_error: T.Optional[Exception] = dataclasses.field(default=None)

    def shall_we_retry(self, now: datetime) -> bool:
        """
        Check whether we should retry sending the data to the sink.
        """
        # We never fail before, so we should retry.
        if self.last_attempt_time is None:
            return True

        # let's say exp_backoff = [1, 2, 4]
        # we already made 2 attempts, we have wait 1 seconds between
        # the first and the second attempt. Then ``now - last_fail_time``
        # should be greater than 2 seconds, which is ``exp_backoff[1]``
        elapsed = (now - self.last_attempt_time).total_seconds()
        if self.attempts >= len(self.exp_backoff):
            threshold = self.exp_backoff[-1]
        else:
            threshold = self.exp_backoff[self.attempts - 1]
        return elapsed >= threshold

    def mark_start_retry(self, now: datetime):
        self.attempts += 1
        if self.first_attempt_time is None:
            self.first_attempt_time = now
        self.last_attempt_time = now

    def mark_retry_failed(self, error: Exception):
        self.last_error = error

    def reset_tracker(self):
        self.attempts = 0
        self.first_attempt_time = None
        self.last_attempt_time = None
        self.last_error = None

    def show(self):
        logger.info("current retry config: ")
        with logger.indent():
            logger.info(f"exp_backoff = {self.exp_backoff}")
            logger.info(f"attempts = {self.attempts}")
            logger.info(f"first_attempt_time = {self.first_attempt_time}")
            logger.info(f"last_attempt_time = {self.last_attempt_time}")
            logger.info(f"last_error = {self.last_error}")


@dataclasses.dataclass
class BaseProducer(AbcProducer):
    """
    todo: docstring

    A producer has to have a buffer backend and a retry config.
    """

    buffer: T_BUFFER = dataclasses.field()
    retry_config: RetryConfig = dataclasses.field()

    @logger.emoji_block(
        msg="put record",
        emoji="📤",
    )
    def _put(
        self,
        record: T_RECORD,
        skip_error: bool = True,
    ):
        """
        This method will be called everytime we put a record to the buffer.

        It checks the exponential backoff to see whether we should try to
        send the emitted records to the sink. If we should, then it takes
        the data from the buffer and call the
        :meth:`unistream.abstraction.AbcProducer.send` method. It also
        handles the exceptions gracefully.
        """
        logger.info(f"record = {record.serialize()}")
        self.buffer.put(record)

        # self.retry_config.show()
        self.retry_config.skip_error = skip_error  # override the

        now = get_utc_now()
        if self.retry_config.shall_we_retry(now=now):
            if self.buffer.should_i_emit():
                records = self.buffer.emit()
                self.retry_config.mark_start_retry(now=now)
                try:
                    logger.info(f"📤 send records: {[record.id for record in records]}")
                    self.send(records)
                    logger.info("🟢 succeeded")
                    self.buffer.commit()
                    self.retry_config.reset_tracker()
                    return
                except Exception as e:
                    logger.info(f"🔴 failed, error: {e!r}")
                    self.retry_config.mark_retry_failed(error=e)  # this may raise error
                    if not skip_error:
                        raise e
                    return
            else:
                logger.info("🚫 we should not emit")
                return
        else:
            logger.info("🚫 on hold due to exponential backoff")
            return

    def put(
        self,
        record: T_RECORD,
        skip_error: bool = True,
        verbose: bool = False,
    ):
        with logger.disabled(
            disable=not verbose,
        ):
            return self._put(
                record=record,
                skip_error=skip_error,
            )
