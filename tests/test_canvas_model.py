"""Unit tests for canvas_model module."""

from lucent.canvas_items import (
    RectangleItem,
    EllipseItem,
    LayerItem,
    PathItem,
    TextItem,
)
from lucent.commands import DEFAULT_DUPLICATE_OFFSET
from test_helpers import (
    make_rectangle,
    make_ellipse,
    make_path,
    make_layer,
    make_text,
)


class TestCanvasModelBasics:
    """Tests for basic CanvasModel operations."""

    def test_initial_state_empty(self, canvas_model):
        """Test that a new CanvasModel starts empty."""
        assert canvas_model.count() == 0
        assert canvas_model.getItems() == []

    def test_add_rectangle_item(self, canvas_model, qtbot):
        """Test adding a rectangle item to the model."""
        item_data = make_rectangle(
            x=10, y=20, width=100, height=50, stroke_color="#ff0000"
        )

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000) as blocker:
            canvas_model.addItem(item_data)

        assert canvas_model.count() == 1
        assert blocker.args == [0]

        items = canvas_model.getItems()
        assert len(items) == 1
        assert isinstance(items[0], RectangleItem)
        assert items[0].geometry.x == 10
        assert items[0].geometry.y == 20

    def test_add_ellipse_item(self, canvas_model, qtbot):
        """Test adding an ellipse item to the model."""
        item_data = make_ellipse(center_x=50, center_y=75, radius_x=30, radius_y=20)

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000) as blocker:
            canvas_model.addItem(item_data)

        assert canvas_model.count() == 1
        assert blocker.args == [0]

        items = canvas_model.getItems()
        assert len(items) == 1
        assert isinstance(items[0], EllipseItem)
        assert items[0].geometry.center_x == 50
        assert items[0].geometry.center_y == 75

    def test_add_multiple_items(self, canvas_model, qtbot):
        """Test adding multiple items maintains correct order."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=10, height=10))
        canvas_model.addItem(
            make_ellipse(center_x=20, center_y=20, radius_x=5, radius_y=5)
        )

        assert canvas_model.count() == 2
        items = canvas_model.getItems()
        assert isinstance(items[0], RectangleItem)
        assert isinstance(items[1], EllipseItem)

    def test_add_path_item(self, canvas_model, qtbot):
        """Test adding a path item to the model."""
        item_data = make_path(
            points=[{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}],
            closed=True,
            stroke_width=1.5,
        )

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            canvas_model.addItem(item_data)

        assert canvas_model.count() == 1
        items = canvas_model.getItems()
        assert isinstance(items[0], PathItem)
        assert items[0].geometry.closed is True

    def test_add_unknown_item_type_ignored(self, canvas_model, qtbot):
        """Test that adding an unknown item type is safely ignored."""
        item_data = {"type": "triangle", "x": 0, "y": 0}
        canvas_model.addItem(item_data)
        assert canvas_model.count() == 0

    def test_data_invalid_index_returns_none(self, canvas_model):
        """Test that data() returns None for invalid index."""
        canvas_model.addItem(make_rectangle())
        index = canvas_model.index(999, 0)
        assert canvas_model.data(index, canvas_model.NameRole) is None


class TestCanvasModelRemove:
    """Tests for removing items from CanvasModel."""

    def test_remove_item(self, canvas_model, qtbot):
        """Test removing an item by index."""
        canvas_model.addItem(make_rectangle(name="Rect1"))
        canvas_model.addItem(make_ellipse(name="Ellipse1"))

        with qtbot.waitSignal(canvas_model.itemRemoved, timeout=1000) as blocker:
            canvas_model.removeItem(0)

        assert canvas_model.count() == 1
        assert blocker.args == [0]
        assert canvas_model.getItems()[0].name == "Ellipse1"

    def test_remove_invalid_index_no_op(self, canvas_model):
        """Test that removing invalid index does nothing."""
        canvas_model.addItem(make_rectangle())
        canvas_model.removeItem(999)
        assert canvas_model.count() == 1


class TestCanvasModelUpdate:
    """Tests for updating items in CanvasModel."""

    def test_update_item(self, canvas_model, qtbot):
        """Test updating an item's properties."""
        canvas_model.addItem(
            make_rectangle(x=0, y=0, width=10, height=10, name="Original")
        )

        new_data = make_rectangle(x=50, y=50, width=20, height=20, name="Updated")

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.updateItem(0, new_data)

        item = canvas_model.getItems()[0]
        assert item.geometry.x == 50
        assert item.name == "Updated"


class TestCanvasModelDataRoles:
    """Tests for data roles in CanvasModel."""

    def test_name_role(self, canvas_model):
        """Test NameRole returns correct name."""
        canvas_model.addItem(make_rectangle(name="MyRect"))
        index = canvas_model.index(0, 0)
        assert canvas_model.data(index, canvas_model.NameRole) == "MyRect"

    def test_type_role(self, canvas_model):
        """Test TypeRole returns correct type."""
        canvas_model.addItem(make_rectangle())
        index = canvas_model.index(0, 0)
        assert canvas_model.data(index, canvas_model.TypeRole) == "rectangle"

    def test_visible_role(self, canvas_model):
        """Test VisibleRole returns correct visibility."""
        canvas_model.addItem(make_rectangle(visible=False))
        index = canvas_model.index(0, 0)
        assert canvas_model.data(index, canvas_model.VisibleRole) is False

    def test_locked_role(self, canvas_model):
        """Test LockedRole returns correct locked state."""
        canvas_model.addItem(make_rectangle(locked=True))
        index = canvas_model.index(0, 0)
        assert canvas_model.data(index, canvas_model.LockedRole) is True


class TestCanvasModelBoundingBox:
    """Tests for bounding box calculations."""

    def test_rectangle_bounding_box(self, canvas_model):
        """Test bounding box for rectangle."""
        canvas_model.addItem(make_rectangle(x=10, y=20, width=100, height=50))
        bbox = canvas_model.getBoundingBox(0)
        assert bbox == {"x": 10.0, "y": 20.0, "width": 100.0, "height": 50.0}

    def test_ellipse_bounding_box(self, canvas_model):
        """Test bounding box for ellipse."""
        canvas_model.addItem(
            make_ellipse(center_x=100, center_y=100, radius_x=50, radius_y=30)
        )
        bbox = canvas_model.getBoundingBox(0)
        assert bbox == {"x": 50.0, "y": 70.0, "width": 100.0, "height": 60.0}

    def test_path_bounding_box(self, canvas_model):
        """Test bounding box for path."""
        canvas_model.addItem(
            make_path(points=[{"x": -2, "y": 3}, {"x": 4, "y": 5}, {"x": 1, "y": -1}])
        )
        bbox = canvas_model.getBoundingBox(0)
        assert bbox == {"x": -2.0, "y": -1.0, "width": 6.0, "height": 6.0}


class TestCanvasModelLayers:
    """Tests for layer functionality."""

    def test_add_layer(self, canvas_model, qtbot):
        """Test adding a layer."""
        layer_data = make_layer(name="Background")

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            canvas_model.addItem(layer_data)

        assert canvas_model.count() == 1
        items = canvas_model.getItems()
        assert isinstance(items[0], LayerItem)
        assert items[0].name == "Background"

    def test_items_with_parent_layer(self, canvas_model):
        """Test items can reference a parent layer."""
        canvas_model.addItem(make_layer(name="Layer1", layer_id="layer-1"))
        canvas_model.addItem(make_rectangle(name="Rect1", parent_id="layer-1"))

        items = canvas_model.getItems()
        assert items[1].parent_id == "layer-1"


class TestCanvasModelRenderItems:
    """Tests for render item ordering."""

    def test_render_items_respects_visibility(self, canvas_model):
        """Invisible items should not be in render items."""
        canvas_model.addItem(make_rectangle(visible=True))
        canvas_model.addItem(make_rectangle(visible=False))

        render_items = canvas_model.getRenderItems()
        assert len(render_items) == 1

    def test_render_items_order(self, canvas_model):
        """Render items should be in model order."""
        canvas_model.addItem(make_path(points=[{"x": 0, "y": 0}, {"x": 10, "y": 0}]))
        canvas_model.addItem(make_rectangle())

        items = canvas_model.getRenderItems()
        assert len(items) == 2
        assert isinstance(items[0], PathItem)
        assert isinstance(items[1], RectangleItem)


class TestCanvasModelClear:
    """Tests for clearing the model."""

    def test_clear_removes_all_items(self, canvas_model, qtbot):
        """Test that clear removes all items."""
        canvas_model.addItem(make_rectangle())
        canvas_model.addItem(make_ellipse())
        canvas_model.addItem(make_path(points=[{"x": 0, "y": 0}, {"x": 1, "y": 1}]))

        with qtbot.waitSignal(canvas_model.modelReset, timeout=1000):
            canvas_model.clear()

        assert canvas_model.count() == 0


class TestCanvasModelDuplicate:
    """Tests for duplicating items."""

    def test_duplicate_rectangle(self, canvas_model, qtbot):
        """Test duplicating a rectangle creates offset copy."""
        canvas_model.addItem(
            make_rectangle(x=10, y=20, width=50, height=30, name="Original")
        )

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            canvas_model.duplicateItem(0)

        assert canvas_model.count() == 2
        items = canvas_model.getItems()
        # Duplicate should be offset
        assert items[1].geometry.x == 10 + DEFAULT_DUPLICATE_OFFSET
        assert items[1].geometry.y == 20 + DEFAULT_DUPLICATE_OFFSET


class TestCanvasModelMoveItems:
    """Tests for moving items in the model order."""

    def test_move_item_up(self, canvas_model):
        """Test moving an item up in the order."""
        canvas_model.addItem(make_rectangle(name="A"))
        canvas_model.addItem(make_rectangle(name="B"))
        canvas_model.addItem(make_rectangle(name="C"))

        canvas_model.moveItem(2, 0)

        items = canvas_model.getItems()
        assert items[0].name == "C"
        assert items[1].name == "A"
        assert items[2].name == "B"


class TestCanvasModelText:
    """Tests for text items in the model."""

    def test_add_text_item(self, canvas_model, qtbot):
        """Test adding a text item."""
        item_data = make_text(x=10, y=20, text="Hello World", font_size=24)

        with qtbot.waitSignal(canvas_model.itemAdded, timeout=1000):
            canvas_model.addItem(item_data)

        assert canvas_model.count() == 1
        items = canvas_model.getItems()
        assert isinstance(items[0], TextItem)
        assert items[0].text == "Hello World"
        assert items[0].font_size == 24


class TestCanvasModelItemData:
    """Tests for getItemData method."""

    def test_get_item_data_rectangle(self, canvas_model):
        """Test getItemData returns dictionary for rectangle."""
        canvas_model.addItem(
            make_rectangle(x=10, y=20, width=100, height=50, name="MyRect")
        )

        data = canvas_model.getItemData(0)
        assert data["type"] == "rectangle"
        assert data["name"] == "MyRect"
        assert data["geometry"]["x"] == 10
        assert data["geometry"]["width"] == 100

    def test_get_item_data_invalid_index(self, canvas_model):
        """Test getItemData returns None for invalid index."""
        assert canvas_model.getItemData(999) is None


class TestCanvasModelVisibility:
    """Tests for visibility toggling."""

    def test_toggle_visibility(self, canvas_model, qtbot):
        """Test toggling item visibility."""
        canvas_model.addItem(make_rectangle(visible=True))

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.toggleVisibility(0)

        items = canvas_model.getItems()
        assert items[0].visible is False


class TestCanvasModelLock:
    """Tests for lock toggling."""

    def test_toggle_lock(self, canvas_model, qtbot):
        """Test toggling item lock state."""
        canvas_model.addItem(make_rectangle(locked=False))

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.toggleLocked(0)

        items = canvas_model.getItems()
        assert items[0].locked is True


class TestCanvasModelSetBoundingBox:
    """Tests for setBoundingBox method."""

    def test_set_rectangle_bounding_box(self, canvas_model):
        """Test setting bounding box for rectangle."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=50, height=50))

        result = canvas_model.setBoundingBox(
            0, {"x": 100, "y": 100, "width": 75, "height": 25}
        )
        assert result is True

        item = canvas_model.getItems()[0]
        assert item.geometry.x == 100
        assert item.geometry.y == 100
        assert item.geometry.width == 75
        assert item.geometry.height == 25

    def test_set_ellipse_bounding_box(self, canvas_model):
        """Test setting bounding box for ellipse."""
        canvas_model.addItem(
            make_ellipse(center_x=50, center_y=50, radius_x=25, radius_y=25)
        )

        result = canvas_model.setBoundingBox(
            0, {"x": 0, "y": 0, "width": 100, "height": 50}
        )
        assert result is True

        item = canvas_model.getItems()[0]
        assert item.geometry.center_x == 50
        assert item.geometry.center_y == 25
        assert item.geometry.radius_x == 50
        assert item.geometry.radius_y == 25

    def test_set_path_bounding_box(self, canvas_model):
        """Test setting bounding box for path translates points."""
        canvas_model.addItem(make_path(points=[{"x": 0, "y": 0}, {"x": 10, "y": 10}]))

        result = canvas_model.setBoundingBox(
            0, {"x": 100, "y": 100, "width": 10, "height": 10}
        )
        assert result is True

        item = canvas_model.getItems()[0]
        assert item.geometry.points[0]["x"] == 100
        assert item.geometry.points[0]["y"] == 100
        assert item.geometry.points[1]["x"] == 110
        assert item.geometry.points[1]["y"] == 110

    def test_set_text_bounding_box(self, canvas_model):
        """Test setting bounding box for text."""
        canvas_model.addItem(make_text(x=0, y=0, text="Hello"))

        result = canvas_model.setBoundingBox(
            0, {"x": 50, "y": 50, "width": 200, "height": 30}
        )
        assert result is True

        item = canvas_model.getItems()[0]
        assert item.x == 50
        assert item.y == 50
        assert item.width == 200
        assert item.height == 30

    def test_set_bounding_box_invalid_index(self, canvas_model):
        """Test setting bounding box with invalid index returns False."""
        result = canvas_model.setBoundingBox(
            999, {"x": 0, "y": 0, "width": 10, "height": 10}
        )
        assert result is False

    def test_set_bounding_box_layer_returns_false(self, canvas_model):
        """Test setting bounding box on layer returns False."""
        canvas_model.addItem(make_layer())

        result = canvas_model.setBoundingBox(
            0, {"x": 0, "y": 0, "width": 10, "height": 10}
        )
        assert result is False

    def test_set_path_bounding_box_empty_points(self, canvas_model):
        """Test setting bounding box on empty path returns False."""
        canvas_model.addItem(make_path(points=[]))

        result = canvas_model.setBoundingBox(
            0, {"x": 0, "y": 0, "width": 10, "height": 10}
        )
        assert result is False


class TestCanvasModelGrouping:
    """Tests for grouping and ungrouping items."""

    def test_group_items(self, canvas_model):
        """Test grouping multiple items."""
        canvas_model.addItem(make_rectangle(name="A"))
        canvas_model.addItem(make_rectangle(name="B"))

        group_idx = canvas_model.groupItems([0, 1])
        assert group_idx >= 0
        # Group should exist
        assert canvas_model.count() == 3

    def test_ungroup_items(self, canvas_model):
        """Test ungrouping a group."""
        canvas_model.addItem(make_rectangle(name="A"))
        canvas_model.addItem(make_rectangle(name="B"))

        group_idx = canvas_model.groupItems([0, 1])

        canvas_model.ungroup(group_idx)
        # Group should be removed, items should remain
        # Only shapes should remain (group is removed)
        items = canvas_model.getItems()
        shapes = [i for i in items if isinstance(i, RectangleItem)]
        assert len(shapes) == 2

    def test_ungroup_invalid_index(self, canvas_model):
        """Test ungrouping invalid index does nothing."""
        canvas_model.addItem(make_rectangle())
        canvas_model.ungroup(999)  # Should not crash
        assert canvas_model.count() == 1

    def test_ungroup_non_group_item(self, canvas_model):
        """Test ungrouping a non-group item does nothing."""
        canvas_model.addItem(make_rectangle())
        canvas_model.ungroup(0)  # Rectangle is not a group
        assert canvas_model.count() == 1


class TestCanvasModelMoveGroup:
    """Tests for moving groups."""

    def test_move_group_translates_children(self, canvas_model):
        """Test that moveGroup translates all descendant shapes."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=10, height=10, name="A"))
        canvas_model.addItem(make_rectangle(x=20, y=20, width=10, height=10, name="B"))

        group_idx = canvas_model.groupItems([0, 1])

        canvas_model.moveGroup(group_idx, 100, 50)

        items = canvas_model.getItems()
        rects = [i for i in items if isinstance(i, RectangleItem)]
        assert rects[0].geometry.x == 100
        assert rects[0].geometry.y == 50
        assert rects[1].geometry.x == 120
        assert rects[1].geometry.y == 70

    def test_move_group_invalid_index(self, canvas_model):
        """Test moveGroup with invalid index does nothing."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=10, height=10))
        canvas_model.moveGroup(999, 100, 50)  # Should not crash
        item = canvas_model.getItems()[0]
        assert item.geometry.x == 0

    def test_move_group_non_container(self, canvas_model):
        """Test moveGroup on non-container does nothing."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=10, height=10))
        canvas_model.moveGroup(0, 100, 50)  # Rectangle is not a container
        item = canvas_model.getItems()[0]
        assert item.geometry.x == 0


class TestCanvasModelReparent:
    """Tests for reparenting items."""

    def test_reparent_item_to_layer(self, canvas_model):
        """Test reparenting an item to a layer."""
        canvas_model.addItem(make_layer(name="Layer1", layer_id="layer-1"))
        canvas_model.addItem(make_rectangle(name="Rect"))

        canvas_model.reparentItem(1, "layer-1")

        items = canvas_model.getItems()
        rect = [i for i in items if isinstance(i, RectangleItem)][0]
        assert rect.parent_id == "layer-1"

    def test_reparent_invalid_index(self, canvas_model):
        """Test reparenting invalid index does nothing."""
        canvas_model.addItem(make_layer(layer_id="layer-1"))
        canvas_model.reparentItem(999, "layer-1")  # Should not crash


class TestCanvasModelEffectivelyLocked:
    """Tests for isEffectivelyLocked method."""

    def test_is_effectively_locked_item_locked(self, canvas_model):
        """Test that locked item returns True."""
        canvas_model.addItem(make_rectangle(locked=True))
        assert canvas_model.isEffectivelyLocked(0) is True

    def test_is_effectively_locked_parent_locked(self, canvas_model):
        """Test that item with locked parent returns True."""
        canvas_model.addItem(make_layer(layer_id="layer-1", locked=True))
        canvas_model.addItem(make_rectangle(parent_id="layer-1", locked=False))
        assert canvas_model.isEffectivelyLocked(1) is True

    def test_is_effectively_locked_unlocked(self, canvas_model):
        """Test that unlocked item with unlocked parent returns False."""
        canvas_model.addItem(make_layer(layer_id="layer-1", locked=False))
        canvas_model.addItem(make_rectangle(parent_id="layer-1", locked=False))
        assert canvas_model.isEffectivelyLocked(1) is False


class TestCanvasModelDuplicateItems:
    """Tests for duplicating multiple items."""

    def test_duplicate_multiple_items(self, canvas_model):
        """Test duplicating multiple items at once."""
        canvas_model.addItem(make_rectangle(x=10, y=10, name="A"))
        canvas_model.addItem(make_rectangle(x=20, y=20, name="B"))

        new_indices = canvas_model.duplicateItems([0, 1])

        assert len(new_indices) == 2
        assert canvas_model.count() == 4


class TestCanvasModelRenameItem:
    """Tests for renaming items."""

    def test_rename_item(self, canvas_model, qtbot):
        """Test renaming an item."""
        canvas_model.addItem(make_rectangle(name="Original"))

        with qtbot.waitSignal(canvas_model.itemModified, timeout=1000):
            canvas_model.renameItem(0, "Renamed")

        items = canvas_model.getItems()
        assert items[0].name == "Renamed"

    def test_rename_invalid_index(self, canvas_model):
        """Test renaming invalid index does nothing."""
        canvas_model.addItem(make_rectangle(name="Original"))
        canvas_model.renameItem(999, "Renamed")  # Should not crash
        items = canvas_model.getItems()
        assert items[0].name == "Original"


class TestCanvasModelUndoRedo:
    """Tests for undo/redo functionality."""

    def test_undo_add_item(self, canvas_model):
        """Test undoing an add operation."""
        canvas_model.addItem(make_rectangle())
        assert canvas_model.count() == 1

        result = canvas_model.undo()
        assert result is True
        assert canvas_model.count() == 0

    def test_redo_add_item(self, canvas_model):
        """Test redoing an add operation."""
        canvas_model.addItem(make_rectangle())
        canvas_model.undo()
        assert canvas_model.count() == 0

        result = canvas_model.redo()
        assert result is True
        assert canvas_model.count() == 1

    def test_can_undo_property(self, canvas_model):
        """Test canUndo property."""
        assert canvas_model.canUndo is False
        canvas_model.addItem(make_rectangle())
        assert canvas_model.canUndo is True

    def test_can_redo_property(self, canvas_model):
        """Test canRedo property."""
        canvas_model.addItem(make_rectangle())
        assert canvas_model.canRedo is False
        canvas_model.undo()
        assert canvas_model.canRedo is True


class TestCanvasModelTransaction:
    """Tests for transaction functionality."""

    def test_transaction_batches_updates(self, canvas_model, qtbot):
        """Test that transactions batch multiple update commands into one undo."""
        # Add items first (outside transaction)
        canvas_model.addItem(make_rectangle(x=0, y=0, name="A"))
        canvas_model.addItem(make_rectangle(x=10, y=10, name="B"))
        assert canvas_model.count() == 2

        # Now do a transaction that updates both items
        canvas_model.beginTransaction()

        # Update first item
        item_data_a = canvas_model.getItemData(0)
        item_data_a["geometry"]["x"] = 100
        canvas_model.updateItem(0, item_data_a)

        # Update second item
        item_data_b = canvas_model.getItemData(1)
        item_data_b["geometry"]["x"] = 200
        canvas_model.updateItem(1, item_data_b)

        canvas_model.endTransaction()

        # Verify updates were applied
        items = canvas_model.getItems()
        assert items[0].geometry.x == 100
        assert items[1].geometry.x == 200

        # Single undo should revert both updates
        canvas_model.undo()
        items = canvas_model.getItems()
        assert items[0].geometry.x == 0
        assert items[1].geometry.x == 10


class TestCanvasModelGetLayerItems:
    """Tests for getLayerItems method."""

    def test_get_layer_items(self, canvas_model):
        """Test getting items that belong to a specific layer."""
        canvas_model.addItem(make_layer(layer_id="layer-1", name="Layer1"))
        canvas_model.addItem(make_rectangle(parent_id="layer-1", name="A"))
        canvas_model.addItem(make_rectangle(parent_id="layer-1", name="B"))
        canvas_model.addItem(make_rectangle(name="C"))  # Not in layer

        layer_items = canvas_model.getLayerItems("layer-1")
        assert len(layer_items) == 2
        names = [i.name for i in layer_items]
        assert "A" in names
        assert "B" in names


class TestCanvasModelLayerBounds:
    """Tests for getLayerBounds method."""

    def test_get_layer_bounds(self, canvas_model):
        """Test getting bounding box of all items in a layer."""
        canvas_model.addItem(make_layer(layer_id="layer-1", name="Layer1"))
        canvas_model.addItem(
            make_rectangle(x=0, y=0, width=50, height=50, parent_id="layer-1")
        )
        canvas_model.addItem(
            make_rectangle(x=100, y=100, width=50, height=50, parent_id="layer-1")
        )

        bounds = canvas_model.getLayerBounds("layer-1")
        assert bounds["x"] == 0
        assert bounds["y"] == 0
        assert bounds["width"] == 150
        assert bounds["height"] == 150


class TestCanvasModelBoundingBoxEdgeCases:
    """Edge case tests for bounding box methods."""

    def test_get_bounding_box_invalid_index(self, canvas_model):
        """Test getBoundingBox with invalid index returns None."""
        result = canvas_model.getBoundingBox(999)
        assert result is None

    def test_get_bounding_box_text_auto_height(self, canvas_model):
        """Test getBoundingBox for text with auto height."""
        canvas_model.addItem(make_text(x=10, y=20, text="Test", height=0, font_size=20))
        bbox = canvas_model.getBoundingBox(0)
        assert bbox["x"] == 10
        assert bbox["y"] == 20
        # Height is calculated by QTextDocument, should be reasonable for font size 20
        assert bbox["height"] > 0

    def test_get_bounding_box_group_union(self, canvas_model):
        """Test getBoundingBox for group returns union of children."""
        canvas_model.addItem(make_rectangle(x=0, y=0, width=50, height=50, name="A"))
        canvas_model.addItem(
            make_rectangle(x=100, y=100, width=50, height=50, name="B")
        )

        group_idx = canvas_model.groupItems([0, 1])
        bbox = canvas_model.getBoundingBox(group_idx)

        assert bbox["x"] == 0
        assert bbox["y"] == 0
        assert bbox["width"] == 150
        assert bbox["height"] == 150


class TestCanvasModelGetGeometryBounds:
    """Tests for getGeometryBounds method (untransformed bounds)."""

    def test_get_geometry_bounds_rectangle(self, canvas_model):
        """getGeometryBounds returns untransformed rectangle bounds."""
        canvas_model.addItem(make_rectangle(x=10, y=20, width=100, height=50))
        bounds = canvas_model.getGeometryBounds(0)
        assert bounds["x"] == 10
        assert bounds["y"] == 20
        assert bounds["width"] == 100
        assert bounds["height"] == 50

    def test_get_geometry_bounds_ellipse(self, canvas_model):
        """getGeometryBounds returns untransformed ellipse bounds."""
        canvas_model.addItem(
            make_ellipse(center_x=50, center_y=50, radius_x=30, radius_y=20)
        )
        bounds = canvas_model.getGeometryBounds(0)
        assert bounds["x"] == 20  # center_x - radius_x
        assert bounds["y"] == 30  # center_y - radius_y
        assert bounds["width"] == 60  # radius_x * 2
        assert bounds["height"] == 40  # radius_y * 2

    def test_get_geometry_bounds_path(self, canvas_model):
        """getGeometryBounds returns untransformed path bounds."""
        canvas_model.addItem(
            make_path(points=[{"x": 10, "y": 20}, {"x": 110, "y": 70}])
        )
        bounds = canvas_model.getGeometryBounds(0)
        assert bounds["x"] == 10
        assert bounds["y"] == 20
        assert bounds["width"] == 100
        assert bounds["height"] == 50

    def test_get_geometry_bounds_ignores_transform(self, canvas_model):
        """getGeometryBounds should ignore item transform."""
        data = make_rectangle(x=0, y=0, width=100, height=50)
        data["transform"] = {"translateX": 50, "translateY": 25, "rotate": 45}
        canvas_model.addItem(data)
        bounds = canvas_model.getGeometryBounds(0)
        # Should be the raw geometry, not affected by transform
        assert bounds["x"] == 0
        assert bounds["y"] == 0
        assert bounds["width"] == 100
        assert bounds["height"] == 50

    def test_get_geometry_bounds_invalid_index(self, canvas_model):
        """getGeometryBounds returns None for invalid index."""
        assert canvas_model.getGeometryBounds(-1) is None
        assert canvas_model.getGeometryBounds(999) is None

    def test_get_geometry_bounds_layer_returns_none(self, canvas_model):
        """getGeometryBounds returns None for layers (no geometry)."""
        canvas_model.addItem(make_layer(name="Layer"))
        assert canvas_model.getGeometryBounds(0) is None
