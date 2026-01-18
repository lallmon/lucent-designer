# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""CanvasModel artboard and parent/child behaviours."""

from lucent.canvas_items import RectangleItem, ArtboardItem
from test_helpers import (
    make_rectangle,
    make_ellipse,
    make_artboard,
    make_artboard_with_children,
)


class TestCanvasModelArtboards:
    """Tests for artboard functionality."""

    def test_add_artboard(self, canvas_model, qtbot):
        artboard_data = make_artboard(
            x=0, y=0, width=800, height=600, name="Background"
        )

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            canvas_model.addItem(artboard_data)

        assert canvas_model.count() == 1
        items = canvas_model.getItems()
        assert isinstance(items[0], ArtboardItem)
        assert items[0].name == "Background"

    def test_artboard_has_geometry(self, canvas_model):
        """Artboards have position and size."""
        canvas_model.addItem(make_artboard(x=100, y=50, width=400, height=300))

        artboard = canvas_model.getItems()[0]
        assert artboard.x == 100
        assert artboard.y == 50
        assert artboard.width == 400
        assert artboard.height == 300

    def test_artboard_get_bounds(self, canvas_model):
        """Artboard bounds reflect its geometry."""
        canvas_model.addItem(make_artboard(x=10, y=20, width=200, height=150))

        bounds = canvas_model.getBoundingBox(0)
        assert bounds["x"] == 10
        assert bounds["y"] == 20
        assert bounds["width"] == 200
        assert bounds["height"] == 150

    def test_update_artboard_background_color(self, canvas_model):
        """Artboard background color should update through updateItem."""
        canvas_model.addItem(
            make_artboard(x=0, y=0, width=100, height=100, background_color="#ffffff")
        )

        canvas_model.updateItem(0, {"backgroundColor": "#112233"})

        data = canvas_model.getItemData(0)
        assert data["backgroundColor"] == "#112233"

    def test_items_with_parent_artboard(self, canvas_model):
        artboard_and_child = make_artboard_with_children(
            [make_rectangle(name="Rect1")], name="Artboard1", artboard_id="artboard-1"
        )
        for item in artboard_and_child:
            canvas_model.addItem(item)

        items = canvas_model.getItems()
        assert items[1].parent_id == "artboard-1"


class TestCanvasModelEffectivelyLocked:
    """Effective locked semantics with artboard ancestry."""

    def test_is_effectively_locked_item_locked(self, canvas_model):
        canvas_model.addItem(make_rectangle(locked=True))
        assert canvas_model.isEffectivelyLocked(0) is True

    def test_is_effectively_locked_parent_locked(self, canvas_model):
        canvas_model.addItem(make_artboard(artboard_id="artboard-1", locked=True))
        canvas_model.addItem(make_rectangle(parent_id="artboard-1", locked=False))
        assert canvas_model.isEffectivelyLocked(1) is False

    def test_is_effectively_locked_unlocked(self, canvas_model):
        canvas_model.addItem(make_artboard(artboard_id="artboard-1", locked=False))
        canvas_model.addItem(make_rectangle(parent_id="artboard-1", locked=False))
        assert canvas_model.isEffectivelyLocked(1) is False


class TestCanvasModelGetArtboardItems:
    """Tests for getArtboardItems method."""

    def test_get_artboard_items(self, canvas_model):
        artboard_with_children = make_artboard_with_children(
            [make_rectangle(name="A"), make_rectangle(name="B")],
            name="Artboard1",
            artboard_id="artboard-1",
        )
        for item in artboard_with_children:
            canvas_model.addItem(item)
        canvas_model.addItem(make_rectangle(name="C"))

        artboard_items = canvas_model.getArtboardItems("artboard-1")
        assert len(artboard_items) == 2
        names = [i.name for i in artboard_items]
        assert "A" in names
        assert "B" in names


class TestCanvasModelArtboardBounds:
    """Tests for getArtboardBounds method."""

    def test_get_artboard_bounds_uses_artboard_geometry(self, canvas_model):
        """Artboard bounds come from artboard geometry, not children."""
        canvas_model.addItem(
            make_artboard(
                x=0, y=0, width=800, height=600, artboard_id="artboard-1", name="Main"
            )
        )
        # Children extend beyond artboard bounds
        canvas_model.addItem(
            make_rectangle(x=700, y=500, width=200, height=200, parent_id="artboard-1")
        )

        bounds = canvas_model.getArtboardBounds("artboard-1")
        # Should return artboard's own bounds, not union of children
        assert bounds["x"] == 0
        assert bounds["y"] == 0
        assert bounds["width"] == 800
        assert bounds["height"] == 600


class TestCanvasModelReparent:
    """Tests for reparenting items."""

    def test_reparent_item_to_artboard(self, canvas_model):
        canvas_model.addItem(make_artboard(name="Artboard1", artboard_id="artboard-1"))
        canvas_model.addItem(make_rectangle(name="Rect"))

        canvas_model.reparentItem(1, "artboard-1")

        items = canvas_model.getItems()
        rect = [i for i in items if isinstance(i, RectangleItem)][0]
        assert rect.parent_id == "artboard-1"

    def test_reparent_invalid_index(self, canvas_model):
        canvas_model.addItem(make_artboard(artboard_id="artboard-1"))
        canvas_model.reparentItem(999, "artboard-1")


class TestCanvasModelSetParent:
    """Tests for setParent method."""

    def test_set_parent_rectangle(self, canvas_model):
        canvas_model.addItem(make_artboard(name="Parent Artboard"))
        canvas_model.addItem(make_rectangle(x=0, y=0, width=50, height=50))

        artboard = canvas_model.getItems()[0]
        canvas_model.setParent(1, artboard.id)

        rect = canvas_model.getItems()[1]
        assert rect.parent_id == artboard.id

    def test_set_parent_ellipse(self, canvas_model):
        canvas_model.addItem(make_artboard(name="Parent Artboard"))
        canvas_model.addItem(
            make_ellipse(center_x=50, center_y=50, radius_x=30, radius_y=20)
        )

        artboard = canvas_model.getItems()[0]
        canvas_model.setParent(1, artboard.id)

        ellipse = canvas_model.getItems()[1]
        assert ellipse.parent_id == artboard.id

    def test_set_parent_empty_string_removes_parent(self, canvas_model):
        canvas_model.addItem(make_artboard(name="Parent Artboard"))
        artboard = canvas_model.getItems()[0]

        rect_data = make_rectangle(x=0, y=0, width=50, height=50)
        rect_data["parentId"] = artboard.id
        canvas_model.addItem(rect_data)

        canvas_model.setParent(1, "")

        rect = canvas_model.getItems()[1]
        assert rect.parent_id is None

    def test_set_parent_invalid_index(self, canvas_model):
        canvas_model.addItem(make_artboard(name="Artboard"))
        artboard = canvas_model.getItems()[0]
        canvas_model.setParent(-1, artboard.id)
        canvas_model.setParent(999, artboard.id)

    def test_set_parent_artboard_no_op(self, canvas_model):
        """Artboards cannot be nested - setting parent is a no-op."""
        canvas_model.addItem(make_artboard(name="Artboard 1"))
        canvas_model.addItem(make_artboard(name="Artboard 2"))

        artboard1 = canvas_model.getItems()[0]
        canvas_model.setParent(1, artboard1.id)

        artboard2 = canvas_model.getItems()[1]
        assert not hasattr(artboard2, "parent_id") or artboard2.parent_id is None
