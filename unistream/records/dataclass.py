# -*- coding: utf-8 -*-

"""
todo: docstring
"""

import typing as T
import uuid
import json
import dataclasses

from ..utils import get_utc_now
from ..record import BaseRecord


def id_factory() -> str:
    return str(uuid.uuid4())


def create_at_factory() -> str:
    return get_utc_now().isoformat()


@dataclasses.dataclass
class DataClassRecord(BaseRecord):
    """
    Record built on top of `dataclasses <https://docs.python.org/3/library/dataclasses.html>`_.
    """

    id: str = dataclasses.field(default_factory=id_factory)
    create_at: str = dataclasses.field(default_factory=create_at_factory)

    def serialize(self) -> str:
        return json.dumps(dataclasses.asdict(self))

    @classmethod
    def deserialize(
        cls: T.Type["T_DATA_CLASS_RECORD"],
        data: str,
    ) -> "T_DATA_CLASS_RECORD":
        return cls(**json.loads(data))


T_DATA_CLASS_RECORD = T.TypeVar("T_DATA_CLASS_RECORD", bound=DataClassRecord)
