# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for CanvasModel.deleteItems() method - bulk deletion."""

from test_helpers import (
    make_rectangle,
    make_ellipse,
    make_text,
    make_group,
    make_artboard,
)


# Uses canvas_model fixture from conftest.py


class TestDeleteItemsSingle:
    """Test deleting single items."""

    def test_delete_single_item(self, canvas_model):
        """Deleting a single item removes it from the model."""
        canvas_model.addItem(make_rectangle(x=0, y=0))
        assert canvas_model.count() == 1

        canvas_model.deleteItems([0])

        assert canvas_model.count() == 0

    def test_delete_returns_count(self, canvas_model):
        """deleteItems returns the number of items actually deleted."""
        canvas_model.addItem(make_rectangle())
        canvas_model.addItem(make_ellipse())

        deleted = canvas_model.deleteItems([0])

        assert deleted == 1
        assert canvas_model.count() == 1


class TestDeleteItemsMultiple:
    """Test deleting multiple items."""

    def test_delete_multiple_items(self, canvas_model):
        """Deleting multiple items removes all of them."""
        canvas_model.addItem(make_rectangle(x=0, y=0))
        canvas_model.addItem(make_ellipse(center_x=100, center_y=100))
        canvas_model.addItem(make_text(x=200, y=200))
        assert canvas_model.count() == 3

        canvas_model.deleteItems([0, 1, 2])

        assert canvas_model.count() == 0

    def test_delete_subset_preserves_others(self, canvas_model):
        """Deleting a subset preserves unselected items."""
        canvas_model.addItem(make_rectangle(x=0, y=0, name="Rect1"))
        canvas_model.addItem(make_ellipse(center_x=100, center_y=100, name="Ellipse"))
        canvas_model.addItem(make_rectangle(x=200, y=200, name="Rect2"))

        canvas_model.deleteItems([0, 2])  # Delete first and last

        assert canvas_model.count() == 1
        assert canvas_model.getItemData(0)["name"] == "Ellipse"

    def test_delete_handles_index_order(self, canvas_model):
        """Deletion works regardless of index order in the input list."""
        canvas_model.addItem(make_rectangle(name="A"))
        canvas_model.addItem(make_rectangle(name="B"))
        canvas_model.addItem(make_rectangle(name="C"))

        # Indices in ascending order - should still work
        canvas_model.deleteItems([0, 1])

        assert canvas_model.count() == 1
        assert canvas_model.getItemData(0)["name"] == "C"


class TestDeleteItemsLocked:
    """Test that locked items are not deleted."""

    def test_locked_item_not_deleted(self, canvas_model):
        """Locked items should not be deleted."""
        canvas_model.addItem(make_rectangle(locked=True))

        deleted = canvas_model.deleteItems([0])

        assert deleted == 0
        assert canvas_model.count() == 1

    def test_effectively_locked_item_not_deleted(self, canvas_model):
        """Items in locked artboards should still be deleted."""
        canvas_model.addItem(
            make_artboard(name="Layer", artboard_id="layer1", locked=True)
        )
        canvas_model.addItem(make_rectangle(parent_id="layer1"))

        deleted = canvas_model.deleteItems([1])

        assert deleted == 1
        assert canvas_model.count() == 1

    def test_mixed_locked_unlocked(self, canvas_model):
        """Only unlocked items are deleted from mixed selection."""
        canvas_model.addItem(make_rectangle(name="Unlocked1"))
        canvas_model.addItem(make_rectangle(name="Locked", locked=True))
        canvas_model.addItem(make_rectangle(name="Unlocked2"))

        deleted = canvas_model.deleteItems([0, 1, 2])

        assert deleted == 2
        assert canvas_model.count() == 1
        assert canvas_model.getItemData(0)["name"] == "Locked"


class TestDeleteItemsContainers:
    """Test deleting groups and layers."""

    def test_delete_group_removes_children(self, canvas_model):
        """Deleting a group should remove its children too."""
        canvas_model.addItem(make_group(name="Group", group_id="grp1"))
        canvas_model.addItem(make_rectangle(parent_id="grp1"))
        canvas_model.addItem(make_ellipse(parent_id="grp1"))
        assert canvas_model.count() == 3

        canvas_model.deleteItems([0])  # Delete just the group

        # Group and children should all be gone
        assert canvas_model.count() == 0

    def test_delete_layer_removes_children(self, canvas_model):
        """Deleting a layer should remove its children too."""
        canvas_model.addItem(make_artboard(name="Layer", artboard_id="layer1"))
        canvas_model.addItem(make_rectangle(parent_id="layer1"))
        assert canvas_model.count() == 2

        canvas_model.deleteItems([0])

        assert canvas_model.count() == 0


class TestDeleteItemsUndoRedo:
    """Test undo/redo for deleteItems."""

    def test_delete_is_undoable(self, canvas_model):
        """deleteItems should be undoable."""
        canvas_model.addItem(make_rectangle(name="Test"))
        assert canvas_model.count() == 1

        canvas_model.deleteItems([0])
        assert canvas_model.count() == 0

        canvas_model.undo()
        assert canvas_model.count() == 1
        assert canvas_model.getItemData(0)["name"] == "Test"

    def test_delete_is_redoable(self, canvas_model):
        """deleteItems should be redoable after undo."""
        canvas_model.addItem(make_rectangle())

        canvas_model.deleteItems([0])
        canvas_model.undo()
        canvas_model.redo()

        assert canvas_model.count() == 0

    def test_delete_multiple_single_undo(self, canvas_model):
        """Deleting multiple items should undo as a single operation."""
        canvas_model.addItem(make_rectangle(name="A"))
        canvas_model.addItem(make_rectangle(name="B"))
        canvas_model.addItem(make_rectangle(name="C"))

        canvas_model.deleteItems([0, 1, 2])
        assert canvas_model.count() == 0

        # Single undo should restore all
        canvas_model.undo()
        assert canvas_model.count() == 3


class TestDeleteItemsEdgeCases:
    """Test edge cases for deleteItems."""

    def test_empty_indices_list(self, canvas_model):
        """Empty indices list should be a no-op."""
        canvas_model.addItem(make_rectangle())

        deleted = canvas_model.deleteItems([])

        assert deleted == 0
        assert canvas_model.count() == 1

    def test_invalid_indices_ignored(self, canvas_model):
        """Invalid indices should be silently ignored."""
        canvas_model.addItem(make_rectangle())

        deleted = canvas_model.deleteItems([0, 99, -1])

        assert deleted == 1
        assert canvas_model.count() == 0

    def test_duplicate_indices_handled(self, canvas_model):
        """Duplicate indices in the list should not cause issues."""
        canvas_model.addItem(make_rectangle())
        canvas_model.addItem(make_ellipse())

        deleted = canvas_model.deleteItems([0, 0, 1, 1])

        assert deleted == 2
        assert canvas_model.count() == 0
