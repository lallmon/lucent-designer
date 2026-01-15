# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Unit tests for pen_tool_state module with bezier support."""

import pytest
from lucent.pen_tool_state import PenToolState


class TestPenToolStateBasics:
    """Basic state machine tests."""

    def test_initial_state(self):
        """Test initial state is empty and not dragging."""
        state = PenToolState()
        assert state.points == []
        assert state.is_dragging is False
        assert state.closed is False

    def test_reset_clears_state(self):
        """Test reset clears all state."""
        state = PenToolState()
        state.begin_point(10, 20)
        state.end_point(50, 20)
        state.reset()

        assert state.points == []
        assert state.is_dragging is False
        assert state.closed is False
        assert state.drag_start is None


class TestBeginPoint:
    """Tests for begin_point (mouse press)."""

    def test_begin_point_starts_drag(self):
        """Pressing starts drag mode and records position."""
        state = PenToolState()
        state.begin_point(100, 200)

        assert state.is_dragging is True
        assert state.drag_start == (100.0, 200.0)

    def test_begin_point_does_not_add_to_points_yet(self):
        """Point is not committed until mouse release."""
        state = PenToolState()
        state.begin_point(100, 200)

        assert state.points == []


class TestEndPoint:
    """Tests for end_point (mouse release)."""

    def test_end_point_click_creates_corner(self):
        """Release at same position creates corner point (no handles)."""
        state = PenToolState()
        state.begin_point(100, 200)
        state.end_point(100, 200)  # Same position = click

        assert len(state.points) == 1
        point = state.points[0]
        assert point["x"] == 100.0
        assert point["y"] == 200.0
        assert point.get("handleIn") is None
        assert point.get("handleOut") is None

    def test_end_point_click_within_threshold_creates_corner(self):
        """Release within small threshold still creates corner."""
        state = PenToolState()
        state.begin_point(100, 200)
        state.end_point(101, 201)  # Slightly moved but within threshold

        point = state.points[0]
        assert point.get("handleIn") is None
        assert point.get("handleOut") is None

    def test_end_point_drag_creates_smooth(self):
        """Release far from press creates smooth point with handles."""
        state = PenToolState()
        state.begin_point(100, 200)
        state.end_point(150, 200)  # Dragged 50 pixels right

        assert len(state.points) == 1
        point = state.points[0]
        assert point["x"] == 100.0
        assert point["y"] == 200.0
        # handleOut is at cursor position
        assert point["handleOut"] == {"x": 150.0, "y": 200.0}

    def test_end_point_clears_drag_state(self):
        """Release clears dragging state."""
        state = PenToolState()
        state.begin_point(100, 200)
        state.end_point(150, 200)

        assert state.is_dragging is False
        assert state.drag_start is None


class TestSymmetricHandles:
    """Tests for symmetric handle calculation."""

    def test_symmetric_handles_calculated_correctly(self):
        """handleIn should mirror handleOut across the anchor."""
        state = PenToolState()
        # First point - establish context
        state.begin_point(0, 0)
        state.end_point(50, 0)  # First point with handleOut at (50, 0)

        # Second point with drag
        state.begin_point(100, 0)
        state.end_point(130, 20)  # handleOut at (130, 20)

        second_point = state.points[1]
        # Anchor at (100, 0), handleOut at (130, 20)
        # handleIn should be mirror: (100 - 30, 0 - 20) = (70, -20)
        assert second_point["handleIn"] == {"x": 70.0, "y": -20.0}
        assert second_point["handleOut"] == {"x": 130.0, "y": 20.0}

    def test_first_point_has_no_handle_in_for_open_path(self):
        """First point should not have handleIn for open paths."""
        state = PenToolState()
        state.begin_point(100, 200)
        state.end_point(150, 200)  # Drag to create handles

        first_point = state.points[0]
        assert first_point.get("handleIn") is None
        # But handleOut should exist
        assert first_point["handleOut"] == {"x": 150.0, "y": 200.0}

    def test_first_point_gets_handle_in_when_closed(self):
        """First point should get symmetric handleIn when path is closed."""
        state = PenToolState()
        # First point with handleOut
        state.begin_point(100, 100)
        state.end_point(130, 100)  # handleOut at (130, 100), dx=30

        # Second point
        state.begin_point(200, 100)
        state.end_point(200, 100)

        # Close the path
        state.try_close(100, 100, tolerance=10.0)

        first_point = state.points[0]
        # handleIn should be symmetric: (100 - 30, 100) = (70, 100)
        assert first_point["handleIn"] == {"x": 70.0, "y": 100.0}
        assert first_point["handleOut"] == {"x": 130.0, "y": 100.0}

    def test_first_point_corner_stays_corner_when_closed(self):
        """First point without handleOut should not get handleIn when closed."""
        state = PenToolState()
        # First point as corner (click, no drag)
        state.begin_point(100, 100)
        state.end_point(100, 100)

        # Second point
        state.begin_point(200, 100)
        state.end_point(200, 100)

        # Close the path
        state.try_close(100, 100, tolerance=10.0)

        first_point = state.points[0]
        # Corner point should stay a corner
        assert first_point.get("handleIn") is None
        assert first_point.get("handleOut") is None


class TestUpdateDrag:
    """Tests for update_drag (mouse move during drag)."""

    def test_update_drag_returns_handle_position(self):
        """During drag, update_drag returns current handle position."""
        state = PenToolState()
        state.begin_point(100, 200)
        handle_pos = state.update_drag(150, 220)

        assert handle_pos == (150.0, 220.0)

    def test_update_drag_returns_none_when_not_dragging(self):
        """Returns None if not in drag mode."""
        state = PenToolState()
        handle_pos = state.update_drag(100, 200)

        assert handle_pos is None


class TestPreviewTo:
    """Tests for preview_to (mouse move when not dragging)."""

    def test_preview_to_sets_preview_point(self):
        """Sets preview point for rendering preview line."""
        state = PenToolState()
        state.begin_point(0, 0)
        state.end_point(0, 0)  # Place first point

        state.preview_to(100, 50)
        assert state.preview_point == (100.0, 50.0)

    def test_preview_to_ignored_during_drag(self):
        """preview_to should not update during drag."""
        state = PenToolState()
        state.begin_point(0, 0)  # Start dragging
        state.preview_to(100, 50)

        assert state.preview_point is None


class TestTryClose:
    """Tests for try_close (closing the path)."""

    def test_try_close_near_first_point(self):
        """Clicking near first point closes the path."""
        state = PenToolState()
        # Place 3 points to form a triangle
        state.begin_point(0, 0)
        state.end_point(0, 0)
        state.begin_point(100, 0)
        state.end_point(100, 0)
        state.begin_point(50, 100)
        state.end_point(50, 100)

        # Try to close near first point
        result = state.try_close(2, 2, tolerance=5.0)

        assert result is True
        assert state.closed is True

    def test_try_close_not_near_first_point(self):
        """Returns False if not near first point."""
        state = PenToolState()
        state.begin_point(0, 0)
        state.end_point(0, 0)
        state.begin_point(100, 0)
        state.end_point(100, 0)

        result = state.try_close(50, 50, tolerance=5.0)

        assert result is False
        assert state.closed is False

    def test_try_close_requires_at_least_two_points(self):
        """Cannot close with fewer than 2 points."""
        state = PenToolState()
        state.begin_point(0, 0)
        state.end_point(0, 0)

        result = state.try_close(0, 0, tolerance=5.0)

        assert result is False


class TestToItemData:
    """Tests for to_item_data output format."""

    def test_to_item_data_includes_handles(self):
        """Output should include handle data for smooth points."""
        state = PenToolState()
        state.begin_point(0, 0)
        state.end_point(30, 0)  # Smooth point with handles
        state.begin_point(100, 50)
        state.end_point(130, 50)  # Another smooth point

        data = state.to_item_data()

        assert data["type"] == "path"
        geometry = data["geometry"]
        assert geometry["points"][0]["handleOut"] == {"x": 30.0, "y": 0.0}
        assert geometry["points"][1]["handleIn"] is not None
        assert geometry["points"][1]["handleOut"] == {"x": 130.0, "y": 50.0}

    def test_to_item_data_corner_points_no_handles(self):
        """Corner points should have no handles in output."""
        state = PenToolState()
        state.begin_point(0, 0)
        state.end_point(0, 0)  # Click = corner
        state.begin_point(100, 0)
        state.end_point(100, 0)  # Click = corner

        data = state.to_item_data()

        geometry = data["geometry"]
        assert geometry["points"][0].get("handleIn") is None
        assert geometry["points"][0].get("handleOut") is None

    def test_to_item_data_includes_appearances(self):
        """Output should include stroke and fill appearances."""
        state = PenToolState()
        state.begin_point(0, 0)
        state.end_point(0, 0)
        state.begin_point(100, 0)
        state.end_point(100, 0)

        data = state.to_item_data(
            settings={
                "strokeWidth": 2,
                "strokeColor": "#ff0000",
                "strokeOpacity": 0.8,
                "fillColor": "#00ff00",
                "fillOpacity": 0.5,
            }
        )

        fill = data["appearances"][0]
        stroke = data["appearances"][1]
        assert fill["type"] == "fill"
        assert fill["color"] == "#00ff00"
        assert fill["opacity"] == 0.5
        assert stroke["type"] == "stroke"
        assert stroke["color"] == "#ff0000"
        assert stroke["width"] == 2
        assert stroke["opacity"] == 0.8

    def test_to_item_data_closed_path(self):
        """Closed path should have closed=True in geometry."""
        state = PenToolState()
        state.begin_point(0, 0)
        state.end_point(0, 0)
        state.begin_point(100, 0)
        state.end_point(100, 0)
        state.try_close(0, 0, tolerance=5.0)

        data = state.to_item_data()

        assert data["geometry"]["closed"] is True

    def test_to_item_data_requires_two_points(self):
        """Should raise if fewer than 2 points."""
        state = PenToolState()
        state.begin_point(0, 0)
        state.end_point(0, 0)

        with pytest.raises(ValueError, match="at least two points"):
            state.to_item_data()
