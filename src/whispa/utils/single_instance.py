"""Single instance lock to prevent multiple app instances."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SingleInstanceLock:
    """Mutex-based single instance lock for Windows."""

    def __init__(self, name: str):
        """Initialize the lock.

        Args:
            name: Unique name for the mutex
        """
        self.name = name
        self._mutex: Optional[int] = None

    def acquire(self) -> bool:
        """Try to acquire the lock.

        Returns:
            True if lock acquired, False if another instance is running
        """
        try:
            import win32event
            import win32api
            import winerror

            self._mutex = win32event.CreateMutex(None, False, self.name)
            last_error = win32api.GetLastError()

            if last_error == winerror.ERROR_ALREADY_EXISTS:
                logger.debug("Mutex already exists - another instance is running")
                return False

            logger.debug("Mutex acquired successfully")
            return True

        except ImportError:
            logger.warning("pywin32 not available, single instance check disabled")
            return True
        except Exception as e:
            logger.warning("Failed to acquire mutex: %s", e)
            return True

    def release(self) -> None:
        """Release the lock."""
        if self._mutex is not None:
            try:
                import win32api

                win32api.CloseHandle(self._mutex)
                logger.debug("Mutex released")
            except Exception as e:
                logger.warning("Failed to release mutex: %s", e)
            finally:
                self._mutex = None
