"""
State machine pattern implementation for OPSVI Foundation.

Provides a robust state management system for complex workflows.
"""

import asyncio
import logging
from abc import ABC
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class StateTransitionError(Exception):
    """Exception raised when state transition is invalid."""


@dataclass
class StateTransition:
    """Represents a state transition."""

    from_state: str
    to_state: str
    trigger: str
    condition: Callable | None = None
    action: Callable | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StateEvent:
    """Event that triggers state transitions."""

    event_type: str
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    source: str | None = None


class State(ABC):
    """Abstract base class for states."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._entry_actions: list[Callable] = []
        self._exit_actions: list[Callable] = []
        self._internal_actions: dict[str, Callable] = {}

    def add_entry_action(self, action: Callable) -> None:
        """Add an action to execute when entering this state."""
        self._entry_actions.append(action)

    def add_exit_action(self, action: Callable) -> None:
        """Add an action to execute when exiting this state."""
        self._exit_actions.append(action)

    def add_internal_action(self, trigger: str, action: Callable) -> None:
        """Add an internal action for this state."""
        self._internal_actions[trigger] = action

    async def on_entry(self, context: Any) -> None:
        """Execute entry actions."""
        for action in self._entry_actions:
            try:
                if asyncio.iscoroutinefunction(action):
                    await action(context)
                else:
                    action(context)
            except Exception as e:
                logger.error(f"Error in entry action for state {self.name}: {e}")

    async def on_exit(self, context: Any) -> None:
        """Execute exit actions."""
        for action in self._exit_actions:
            try:
                if asyncio.iscoroutinefunction(action):
                    await action(context)
                else:
                    action(context)
            except Exception as e:
                logger.error(f"Error in exit action for state {self.name}: {e}")

    async def on_internal_event(self, trigger: str, context: Any) -> bool:
        """Handle internal events within this state."""
        if trigger in self._internal_actions:
            try:
                action = self._internal_actions[trigger]
                if asyncio.iscoroutinefunction(action):
                    await action(context)
                else:
                    action(context)
                return True
            except Exception as e:
                logger.error(f"Error in internal action for state {self.name}: {e}")
        return False


class StateMachine:
    """State machine implementation."""

    def __init__(self, initial_state: str) -> None:
        self.states: dict[str, State] = {}
        self.transitions: list[StateTransition] = []
        self.current_state: str | None = None
        self.initial_state = initial_state
        self.context: Any = None
        self._history: list[
            tuple[str, str, datetime]
        ] = []  # (from_state, to_state, timestamp)
        self._max_history: int = 1000

    def add_state(self, state: State) -> None:
        """Add a state to the state machine."""
        self.states[state.name] = state
        logger.debug(f"Added state: {state.name}")

    def add_transition(self, transition: StateTransition) -> None:
        """Add a transition to the state machine."""
        self.transitions.append(transition)
        logger.debug(
            f"Added transition: {transition.from_state} -> {transition.to_state} ({transition.trigger})",
        )

    def get_valid_transitions(self, state: str) -> list[StateTransition]:
        """Get all valid transitions from a state."""
        return [
            transition
            for transition in self.transitions
            if transition.from_state == state
        ]

    def can_transition(self, from_state: str, trigger: str) -> bool:
        """Check if a transition is valid."""
        for transition in self.transitions:
            if transition.from_state == from_state and transition.trigger == trigger:
                if transition.condition is None:
                    return True
                try:
                    return transition.condition(self.context)
                except Exception as e:
                    logger.error(f"Error checking transition condition: {e}")
                    return False
        return False

    async def start(self, context: Any = None) -> None:
        """Start the state machine."""
        if self.initial_state not in self.states:
            raise StateTransitionError(
                f"Initial state '{self.initial_state}' not found",
            )

        self.context = context
        self.current_state = self.initial_state

        # Execute entry actions for initial state
        await self.states[self.current_state].on_entry(self.context)
        logger.info(f"State machine started in state: {self.current_state}")

    async def trigger(self, trigger: str, event_data: Any = None) -> bool:
        """Trigger a state transition."""
        if self.current_state is None:
            raise StateTransitionError("State machine not started")

        # Check for internal actions first
        current_state_obj = self.states[self.current_state]
        if await current_state_obj.on_internal_event(trigger, self.context):
            logger.debug(
                f"Internal action executed for trigger '{trigger}' in state '{self.current_state}'",
            )
            return True

        # Find valid transition
        for transition in self.transitions:
            if (
                transition.from_state == self.current_state
                and transition.trigger == trigger
            ):
                # Check condition if present
                if transition.condition is not None:
                    try:
                        if not transition.condition(self.context):
                            logger.debug(
                                f"Transition condition failed for {transition.from_state} -> {transition.to_state}",
                            )
                            continue
                    except Exception as e:
                        logger.error(f"Error evaluating transition condition: {e}")
                        continue

                # Execute transition
                return await self._execute_transition(transition, event_data)

        logger.warning(
            f"No valid transition found for trigger '{trigger}' in state '{self.current_state}'",
        )
        return False

    async def _execute_transition(
        self,
        transition: StateTransition,
        event_data: Any,
    ) -> bool:
        """Execute a state transition."""
        try:
            # Execute exit actions for current state
            await self.states[self.current_state].on_exit(self.context)

            # Execute transition action if present
            if transition.action is not None:
                if asyncio.iscoroutinefunction(transition.action):
                    await transition.action(self.context, event_data)
                else:
                    transition.action(self.context, event_data)

            # Update state
            old_state = self.current_state
            self.current_state = transition.to_state

            # Record in history
            self._history.append((old_state, self.current_state, datetime.now()))
            if len(self._history) > self._max_history:
                self._history.pop(0)

            # Execute entry actions for new state
            await self.states[self.current_state].on_entry(self.context)

            logger.info(
                f"State transition: {old_state} -> {self.current_state} (trigger: {transition.trigger})",
            )
            return True

        except Exception as e:
            logger.error(f"Error during state transition: {e}")
            raise StateTransitionError(f"Transition failed: {e}")

    def get_current_state(self) -> str | None:
        """Get the current state."""
        return self.current_state

    def get_state_history(self) -> list[tuple[str, str, datetime]]:
        """Get the state transition history."""
        return self._history.copy()

    def is_in_state(self, state: str) -> bool:
        """Check if the state machine is in a specific state."""
        return self.current_state == state

    def get_available_triggers(self) -> list[str]:
        """Get all available triggers for the current state."""
        if self.current_state is None:
            return []

        return [
            transition.trigger
            for transition in self.transitions
            if transition.from_state == self.current_state
        ]


class StateMachineBuilder:
    """Builder pattern for creating state machines."""

    def __init__(self) -> None:
        self.states: dict[str, State] = {}
        self.transitions: list[StateTransition] = []
        self.initial_state: str | None = None

    def add_state(self, state: State) -> "StateMachineBuilder":
        """Add a state to the builder."""
        self.states[state.name] = state
        return self

    def set_initial_state(self, state_name: str) -> "StateMachineBuilder":
        """Set the initial state."""
        self.initial_state = state_name
        return self

    def add_transition(
        self,
        from_state: str,
        to_state: str,
        trigger: str,
        condition: Callable | None = None,
        action: Callable | None = None,
    ) -> "StateMachineBuilder":
        """Add a transition to the builder."""
        transition = StateTransition(
            from_state=from_state,
            to_state=to_state,
            trigger=trigger,
            condition=condition,
            action=action,
        )
        self.transitions.append(transition)
        return self

    def build(self) -> StateMachine:
        """Build the state machine."""
        if self.initial_state is None:
            raise ValueError("Initial state must be set")

        if self.initial_state not in self.states:
            raise ValueError(
                f"Initial state '{self.initial_state}' not found in states",
            )

        state_machine = StateMachine(self.initial_state)

        # Add all states
        for state in self.states.values():
            state_machine.add_state(state)

        # Add all transitions
        for transition in self.transitions:
            state_machine.add_transition(transition)

        return state_machine


# Example state implementations


class SimpleState(State):
    """Simple state implementation."""

    def __init__(self, name: str) -> None:
        super().__init__(name)


class WorkflowState(State):
    """Workflow state with additional metadata."""

    def __init__(self, name: str, description: str = "") -> None:
        super().__init__(name)
        self.description = description
        self.metadata: dict[str, Any] = {}

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the state."""
        self.metadata[key] = value
