"""Bound concurrent online model operations within one API worker."""

import os
from contextlib import contextmanager
from threading import BoundedSemaphore


class ModelBusy(RuntimeError):
    pass


def configured_slots() -> int:
    value = os.environ.get("MODEL_MAX_CONCURRENT", "2")
    if not value.isascii() or not value.isdecimal() or len(value) > 2:
        raise ValueError("MODEL_MAX_CONCURRENT must be an integer in 1..32")
    limit = int(value)
    if not 1 <= limit <= 32:
        raise ValueError("MODEL_MAX_CONCURRENT must be an integer in 1..32")
    return limit


_slots = BoundedSemaphore(configured_slots())


@contextmanager
def model_slot():
    if not _slots.acquire(blocking=False):
        raise ModelBusy
    try:
        yield
    finally:
        _slots.release()
