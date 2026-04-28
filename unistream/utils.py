# -*- coding: utf-8 -*-

from datetime import datetime, timezone

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
EPOCH_STR = EPOCH.isoformat()


def get_utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)
