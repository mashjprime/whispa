"""Application state machine."""

import logging
from enum import Enum, auto
from typing import Callable, Optional, Set
import threading

logger = logging.getLogger(__name__)


class AppState(Enum):
    """Application states."""

    INITIALIZING = auto()
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    ERROR = auto()
    SHUTDOWN = auto()


# Valid state transitions (SHUTDOWN allowed from any state)
VALID_TRANSITIONS = {
    AppState.INITIALIZING: {AppState.IDLE, AppState.ERROR, AppState.SHUTDOWN},
    AppState.IDLE: {AppState.LISTENING, AppState.SHUTDOWN, AppState.ERROR},
    AppState.LISTENING: {AppState.IDLE, AppState.PROCESSING, AppState.ERROR, AppState.SHUTDOWN},
    AppState.PROCESSING: {AppState.IDLE, AppState.ERROR, AppState.SHUTDOWN},
    AppState.ERROR: {AppState.IDLE, AppState.SHUTDOWN},
    AppState.SHUTDOWN: set(),
}


class StateMachine:
    """Manages application state transitions."""

    def __init__(self, initial_state: AppState = AppState.INITIALIZING):
        """Initialize state machine.

        Args:
            initial_state: Starting state
        """
        self._state = initial_state
        self._lock = threading.RLock()  # Reentrant lock to allow nested locking
        self._listeners: list[Callable[[AppState, AppState], None]] = []

    @property
    def state(self) -> AppState:
        """Get current state."""
        with self._lock:
            return self._state

    def can_transition_to(self, new_state: AppState) -> bool:
        """Check if transition to new state is valid.

        Args:
            new_state: Target state

        Returns:
            True if transition is valid
        """
        with self._lock:
            valid_states = VALID_TRANSITIONS.get(self._state, set())
            return new_state in valid_states

    def transition_to(self, new_state: AppState) -> bool:
        """Transition to a new state.

        Args:
            new_state: Target state

        Returns:
            True if transition successful
        """
        with self._lock:
            if not self.can_transition_to(new_state):
                logger.warning(
                    "Invalid state transition: %s -> %s",
                    self._state.name,
                    new_state.name,
                )
                return False

            old_state = self._state
            self._state = new_state
            logger.debug("State transition: %s -> %s", old_state.name, new_state.name)

        # Notify listeners outside lock
        self._notify_listeners(old_state, new_state)
        return True

    def force_state(self, new_state: AppState) -> None:
        """Force transition to state (bypasses validation).

        Args:
            new_state: Target state
        """
        with self._lock:
            old_state = self._state
            self._state = new_state
            logger.warning(
                "Forced state transition: %s -> %s", old_state.name, new_state.name
            )

        self._notify_listeners(old_state, new_state)

    def add_listener(self, callback: Callable[[AppState, AppState], None]) -> None:
        """Add state change listener.

        Args:
            callback: Function called with (old_state, new_state)
        """
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[AppState, AppState], None]) -> None:
        """Remove state change listener.

        Args:
            callback: Listener to remove
        """
        try:
            self._listeners.remove(callback)
        except ValueError:
            pass

    def _notify_listeners(self, old_state: AppState, new_state: AppState) -> None:
        """Notify all listeners of state change."""
        for listener in self._listeners:
            try:
                listener(old_state, new_state)
            except Exception as e:
                logger.error("State listener error: %s", e)

    def is_idle(self) -> bool:
        """Check if in idle state."""
        return self.state == AppState.IDLE

    def is_listening(self) -> bool:
        """Check if in listening state."""
        return self.state == AppState.LISTENING

    def is_processing(self) -> bool:
        """Check if in processing state."""
        return self.state == AppState.PROCESSING
