# -*- coding: utf-8 -*-

"""
Implements :class:`BaseBuffer`, the base class for all buffer backends.
"""

from .abstraction import AbcBuffer


class BaseBuffer(AbcBuffer):
    """
    Base class for buffer implementations.

    Subclasses should implement the persistence-backed buffer operations
    defined in :class:`~unistream.abstraction.AbcBuffer`.

    See :class:`~unistream.buffers.file_buffer.FileBuffer` for a concrete
    implementation using local WAL files.
    """
