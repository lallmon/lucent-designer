# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later


from lucent.commands import Command
from test_helpers import make_layer, make_rectangle


class _DummyCommand(Command):
    def __init__(self):
        self.executed = False

    @property
    def description(self) -> str:
        return "Dummy"

    def execute(self) -> None:
        self.executed = True

    def undo(self) -> None:
        self.executed = False


class _UnknownItem:
    def __init__(self):
        self.name = "Unknown"


def test_row_count_with_parent_returns_zero(canvas_model):
    canvas_model.addItem(make_rectangle())
    parent = canvas_model.index(0, 0)
    assert parent.isValid()
    assert canvas_model.rowCount(parent) == 0


def test_data_type_role_unknown(canvas_model):
    canvas_model._items.append(_UnknownItem())
    index = canvas_model.index(len(canvas_model._items) - 1, 0)
    assert canvas_model.data(index, canvas_model.TypeRole) == "unknown"


def test_data_parent_id_role_none_for_layer(canvas_model):
    canvas_model.addItem(make_layer())
    index = canvas_model.index(0, 0)
    assert canvas_model.data(index, canvas_model.ParentIdRole) is None


def test_execute_command_without_record(canvas_model):
    command = _DummyCommand()
    canvas_model._execute_command(command, record=False)
    assert command.executed is True


def test_begin_transaction_reentrant_noop(canvas_model):
    canvas_model.addItem(make_rectangle())
    canvas_model.beginTransaction()
    snapshot_id = id(canvas_model._transaction_snapshot)
    canvas_model.beginTransaction()
    assert id(canvas_model._transaction_snapshot) == snapshot_id


def test_end_transaction_without_begin_is_noop(canvas_model):
    canvas_model.endTransaction()
    assert canvas_model.canUndo is False
