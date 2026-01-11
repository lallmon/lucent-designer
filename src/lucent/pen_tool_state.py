# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""State container for the Pen tool interactions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


def _to_point(x: float, y: float) -> Tuple[float, float]:
    return float(x), float(y)


@dataclass
class PenToolState:
    """Lightweight state machine used by the pen tool.

    Keeps track of placed points, preview point, and closed state so it can be
    unit tested without QML.
    """

    points: List[Tuple[float, float]] = field(default_factory=list)
    preview_point: Optional[Tuple[float, float]] = None
    closed: bool = False

    def add_point(self, x: float, y: float) -> None:
        if self.closed:
            return
        self.points.append(_to_point(x, y))
        self.preview_point = None

    def preview_to(
        self, x: float, y: float
    ) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
        if self.closed or not self.points:
            return None
        self.preview_point = _to_point(x, y)
        return self.points[-1], self.preview_point

    def try_close_on(self, x: float, y: float, tolerance: float = 0.001) -> bool:
        if self.closed or len(self.points) < 2:
            return False
        first_x, first_y = self.points[0]
        dx = abs(first_x - float(x))
        dy = abs(first_y - float(y))
        if dx <= tolerance and dy <= tolerance:
            self.closed = True
            self.preview_point = None
            return True
        return False

    def reset(self) -> None:
        self.points.clear()
        self.preview_point = None
        self.closed = False

    def to_item_data(
        self, settings: Optional[Dict[str, float]] = None
    ) -> Dict[str, object]:
        """Convert state to item data in new geometry/appearances format."""
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
                "points": [{"x": x, "y": y} for (x, y) in self.points],
                "closed": bool(self.closed),
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
