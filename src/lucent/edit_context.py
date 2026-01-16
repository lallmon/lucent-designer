# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Edit context helpers for path/node editing."""

from typing import Dict, Optional, Tuple

from PySide6.QtCore import QPointF

from lucent.transforms import Transform


class EditContext:
    """Lightweight edit state and transform helpers."""

    def __init__(self) -> None:
        self._locked_pivots: Dict[int, Tuple[float, float]] = {}

    def lock_pivot(self, index: int, pivot_x: float, pivot_y: float) -> None:
        """Lock the pivot for a given item index."""
        self._locked_pivots[index] = (pivot_x, pivot_y)

    def unlock_pivot(self, index: int) -> None:
        """Unlock any stored pivot for a given item index."""
        self._locked_pivots.pop(index, None)

    def get_locked_pivot(self, index: int) -> Optional[Tuple[float, float]]:
        """Return the locked pivot for an item index, if any."""
        return self._locked_pivots.get(index)

    def map_screen_to_geometry(
        self,
        transform: Transform,
        screen_x: float,
        screen_y: float,
        pivot_override: Optional[Tuple[float, float]] = None,
    ) -> Dict[str, float]:
        """Map screen-space coordinates to geometry space."""
        if transform.is_identity():
            return {"x": screen_x, "y": screen_y}

        pivot_x, pivot_y = pivot_override or (transform.pivot_x, transform.pivot_y)
        qtransform = transform.to_qtransform_centered(pivot_x, pivot_y)
        inverted, ok = qtransform.inverted()
        if not ok:
            return {"x": screen_x, "y": screen_y}

        geom_pt = inverted.map(QPointF(screen_x, screen_y))
        return {"x": geom_pt.x(), "y": geom_pt.y()}
