# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Unit tests for appearances module."""

import pytest
from PySide6.QtGui import QPainter, QImage, QColor, QPainterPath

from lucent.appearances import (
    Appearance,
    Fill,
    Stroke,
)


class TestFill:
    """Tests for Fill appearance class."""

    def test_basic_creation(self):
        """Test creating a basic fill with default parameters."""
        fill = Fill()
        assert fill.color == "#ffffff"
        assert fill.opacity == 0.0
        assert fill.visible is True

    def test_creation_with_parameters(self):
        """Test creating a fill with custom parameters."""
        fill = Fill(color="#ff0000", opacity=0.5, visible=False)
        assert fill.color == "#ff0000"
        assert fill.opacity == 0.5
        assert fill.visible is False

    def test_opacity_minimum_clamped(self):
        """Test that opacity below 0 is clamped to 0."""
        fill = Fill(opacity=-0.5)
        assert fill.opacity == 0.0

    def test_opacity_maximum_clamped(self):
        """Test that opacity above 1 is clamped to 1."""
        fill = Fill(opacity=1.5)
        assert fill.opacity == 1.0

    def test_to_dict(self):
        """Test serialization to dictionary."""
        fill = Fill(color="#00ff00", opacity=0.75, visible=True)
        data = fill.to_dict()
        assert data == {
            "type": "fill",
            "color": "#00ff00",
            "opacity": 0.75,
            "visible": True,
        }

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "type": "fill",
            "color": "#0000ff",
            "opacity": 0.3,
            "visible": False,
        }
        fill = Fill.from_dict(data)
        assert fill.color == "#0000ff"
        assert fill.opacity == 0.3
        assert fill.visible is False

    def test_from_dict_defaults(self):
        """Test from_dict uses defaults for missing fields."""
        data = {"type": "fill"}
        fill = Fill.from_dict(data)
        assert fill.color == "#ffffff"
        assert fill.opacity == 0.0
        assert fill.visible is True

    def test_from_dict_clamps_opacity(self):
        """Test from_dict clamps opacity values."""
        data = {"type": "fill", "opacity": 5.0}
        fill = Fill.from_dict(data)
        assert fill.opacity == 1.0

    def test_round_trip(self):
        """Test serialization round-trip."""
        original = Fill(color="#abcdef", opacity=0.6, visible=False)
        data = original.to_dict()
        restored = Fill.from_dict(data)
        assert restored.color == original.color
        assert restored.opacity == original.opacity
        assert restored.visible == original.visible

    def test_render_smoke_test(self, qtbot):
        """Smoke test: render does not crash."""
        img = QImage(100, 100, QImage.Format.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)

        fill = Fill(color="#ff0000", opacity=0.5, visible=True)
        path = QPainterPath()
        path.addRect(10, 10, 50, 50)

        fill.render(painter, path, zoom_level=1.0, offset_x=0, offset_y=0)
        painter.end()

    def test_render_not_visible_does_nothing(self, qtbot):
        """Test that render does nothing when visible is False."""
        img = QImage(100, 100, QImage.Format.Format_ARGB32)
        img.fill(0xFFFFFFFF)
        painter = QPainter(img)

        fill = Fill(color="#ff0000", opacity=1.0, visible=False)
        path = QPainterPath()
        path.addRect(10, 10, 50, 50)

        fill.render(painter, path, zoom_level=1.0, offset_x=0, offset_y=0)
        painter.end()

        # Image should still be white (no red painted)
        center_pixel = img.pixelColor(35, 35)
        assert center_pixel == QColor(0xFFFFFFFF)

    def test_render_zero_opacity_does_nothing(self, qtbot):
        """Test that render does nothing when opacity is 0."""
        img = QImage(100, 100, QImage.Format.Format_ARGB32)
        img.fill(0xFFFFFFFF)
        painter = QPainter(img)

        fill = Fill(color="#ff0000", opacity=0.0, visible=True)
        path = QPainterPath()
        path.addRect(10, 10, 50, 50)

        fill.render(painter, path, zoom_level=1.0, offset_x=0, offset_y=0)
        painter.end()

        center_pixel = img.pixelColor(35, 35)
        assert center_pixel == QColor(0xFFFFFFFF)

    def test_render_with_offset(self, qtbot):
        """Test that render applies offset correctly."""
        img = QImage(100, 100, QImage.Format.Format_ARGB32)
        img.fill(0xFFFFFFFF)
        painter = QPainter(img)

        fill = Fill(color="#ff0000", opacity=1.0, visible=True)
        path = QPainterPath()
        path.addRect(0, 0, 20, 20)

        fill.render(painter, path, zoom_level=1.0, offset_x=40, offset_y=40)
        painter.end()

        offset_pixel = img.pixelColor(50, 50)
        assert offset_pixel.red() == 255
        origin_pixel = img.pixelColor(10, 10)
        assert origin_pixel == QColor(0xFFFFFFFF)


class TestStroke:
    """Tests for Stroke appearance class."""

    def test_basic_creation(self):
        """Test creating a basic stroke with default parameters."""
        stroke = Stroke()
        assert stroke.color == "#ffffff"
        assert stroke.width == 1.0
        assert stroke.opacity == 1.0
        assert stroke.visible is True
        assert stroke.cap == "butt"
        assert stroke.align == "center"
        assert stroke.order == "top"

    def test_creation_with_parameters(self):
        """Test creating a stroke with custom parameters."""
        stroke = Stroke(color="#00ff00", width=3.0, opacity=0.8, visible=False)
        assert stroke.color == "#00ff00"
        assert stroke.width == 3.0
        assert stroke.opacity == 0.8
        assert stroke.visible is False

    def test_width_minimum_clamped(self):
        """Test that width below 0 is clamped to 0."""
        stroke = Stroke(width=-5)
        assert stroke.width == 0.0

    def test_width_maximum_clamped(self):
        """Test that width above 100 is clamped to 100."""
        stroke = Stroke(width=150)
        assert stroke.width == 100.0

    def test_opacity_minimum_clamped(self):
        """Test that opacity below 0 is clamped to 0."""
        stroke = Stroke(opacity=-0.5)
        assert stroke.opacity == 0.0

    def test_opacity_maximum_clamped(self):
        """Test that opacity above 1 is clamped to 1."""
        stroke = Stroke(opacity=1.5)
        assert stroke.opacity == 1.0

    def test_to_dict(self):
        """Test serialization to dictionary."""
        stroke = Stroke(color="#0000ff", width=2.5, opacity=0.9, visible=True)
        data = stroke.to_dict()
        assert data == {
            "type": "stroke",
            "color": "#0000ff",
            "width": 2.5,
            "opacity": 0.9,
            "visible": True,
            "cap": "butt",
            "align": "center",
            "order": "top",
        }

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "type": "stroke",
            "color": "#ff00ff",
            "width": 4.0,
            "opacity": 0.6,
            "visible": False,
        }
        stroke = Stroke.from_dict(data)
        assert stroke.color == "#ff00ff"
        assert stroke.width == 4.0
        assert stroke.opacity == 0.6
        assert stroke.visible is False

    def test_from_dict_defaults(self):
        """Test from_dict uses defaults for missing fields."""
        data = {"type": "stroke"}
        stroke = Stroke.from_dict(data)
        assert stroke.color == "#ffffff"
        assert stroke.width == 1.0
        assert stroke.opacity == 1.0
        assert stroke.visible is True
        assert stroke.cap == "butt"
        assert stroke.align == "center"
        assert stroke.order == "top"

    def test_from_dict_clamps_values(self):
        """Test from_dict clamps width and opacity values."""
        data = {"type": "stroke", "width": 200, "opacity": -1.0}
        stroke = Stroke.from_dict(data)
        assert stroke.width == 100.0
        assert stroke.opacity == 0.0

    def test_round_trip(self):
        """Test serialization round-trip."""
        original = Stroke(
            color="#123456",
            width=5.0,
            opacity=0.7,
            visible=False,
            cap="round",
            align="outer",
            order="bottom",
        )
        data = original.to_dict()
        restored = Stroke.from_dict(data)
        assert restored.color == original.color
        assert restored.width == original.width
        assert restored.opacity == original.opacity
        assert restored.visible == original.visible
        assert restored.cap == original.cap
        assert restored.align == original.align
        assert restored.order == original.order

    def test_cap_values(self):
        """Test that all valid cap values are accepted."""
        for cap_value in ("butt", "square", "round"):
            stroke = Stroke(cap=cap_value)
            assert stroke.cap == cap_value

    def test_cap_invalid_defaults_to_butt(self):
        """Test that invalid cap values default to butt."""
        stroke = Stroke(cap="invalid")
        assert stroke.cap == "butt"

    def test_from_dict_with_cap(self):
        """Test deserialization with cap value."""
        data = {"type": "stroke", "cap": "round"}
        stroke = Stroke.from_dict(data)
        assert stroke.cap == "round"

    def test_to_dict_with_cap(self):
        """Test serialization includes cap value."""
        stroke = Stroke(cap="square")
        data = stroke.to_dict()
        assert data["cap"] == "square"

    def test_align_values(self):
        """Test that all valid align values are accepted."""
        for align_value in ("center", "inner", "outer"):
            stroke = Stroke(align=align_value)
            assert stroke.align == align_value

    def test_align_invalid_defaults_to_center(self):
        """Test that invalid align values default to center."""
        stroke = Stroke(align="invalid")
        assert stroke.align == "center"

    def test_from_dict_with_align(self):
        """Test deserialization with align value."""
        data = {"type": "stroke", "align": "inner"}
        stroke = Stroke.from_dict(data)
        assert stroke.align == "inner"

    def test_to_dict_with_align(self):
        """Test serialization includes align value."""
        stroke = Stroke(align="outer")
        data = stroke.to_dict()
        assert data["align"] == "outer"

    def test_order_values(self):
        """Test that all valid order values are accepted."""
        for order_value in ("top", "bottom"):
            stroke = Stroke(order=order_value)
            assert stroke.order == order_value

    def test_order_invalid_defaults_to_top(self):
        """Test that invalid order values default to top."""
        stroke = Stroke(order="invalid")
        assert stroke.order == "top"

    def test_from_dict_with_order(self):
        """Test deserialization with order value."""
        data = {"type": "stroke", "order": "bottom"}
        stroke = Stroke.from_dict(data)
        assert stroke.order == "bottom"

    def test_to_dict_with_order(self):
        """Test serialization includes order value."""
        stroke = Stroke(order="bottom")
        data = stroke.to_dict()
        assert data["order"] == "bottom"

    def test_render_smoke_test(self, qtbot):
        """Smoke test: render does not crash."""
        img = QImage(100, 100, QImage.Format.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)

        stroke = Stroke(color="#00ff00", width=2.0, opacity=1.0, visible=True)
        path = QPainterPath()
        path.addRect(10, 10, 50, 50)

        stroke.render(painter, path, zoom_level=1.0, offset_x=0, offset_y=0)
        painter.end()

    def test_render_inner_align(self, qtbot):
        """Test that inner alignment renders without crashing."""
        img = QImage(100, 100, QImage.Format.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)

        stroke = Stroke(
            color="#ff0000", width=5.0, opacity=1.0, visible=True, align="inner"
        )
        path = QPainterPath()
        path.addRect(20, 20, 60, 60)

        stroke.render(painter, path, zoom_level=1.0, offset_x=0, offset_y=0)
        painter.end()

    def test_render_outer_align(self, qtbot):
        """Test that outer alignment renders without crashing."""
        img = QImage(100, 100, QImage.Format.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)

        stroke = Stroke(
            color="#0000ff", width=5.0, opacity=1.0, visible=True, align="outer"
        )
        path = QPainterPath()
        path.addRect(20, 20, 60, 60)

        stroke.render(painter, path, zoom_level=1.0, offset_x=0, offset_y=0)
        painter.end()

    def test_render_not_visible_does_nothing(self, qtbot):
        """Test that render does nothing when visible is False."""
        img = QImage(100, 100, QImage.Format.Format_ARGB32)
        img.fill(0xFFFFFFFF)
        painter = QPainter(img)

        stroke = Stroke(color="#ff0000", width=5.0, opacity=1.0, visible=False)
        path = QPainterPath()
        path.addRect(20, 20, 40, 40)

        stroke.render(painter, path, zoom_level=1.0, offset_x=0, offset_y=0)
        painter.end()

        edge_pixel = img.pixelColor(20, 40)
        assert edge_pixel == QColor(0xFFFFFFFF)

    def test_render_zero_width_does_nothing(self, qtbot):
        """Test that render does nothing when width is 0."""
        img = QImage(100, 100, QImage.Format.Format_ARGB32)
        img.fill(0xFFFFFFFF)
        painter = QPainter(img)

        stroke = Stroke(color="#ff0000", width=0.0, opacity=1.0, visible=True)
        path = QPainterPath()
        path.addRect(20, 20, 40, 40)

        stroke.render(painter, path, zoom_level=1.0, offset_x=0, offset_y=0)
        painter.end()

        edge_pixel = img.pixelColor(20, 40)
        assert edge_pixel == QColor(0xFFFFFFFF)

    def test_render_with_offset(self, qtbot):
        """Test that render applies offset correctly."""
        img = QImage(100, 100, QImage.Format.Format_ARGB32)
        img.fill(0xFFFFFFFF)
        painter = QPainter(img)

        stroke = Stroke(color="#0000ff", width=5.0, opacity=1.0, visible=True)
        path = QPainterPath()
        path.addRect(0, 0, 20, 20)

        stroke.render(painter, path, zoom_level=1.0, offset_x=40, offset_y=40)
        painter.end()

        origin_pixel = img.pixelColor(5, 5)
        assert origin_pixel == QColor(0xFFFFFFFF)


class TestAppearanceIsAbstract:
    """Tests to verify Appearance is properly abstract."""

    def test_cannot_instantiate_appearance_directly(self):
        """Test that Appearance cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Appearance()  # type: ignore


class TestAppearanceFromDict:
    """Tests for Appearance.from_dict factory method."""

    def test_from_dict_creates_fill(self):
        """Test that from_dict creates Fill for type 'fill'."""
        data = {"type": "fill", "color": "#ff0000", "opacity": 0.5}
        appearance = Appearance.from_dict(data)
        assert isinstance(appearance, Fill)
        assert appearance.color == "#ff0000"

    def test_from_dict_creates_stroke(self):
        """Test that from_dict creates Stroke for type 'stroke'."""
        data = {"type": "stroke", "color": "#00ff00", "width": 3.0}
        appearance = Appearance.from_dict(data)
        assert isinstance(appearance, Stroke)
        assert appearance.width == 3.0

    def test_from_dict_unknown_type_raises(self):
        """Test that from_dict raises for unknown type."""
        data = {"type": "unknown"}
        with pytest.raises(ValueError, match="Unknown appearance type"):
            Appearance.from_dict(data)

    def test_from_dict_missing_type_raises(self):
        """Test that from_dict raises for missing type."""
        data = {"color": "#ff0000"}
        with pytest.raises(ValueError, match="Unknown appearance type"):
            Appearance.from_dict(data)
