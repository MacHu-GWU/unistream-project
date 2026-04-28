# -*- coding: utf-8 -*-

"""
Implements :class:`BaseRecord`, the base class for all record types.
"""

from .abstraction import AbcRecord


class BaseRecord(AbcRecord):
    """
    Base class for record implementations.

    Subclasses should provide concrete ``serialize`` and ``deserialize`` methods
    as defined in :class:`~unistream.abstraction.AbcRecord`.

    See :class:`~unistream.records.dataclass.DataClassRecord` for a concrete
    implementation using :mod:`dataclasses`.
    """

    pass
