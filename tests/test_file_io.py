"""Tests for file_io module - save/load functionality for .lucent files.

Written first following TDD Red/Green methodology.
"""

import json
import pytest
from pathlib import Path

from lucent.file_io import (
    LUCENT_VERSION,
    save_document,
    load_document,
    FileVersionError,
)


class TestSaveDocument:
    """Tests for save_document function."""

    def test_save_empty_document_creates_valid_json(self, tmp_path: Path) -> None:
        """Save with no items, verify JSON structure."""
        file_path = tmp_path / "empty.lucent"

        save_document(
            path=file_path,
            items=[],
            viewport={"zoomLevel": 1.0, "offsetX": 0, "offsetY": 0},
            meta={"name": "Untitled"},
        )

        assert file_path.exists()
        data = json.loads(file_path.read_text())
        assert "version" in data
        assert "items" in data
        assert "viewport" in data
        assert "meta" in data
        assert data["items"] == []

    def test_save_includes_version_number(self, tmp_path: Path) -> None:
        """Saved file contains version field set to LUCENT_VERSION."""
        file_path = tmp_path / "versioned.lucent"

        save_document(
            path=file_path,
            items=[],
            viewport={"zoomLevel": 1.0, "offsetX": 0, "offsetY": 0},
            meta={"name": "Test"},
        )

        data = json.loads(file_path.read_text())
        assert data["version"] == LUCENT_VERSION

    def test_save_document_with_items(self, tmp_path: Path) -> None:
        """Save document with items, verify they are serialized."""
        file_path = tmp_path / "with_items.lucent"
        items = [
            {
                "type": "rectangle",
                "name": "Rect 1",
                "x": 100,
                "y": 200,
                "width": 50,
                "height": 50,
                "strokeWidth": 1,
                "strokeColor": "#ff0000",
                "strokeOpacity": 1.0,
                "fillColor": "#00ff00",
                "fillOpacity": 0.5,
                "parentId": None,
                "visible": True,
                "locked": False,
            }
        ]

        save_document(
            path=file_path,
            items=items,
            viewport={"zoomLevel": 2.0, "offsetX": 100, "offsetY": 50},
            meta={"name": "My Drawing"},
        )

        data = json.loads(file_path.read_text())
        assert len(data["items"]) == 1
        assert data["items"][0]["type"] == "rectangle"
        assert data["items"][0]["name"] == "Rect 1"
        assert data["items"][0]["x"] == 100

    def test_save_preserves_viewport_state(self, tmp_path: Path) -> None:
        """Viewport zoom/offset is saved correctly."""
        file_path = tmp_path / "viewport.lucent"
        viewport = {"zoomLevel": 2.5, "offsetX": 123.5, "offsetY": -456.7}

        save_document(
            path=file_path,
            items=[],
            viewport=viewport,
            meta={"name": "Test"},
        )

        data = json.loads(file_path.read_text())
        assert data["viewport"]["zoomLevel"] == 2.5
        assert data["viewport"]["offsetX"] == 123.5
        assert data["viewport"]["offsetY"] == -456.7

    def test_save_preserves_document_metadata(self, tmp_path: Path) -> None:
        """Meta name/timestamps are saved correctly."""
        file_path = tmp_path / "meta.lucent"
        meta = {
            "name": "My Artwork",
            "created": "2026-01-05T12:00:00Z",
            "modified": "2026-01-05T14:30:00Z",
        }

        save_document(
            path=file_path,
            items=[],
            viewport={"zoomLevel": 1.0, "offsetX": 0, "offsetY": 0},
            meta=meta,
        )

        data = json.loads(file_path.read_text())
        assert data["meta"]["name"] == "My Artwork"
        assert data["meta"]["created"] == "2026-01-05T12:00:00Z"
        assert data["meta"]["modified"] == "2026-01-05T14:30:00Z"

    def test_save_accepts_path_as_string(self, tmp_path: Path) -> None:
        """save_document accepts path as string, not just Path object."""
        file_path = str(tmp_path / "string_path.lucent")

        save_document(
            path=file_path,
            items=[],
            viewport={"zoomLevel": 1.0, "offsetX": 0, "offsetY": 0},
            meta={"name": "Test"},
        )

        assert Path(file_path).exists()


class TestLoadDocument:
    """Tests for load_document function."""

    def test_load_nonexistent_file_raises_error(self, tmp_path: Path) -> None:
        """FileNotFoundError on missing file."""
        file_path = tmp_path / "nonexistent.lucent"

        with pytest.raises(FileNotFoundError):
            load_document(file_path)

    def test_load_invalid_json_raises_error(self, tmp_path: Path) -> None:
        """ValueError on malformed JSON."""
        file_path = tmp_path / "invalid.lucent"
        file_path.write_text("{ not valid json }")

        with pytest.raises(ValueError, match="Invalid JSON"):
            load_document(file_path)

    def test_load_future_version_raises_error(self, tmp_path: Path) -> None:
        """FileVersionError when file version > LUCENT_VERSION."""
        file_path = tmp_path / "future.lucent"
        future_data = {
            "version": LUCENT_VERSION + 100,
            "meta": {"name": "Future File"},
            "viewport": {"zoomLevel": 1.0, "offsetX": 0, "offsetY": 0},
            "items": [],
        }
        file_path.write_text(json.dumps(future_data))

        with pytest.raises(FileVersionError):
            load_document(file_path)

    def test_load_missing_version_raises_error(self, tmp_path: Path) -> None:
        """ValueError when file has no version field."""
        file_path = tmp_path / "no_version.lucent"
        data = {
            "meta": {"name": "No Version"},
            "viewport": {"zoomLevel": 1.0, "offsetX": 0, "offsetY": 0},
            "items": [],
        }
        file_path.write_text(json.dumps(data))

        with pytest.raises(ValueError, match="[Mm]issing.*version"):
            load_document(file_path)

    def test_load_returns_document_structure(self, tmp_path: Path) -> None:
        """Loaded document contains items, viewport, and meta."""
        file_path = tmp_path / "valid.lucent"
        data = {
            "version": LUCENT_VERSION,
            "meta": {"name": "Test Doc"},
            "viewport": {"zoomLevel": 1.5, "offsetX": 10, "offsetY": 20},
            "items": [
                {
                    "type": "rectangle",
                    "name": "Rect",
                    "x": 0,
                    "y": 0,
                    "width": 100,
                    "height": 100,
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

        result = load_document(file_path)

        assert "items" in result
        assert "viewport" in result
        assert "meta" in result
        assert len(result["items"]) == 1

    def test_load_accepts_path_as_string(self, tmp_path: Path) -> None:
        """load_document accepts path as string."""
        file_path = tmp_path / "string_path.lucent"
        data = {
            "version": LUCENT_VERSION,
            "meta": {"name": "Test"},
            "viewport": {"zoomLevel": 1.0, "offsetX": 0, "offsetY": 0},
            "items": [],
        }
        file_path.write_text(json.dumps(data))

        result = load_document(str(file_path))

        assert result["meta"]["name"] == "Test"


class TestDocumentDPI:
    """Tests for documentDPI field in file format."""

    def test_save_includes_document_dpi(self, tmp_path: Path) -> None:
        """Saved file includes documentDPI in meta."""
        file_path = tmp_path / "with_dpi.lucent"

        save_document(
            path=file_path,
            items=[],
            viewport={"zoomLevel": 1.0, "offsetX": 0, "offsetY": 0},
            meta={"name": "Test", "documentDPI": 144},
        )

        data = json.loads(file_path.read_text())
        assert data["meta"]["documentDPI"] == 144

    def test_load_returns_document_dpi(self, tmp_path: Path) -> None:
        """load_document returns documentDPI from meta."""
        file_path = tmp_path / "with_dpi.lucent"
        data = {
            "version": LUCENT_VERSION,
            "meta": {"name": "Test", "documentDPI": 300},
            "viewport": {"zoomLevel": 1.0, "offsetX": 0, "offsetY": 0},
            "items": [],
        }
        file_path.write_text(json.dumps(data))

        result = load_document(file_path)

        assert result["meta"]["documentDPI"] == 300

    def test_load_defaults_dpi_to_72_if_missing(self, tmp_path: Path) -> None:
        """load_document returns 72 DPI when documentDPI is missing."""
        file_path = tmp_path / "no_dpi.lucent"
        data = {
            "version": LUCENT_VERSION,
            "meta": {"name": "Test"},
            "viewport": {"zoomLevel": 1.0, "offsetX": 0, "offsetY": 0},
            "items": [],
        }
        file_path.write_text(json.dumps(data))

        result = load_document(file_path)

        assert result["meta"]["documentDPI"] == 72


class TestRoundTrip:
    """Tests for save/load round-trip integrity."""

    def test_save_load_roundtrip_preserves_items(self, tmp_path: Path) -> None:
        """Save items, reload, verify all properties match."""
        file_path = tmp_path / "roundtrip.lucent"
        original_items = [
            {
                "type": "rectangle",
                "name": "Rect 1",
                "x": 100.5,
                "y": 200.5,
                "width": 50,
                "height": 75,
                "strokeWidth": 2.5,
                "strokeColor": "#ff0000",
                "strokeOpacity": 0.8,
                "fillColor": "#00ff00",
                "fillOpacity": 0.5,
                "parentId": None,
                "visible": True,
                "locked": False,
            },
            {
                "type": "ellipse",
                "name": "Circle 1",
                "centerX": 300,
                "centerY": 400,
                "radiusX": 50,
                "radiusY": 50,
                "strokeWidth": 1,
                "strokeColor": "#0000ff",
                "strokeOpacity": 1.0,
                "fillColor": "#ffff00",
                "fillOpacity": 0.3,
                "parentId": None,
                "visible": True,
                "locked": True,
            },
        ]

        save_document(
            path=file_path,
            items=original_items,
            viewport={"zoomLevel": 1.0, "offsetX": 0, "offsetY": 0},
            meta={"name": "Test"},
        )

        result = load_document(file_path)

        assert len(result["items"]) == 2
        # Check rectangle
        rect = result["items"][0]
        assert rect["type"] == "rectangle"
        assert rect["name"] == "Rect 1"
        assert rect["x"] == 100.5
        assert rect["y"] == 200.5
        assert rect["width"] == 50
        assert rect["height"] == 75
        assert rect["strokeWidth"] == 2.5
        assert rect["strokeColor"] == "#ff0000"
        assert rect["strokeOpacity"] == 0.8
        assert rect["fillOpacity"] == 0.5
        assert rect["locked"] is False

        # Check ellipse
        ellipse = result["items"][1]
        assert ellipse["type"] == "ellipse"
        assert ellipse["name"] == "Circle 1"
        assert ellipse["centerX"] == 300
        assert ellipse["centerY"] == 400
        assert ellipse["locked"] is True

    def test_save_load_roundtrip_preserves_viewport(self, tmp_path: Path) -> None:
        """Viewport state round-trips correctly."""
        file_path = tmp_path / "viewport_rt.lucent"
        original_viewport = {"zoomLevel": 3.5, "offsetX": -100.5, "offsetY": 250.75}

        save_document(
            path=file_path,
            items=[],
            viewport=original_viewport,
            meta={"name": "Test"},
        )

        result = load_document(file_path)

        assert result["viewport"]["zoomLevel"] == 3.5
        assert result["viewport"]["offsetX"] == -100.5
        assert result["viewport"]["offsetY"] == 250.75

    def test_save_load_roundtrip_preserves_metadata(self, tmp_path: Path) -> None:
        """Meta name/timestamps round-trip correctly."""
        file_path = tmp_path / "meta_rt.lucent"
        original_meta = {
            "name": "My Project",
            "created": "2026-01-01T00:00:00Z",
            "modified": "2026-01-05T12:34:56Z",
        }

        save_document(
            path=file_path,
            items=[],
            viewport={"zoomLevel": 1.0, "offsetX": 0, "offsetY": 0},
            meta=original_meta,
        )

        result = load_document(file_path)

        assert result["meta"]["name"] == "My Project"
        assert result["meta"]["created"] == "2026-01-01T00:00:00Z"
        assert result["meta"]["modified"] == "2026-01-05T12:34:56Z"

    def test_save_load_roundtrip_all_item_types(self, tmp_path: Path) -> None:
        """All item types (rectangle, ellipse, layer, group, path, text) round-trip."""
        file_path = tmp_path / "all_types.lucent"
        original_items = [
            {
                "type": "layer",
                "id": "layer-1",
                "name": "Background",
                "visible": True,
                "locked": False,
            },
            {
                "type": "rectangle",
                "name": "Rect",
                "x": 0,
                "y": 0,
                "width": 100,
                "height": 100,
                "strokeWidth": 1,
                "strokeColor": "#ffffff",
                "strokeOpacity": 1.0,
                "fillColor": "#ffffff",
                "fillOpacity": 0.0,
                "parentId": "layer-1",
                "visible": True,
                "locked": False,
            },
            {
                "type": "ellipse",
                "name": "Ellipse",
                "centerX": 50,
                "centerY": 50,
                "radiusX": 25,
                "radiusY": 25,
                "strokeWidth": 1,
                "strokeColor": "#ffffff",
                "strokeOpacity": 1.0,
                "fillColor": "#ffffff",
                "fillOpacity": 0.0,
                "parentId": "layer-1",
                "visible": True,
                "locked": False,
            },
            {
                "type": "group",
                "id": "group-1",
                "name": "My Group",
                "parentId": "layer-1",
                "visible": True,
                "locked": False,
            },
            {
                "type": "path",
                "name": "Path",
                "points": [{"x": 0, "y": 0}, {"x": 100, "y": 100}],
                "strokeWidth": 2,
                "strokeColor": "#ff0000",
                "strokeOpacity": 1.0,
                "fillColor": "#ffffff",
                "fillOpacity": 0.0,
                "closed": False,
                "parentId": None,
                "visible": True,
                "locked": False,
            },
            {
                "type": "text",
                "name": "Label",
                "x": 200,
                "y": 200,
                "width": 100,
                "height": 0,
                "text": "Hello World",
                "fontFamily": "Arial",
                "fontSize": 16,
                "textColor": "#000000",
                "textOpacity": 1.0,
                "parentId": None,
                "visible": True,
                "locked": False,
            },
        ]

        save_document(
            path=file_path,
            items=original_items,
            viewport={"zoomLevel": 1.0, "offsetX": 0, "offsetY": 0},
            meta={"name": "All Types"},
        )

        result = load_document(file_path)

        assert len(result["items"]) == 6
        types = [item["type"] for item in result["items"]]
        assert "layer" in types
        assert "rectangle" in types
        assert "ellipse" in types
        assert "group" in types
        assert "path" in types
        assert "text" in types

        # Verify text content
        text_item = next(i for i in result["items"] if i["type"] == "text")
        assert text_item["text"] == "Hello World"
        assert text_item["fontFamily"] == "Arial"

        # Verify path points
        path_item = next(i for i in result["items"] if i["type"] == "path")
        assert len(path_item["points"]) == 2
