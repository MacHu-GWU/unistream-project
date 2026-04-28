# -*- coding: utf-8 -*-

import time
from datetime import timedelta

from unistream.utils import get_utc_now
from unistream.producer import RetryConfig


class TestRetryConfig:
    def _test_basic(self):
        rc = RetryConfig()
        now = get_utc_now()
        # we should retry because we never did before
        assert rc.shall_we_retry(now=now) is True
        assert rc.attempts == 0
        assert rc.first_attempt_time is None
        assert rc.last_attempt_time is None
        assert rc.last_error is None

        # mark_start_retry() should update the tracker
        rc.mark_start_retry(now=now)
        assert rc.attempts == 1
        assert rc.first_attempt_time == now
        assert rc.last_attempt_time == now
        assert rc.last_error is None

        # mark_retry_failed() should update the last_error attribute
        e = Exception("test")
        rc.mark_retry_failed(e)
        assert rc.attempts == 1
        assert rc.first_attempt_time == now
        assert rc.last_attempt_time == now
        assert rc.last_error == e

        # after reset, everything becomes original
        rc.reset_tracker()
        assert rc.attempts == 0
        assert rc.first_attempt_time is None
        assert rc.last_attempt_time is None
        assert rc.last_error is None

    def _test_shall_we_retry_backoff_cap(self):
        """
        When attempts >= len(exp_backoff), use the last value as threshold.
        """
        rc = RetryConfig(exp_backoff=[1, 2, 4])
        now = get_utc_now()

        # simulate 4 attempts (exceeds exp_backoff length of 3)
        for _ in range(4):
            rc.mark_start_retry(now=now)
            now = now + timedelta(seconds=0.1)

        # attempts=4 >= len([1,2,4])=3, so threshold should be 4 (last value)
        # immediately after last attempt, should NOT retry (elapsed < 4)
        assert rc.shall_we_retry(now=now) is False

        # after waiting >= 4 seconds, should retry
        future = now + timedelta(seconds=4)
        assert rc.shall_we_retry(now=future) is True

    def _test_show(self):
        rc = RetryConfig()
        rc.show()

    def test(self):
        self._test_basic()
        self._test_shall_we_retry_backoff_cap()
        self._test_show()


if __name__ == "__main__":
    from unistream.tests import run_cov_test

    run_cov_test(__file__, "unistream.producer", preview=False)
