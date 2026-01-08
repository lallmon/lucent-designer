"""Tests for DocumentManager class - document state and file operations."""

import json
import pytest
from pathlib import Path

from lucent.document_manager import DocumentManager
from lucent.canvas_model import CanvasModel
from lucent.file_io import LUCENT_VERSION
from test_helpers import make_rectangle


@pytest.fixture
def canvas_model(qapp):
    """Create a fresh CanvasModel for testing."""
    return CanvasModel()


@pytest.fixture
def doc_manager(canvas_model):
    """Create a DocumentManager connected to a CanvasModel."""
    dm = DocumentManager(canvas_model)
    dm.startTracking()
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

        canvas_model.addItem(make_rectangle(width=100, height=100))

        assert doc_manager.dirty is True

    def test_dirty_flag_set_on_item_removed(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel
    ) -> None:
        """Removing item sets dirty=True."""
        canvas_model.addItem(make_rectangle(width=100, height=100))
        doc_manager._dirty = False

        canvas_model.removeItem(0)

        assert doc_manager.dirty is True

    def test_dirty_flag_set_on_item_modified(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel
    ) -> None:
        """Modifying item sets dirty=True."""
        canvas_model.addItem(make_rectangle(width=100, height=100))
        doc_manager._dirty = False

        canvas_model.updateItem(0, make_rectangle(x=50, width=100, height=100))

        assert doc_manager.dirty is True

    def test_dirty_changed_signal_emitted(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel, qtbot
    ) -> None:
        """dirtyChanged signal emitted when dirty state changes."""
        with qtbot.waitSignal(doc_manager.dirtyChanged, timeout=1000):
            canvas_model.addItem(make_rectangle(width=100, height=100))


class TestNewDocument:
    """Tests for creating new documents."""

    def test_new_document_clears_canvas(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel
    ) -> None:
        """newDocument() clears all items from canvas."""
        canvas_model.addItem(make_rectangle())
        assert canvas_model.count() == 1

        doc_manager.newDocument()

        assert canvas_model.count() == 0

    def test_new_document_resets_file_path(self, doc_manager: DocumentManager) -> None:
        """newDocument() clears the file path."""
        doc_manager._filePath = "/some/path.lucent"

        doc_manager.newDocument()

        assert doc_manager.filePath == ""

    def test_new_document_resets_dirty(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel
    ) -> None:
        """newDocument() sets dirty=False."""
        canvas_model.addItem(make_rectangle())
        assert doc_manager.dirty is True

        doc_manager.newDocument()

        assert doc_manager.dirty is False


class TestSaveDocument:
    """Tests for saving documents."""

    def test_save_document_writes_file(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel, tmp_path: Path
    ) -> None:
        """saveDocumentAs() writes JSON file to disk."""
        canvas_model.addItem(make_rectangle(x=10, y=20, width=100, height=50))
        file_path = tmp_path / "test.lucent"

        result = doc_manager.saveDocumentAs(str(file_path))

        assert result is True
        assert file_path.exists()

    def test_save_document_clears_dirty(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel, tmp_path: Path
    ) -> None:
        """saveDocumentAs() clears dirty flag on success."""
        canvas_model.addItem(make_rectangle())
        assert doc_manager.dirty is True
        file_path = tmp_path / "test.lucent"

        doc_manager.saveDocumentAs(str(file_path))

        assert doc_manager.dirty is False

    def test_save_document_updates_file_path(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel, tmp_path: Path
    ) -> None:
        """saveDocumentAs() updates filePath property."""
        canvas_model.addItem(make_rectangle())
        file_path = tmp_path / "myfile.lucent"

        doc_manager.saveDocumentAs(str(file_path))

        assert doc_manager.filePath == str(file_path)

    def test_save_document_file_content(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel, tmp_path: Path
    ) -> None:
        """saveDocumentAs() writes correct JSON structure."""
        canvas_model.addItem(
            make_rectangle(x=10, y=20, width=100, height=50, name="Test Rect")
        )
        file_path = tmp_path / "test.lucent"

        doc_manager.saveDocumentAs(str(file_path))

        with open(file_path, "r") as f:
            data = json.load(f)

        assert "version" in data
        assert "items" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Test Rect"


class TestOpenDocument:
    """Tests for opening documents."""

    def test_open_document_loads_items(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel, tmp_path: Path
    ) -> None:
        """openDocument() loads items from file."""
        file_path = tmp_path / "test.lucent"
        data = {
            "version": LUCENT_VERSION,
            "items": [
                {
                    "type": "rectangle",
                    "geometry": {"x": 10, "y": 20, "width": 100, "height": 50},
                    "appearances": [
                        {
                            "type": "fill",
                            "color": "#ffffff",
                            "opacity": 0.0,
                            "visible": True,
                        },
                        {
                            "type": "stroke",
                            "color": "#ffffff",
                            "width": 1.0,
                            "opacity": 1.0,
                            "visible": True,
                        },
                    ],
                    "name": "Loaded Rect",
                    "visible": True,
                    "locked": False,
                }
            ],
        }
        with open(file_path, "w") as f:
            json.dump(data, f)

        result = doc_manager.openDocument(str(file_path))

        assert result is True
        assert canvas_model.count() == 1
        assert canvas_model.getItems()[0].name == "Loaded Rect"

    def test_open_document_updates_file_path(
        self, doc_manager: DocumentManager, tmp_path: Path
    ) -> None:
        """openDocument() updates filePath property."""
        file_path = tmp_path / "test.lucent"
        data = {"version": LUCENT_VERSION, "items": []}
        with open(file_path, "w") as f:
            json.dump(data, f)

        doc_manager.openDocument(str(file_path))

        assert doc_manager.filePath == str(file_path)

    def test_open_document_clears_dirty(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel, tmp_path: Path
    ) -> None:
        """openDocument() clears dirty flag."""
        canvas_model.addItem(make_rectangle())
        assert doc_manager.dirty is True

        file_path = tmp_path / "test.lucent"
        data = {"version": LUCENT_VERSION, "items": []}
        with open(file_path, "w") as f:
            json.dump(data, f)

        doc_manager.openDocument(str(file_path))

        assert doc_manager.dirty is False

    def test_open_nonexistent_file_returns_false(
        self, doc_manager: DocumentManager
    ) -> None:
        """openDocument() returns False for missing file."""
        result = doc_manager.openDocument("/nonexistent/path.lucent")
        assert result is False


class TestDocumentTitle:
    """Tests for document title property."""

    def test_title_is_filename_when_saved(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel, tmp_path: Path
    ) -> None:
        """documentTitle is filename stem after save."""
        canvas_model.addItem(make_rectangle())
        file_path = tmp_path / "mydesign.lucent"

        doc_manager.saveDocumentAs(str(file_path))

        assert doc_manager.documentTitle == "mydesign"

    def test_title_changes_after_save_as(
        self, doc_manager: DocumentManager, canvas_model: CanvasModel, tmp_path: Path
    ) -> None:
        """documentTitle updates on save to new location."""
        canvas_model.addItem(make_rectangle())
        first_path = tmp_path / "first.lucent"
        second_path = tmp_path / "second.lucent"

        doc_manager.saveDocumentAs(str(first_path))
        assert doc_manager.documentTitle == "first"

        doc_manager.saveDocumentAs(str(second_path))
        assert doc_manager.documentTitle == "second"
