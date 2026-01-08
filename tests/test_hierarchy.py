"""Unit tests for hierarchy module - pure logic for parent-child relationships."""

from lucent.hierarchy import (
    get_container_by_id,
    get_direct_children_indices,
    get_descendant_indices,
    is_descendant_of,
    is_effectively_visible,
    is_effectively_locked,
)


class MockItem:
    """Mock item for testing hierarchy functions."""

    def __init__(
        self,
        item_id=None,
        parent_id=None,
        visible=True,
        locked=False,
        is_container=False,
    ):
        self.id = item_id
        self.parent_id = parent_id
        self.visible = visible
        self.locked = locked
        self._is_container = is_container


def is_container(item):
    """Check if item is a container."""
    return getattr(item, "_is_container", False)


class TestGetContainerById:
    """Tests for get_container_by_id function."""

    def test_returns_none_for_none_id(self):
        items = [MockItem(item_id="layer-1", is_container=True)]
        result = get_container_by_id(items, None, is_container)
        assert result is None

    def test_returns_none_for_empty_string_id(self):
        items = [MockItem(item_id="layer-1", is_container=True)]
        result = get_container_by_id(items, "", is_container)
        assert result is None

    def test_finds_container_by_id(self):
        layer = MockItem(item_id="layer-1", is_container=True)
        items = [layer, MockItem()]
        result = get_container_by_id(items, "layer-1", is_container)
        assert result is layer

    def test_returns_none_for_non_container_with_matching_id(self):
        """Non-containers should not be found even with matching ID."""
        item = MockItem(item_id="item-1", is_container=False)
        items = [item]
        result = get_container_by_id(items, "item-1", is_container)
        assert result is None

    def test_returns_none_for_nonexistent_id(self):
        items = [MockItem(item_id="layer-1", is_container=True)]
        result = get_container_by_id(items, "nonexistent", is_container)
        assert result is None


class TestGetDirectChildrenIndices:
    """Tests for get_direct_children_indices function."""

    def test_returns_empty_for_no_children(self):
        items = [MockItem(item_id="layer-1", is_container=True)]
        result = get_direct_children_indices(items, "layer-1")
        assert result == []

    def test_finds_direct_children(self):
        items = [
            MockItem(item_id="layer-1", is_container=True),
            MockItem(parent_id="layer-1"),
            MockItem(parent_id="layer-1"),
            MockItem(parent_id="layer-2"),
        ]
        result = get_direct_children_indices(items, "layer-1")
        assert result == [1, 2]

    def test_excludes_grandchildren(self):
        items = [
            MockItem(item_id="layer-1", is_container=True),
            MockItem(item_id="group-1", parent_id="layer-1", is_container=True),
            MockItem(parent_id="group-1"),
        ]
        result = get_direct_children_indices(items, "layer-1")
        assert result == [1]


class TestGetDescendantIndices:
    """Tests for get_descendant_indices function."""

    def test_returns_empty_for_no_descendants(self):
        items = [MockItem(item_id="layer-1", is_container=True)]
        result = get_descendant_indices(items, "layer-1", is_container)
        assert result == []

    def test_finds_direct_children(self):
        items = [
            MockItem(item_id="layer-1", is_container=True),
            MockItem(parent_id="layer-1"),
            MockItem(parent_id="layer-1"),
        ]
        result = get_descendant_indices(items, "layer-1", is_container)
        assert set(result) == {1, 2}

    def test_finds_all_descendants_recursively(self):
        items = [
            MockItem(item_id="layer-1", is_container=True),
            MockItem(item_id="group-1", parent_id="layer-1", is_container=True),
            MockItem(parent_id="group-1"),
            MockItem(parent_id="layer-1"),
        ]
        result = get_descendant_indices(items, "layer-1", is_container)
        assert set(result) == {1, 2, 3}


class TestIsDescendantOf:
    """Tests for is_descendant_of function."""

    def test_returns_false_for_none_candidate(self):
        items = [MockItem(item_id="layer-1", is_container=True)]
        result = is_descendant_of(items, None, "layer-1", is_container)
        assert result is False

    def test_returns_false_for_same_id(self):
        items = [MockItem(item_id="layer-1", is_container=True)]
        result = is_descendant_of(items, "layer-1", "layer-1", is_container)
        assert result is False

    def test_returns_true_for_direct_child(self):
        items = [
            MockItem(item_id="layer-1", is_container=True),
            MockItem(item_id="group-1", parent_id="layer-1", is_container=True),
        ]
        result = is_descendant_of(items, "group-1", "layer-1", is_container)
        assert result is True

    def test_returns_true_for_grandchild(self):
        items = [
            MockItem(item_id="layer-1", is_container=True),
            MockItem(item_id="group-1", parent_id="layer-1", is_container=True),
            MockItem(item_id="group-2", parent_id="group-1", is_container=True),
        ]
        result = is_descendant_of(items, "group-2", "layer-1", is_container)
        assert result is True

    def test_returns_false_for_unrelated(self):
        items = [
            MockItem(item_id="layer-1", is_container=True),
            MockItem(item_id="layer-2", is_container=True),
        ]
        result = is_descendant_of(items, "layer-2", "layer-1", is_container)
        assert result is False


class TestIsEffectivelyVisible:
    """Tests for is_effectively_visible function."""

    def test_returns_false_for_invalid_index(self):
        items = []
        assert is_effectively_visible(items, 0, is_container) is False
        assert is_effectively_visible(items, -1, is_container) is False

    def test_returns_true_for_visible_orphan(self):
        items = [MockItem(visible=True)]
        assert is_effectively_visible(items, 0, is_container) is True

    def test_returns_false_for_hidden_orphan(self):
        items = [MockItem(visible=False)]
        assert is_effectively_visible(items, 0, is_container) is False

    def test_returns_false_when_parent_hidden(self):
        items = [
            MockItem(item_id="layer-1", visible=False, is_container=True),
            MockItem(visible=True, parent_id="layer-1"),
        ]
        assert is_effectively_visible(items, 1, is_container) is False

    def test_returns_true_when_parent_visible(self):
        items = [
            MockItem(item_id="layer-1", visible=True, is_container=True),
            MockItem(visible=True, parent_id="layer-1"),
        ]
        assert is_effectively_visible(items, 1, is_container) is True

    def test_returns_false_when_grandparent_hidden(self):
        items = [
            MockItem(item_id="layer-1", visible=False, is_container=True),
            MockItem(
                item_id="group-1", visible=True, parent_id="layer-1", is_container=True
            ),
            MockItem(visible=True, parent_id="group-1"),
        ]
        assert is_effectively_visible(items, 2, is_container) is False


class TestIsEffectivelyLocked:
    """Tests for is_effectively_locked function."""

    def test_returns_false_for_invalid_index(self):
        items = []
        assert is_effectively_locked(items, 0, is_container) is False
        assert is_effectively_locked(items, -1, is_container) is False

    def test_returns_false_for_unlocked_orphan(self):
        items = [MockItem(locked=False)]
        assert is_effectively_locked(items, 0, is_container) is False

    def test_returns_true_for_locked_orphan(self):
        items = [MockItem(locked=True)]
        assert is_effectively_locked(items, 0, is_container) is True

    def test_returns_true_when_parent_locked(self):
        items = [
            MockItem(item_id="layer-1", locked=True, is_container=True),
            MockItem(locked=False, parent_id="layer-1"),
        ]
        assert is_effectively_locked(items, 1, is_container) is True

    def test_returns_false_when_parent_unlocked(self):
        items = [
            MockItem(item_id="layer-1", locked=False, is_container=True),
            MockItem(locked=False, parent_id="layer-1"),
        ]
        assert is_effectively_locked(items, 1, is_container) is False

    def test_returns_true_when_grandparent_locked(self):
        items = [
            MockItem(item_id="layer-1", locked=True, is_container=True),
            MockItem(
                item_id="group-1", locked=False, parent_id="layer-1", is_container=True
            ),
            MockItem(locked=False, parent_id="group-1"),
        ]
        assert is_effectively_locked(items, 2, is_container) is True
