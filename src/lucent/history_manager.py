"""Undo/redo orchestration independent of the Qt model."""

from __future__ import annotations

from typing import Callable, List, Optional

from lucent.commands import Command, TransactionCommand


class HistoryManager:
    """Maintains undo/redo stacks and transaction grouping."""

    def __init__(
        self,
        on_undo_stack_changed: Optional[Callable[[], None]] = None,
        on_redo_stack_changed: Optional[Callable[[], None]] = None,
    ) -> None:
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
        self._transaction_commands: Optional[List[Command]] = None
        self._transaction_label: str = "Edit"
        self._on_undo_stack_changed = on_undo_stack_changed or (lambda: None)
        self._on_redo_stack_changed = on_redo_stack_changed or (lambda: None)

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def execute(self, command: Command) -> None:
        """Execute a command, recording it for undo unless inside a transaction."""
        command.execute()

        if self._transaction_commands is not None:
            self._transaction_commands.append(command)
            return

        self._undo_stack.append(command)
        if self._redo_stack:
            self._redo_stack.clear()
            self._notify_redo_stack_changed()
        self._notify_undo_stack_changed()

    def undo(self) -> bool:
        """Undo the most recent command."""
        if not self._undo_stack:
            return False
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        self._notify_undo_stack_changed()
        self._notify_redo_stack_changed()
        return True

    def redo(self) -> bool:
        """Redo the most recently undone command."""
        if not self._redo_stack:
            return False
        command = self._redo_stack.pop()
        command.execute()
        self._undo_stack.append(command)
        self._notify_undo_stack_changed()
        self._notify_redo_stack_changed()
        return True

    def begin_transaction(self, label: str = "Edit") -> None:
        """Start grouping subsequent executes into a single transaction."""
        if self._transaction_commands is not None:
            return  # ignore nested calls
        self._transaction_commands = []
        self._transaction_label = label

    def end_transaction(self) -> None:
        """Finish transaction, pushing grouped commands as one undo step."""
        if self._transaction_commands is None:
            return

        if not self._transaction_commands:
            # Empty transaction: no-op
            self._transaction_commands = None
            return

        txn = TransactionCommand(self._transaction_commands, self._transaction_label)
        self._transaction_commands = None

        self._undo_stack.append(txn)
        if self._redo_stack:
            self._redo_stack.clear()
            self._notify_redo_stack_changed()
        self._notify_undo_stack_changed()

    def _notify_undo_stack_changed(self) -> None:
        self._on_undo_stack_changed()

    def _notify_redo_stack_changed(self) -> None:
        self._on_redo_stack_changed()
