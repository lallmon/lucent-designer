# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
from PySide6.QtCore import QRectF

from lucent.geometry import PathGeometry, RectGeometry


def test_rect_geometry_per_corner_path_bounds():
    geom = RectGeometry(
        x=10,
        y=20,
        width=100,
        height=50,
        corner_radius_tl=10,
        corner_radius_tr=15,
        corner_radius_br=20,
        corner_radius_bl=5,
    )
    path = geom.to_painter_path()
    bounds = path.boundingRect()
    assert bounds == QRectF(10, 20, 100, 50)


def _make_path_geometry_without_init(points, closed):
    geom = PathGeometry.__new__(PathGeometry)
    geom.points = points
    geom.closed = closed
    return geom


def test_path_geometry_to_painter_path_empty():
    geom = _make_path_geometry_without_init(points=[], closed=False)
    path = geom.to_painter_path()
    assert path.elementCount() == 0


def test_path_geometry_bounds_empty_points():
    geom = _make_path_geometry_without_init(points=[], closed=False)
    bounds = geom.get_bounds()
    assert bounds.isEmpty()


def test_path_geometry_flattened_points_empty():
    geom = _make_path_geometry_without_init(points=[], closed=False)
    assert geom._get_flattened_points() == []


def test_path_geometry_from_dict_requires_points_list():
    with pytest.raises(ValueError, match="points must be a list"):
        PathGeometry.from_dict({"points": "nope", "closed": False})


def test_path_geometry_from_dict_requires_two_points():
    with pytest.raises(ValueError, match="at least two points"):
        PathGeometry.from_dict({"points": [{"x": 0, "y": 0}], "closed": False})


def test_path_geometry_control_points_defaults():
    points = [
        {"x": 0, "y": 0},
        {
            "x": 10,
            "y": 0,
            "handleIn": {"x": 5, "y": 5},
            "handleOut": {"x": 15, "y": -5},
        },
        {"x": 20, "y": 0},
    ]
    geom = PathGeometry(points=points, closed=False)
    path = geom.to_painter_path()
    assert path.elementCount() > 0


def test_path_geometry_flatten_handles_closed_last_segment():
    points = [
        {"x": 0, "y": 0, "handleIn": {"x": -5, "y": 5}},
        {"x": 10, "y": 0, "handleOut": {"x": 15, "y": -5}},
    ]
    geom = PathGeometry(points=points, closed=True)
    flat = geom._get_flattened_points()
    assert len(flat) >= 2


def test_path_geometry_fill_vertices_empty_for_open():
    geom = PathGeometry(points=[{"x": 0, "y": 0}, {"x": 10, "y": 0}], closed=False)
    assert geom.to_fill_vertices() == []


def test_path_geometry_fill_vertices_empty_for_small_closed():
    geom = PathGeometry(points=[{"x": 0, "y": 0}, {"x": 10, "y": 0}], closed=True)
    assert geom.to_fill_vertices() == []


def test_path_geometry_stroke_vertices_handles_zero_length():
    points = [
        {
            "x": 0,
            "y": 0,
            "handleOut": {"x": 0, "y": 0},
        },
        {
            "x": 0,
            "y": 0,
            "handleIn": {"x": 0, "y": 0},
        },
    ]
    geom = PathGeometry(points=points, closed=False)
    vertices = geom.to_stroke_vertices(stroke_width=2.0)
    assert len(vertices) == 4


def test_path_geometry_stroke_vertices_empty_for_single_point():
    geom = _make_path_geometry_without_init(points=[{"x": 0, "y": 0}], closed=False)
    assert geom.to_stroke_vertices() == []
