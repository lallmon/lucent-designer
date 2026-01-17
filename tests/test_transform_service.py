# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Unit tests for TransformService."""

from lucent.appearances import Fill, Stroke
from lucent.canvas_items import RectangleItem
from lucent.edit_context import EditContext
from lucent.geometry import RectGeometry
from lucent.item_schema import parse_item, parse_item_data, item_to_dict
from lucent.transform_service import TransformService


def _make_rectangle_item():
    geometry = RectGeometry(x=0, y=0, width=100, height=50)
    appearances = [Fill("#ffffff", 1.0, True), Stroke("#000000", 1.0, 1.0, True)]
    return RectangleItem(geometry=geometry, appearances=appearances)


def _make_service(items, begin_calls=None, end_calls=None):
    edit_context = EditContext()

    def get_item(index):
        return items[index] if 0 <= index < len(items) else None

    def is_valid_index(index):
        return 0 <= index < len(items)

    def update_item(index, data):
        parsed = parse_item_data(data)
        items[index] = parse_item(parsed.data)

    def emit_transform_changed(index):
        pass

    def begin_transaction():
        if begin_calls is not None:
            begin_calls.append(True)

    def end_transaction():
        if end_calls is not None:
            end_calls.append(True)

    return TransformService(
        get_item=get_item,
        is_valid_index=is_valid_index,
        edit_context=edit_context,
        item_to_dict=item_to_dict,
        update_item=update_item,
        emit_transform_changed=emit_transform_changed,
        begin_transaction=begin_transaction,
        end_transaction=end_transaction,
    )


def test_rotate_item_normalizes_degrees():
    items = [_make_rectangle_item()]
    service = _make_service(items)

    service.rotate_item(0, 370)

    assert items[0].transform.rotate == 10


def test_get_item_transform_reports_origin():
    items = [_make_rectangle_item()]
    service = _make_service(items)

    transform = service.get_item_transform(0)

    assert transform["originX"] == 0.5
    assert transform["originY"] == 0.5


def test_set_displayed_size_proportional_scales_both_axes():
    items = [_make_rectangle_item()]
    begin_calls = []
    end_calls = []
    service = _make_service(items, begin_calls=begin_calls, end_calls=end_calls)

    service.set_displayed_size(0, "width", 200, True)

    assert items[0].transform.scale_x == 2.0
    assert items[0].transform.scale_y == 2.0
    assert len(begin_calls) == 1
    assert len(end_calls) == 1


def test_set_item_position_moves_pivot_to_target():
    items = [_make_rectangle_item()]
    service = _make_service(items)

    service.set_item_position(0, "x", 100)

    assert items[0].transform.translate_x == 50
