"""Thread-safe utilities for Whispa."""

import threading
from functools import wraps
from typing import TypeVar, Callable, Any


T = TypeVar("T")


class ThreadSafeValue:
    """Thread-safe wrapper for a value."""

    def __init__(self, initial_value: Any = None):
        self._value = initial_value
        self._lock = threading.Lock()

    @property
    def value(self) -> Any:
        with self._lock:
            return self._value

    @value.setter
    def value(self, new_value: Any) -> None:
        with self._lock:
            self._value = new_value


def synchronized(lock: threading.Lock) -> Callable:
    """Decorator to synchronize method access with a lock."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            with lock:
                return func(*args, **kwargs)

        return wrapper

    return decorator


class AtomicCounter:
    """Thread-safe counter."""

    def __init__(self, initial: int = 0):
        self._value = initial
        self._lock = threading.Lock()

    def increment(self) -> int:
        with self._lock:
            self._value += 1
            return self._value

    def decrement(self) -> int:
        with self._lock:
            self._value -= 1
            return self._value

    @property
    def value(self) -> int:
        with self._lock:
            return self._value
