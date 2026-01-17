# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

import xml.etree.ElementTree as ET

from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage

from lucent.appearances import Fill, Stroke
from lucent.canvas_items import EllipseItem, PathItem, RectangleItem, TextItem
from lucent.exporter import ExportOptions, compute_bounds, export_png, export_svg
from lucent.exporter import _item_to_svg_element
from lucent.geometry import EllipseGeometry, PathGeometry, RectGeometry, TextGeometry


class _ExplodingItem:
    def paint(self, *args, **kwargs):
        raise RuntimeError("boom")


def _make_rectangle_item(**geom_kwargs):
    geometry = RectGeometry(**geom_kwargs)
    appearances = [
        Fill("#ffffff", 1.0, True),
        Stroke("#000000", 1.0, 1.0, True),
    ]
    return RectangleItem(geometry=geometry, appearances=appearances)


def _make_path_item(points, closed=False, fill_opacity=1.0):
    geometry = PathGeometry(points=points, closed=closed)
    appearances = [
        Fill("#ff00ff", fill_opacity, True),
        Stroke("#000000", 1.0, 1.0, True),
    ]
    return PathItem(geometry=geometry, appearances=appearances)


def test_compute_bounds_padding_expands():
    rect = _make_rectangle_item(x=10, y=20, width=30, height=40)
    bounds = compute_bounds([rect], padding=2)
    assert bounds.x() == 8
    assert bounds.y() == 18
    assert bounds.width() == 34
    assert bounds.height() == 44


def test_compute_bounds_empty_returns_empty():
    bounds = compute_bounds([])
    assert bounds.isEmpty()


def test_export_png_returns_false_on_empty_bounds(tmp_path):
    options = ExportOptions()
    result = export_png([], QRectF(), tmp_path / "out.png", options)
    assert result is False


def test_export_png_returns_false_on_zero_pixel_size(tmp_path):
    options = ExportOptions()
    bounds = QRectF(0, 0, 0.1, 10)  # width rounds to 0px
    result = export_png([], bounds, tmp_path / "out.png", options)
    assert result is False


def test_export_png_handles_paint_errors(tmp_path):
    options = ExportOptions()
    bounds = QRectF(0, 0, 10, 10)
    result = export_png([_ExplodingItem()], bounds, tmp_path / "out.png", options)
    assert result is True
    assert (tmp_path / "out.png").exists()


def test_export_png_returns_false_on_save_exception(tmp_path, monkeypatch):
    def raise_save(self, *args, **kwargs):
        raise RuntimeError("save failed")

    monkeypatch.setattr(QImage, "save", raise_save, raising=True)
    options = ExportOptions()
    bounds = QRectF(0, 0, 10, 10)
    result = export_png([], bounds, tmp_path / "out.png", options)
    assert result is False


def test_item_to_svg_element_rectangle_uniform():
    rect = _make_rectangle_item(x=0, y=0, width=100, height=50, corner_radius=10)
    elem = _item_to_svg_element(rect)
    assert elem is not None
    assert elem.tag == "rect"
    assert elem.get("rx") == "5.0"
    assert elem.get("ry") == "5.0"


def test_item_to_svg_element_rectangle_per_corner():
    rect = _make_rectangle_item(
        x=0,
        y=0,
        width=100,
        height=50,
        corner_radius_tl=10,
        corner_radius_tr=15,
        corner_radius_br=20,
        corner_radius_bl=5,
    )
    elem = _item_to_svg_element(rect)
    assert elem is not None
    assert elem.tag == "path"
    assert "A" in (elem.get("d") or "")


def test_item_to_svg_element_path_fill_none_when_transparent():
    path = _make_path_item(
        points=[{"x": 0, "y": 0}, {"x": 10, "y": 0}],
        closed=False,
        fill_opacity=0.0,
    )
    elem = _item_to_svg_element(path)
    assert elem is not None
    assert elem.tag == "path"
    assert elem.get("fill") == "none"


def test_item_to_svg_element_ellipse():
    ellipse = EllipseItem(
        geometry=EllipseGeometry(center_x=50, center_y=50, radius_x=20, radius_y=10),
        appearances=[
            Fill("#ffffff", 0.0, True),
            Stroke("#ffffff", 1.0, 1.0, True),
        ],
    )
    elem = _item_to_svg_element(ellipse)
    assert elem is not None
    assert elem.tag == "ellipse"
    assert elem.get("cx") == "50.0"
    assert elem.get("rx") == "20.0"


def test_item_to_svg_element_text():
    text = TextItem(
        geometry=TextGeometry(x=10, y=20, width=100, height=30),
        text="Hello",
        font_family="Arial",
        font_size=12,
        text_color="#000000",
    )
    elem = _item_to_svg_element(text)
    assert elem is not None
    assert elem.tag == "text"
    assert elem.get("x") == "10.0"


def test_export_svg_writes_with_background(tmp_path):
    rect = _make_rectangle_item(x=0, y=0, width=10, height=10)
    bounds = QRectF(0, 0, 10, 10)
    options = ExportOptions(background="#ff0000")

    out_path = tmp_path / "out.svg"
    assert export_svg([rect], bounds, out_path, options) is True

    tree = ET.parse(out_path)
    root = tree.getroot()
    assert root.tag.endswith("svg")
    # First child should be background rect
    bg = list(root)[0]
    assert bg.tag.endswith("rect")
    assert bg.get("fill") == "#ff0000"


def test_export_svg_returns_false_on_write_error(tmp_path, monkeypatch):
    def raise_write(self, *args, **kwargs):
        raise RuntimeError("write failed")

    monkeypatch.setattr(ET.ElementTree, "write", raise_write, raising=True)
    options = ExportOptions()
    bounds = QRectF(0, 0, 10, 10)
    result = export_svg([], bounds, tmp_path / "out.svg", options)
    assert result is False
