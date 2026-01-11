# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

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
from test_helpers import (
    make_rectangle,
    make_ellipse,
    make_path,
    make_layer,
    make_group,
    make_text,
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
            make_rectangle(
                x=100,
                y=200,
                width=50,
                height=50,
                stroke_color="#ff0000",
                fill_color="#00ff00",
                fill_opacity=0.5,
                name="Rect 1",
            )
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
        assert data["items"][0]["geometry"]["x"] == 100

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
            "items": [make_rectangle(x=0, y=0, width=100, height=100, name="Rect")],
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
            make_rectangle(
                x=100.5,
                y=200.5,
                width=50,
                height=75,
                stroke_width=2.5,
                stroke_color="#ff0000",
                stroke_opacity=0.8,
                fill_color="#00ff00",
                fill_opacity=0.5,
                name="Rect 1",
            ),
            make_ellipse(
                center_x=300,
                center_y=400,
                radius_x=50,
                radius_y=50,
                stroke_color="#0000ff",
                fill_color="#ffff00",
                fill_opacity=0.3,
                name="Circle 1",
                locked=True,
            ),
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
        assert rect["geometry"]["x"] == 100.5
        assert rect["geometry"]["y"] == 200.5
        assert rect["geometry"]["width"] == 50
        assert rect["geometry"]["height"] == 75
        stroke = next(a for a in rect["appearances"] if a["type"] == "stroke")
        fill = next(a for a in rect["appearances"] if a["type"] == "fill")
        assert stroke["width"] == 2.5
        assert stroke["color"] == "#ff0000"
        assert stroke["opacity"] == 0.8
        assert fill["opacity"] == 0.5
        assert rect["locked"] is False

        # Check ellipse
        ellipse = result["items"][1]
        assert ellipse["type"] == "ellipse"
        assert ellipse["name"] == "Circle 1"
        assert ellipse["geometry"]["centerX"] == 300
        assert ellipse["geometry"]["centerY"] == 400
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
            make_layer(name="Background", layer_id="layer-1"),
            make_rectangle(
                x=0, y=0, width=100, height=100, name="Rect", parent_id="layer-1"
            ),
            make_ellipse(
                center_x=50,
                center_y=50,
                radius_x=25,
                radius_y=25,
                name="Ellipse",
                parent_id="layer-1",
            ),
            make_group(name="My Group", group_id="group-1", parent_id="layer-1"),
            make_path(
                points=[{"x": 0, "y": 0}, {"x": 100, "y": 100}],
                stroke_width=2,
                stroke_color="#ff0000",
                name="Path",
            ),
            make_text(
                x=200,
                y=200,
                text="Hello World",
                font_family="Arial",
                font_size=16,
                text_color="#000000",
                name="Label",
            ),
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
        assert len(path_item["geometry"]["points"]) == 2
