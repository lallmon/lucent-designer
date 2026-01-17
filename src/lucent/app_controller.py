# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Application-level controller for cross-cutting UI concerns.

This controller provides a decoupled way for nested QML components to trigger
application-level actions without signal chains through intermediate containers.
"""

from PySide6.QtCore import QObject, Signal, Slot


class AppController(QObject):
    """Handles application-level actions that span multiple UI components."""

    # Emitted when a component requests the export dialog
    exportRequested = Signal(str, str, arguments=["artboardId", "artboardName"])

    # Emitted when a component requests focus return to the canvas
    focusCanvasRequested = Signal()

    @Slot(str, str)
    def openExportDialog(self, artboard_id: str, artboard_name: str) -> None:
        """Request the export dialog to open for a specific artboard."""
        self.exportRequested.emit(artboard_id, artboard_name)

    @Slot()
    def focusCanvas(self) -> None:
        """Request focus to return to the canvas/viewport."""
        self.focusCanvasRequested.emit()
