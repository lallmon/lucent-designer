# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""State container for the Pen tool with bezier curve support.

This module provides a state machine for the pen tool that supports:
- Click to place corner points (no handles)
- Click+drag to place smooth points with symmetric handles
- Path closing when clicking near first point
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Minimum drag distance (in canvas units) to create handles instead of corner
DRAG_THRESHOLD = 6.0


@dataclass
class PenToolState:
    """State machine for bezier pen tool.

    Tracks placed points with their handles, current drag state,
    and preview position for rendering.
    """

    # Committed points with optional handles
    points: List[Dict[str, Any]] = field(default_factory=list)

    # Drag state
    is_dragging: bool = False
    drag_start: Optional[Tuple[float, float]] = None

    # Preview position (cursor when not dragging)
    preview_point: Optional[Tuple[float, float]] = None

    # Path state
    closed: bool = False

    def begin_point(self, x: float, y: float) -> None:
        """Start placing a new anchor point (mouse press).

        The point is not committed until end_point() is called,
        allowing the user to drag out handles.
        """
        if self.closed:
            return

        self.is_dragging = True
        self.drag_start = (float(x), float(y))
        self.preview_point = None

    def update_drag(self, x: float, y: float) -> Optional[Tuple[float, float]]:
        """Update during drag to show handle preview (mouse move while pressed).

        Returns the current handle position for preview rendering,
        or None if not currently dragging.
        """
        if not self.is_dragging or self.drag_start is None:
            return None

        return (float(x), float(y))

    def end_point(self, x: float, y: float) -> None:
        """Finalize point placement (mouse release).

        If the drag distance is small, creates a corner point.
        If dragged, creates a smooth point with symmetric handles.
        """
        if not self.is_dragging or self.drag_start is None:
            return

        anchor_x, anchor_y = self.drag_start
        end_x, end_y = float(x), float(y)

        dx = end_x - anchor_x
        dy = end_y - anchor_y
        drag_distance = (dx**2 + dy**2) ** 0.5

        is_first_point = len(self.points) == 0

        if drag_distance < DRAG_THRESHOLD:
            point: Dict[str, Any] = {"x": anchor_x, "y": anchor_y}
        else:
            handle_out = {"x": end_x, "y": end_y}

            point = {
                "x": anchor_x,
                "y": anchor_y,
                "handleOut": handle_out,
            }

            if not is_first_point:
                handle_in = {"x": anchor_x - dx, "y": anchor_y - dy}
                point["handleIn"] = handle_in

        self.points.append(point)
        self.is_dragging = False
        self.drag_start = None

    def preview_to(self, x: float, y: float) -> None:
        """Set preview point for rendering preview line (mouse move, not dragging).

        This is ignored during drag operations.
        """
        if self.is_dragging:
            return

        self.preview_point = (float(x), float(y))

    def try_close(self, x: float, y: float, tolerance: float = 10.0) -> bool:
        """Check if position is near first point to close the path.

        Returns True if path was closed, False otherwise.
        When closing, adds symmetric handleIn to first point if it has handleOut,
        so the closing segment has proper bezier control.
        """
        if self.closed or len(self.points) < 2:
            return False

        first = self.points[0]
        dx = abs(first["x"] - float(x))
        dy = abs(first["y"] - float(y))

        if dx <= tolerance and dy <= tolerance:
            self.closed = True
            self.preview_point = None

            # Add symmetric handleIn to first point for proper closing curve
            if "handleOut" in first and "handleIn" not in first:
                anchor_x, anchor_y = first["x"], first["y"]
                handle_out = first["handleOut"]
                ho_dx = handle_out["x"] - anchor_x
                ho_dy = handle_out["y"] - anchor_y
                first["handleIn"] = {"x": anchor_x - ho_dx, "y": anchor_y - ho_dy}

            return True

        return False

    def reset(self) -> None:
        """Clear all state to start a new path."""
        self.points.clear()
        self.is_dragging = False
        self.drag_start = None
        self.preview_point = None
        self.closed = False

    def to_item_data(self, settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convert current state to item data for canvas model.

        Args:
            settings: Optional appearance settings (strokeWidth, strokeColor, etc.)

        Returns:
            Dictionary with type, geometry, and appearances for path item.

        Raises:
            ValueError: If fewer than 2 points are placed.
        """
        if len(self.points) < 2:
            raise ValueError("Path must have at least two points")

        style = settings or {}
        stroke_width = float(style.get("strokeWidth", 1))
        stroke_color = style.get("strokeColor", "#ffffff")
        stroke_opacity = float(style.get("strokeOpacity", 1.0))
        fill_color = style.get("fillColor", "#ffffff")
        fill_opacity = float(style.get("fillOpacity", 0.0))

        return {
            "type": "path",
            "geometry": {
                "points": self.points,
                "closed": self.closed,
            },
            "appearances": [
                {
                    "type": "fill",
                    "color": fill_color,
                    "opacity": fill_opacity,
                    "visible": True,
                },
                {
                    "type": "stroke",
                    "color": stroke_color,
                    "width": stroke_width,
                    "opacity": stroke_opacity,
                    "visible": True,
                },
            ],
        }
