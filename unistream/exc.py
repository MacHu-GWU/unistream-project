# -*- coding: utf-8 -*-


class BufferIsEmptyError(IndexError):
    """
    Raised when try to take item from an empty buffer.
    """

    pass


class SendError(Exception):
    """
    Raised when producer failed to send records.
    """

    pass


class ProcessError(Exception):
    """
    Raised when consumer failed to process record.
    """

    pass


class StreamIsClosedError(Exception):
    """
    Raised when stream says that you cannot consume from it. This is not about
    stream is disconnected. The stream system is still healthy, but it confirms
    that you cannot consume from it due to recent node re-balance or other reasons.
    """

    pass
