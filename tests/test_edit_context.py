#!/usr/bin/env python3
# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for EditContext helpers."""

from lucent.edit_context import EditContext
from lucent.transforms import Transform


def test_lock_and_unlock_pivot():
    context = EditContext()
    assert context.get_locked_pivot(1) is None

    context.lock_pivot(1, 12.5, -3.0)
    assert context.get_locked_pivot(1) == (12.5, -3.0)

    context.unlock_pivot(1)
    assert context.get_locked_pivot(1) is None


def test_map_screen_to_geometry_uses_locked_pivot():
    transform = Transform(rotate=90, pivot_x=0, pivot_y=0)
    context = EditContext()
    locked_pivot = (10.0, 10.0)

    from PySide6.QtCore import QPointF

    qtransform = transform.to_qtransform_centered(*locked_pivot)
    screen_point = qtransform.map(QPointF(20.0, 10.0))

    geom_point = context.map_screen_to_geometry(
        transform, screen_point.x(), screen_point.y(), locked_pivot
    )
    assert abs(geom_point["x"] - 20.0) < 0.001
    assert abs(geom_point["y"] - 10.0) < 0.001
