"""Tests for DocumentManager class - document state and file operations.

Written first following TDD Red/Green methodology.
"""

import json
import pytest
from pathlib import Path

from lucent.document_manager import DocumentManager
from lucent.canvas_model import CanvasModel
from lucent.file_io import LUCENT_VERSION


@pytest.fixture
def canvas_model(qapp):
    """Create a fresh CanvasModel for testing."""
    return CanvasModel()


@pytest.fixture
def doc_manager(canvas_model):
    """Create a DocumentManager connected to a CanvasModel."""
    dm = DocumentManager(canvas_model)
    dm.startTracking()  # Enable dirty tracking as app would do on startup
    return dm


class TestInitialState:
    """Tests for initial DocumentManager state."""

    def test_new_document_is_not_dirty(self, doc_manager: DocumentManager) -> None:
        """Fresh DocumentManager has dirty=False."""
        assert doc_manager.dirty is False

    def test_document_title_is_untitled_for_new(
        self, doc_manager: DocumentManager
    ) -> None:
        """New document title is 'Untitled'."""
        assert doc_manager.documentTitle == "Untitled"

    def test_file_path_is_empty_for_new(self, doc_manager: DocumentManager) -> None:
        """New document has empty filePath."""
        assert doc_manager.filePath == ""

    def test_has_unsaved_changes_reflects_dirty_state(
        self, doc_manager: DocumentManager
    ) -> None:
        """hasUnsavedChanges() matches dirty property."""
        assert doc_manager.hasUnsavedChanges() is False
        doc_manager._dirty = True
        assert doc_manager.hasUnsavedChanges() is True


class TestDirtyTracking:
    """Tests for dirty flag behavior."""

    def test_dirty_flag_set_on_item_added(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel
    ) -> None:
        """Adding item sets dirty=True."""
        assert doc_manager.dirty is False

        canvas_model.addItem(
            {
                "type": "rectangle",
                "x": 0,
                "y": 0,
                "width": 100,
                "height": 100,
            }
        )

        assert doc_manager.dirty is True

    def test_dirty_flag_set_on_item_removed(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel
    ) -> None:
        """Removing item sets dirty=True."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )
        doc_manager._dirty = False  # Reset after add

        canvas_model.removeItem(0)

        assert doc_manager.dirty is True

    def test_dirty_flag_set_on_item_modified(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel
    ) -> None:
        """Modifying item sets dirty=True."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )
        doc_manager._dirty = False  # Reset after add

        canvas_model.updateItem(0, {"x": 50})

        assert doc_manager.dirty is True

    def test_dirty_flag_set_on_clear(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel
    ) -> None:
        """Clearing canvas sets dirty=True."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )
        doc_manager._dirty = False  # Reset after add

        canvas_model.clear()

        assert doc_manager.dirty is True

    def test_dirty_flag_cleared_after_save(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel, tmp_path: Path
    ) -> None:
        """Successful save sets dirty=False."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )
        assert doc_manager.dirty is True

        file_path = tmp_path / "test.lucent"
        doc_manager.saveDocumentAs(str(file_path))

        assert doc_manager.dirty is False


class TestSaveOperations:
    """Tests for save functionality."""

    def test_save_document_without_path_returns_false(
        self, doc_manager: DocumentManager
    ) -> None:
        """saveDocument() returns False if no filePath set."""
        result = doc_manager.saveDocument()
        assert result is False

    def test_save_document_as_creates_file(
        self, doc_manager: DocumentManager, tmp_path: Path
    ) -> None:
        """saveDocumentAs creates file at specified path."""
        file_path = tmp_path / "saved.lucent"

        result = doc_manager.saveDocumentAs(str(file_path))

        assert result is True
        assert file_path.exists()

    def test_save_document_as_sets_file_path(
        self, doc_manager: DocumentManager, tmp_path: Path
    ) -> None:
        """saveDocumentAs updates filePath property."""
        file_path = tmp_path / "saved.lucent"

        doc_manager.saveDocumentAs(str(file_path))

        assert doc_manager.filePath == str(file_path)

    def test_save_document_uses_current_path(
        self, doc_manager: DocumentManager, tmp_path: Path
    ) -> None:
        """saveDocument() saves to current filePath."""
        file_path = tmp_path / "existing.lucent"
        doc_manager.saveDocumentAs(str(file_path))

        # Modify and save again
        doc_manager._canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 50, "height": 50}
        )

        result = doc_manager.saveDocument()

        assert result is True
        # Verify file was updated
        data = json.loads(file_path.read_text())
        assert len(data["items"]) == 1

    def test_save_document_includes_all_items(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel, tmp_path: Path
    ) -> None:
        """Saved file contains all canvas items."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 10, "y": 20, "width": 100, "height": 50}
        )
        canvas_model.addItem(
            {
                "type": "ellipse",
                "centerX": 100,
                "centerY": 100,
                "radiusX": 30,
                "radiusY": 20,
            }
        )

        file_path = tmp_path / "items.lucent"
        doc_manager.saveDocumentAs(str(file_path))

        data = json.loads(file_path.read_text())
        assert len(data["items"]) == 2


class TestOpenOperations:
    """Tests for open/load functionality."""

    def test_open_document_loads_items(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel, tmp_path: Path
    ) -> None:
        """Opening file populates canvas model."""
        file_path = tmp_path / "load_test.lucent"
        data = {
            "version": LUCENT_VERSION,
            "meta": {"name": "Test Doc"},
            "viewport": {"zoomLevel": 1.0, "offsetX": 0, "offsetY": 0},
            "items": [
                {
                    "type": "rectangle",
                    "name": "Rect 1",
                    "x": 100,
                    "y": 200,
                    "width": 50,
                    "height": 50,
                    "strokeWidth": 1,
                    "strokeColor": "#ffffff",
                    "strokeOpacity": 1.0,
                    "fillColor": "#ffffff",
                    "fillOpacity": 0.0,
                    "parentId": None,
                    "visible": True,
                    "locked": False,
                }
            ],
        }
        file_path.write_text(json.dumps(data))

        result = doc_manager.openDocument(str(file_path))

        assert result is True
        assert canvas_model.count() == 1

    def test_open_document_clears_dirty_flag(
        self, doc_manager: DocumentManager, tmp_path: Path
    ) -> None:
        """Opening file sets dirty=False."""
        file_path = tmp_path / "open_test.lucent"
        data = {
            "version": LUCENT_VERSION,
            "meta": {"name": "Test"},
            "viewport": {"zoomLevel": 1.0, "offsetX": 0, "offsetY": 0},
            "items": [],
        }
        file_path.write_text(json.dumps(data))

        doc_manager.openDocument(str(file_path))

        assert doc_manager.dirty is False

    def test_open_document_sets_file_path(
        self, doc_manager: DocumentManager, tmp_path: Path
    ) -> None:
        """Opening file updates filePath property."""
        file_path = tmp_path / "path_test.lucent"
        data = {
            "version": LUCENT_VERSION,
            "meta": {"name": "Test"},
            "viewport": {"zoomLevel": 1.0, "offsetX": 0, "offsetY": 0},
            "items": [],
        }
        file_path.write_text(json.dumps(data))

        doc_manager.openDocument(str(file_path))

        assert doc_manager.filePath == str(file_path)

    def test_open_document_returns_false_on_missing_file(
        self, doc_manager: DocumentManager, tmp_path: Path
    ) -> None:
        """Opening non-existent file returns False."""
        file_path = tmp_path / "nonexistent.lucent"

        result = doc_manager.openDocument(str(file_path))

        assert result is False

    def test_open_document_clears_existing_items(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel, tmp_path: Path
    ) -> None:
        """Opening file clears existing canvas items."""
        # Add some items first
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )
        assert canvas_model.count() == 1

        # Open empty document
        file_path = tmp_path / "empty.lucent"
        data = {
            "version": LUCENT_VERSION,
            "meta": {"name": "Empty"},
            "viewport": {"zoomLevel": 1.0, "offsetX": 0, "offsetY": 0},
            "items": [],
        }
        file_path.write_text(json.dumps(data))

        doc_manager.openDocument(str(file_path))

        assert canvas_model.count() == 0


class TestDocumentTitle:
    """Tests for document title behavior."""

    def test_document_title_is_filename_after_save(
        self, doc_manager: DocumentManager, tmp_path: Path
    ) -> None:
        """After save, title is filename without extension."""
        file_path = tmp_path / "my_artwork.lucent"

        doc_manager.saveDocumentAs(str(file_path))

        assert doc_manager.documentTitle == "my_artwork"

    def test_document_title_is_filename_after_open(
        self, doc_manager: DocumentManager, tmp_path: Path
    ) -> None:
        """After open, title is filename without extension."""
        file_path = tmp_path / "loaded_doc.lucent"
        data = {
            "version": LUCENT_VERSION,
            "meta": {"name": "Test"},
            "viewport": {"zoomLevel": 1.0, "offsetX": 0, "offsetY": 0},
            "items": [],
        }
        file_path.write_text(json.dumps(data))

        doc_manager.openDocument(str(file_path))

        assert doc_manager.documentTitle == "loaded_doc"

    def test_document_title_resets_on_new(
        self, doc_manager: DocumentManager, tmp_path: Path
    ) -> None:
        """New document resets title to 'Untitled'."""
        # Save first to set a title
        file_path = tmp_path / "saved.lucent"
        doc_manager.saveDocumentAs(str(file_path))
        assert doc_manager.documentTitle == "saved"

        doc_manager.newDocument()

        assert doc_manager.documentTitle == "Untitled"


class TestNewDocument:
    """Tests for new document functionality."""

    def test_new_document_clears_canvas(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel
    ) -> None:
        """newDocument() clears all items."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )
        assert canvas_model.count() == 1

        doc_manager.newDocument()

        assert canvas_model.count() == 0

    def test_new_document_clears_file_path(
        self, doc_manager: DocumentManager, tmp_path: Path
    ) -> None:
        """newDocument() clears filePath."""
        file_path = tmp_path / "test.lucent"
        doc_manager.saveDocumentAs(str(file_path))
        assert doc_manager.filePath != ""

        doc_manager.newDocument()

        assert doc_manager.filePath == ""

    def test_new_document_clears_dirty_flag(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel
    ) -> None:
        """newDocument() sets dirty=False."""
        canvas_model.addItem(
            {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 100}
        )
        assert doc_manager.dirty is True

        doc_manager.newDocument()

        assert doc_manager.dirty is False

    def test_new_document_returns_true(self, doc_manager: DocumentManager) -> None:
        """newDocument() returns True."""
        result = doc_manager.newDocument()
        assert result is True


class TestViewportState:
    """Tests for viewport state persistence."""

    def test_get_viewport_returns_current_state(
        self, doc_manager: DocumentManager
    ) -> None:
        """getViewport() returns current viewport dictionary."""
        # Set viewport via the setter
        doc_manager.setViewport(2.0, 100.5, -50.25)

        viewport = doc_manager.getViewport()

        assert viewport["zoomLevel"] == 2.0
        assert viewport["offsetX"] == 100.5
        assert viewport["offsetY"] == -50.25

    def test_saved_document_includes_viewport(
        self, doc_manager: DocumentManager, tmp_path: Path
    ) -> None:
        """Saved file includes viewport state."""
        doc_manager.setViewport(3.0, 200, 150)

        file_path = tmp_path / "viewport.lucent"
        doc_manager.saveDocumentAs(str(file_path))

        data = json.loads(file_path.read_text())
        assert data["viewport"]["zoomLevel"] == 3.0
        assert data["viewport"]["offsetX"] == 200
        assert data["viewport"]["offsetY"] == 150
