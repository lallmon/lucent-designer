# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later


from lucent.quadtree import Rect, SpatialIndex


class TestRect:
    def test_intersects_overlapping(self):
        r1 = Rect(0, 0, 10, 10)
        r2 = Rect(5, 5, 10, 10)
        assert r1.intersects(r2)
        assert r2.intersects(r1)

    def test_intersects_touching_edge(self):
        """Touching edges don't count as intersection."""
        r1 = Rect(0, 0, 10, 10)
        r2 = Rect(10, 0, 10, 10)
        assert not r1.intersects(r2)

    def test_intersects_separate(self):
        r1 = Rect(0, 0, 10, 10)
        r2 = Rect(100, 100, 10, 10)
        assert not r1.intersects(r2)

    def test_contains_point_inside(self):
        r = Rect(0, 0, 10, 10)
        assert r.contains_point(5, 5)

    def test_contains_point_on_edge(self):
        r = Rect(0, 0, 10, 10)
        assert r.contains_point(0, 0)  # Top-left corner included
        assert not r.contains_point(10, 10)  # Bottom-right excluded

    def test_contains_rect(self):
        outer = Rect(0, 0, 100, 100)
        inner = Rect(10, 10, 50, 50)
        assert outer.contains_rect(inner)
        assert not inner.contains_rect(outer)


class TestSpatialIndex:
    def test_insert_and_query(self):
        index = SpatialIndex()
        index.insert("item1", Rect(0, 0, 10, 10))
        index.insert("item2", Rect(100, 100, 10, 10))

        # Query that intersects item1 only
        result = index.query(Rect(-5, -5, 20, 20))
        assert result == {"item1"}

        # Query that intersects item2 only
        result = index.query(Rect(95, 95, 20, 20))
        assert result == {"item2"}

    def test_query_multiple_items(self):
        index = SpatialIndex()
        index.insert("item1", Rect(0, 0, 50, 50))
        index.insert("item2", Rect(25, 25, 50, 50))
        index.insert("item3", Rect(100, 100, 10, 10))

        # Query that intersects both item1 and item2
        result = index.query(Rect(20, 20, 20, 20))
        assert result == {"item1", "item2"}

    def test_query_no_matches(self):
        index = SpatialIndex()
        index.insert("item1", Rect(0, 0, 10, 10))

        result = index.query(Rect(1000, 1000, 10, 10))
        assert result == set()

    def test_remove_item(self):
        index = SpatialIndex()
        index.insert("item1", Rect(0, 0, 10, 10))

        assert index.remove("item1")
        assert index.query(Rect(-5, -5, 20, 20)) == set()

    def test_remove_nonexistent(self):
        index = SpatialIndex()
        assert not index.remove("nonexistent")

    def test_update_item(self):
        index = SpatialIndex()
        index.insert("item1", Rect(0, 0, 10, 10))

        # Move item to new location
        index.update("item1", Rect(100, 100, 10, 10))

        # Should not find at old location
        assert index.query(Rect(-5, -5, 20, 20)) == set()

        # Should find at new location
        assert index.query(Rect(95, 95, 20, 20)) == {"item1"}

    def test_clear(self):
        index = SpatialIndex()
        index.insert("item1", Rect(0, 0, 10, 10))
        index.insert("item2", Rect(50, 50, 10, 10))

        index.clear()

        assert len(index) == 0
        assert index.query(Rect(-1000, -1000, 2000, 2000)) == set()

    def test_len(self):
        index = SpatialIndex()
        assert len(index) == 0

        index.insert("item1", Rect(0, 0, 10, 10))
        assert len(index) == 1

        index.insert("item2", Rect(50, 50, 10, 10))
        assert len(index) == 2

        index.remove("item1")
        assert len(index) == 1

    def test_contains(self):
        index = SpatialIndex()
        index.insert("item1", Rect(0, 0, 10, 10))

        assert "item1" in index
        assert "item2" not in index

    def test_query_all(self):
        index = SpatialIndex()
        index.insert("item1", Rect(0, 0, 10, 10))
        index.insert("item2", Rect(100, 100, 10, 10))

        assert index.query_all() == {"item1", "item2"}

    def test_large_number_of_items(self):
        """Performance test: ensure index handles many items."""
        index = SpatialIndex(max_items_per_node=4, max_depth=8)

        # Insert 1000 items in a grid
        for i in range(100):
            for j in range(10):
                item_id = f"item_{i}_{j}"
                index.insert(item_id, Rect(i * 100, j * 100, 50, 50))

        assert len(index) == 1000

        # Query a small region
        result = index.query(Rect(450, 450, 100, 100))
        # Should find items near (450, 450) - items at positions 4,4 and 5,5 etc.
        assert len(result) > 0
        assert len(result) < 100  # Should be a small subset

    def test_overlapping_items(self):
        """Items can overlap and both should be returned."""
        index = SpatialIndex()
        index.insert("item1", Rect(0, 0, 100, 100))
        index.insert("item2", Rect(0, 0, 100, 100))  # Same bounds

        result = index.query(Rect(50, 50, 10, 10))
        assert result == {"item1", "item2"}

    def test_negative_coordinates(self):
        """Index should handle negative coordinates."""
        index = SpatialIndex()
        index.insert("item1", Rect(-100, -100, 50, 50))

        result = index.query(Rect(-120, -120, 100, 100))
        assert result == {"item1"}

    def test_item_spanning_quadrants(self):
        """Large items that span multiple quadrants."""
        index = SpatialIndex(
            world_bounds=Rect(-1000, -1000, 2000, 2000),
            max_items_per_node=2,
        )

        # Insert a large item centered at origin (-500,-500) to (500,500)
        index.insert("big", Rect(-500, -500, 1000, 1000))

        # Query regions that intersect different corners of the big item
        # Top-left quadrant query
        assert index.query(Rect(-600, -600, 200, 200)) == {"big"}
        # Bottom-right quadrant query
        assert index.query(Rect(400, 400, 200, 200)) == {"big"}
        # Top-right quadrant query
        assert index.query(Rect(400, -600, 200, 200)) == {"big"}
        # Bottom-left quadrant query
        assert index.query(Rect(-600, 400, 200, 200)) == {"big"}

        # Query outside the big item should return empty
        assert index.query(Rect(-800, -800, 100, 100)) == set()
