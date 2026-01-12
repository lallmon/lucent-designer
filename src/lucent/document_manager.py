# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Document manager for Lucent - handles file operations and document state."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtCore import QObject, Property, Signal, Slot, QUrl

from lucent.file_io import save_document, load_document, FileVersionError
from lucent.item_schema import item_to_dict
from lucent.unit_settings import UnitSettings

if TYPE_CHECKING:
    from lucent.canvas_model import CanvasModel


class DocumentManager(QObject):
    """Manages document state including file path, dirty flag, and file operations.

    This class bridges the CanvasModel with file I/O operations and tracks
    document state for the UI (dirty indicator, window title, etc.).
    """

    dirtyChanged = Signal()
    filePathChanged = Signal()
    documentTitleChanged = Signal()
    viewportChanged = Signal()
    documentDPIChanged = Signal()

    def __init__(
        self,
        canvas_model: "CanvasModel",
        unit_settings: Optional[UnitSettings] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._canvas_model = canvas_model
        self._unit_settings = unit_settings
        self._dirty = False
        self._file_path = ""
        self._document_title = "Untitled"

        # Viewport state (to be saved/restored with document)
        self._viewport_zoom = 1.0
        self._viewport_offset_x = 0.0
        self._viewport_offset_y = 0.0

        # Document DPI for export/metadata (decoupled from preview DPI)
        self._document_dpi = 300

        # Don't track changes until app is fully initialized
        # Call startTracking() from QML after Component.onCompleted
        self._tracking_enabled = False

    def _connect_model_signals(self) -> None:
        """Connect to CanvasModel signals for dirty tracking."""
        self._canvas_model.itemAdded.connect(self._on_model_changed)
        self._canvas_model.itemRemoved.connect(self._on_model_changed)
        self._canvas_model.itemModified.connect(self._on_model_changed)
        self._canvas_model.itemsCleared.connect(self._on_model_changed)
        self._canvas_model.itemsReordered.connect(self._on_model_changed)

    def _disconnect_model_signals(self) -> None:
        """Disconnect from CanvasModel signals temporarily."""
        try:
            self._canvas_model.itemAdded.disconnect(self._on_model_changed)
            self._canvas_model.itemRemoved.disconnect(self._on_model_changed)
            self._canvas_model.itemModified.disconnect(self._on_model_changed)
            self._canvas_model.itemsCleared.disconnect(self._on_model_changed)
            self._canvas_model.itemsReordered.disconnect(self._on_model_changed)
        except RuntimeError:
            # Signals may not be connected
            pass

    def _on_model_changed(self, *args: Any) -> None:
        """Handle any change to the canvas model."""
        if self._tracking_enabled:
            self._set_dirty(True)

    def _set_dirty(self, value: bool) -> None:
        """Set dirty flag and emit signal if changed."""
        if self._dirty != value:
            self._dirty = value
            self.dirtyChanged.emit()

    def _set_file_path(self, value: str) -> None:
        """Set file path and emit signal if changed."""
        if self._file_path != value:
            self._file_path = value
            self.filePathChanged.emit()
            self._update_title()

    def _update_title(self) -> None:
        """Update document title based on current file path."""
        if self._file_path:
            new_title = Path(self._file_path).stem
        else:
            new_title = "Untitled"

        if self._document_title != new_title:
            self._document_title = new_title
            self.documentTitleChanged.emit()

    def _url_to_path(self, url_or_path: str) -> str:
        """Convert a file URL or path to a local file path.

        Handles both 'file:///path' URLs and plain '/path' strings.
        """
        if url_or_path.startswith("file:"):
            qurl = QUrl(url_or_path)
            return qurl.toLocalFile()
        return url_or_path

    def _get_dirty(self) -> bool:
        return self._dirty

    dirty = Property(bool, _get_dirty, notify=dirtyChanged)

    def _get_file_path(self) -> str:
        return self._file_path

    filePath = Property(str, _get_file_path, notify=filePathChanged)

    def _get_document_title(self) -> str:
        return self._document_title

    documentTitle = Property(str, _get_document_title, notify=documentTitleChanged)

    def _get_document_dpi(self) -> int:
        return self._document_dpi

    documentDPI = Property(int, _get_document_dpi, notify=documentDPIChanged)

    @Slot(int)
    def setDocumentDPI(self, dpi: int) -> None:
        """Set document DPI for export scaling.

        Args:
            dpi: Target DPI (e.g., 72 for screen, 300 for print)
        """
        if self._document_dpi != dpi:
            self._document_dpi = dpi
            self.documentDPIChanged.emit()

    @Slot(result=bool)
    def hasUnsavedChanges(self) -> bool:
        """Check if document has unsaved changes."""
        return self._dirty

    @Slot()
    def startTracking(self) -> None:
        """Enable dirty tracking after app initialization.

        Call this from QML after Component.onCompleted to avoid
        marking the document dirty during app startup.
        """
        if not self._tracking_enabled:
            self._connect_model_signals()
            self._tracking_enabled = True

    @Slot(result=bool)
    def newDocument(self) -> bool:
        """Create a new empty document.

        Clears the canvas, resets file path, dirty flag, and DPI to defaults.

        Returns:
            True always (operation cannot fail)
        """
        # Disconnect signals to avoid dirty flag during clear
        self._disconnect_model_signals()

        self._canvas_model.clear()
        self._connect_model_signals()
        self._set_file_path("")
        self._set_dirty(False)
        self.setDocumentDPI(300)
        if self._unit_settings:
            # Reset unit and grid spacing to defaults
            self._unit_settings._set_display_unit("px")
            self._unit_settings._set_grid_spacing_value(10.0)
            self._unit_settings._set_grid_spacing_unit("mm")

        return True

    @Slot(str, result=bool)
    def openDocument(self, path: str) -> bool:
        """Open a document from the specified file path.

        Args:
            path: Path or file URL to the .lucent file to open

        Returns:
            True if document was opened successfully, False on error
        """
        local_path = self._url_to_path(path)

        try:
            data = load_document(local_path)
        except (FileNotFoundError, ValueError, FileVersionError) as e:
            print(f"Error opening document: {e}")
            return False

        # Disconnect during load to avoid marking document dirty
        self._disconnect_model_signals()
        self._canvas_model.clear()

        for item_data in data.get("items", []):
            self._canvas_model.addItem(item_data)

        viewport = data.get("viewport", {})
        self._viewport_zoom = viewport.get("zoomLevel", 1.0)
        self._viewport_offset_x = viewport.get("offsetX", 0.0)
        self._viewport_offset_y = viewport.get("offsetY", 0.0)
        self.viewportChanged.emit()

        # Load document metadata (DPI and unit-related)
        meta = data.get("meta", {})
        dpi_value = meta.get("documentDPI", self._document_dpi)
        self.setDocumentDPI(
            int(dpi_value)
            if isinstance(dpi_value, (int, float))
            else self._document_dpi
        )
        if self._unit_settings:
            self._unit_settings.load_from_meta(meta)

        self._connect_model_signals()

        self._set_file_path(local_path)
        self._set_dirty(False)

        return True

    @Slot(result=bool)
    def saveDocument(self) -> bool:
        """Save document to current file path.

        Returns:
            True if saved successfully, False if no path set or error
        """
        if not self._file_path:
            return False

        return self.saveDocumentAs(self._file_path)

    @Slot(str, result=bool)
    def saveDocumentAs(self, path: str) -> bool:
        """Save document to the specified file path.

        Args:
            path: Path or file URL to save the .lucent file to

        Returns:
            True if saved successfully, False on error
        """
        local_path = self._url_to_path(path)

        try:
            items: List[Dict[str, Any]] = []
            for item in self._canvas_model.getItems():
                items.append(item_to_dict(item))

            viewport = {
                "zoomLevel": self._viewport_zoom,
                "offsetX": self._viewport_offset_x,
                "offsetY": self._viewport_offset_y,
            }

            meta: Dict[str, Any] = {
                "name": Path(local_path).stem,
                "documentDPI": self._document_dpi,
            }

            if self._unit_settings:
                meta.update(self._unit_settings.to_meta())

            save_document(path=local_path, items=items, viewport=viewport, meta=meta)

            self._set_file_path(local_path)
            self._set_dirty(False)

            return True
        except OSError as e:
            print(f"Error saving document: {e}")
            return False

    @Slot(float, float, float)
    def setViewport(self, zoom: float, offset_x: float, offset_y: float) -> None:
        """Set viewport state for saving with document.

        Args:
            zoom: Current zoom level
            offset_x: Current X offset
            offset_y: Current Y offset
        """
        self._viewport_zoom = zoom
        self._viewport_offset_x = offset_x
        self._viewport_offset_y = offset_y

    @Slot(result="QVariant")  # type: ignore[arg-type]
    def getViewport(self) -> Dict[str, float]:
        """Get current viewport state.

        Returns:
            Dictionary with zoomLevel, offsetX, offsetY
        """
        return {
            "zoomLevel": self._viewport_zoom,
            "offsetX": self._viewport_offset_x,
            "offsetY": self._viewport_offset_y,
        }

    @Slot(str, str, int, float, str, result=bool)
    def exportLayer(
        self,
        layer_id: str,
        path: str,
        target_dpi: int,
        padding: float,
        background: str,
    ) -> bool:
        """Export a layer to PNG or SVG.

        Args:
            layer_id: ID of the layer to export
            path: Output file path (format determined by extension)
            target_dpi: Target DPI for export (e.g., 72, 144, 300)
            padding: Padding in canvas units
            background: Background color (empty for transparent)

        Returns:
            True if export succeeded, False on error
        """
        from lucent.exporter import (
            ExportOptions,
            export_png,
            export_svg,
            compute_bounds,
        )

        local_path = self._url_to_path(path)
        items = self._canvas_model.getLayerItems(layer_id)

        if not items:
            return False

        options = ExportOptions(
            document_dpi=self._document_dpi,
            target_dpi=target_dpi,
            padding=padding,
            background=background if background else None,
        )

        bounds = compute_bounds(items, padding)
        if bounds.isEmpty():
            return False

        # Determine format from extension
        if local_path.lower().endswith(".svg"):
            return export_svg(items, bounds, local_path, options)
        else:
            return export_png(items, bounds, local_path, options)
