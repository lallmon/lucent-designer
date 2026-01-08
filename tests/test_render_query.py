"""Unit tests for render_query module - pure logic for render/hit-test queries."""

from lucent.render_query import get_render_items, get_hit_test_items


class MockItem:
    """Mock item for testing render query functions."""

    def __init__(self, item_type="shape", item_id=None):
        self.type = item_type
        self.id = item_id


def is_container(item):
    """Check if item is a container."""
    return item.type in ("layer", "group")


def is_renderable(item):
    """Check if item is renderable."""
    return item.type in ("rectangle", "ellipse", "path", "text")


class TestGetRenderItems:
    """Tests for get_render_items function."""

    def test_returns_empty_for_empty_list(self):
        result = get_render_items([], is_container, is_renderable, lambda i: True)
        assert result == []

    def test_returns_renderable_items(self):
        items = [
            MockItem("rectangle"),
            MockItem("ellipse"),
            MockItem("path"),
            MockItem("text"),
        ]
        result = get_render_items(items, is_container, is_renderable, lambda i: True)
        assert len(result) == 4
        assert result == items

    def test_excludes_containers(self):
        items = [
            MockItem("layer"),
            MockItem("rectangle"),
            MockItem("group"),
            MockItem("ellipse"),
        ]
        result = get_render_items(items, is_container, is_renderable, lambda i: True)
        assert len(result) == 2
        assert result[0].type == "rectangle"
        assert result[1].type == "ellipse"

    def test_excludes_invisible_items(self):
        items = [
            MockItem("rectangle"),
            MockItem("ellipse"),
            MockItem("path"),
        ]

        def is_visible(idx):
            return idx != 1

        result = get_render_items(items, is_container, is_renderable, is_visible)
        assert len(result) == 2
        assert result[0].type == "rectangle"
        assert result[1].type == "path"

    def test_preserves_order(self):
        items = [
            MockItem("rectangle", "first"),
            MockItem("ellipse", "second"),
            MockItem("path", "third"),
        ]
        result = get_render_items(items, is_container, is_renderable, lambda i: True)
        assert result[0].id == "first"
        assert result[1].id == "second"
        assert result[2].id == "third"


class TestGetHitTestItems:
    """Tests for get_hit_test_items function."""

    def test_returns_empty_for_empty_list(self):
        result = get_hit_test_items(
            [], lambda i: True, lambda item: {"type": item.type}
        )
        assert result == []

    def test_returns_visible_items_with_indices(self):
        items = [MockItem("rectangle"), MockItem("ellipse")]

        def item_to_dict(item):
            return {"type": item.type}

        result = get_hit_test_items(items, lambda i: True, item_to_dict)
        assert len(result) == 2
        assert result[0] == {"type": "rectangle", "modelIndex": 0}
        assert result[1] == {"type": "ellipse", "modelIndex": 1}

    def test_excludes_invisible_items(self):
        items = [
            MockItem("rectangle"),
            MockItem("ellipse"),
            MockItem("path"),
        ]

        def is_visible(idx):
            return idx != 1

        def item_to_dict(item):
            return {"type": item.type}

        result = get_hit_test_items(items, is_visible, item_to_dict)
        assert len(result) == 2
        assert result[0]["modelIndex"] == 0
        assert result[1]["modelIndex"] == 2

    def test_includes_all_item_types(self):
        """Hit test includes all types, not just renderable ones."""
        items = [
            MockItem("layer"),
            MockItem("group"),
            MockItem("rectangle"),
        ]

        def item_to_dict(item):
            return {"type": item.type}

        result = get_hit_test_items(items, lambda i: True, item_to_dict)
        assert len(result) == 3
        types = [r["type"] for r in result]
        assert "layer" in types
        assert "group" in types
        assert "rectangle" in types
