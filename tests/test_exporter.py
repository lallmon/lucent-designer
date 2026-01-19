# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage, QImageWriter, QColor
import pytest

from lucent.appearances import Fill, Stroke
from lucent.canvas_items import RectangleItem
from lucent.exporter import (
    ExportOptions,
    compute_bounds,
    export_jpg,
    export_pdf,
    export_png,
    export_svg,
)
from lucent.geometry import RectGeometry


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


def test_export_jpg_writes_file(tmp_path):
    formats = {bytes(fmt).lower() for fmt in QImageWriter.supportedImageFormats()}
    if b"jpg" not in formats and b"jpeg" not in formats:
        pytest.skip("JPEG image format plugin not available")
    probe_path = tmp_path / "_probe.jpg"
    probe_writer = QImageWriter(str(probe_path), b"jpg")
    probe_image = QImage(1, 1, QImage.Format.Format_RGB32)
    probe_image.fill(QColor("#ffffff"))
    if not probe_writer.write(probe_image):
        pytest.skip(f"JPEG writer unavailable: {probe_writer.errorString()}")
    options = ExportOptions(background="#ffffff")
    bounds = QRectF(0, 0, 10, 10)
    result = export_jpg([], bounds, tmp_path / "out.jpg", options)
    assert result is True
    assert (tmp_path / "out.jpg").exists()


def test_export_jpg_returns_false_on_empty_bounds(tmp_path):
    options = ExportOptions(background="#ffffff")
    result = export_jpg([], QRectF(), tmp_path / "out.jpg", options)
    assert result is False


def test_export_pdf_writes_file(tmp_path):
    options = ExportOptions()
    bounds = QRectF(0, 0, 10, 10)
    result = export_pdf([], bounds, tmp_path / "out.pdf", options)
    assert result is True
    assert (tmp_path / "out.pdf").exists()


def test_export_pdf_returns_false_on_empty_bounds(tmp_path):
    options = ExportOptions()
    result = export_pdf([], QRectF(), tmp_path / "out.pdf", options)
    assert result is False


def test_export_svg_writes_file_with_background(tmp_path):
    rect = _make_rectangle_item(x=0, y=0, width=10, height=10)
    bounds = QRectF(0, 0, 10, 10)
    options = ExportOptions(background="#ff0000")
    out_path = tmp_path / "out.svg"
    assert export_svg([rect], bounds, out_path, options) is True
    assert out_path.exists()
    assert out_path.stat().st_size > 0


def test_export_svg_returns_false_on_empty_bounds(tmp_path):
    options = ExportOptions()
    result = export_svg([], QRectF(), tmp_path / "out.svg", options)
    assert result is False
