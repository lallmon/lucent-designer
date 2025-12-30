"""Tests for HistoryManager undo/redo orchestration."""

import pytest

from lucent.commands import Command, TransactionCommand
from lucent.history_manager import HistoryManager


class DummyCommand(Command):
    """Simple command that mutates shared state for testing."""

    def __init__(self, state: list, token: str):
        self.state = state
        self.token = token

    @property
    def description(self) -> str:
        return f"Dummy {self.token}"

    def execute(self) -> None:
        self.state.append(f"do:{self.token}")

    def undo(self) -> None:
        self.state.append(f"undo:{self.token}")


def test_execute_pushes_undo_and_clears_redo():
    changes = {"undo_changed": 0, "redo_changed": 0}
    history = HistoryManager(
        on_undo_stack_changed=lambda: changes.__setitem__(
            "undo_changed", changes["undo_changed"] + 1
        ),
        on_redo_stack_changed=lambda: changes.__setitem__(
            "redo_changed", changes["redo_changed"] + 1
        ),
    )
    state = []
    cmd = DummyCommand(state, "a")

    history.execute(cmd)

    assert history.can_undo is True
    assert history.can_redo is False
    assert state == ["do:a"]
    assert changes["undo_changed"] == 1
    assert changes["redo_changed"] == 0


def test_undo_and_redo_round_trip():
    history = HistoryManager()
    state = []
    cmd = DummyCommand(state, "a")

    history.execute(cmd)
    assert history.undo() is True
    assert state == ["do:a", "undo:a"]
    assert history.can_redo is True

    assert history.redo() is True
    assert state == ["do:a", "undo:a", "do:a"]


def test_new_action_clears_redo_stack():
    history = HistoryManager()
    state = []
    history.execute(DummyCommand(state, "a"))
    history.undo()
    assert history.can_redo is True

    history.execute(DummyCommand(state, "b"))
    assert history.can_redo is False


def test_transaction_groups_commands_into_single_undo():
    history = HistoryManager()
    state = []

    history.begin_transaction("Txn")
    history.execute(DummyCommand(state, "a"))
    history.execute(DummyCommand(state, "b"))
    history.end_transaction()

    assert history.can_undo is True
    # Two executes happened
    assert state == ["do:a", "do:b"]

    # Single undo should undo both in reverse
    history.undo()
    assert state == ["do:a", "do:b", "undo:b", "undo:a"]
    assert history.can_redo is True

    # Redo should replay both
    history.redo()
    assert state == ["do:a", "do:b", "undo:b", "undo:a", "do:a", "do:b"]


def test_empty_transaction_does_not_push_history():
    history = HistoryManager()
    history.begin_transaction("Txn")
    history.end_transaction()
    assert history.can_undo is False


def test_begin_transaction_while_active_is_ignored():
    history = HistoryManager()
    state = []
    history.begin_transaction("Txn")
    history.begin_transaction("Txn2")  # should be ignored
    history.execute(DummyCommand(state, "a"))
    history.end_transaction()
    assert history.can_undo is True
    # Undo should still work
    history.undo()
    assert state == ["do:a", "undo:a"]


def test_history_exposes_stacks_via_properties():
    history = HistoryManager()
    assert history.can_undo is False
    assert history.can_redo is False


def test_end_transaction_without_begin_is_noop():
    history = HistoryManager()
    history.end_transaction()  # should not throw
    assert history.can_undo is False


def test_transaction_clears_redo_when_executed():
    history = HistoryManager()
    state = []
    history.execute(DummyCommand(state, "a"))
    history.undo()
    assert history.can_redo is True

    history.begin_transaction("Txn")
    history.execute(DummyCommand(state, "b"))
    history.end_transaction()

    assert history.can_redo is False
