"""Tests for state machine."""

import pytest

from whispa.core.state_machine import AppState, StateMachine, VALID_TRANSITIONS


class TestStateMachine:
    """Tests for StateMachine."""

    def test_initial_state(self):
        """Test initial state."""
        sm = StateMachine()
        assert sm.state == AppState.INITIALIZING

        sm2 = StateMachine(initial_state=AppState.IDLE)
        assert sm2.state == AppState.IDLE

    def test_valid_transition(self):
        """Test valid state transition."""
        sm = StateMachine(initial_state=AppState.IDLE)

        result = sm.transition_to(AppState.LISTENING)

        assert result is True
        assert sm.state == AppState.LISTENING

    def test_invalid_transition(self):
        """Test invalid state transition."""
        sm = StateMachine(initial_state=AppState.IDLE)

        # Can't go from IDLE to PROCESSING directly
        result = sm.transition_to(AppState.PROCESSING)

        assert result is False
        assert sm.state == AppState.IDLE

    def test_can_transition_to(self):
        """Test transition validation."""
        sm = StateMachine(initial_state=AppState.IDLE)

        assert sm.can_transition_to(AppState.LISTENING) is True
        assert sm.can_transition_to(AppState.SHUTDOWN) is True
        assert sm.can_transition_to(AppState.PROCESSING) is False

    def test_force_state(self):
        """Test forced state transition."""
        sm = StateMachine(initial_state=AppState.IDLE)

        # Force invalid transition
        sm.force_state(AppState.PROCESSING)

        assert sm.state == AppState.PROCESSING

    def test_state_listener(self):
        """Test state change listener."""
        sm = StateMachine(initial_state=AppState.IDLE)
        transitions = []

        def listener(old_state, new_state):
            transitions.append((old_state, new_state))

        sm.add_listener(listener)
        sm.transition_to(AppState.LISTENING)
        sm.transition_to(AppState.PROCESSING)

        assert len(transitions) == 2
        assert transitions[0] == (AppState.IDLE, AppState.LISTENING)
        assert transitions[1] == (AppState.LISTENING, AppState.PROCESSING)

    def test_remove_listener(self):
        """Test listener removal."""
        sm = StateMachine(initial_state=AppState.IDLE)
        transitions = []

        def listener(old_state, new_state):
            transitions.append((old_state, new_state))

        sm.add_listener(listener)
        sm.transition_to(AppState.LISTENING)

        sm.remove_listener(listener)
        sm.transition_to(AppState.PROCESSING)

        assert len(transitions) == 1

    def test_helper_methods(self):
        """Test helper methods."""
        sm = StateMachine(initial_state=AppState.IDLE)

        assert sm.is_idle() is True
        assert sm.is_listening() is False
        assert sm.is_processing() is False

        sm.transition_to(AppState.LISTENING)

        assert sm.is_idle() is False
        assert sm.is_listening() is True
        assert sm.is_processing() is False

    def test_valid_transitions_defined(self):
        """Test all states have defined transitions."""
        for state in AppState:
            assert state in VALID_TRANSITIONS

    def test_shutdown_is_terminal(self):
        """Test shutdown state has no valid transitions."""
        sm = StateMachine(initial_state=AppState.IDLE)
        sm.force_state(AppState.SHUTDOWN)

        # No transitions from shutdown
        assert sm.can_transition_to(AppState.IDLE) is False
        assert sm.can_transition_to(AppState.LISTENING) is False
