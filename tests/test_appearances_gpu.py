# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for GPU appearance methods (get_sg_color, should_render, etc.).

These tests verify that appearance classes provide correct data
for scene graph rendering.
"""

import pytest
from PySide6.QtGui import QColor
from lucent.appearances import Fill, Stroke


class TestFillGPU:
    """Tests for Fill GPU methods."""

    def test_get_sg_color_returns_qcolor(self):
        """Fill should return QColor with opacity applied."""
        fill = Fill(color="#ff0000", opacity=0.5, visible=True)
        color = fill.get_sg_color()

        assert isinstance(color, QColor)
        assert color.red() == 255
        assert color.green() == 0
        assert color.blue() == 0
        assert abs(color.alphaF() - 0.5) < 0.01

    def test_get_sg_color_invisible_returns_none(self):
        """Invisible fill should return None."""
        fill = Fill(color="#ff0000", opacity=0.5, visible=False)
        assert fill.get_sg_color() is None

    def test_get_sg_color_zero_opacity_returns_none(self):
        """Zero opacity fill should return None."""
        fill = Fill(color="#ff0000", opacity=0.0, visible=True)
        assert fill.get_sg_color() is None

    def test_should_render_true(self):
        """Fill with opacity should render."""
        fill = Fill(color="#ff0000", opacity=0.5, visible=True)
        assert fill.should_render() is True

    def test_should_render_false_invisible(self):
        """Invisible fill should not render."""
        fill = Fill(color="#ff0000", opacity=0.5, visible=False)
        assert fill.should_render() is False

    def test_should_render_false_zero_opacity(self):
        """Zero opacity fill should not render."""
        fill = Fill(color="#ff0000", opacity=0.0, visible=True)
        assert fill.should_render() is False

    def test_get_stroke_width_zero(self):
        """Fill should return 0 for stroke width."""
        fill = Fill(color="#ff0000", opacity=0.5)
        assert fill.get_stroke_width() == 0.0


class TestStrokeGPU:
    """Tests for Stroke GPU methods."""

    def test_get_sg_color_returns_qcolor(self):
        """Stroke should return QColor with opacity applied."""
        stroke = Stroke(color="#00ff00", width=2.0, opacity=0.8, visible=True)
        color = stroke.get_sg_color()

        assert isinstance(color, QColor)
        assert color.red() == 0
        assert color.green() == 255
        assert color.blue() == 0
        assert abs(color.alphaF() - 0.8) < 0.01

    def test_get_sg_color_invisible_returns_none(self):
        """Invisible stroke should return None."""
        stroke = Stroke(color="#00ff00", width=2.0, opacity=0.8, visible=False)
        assert stroke.get_sg_color() is None

    def test_get_sg_color_zero_width_returns_none(self):
        """Zero width stroke should return None."""
        stroke = Stroke(color="#00ff00", width=0.0, opacity=0.8, visible=True)
        assert stroke.get_sg_color() is None

    def test_get_sg_color_zero_opacity_returns_none(self):
        """Zero opacity stroke should return None."""
        stroke = Stroke(color="#00ff00", width=2.0, opacity=0.0, visible=True)
        assert stroke.get_sg_color() is None

    def test_should_render_true(self):
        """Stroke with width and opacity should render."""
        stroke = Stroke(color="#00ff00", width=2.0, opacity=0.8, visible=True)
        assert stroke.should_render() is True

    def test_should_render_false_invisible(self):
        """Invisible stroke should not render."""
        stroke = Stroke(color="#00ff00", width=2.0, opacity=0.8, visible=False)
        assert stroke.should_render() is False

    def test_should_render_false_zero_width(self):
        """Zero width stroke should not render."""
        stroke = Stroke(color="#00ff00", width=0.0, opacity=0.8, visible=True)
        assert stroke.should_render() is False

    def test_get_stroke_width(self):
        """Stroke should return its width."""
        stroke = Stroke(color="#00ff00", width=3.5, opacity=1.0)
        assert stroke.get_stroke_width() == 3.5

    def test_get_scaled_width_normal_zoom(self):
        """Scaled width at normal zoom should be close to original."""
        stroke = Stroke(color="#00ff00", width=2.0, opacity=1.0)
        scaled = stroke.get_scaled_width(1.0)
        # At zoom 1.0, stroke_px = 2.0, which is within clamp range
        assert abs(scaled - 2.0) < 0.1

    def test_get_scaled_width_zoomed_out(self):
        """Scaled width at low zoom should be clamped minimum."""
        stroke = Stroke(color="#00ff00", width=2.0, opacity=1.0)
        scaled = stroke.get_scaled_width(0.1)
        # At zoom 0.1, stroke_px = 0.2, clamped to 0.3, scaled = 3.0
        assert scaled == pytest.approx(3.0, rel=0.01)

    def test_get_scaled_width_zoomed_in(self):
        """Scaled width at high zoom should be clamped maximum."""
        stroke = Stroke(color="#00ff00", width=20.0, opacity=1.0)
        scaled = stroke.get_scaled_width(10.0)
        # At zoom 10.0, stroke_px = 200.0, clamped to 100.0, scaled = 10.0
        assert scaled == pytest.approx(10.0, rel=0.01)


class TestColorParsing:
    """Tests for color parsing in GPU methods."""

    def test_hex_color_parsing(self):
        """Standard hex colors should parse correctly."""
        fill = Fill(color="#123456", opacity=1.0)
        color = fill.get_sg_color()
        assert color.red() == 0x12
        assert color.green() == 0x34
        assert color.blue() == 0x56

    def test_named_color_parsing(self):
        """Named colors should parse correctly."""
        fill = Fill(color="red", opacity=1.0)
        color = fill.get_sg_color()
        assert color.red() == 255
        assert color.green() == 0
        assert color.blue() == 0

    def test_rgb_with_alpha_preserved(self):
        """Opacity should override any alpha in the color string."""
        fill = Fill(color="#ff000080", opacity=1.0)
        color = fill.get_sg_color()
        # Opacity parameter should set alpha to 1.0
        assert abs(color.alphaF() - 1.0) < 0.01
