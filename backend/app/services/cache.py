"""A tiny thread-safe in-process TTL cache.

The Dashboard and Skills analytics are global aggregations over the whole
dataset that change only when data is re-imported, so caching their results for
a short period removes repeated multi-second recomputation while keeping the
implementation dependency-free (a drop-in stand-in for the Redis layer named in
the design).  Caching can be globally disabled (e.g. in the test-suite) by
setting ``ENABLED = False``.
"""
from __future__ import annotations

import functools
import threading
import time

ENABLED = True
DEFAULT_TTL = 300  # seconds

_lock = threading.Lock()
_registry: list = []


def ttl_cache(seconds: int = DEFAULT_TTL):
    def decorator(fn):
        store: dict = {}
        _registry.append(store)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if not ENABLED:
                return fn(*args, **kwargs)
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()
            with _lock:
                hit = store.get(key)
                if hit is not None and now - hit[1] < seconds:
                    return hit[0]
            value = fn(*args, **kwargs)
            with _lock:
                store[key] = (value, now)
            return value

        wrapper.cache_clear = store.clear  # type: ignore[attr-defined]
        return wrapper

    return decorator


def clear_all() -> None:
    with _lock:
        for store in _registry:
            store.clear()
