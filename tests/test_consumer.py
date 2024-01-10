# -*- coding: utf-8 -*-

from unistream.consumer import (
    BaseConsumer,
)


class TestBaseConsumer:
    def test(self):
        pass


if __name__ == "__main__":
    from unistream.tests import run_cov_test

    run_cov_test(__file__, "unistream.consumer", preview=False)
