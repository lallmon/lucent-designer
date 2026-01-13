# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Unit and DPI settings exposed to QML."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Property, Signal, Slot

from lucent.units import canvas_to_unit, unit_to_canvas, Unit


class UnitSettings(QObject):
    displayUnitChanged = Signal()
    previewDPIChanged = Signal()
    gridSpacingValueChanged = Signal()
    gridSpacingUnitChanged = Signal()
    gridSpacingCanvasChanged = Signal()

    def __init__(
        self,
        display_unit: Unit = "px",
        preview_dpi: float = 96.0,
        grid_spacing_value: float = 10.0,
        grid_spacing_unit: Unit = "mm",
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._display_unit: Unit = display_unit
        self._preview_dpi: float = preview_dpi
        self._grid_spacing_value: float = grid_spacing_value
        self._grid_spacing_unit: Unit = grid_spacing_unit

    # Display unit
    def _get_display_unit(self) -> Unit:
        return self._display_unit

    def _set_display_unit(self, value: Unit) -> None:
        if value == self._display_unit:
            return
        self._display_unit = value
        self.displayUnitChanged.emit()
        self.gridSpacingCanvasChanged.emit()

    displayUnit = Property(
        str, _get_display_unit, _set_display_unit, notify=displayUnitChanged
    )

    # Preview DPI (used for on-canvas conversions and buffer sizing)
    def _get_preview_dpi(self) -> float:
        return self._preview_dpi

    def _set_preview_dpi(self, value: float) -> None:
        if value <= 0:
            return
        if abs(value - self._preview_dpi) < 1e-9:
            return
        self._preview_dpi = value
        self.previewDPIChanged.emit()
        self.gridSpacingCanvasChanged.emit()

    previewDPI = Property(
        float, _get_preview_dpi, _set_preview_dpi, notify=previewDPIChanged
    )

    # Grid spacing value
    def _get_grid_spacing_value(self) -> float:
        return self._grid_spacing_value

    def _set_grid_spacing_value(self, value: float) -> None:
        if value <= 0:
            return
        if abs(value - self._grid_spacing_value) < 1e-9:
            return
        self._grid_spacing_value = value
        self.gridSpacingValueChanged.emit()
        self.gridSpacingCanvasChanged.emit()

    gridSpacingValue = Property(
        float,
        _get_grid_spacing_value,
        _set_grid_spacing_value,
        notify=gridSpacingValueChanged,
    )

    # Grid spacing unit
    def _get_grid_spacing_unit(self) -> Unit:
        return self._grid_spacing_unit

    def _set_grid_spacing_unit(self, value: Unit) -> None:
        if value == self._grid_spacing_unit:
            return
        self._grid_spacing_unit = value
        self.gridSpacingUnitChanged.emit()
        self.gridSpacingCanvasChanged.emit()

    gridSpacingUnit = Property(
        str,
        _get_grid_spacing_unit,
        _set_grid_spacing_unit,
        notify=gridSpacingUnitChanged,
    )

    # Derived canvas spacing
    def _get_grid_spacing_canvas(self) -> float:
        return unit_to_canvas(
            self._grid_spacing_value, self._grid_spacing_unit, self._preview_dpi
        )

    gridSpacingCanvas = Property(
        float, _get_grid_spacing_canvas, notify=gridSpacingCanvasChanged
    )

    # Unit-aware grid defaults (minor, major multiplier, label style, target px)
    @Slot(result="QVariantMap")  # type: ignore[arg-type]
    def gridConfig(self) -> dict[str, object]:
        unit = self._display_unit
        dpi = self._preview_dpi
        if unit == "in":
            minor_canvas = unit_to_canvas(0.5, "in", dpi)  # 1/2"
            major_mult = 4  # 2"
            label_style = "fraction"
            target_px = 100.0
            allowed_major = [2.0, 4.0, 8.0]  # inches
        elif unit == "mm":
            minor_canvas = unit_to_canvas(20.0, "mm", dpi)  # 20 mm
            major_mult = 5  # 100 mm
            label_style = "decimal"
            target_px = 120.0
            allowed_major = [100.0, 200.0, 500.0]  # mm
        else:  # px
            minor_canvas = 10.0
            major_mult = 10
            label_style = "decimal"
            target_px = 100.0
            allowed_major = [100.0, 200.0, 400.0]  # px

        return {
            "minorCanvas": minor_canvas,
            "majorMultiplier": major_mult,
            "labelStyle": label_style,
            "targetMajorPx": target_px,
            "allowedMajorUnits": allowed_major,
        }

    # Conversion helpers exposed to QML
    @Slot(float, result=float)
    def canvasToDisplay(self, value: float) -> float:
        return canvas_to_unit(value, self._display_unit, self._preview_dpi)

    @Slot(float, result=float)
    def displayToCanvas(self, value: float) -> float:
        return unit_to_canvas(value, self._display_unit, self._preview_dpi)

    # Helpers for syncing
    def load_from_meta(self, meta: dict[str, object]) -> None:
        """Load settings from document meta dict."""
        unit = meta.get("displayUnit", self._display_unit)
        dpi = meta.get("previewDPI", meta.get("documentDPI", self._preview_dpi))
        grid_value = meta.get("gridSpacingValue", self._grid_spacing_value)
        grid_unit = meta.get("gridSpacingUnit", self._grid_spacing_unit)

        if isinstance(unit, str):
            self._set_display_unit(unit)  # type: ignore[arg-type]
        if isinstance(dpi, (int, float)):
            self._set_preview_dpi(float(dpi))
        if isinstance(grid_value, (int, float)):
            self._set_grid_spacing_value(float(grid_value))
        if isinstance(grid_unit, str):
            self._set_grid_spacing_unit(grid_unit)  # type: ignore[arg-type]

    def to_meta(self) -> dict[str, object]:
        """Serialize settings to document meta dict."""
        return {
            "displayUnit": self._display_unit,
            "previewDPI": self._preview_dpi,
            "gridSpacingValue": self._grid_spacing_value,
            "gridSpacingUnit": self._grid_spacing_unit,
        }
