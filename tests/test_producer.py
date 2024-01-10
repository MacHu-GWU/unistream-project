# -*- coding: utf-8 -*-

from unistream.utils import get_utc_now
from unistream.producer import RetryConfig


class TestRetryConfig:
    def test(self):
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


if __name__ == "__main__":
    from unistream.tests import run_cov_test

    run_cov_test(__file__, "unistream.producer", preview=False)
