"""Backend-safe caching primitives.

This module intentionally avoids any Streamlit dependency so the same service
layer can be reused by FastAPI, scripts, and the temporary Streamlit UI.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from threading import RLock
from time import monotonic
from typing import Any


class InMemoryTTLCache:
    """Simple in-process TTL cache that can be replaced later by Redis/filesystem."""

    def __init__(self) -> None:
        self._data: dict[Any, tuple[float, Any]] = {}
        self._lock = RLock()

    def get(self, key: Any) -> Any | None:
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None

            expires_at, value = entry
            if monotonic() >= expires_at:
                self._data.pop(key, None)
                return None

            return value

    def set(self, key: Any, value: Any, ttl_seconds: int) -> None:
        with self._lock:
            self._data[key] = (monotonic() + ttl_seconds, value)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


_DEFAULT_CACHE = InMemoryTTLCache()


def _make_key(args: tuple[Any, ...], kwargs: dict[str, Any]) -> tuple[Any, ...]:
    return args, tuple(sorted(kwargs.items()))


def ttl_cache(ttl_seconds: int) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Cache function calls using the default in-memory backend."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = (func.__module__, func.__name__, _make_key(args, kwargs))
            cached = _DEFAULT_CACHE.get(key)
            if cached is not None:
                return cached

            value = func(*args, **kwargs)
            _DEFAULT_CACHE.set(key, value, ttl_seconds)
            return value

        return wrapper

    return decorator
