# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Quadtree spatial index for fast viewport queries.

This module provides a Quadtree data structure optimized for 2D spatial
queries, enabling efficient O(log n + k) lookups for items intersecting
a given rectangle (e.g., viewport or tile bounds).
"""

from dataclasses import dataclass, field
from typing import List, Set, Optional, Any, Dict


@dataclass
class Rect:
    """Axis-aligned bounding rectangle."""

    x: float
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    def intersects(self, other: "Rect") -> bool:
        """Check if this rectangle intersects another."""
        return not (
            self.right <= other.x
            or other.right <= self.x
            or self.bottom <= other.y
            or other.bottom <= self.y
        )

    def contains_point(self, px: float, py: float) -> bool:
        """Check if a point is inside this rectangle."""
        return self.x <= px < self.right and self.y <= py < self.bottom

    def contains_rect(self, other: "Rect") -> bool:
        """Check if this rectangle fully contains another."""
        return (
            self.x <= other.x
            and self.right >= other.right
            and self.y <= other.y
            and self.bottom >= other.bottom
        )

    @classmethod
    def from_qrectf(cls, qrect: Any) -> "Rect":
        """Create from a QRectF."""
        return cls(
            x=qrect.x(),
            y=qrect.y(),
            width=qrect.width(),
            height=qrect.height(),
        )


@dataclass
class QuadTreeNode:
    """A node in the quadtree."""

    bounds: Rect
    max_items: int = 8
    max_depth: int = 8
    depth: int = 0

    # Items stored in this node (leaf nodes only)
    items: Dict[Any, Rect] = field(default_factory=dict)

    # Child nodes (None if leaf, 4 children if subdivided)
    children: Optional[List["QuadTreeNode"]] = None

    def is_leaf(self) -> bool:
        return self.children is None

    def subdivide(self) -> None:
        """Split this node into 4 quadrants."""
        if self.children is not None:
            return

        half_w = self.bounds.width / 2
        half_h = self.bounds.height / 2
        x, y = self.bounds.x, self.bounds.y

        self.children = [
            # NW (top-left)
            QuadTreeNode(
                bounds=Rect(x, y, half_w, half_h),
                max_items=self.max_items,
                max_depth=self.max_depth,
                depth=self.depth + 1,
            ),
            # NE (top-right)
            QuadTreeNode(
                bounds=Rect(x + half_w, y, half_w, half_h),
                max_items=self.max_items,
                max_depth=self.max_depth,
                depth=self.depth + 1,
            ),
            # SW (bottom-left)
            QuadTreeNode(
                bounds=Rect(x, y + half_h, half_w, half_h),
                max_items=self.max_items,
                max_depth=self.max_depth,
                depth=self.depth + 1,
            ),
            # SE (bottom-right)
            QuadTreeNode(
                bounds=Rect(x + half_w, y + half_h, half_w, half_h),
                max_items=self.max_items,
                max_depth=self.max_depth,
                depth=self.depth + 1,
            ),
        ]

        # Redistribute items to children
        for item_id, item_bounds in list(self.items.items()):
            for child in self.children:
                if child.bounds.intersects(item_bounds):
                    child.items[item_id] = item_bounds
        self.items.clear()

    def insert(self, item_id: Any, item_bounds: Rect) -> None:
        """Insert an item into the quadtree."""
        if not self.bounds.intersects(item_bounds):
            return

        if self.is_leaf():
            self.items[item_id] = item_bounds

            # Subdivide if we exceed capacity and haven't hit max depth
            if len(self.items) > self.max_items and self.depth < self.max_depth:
                self.subdivide()
        else:
            # Insert into children that intersect
            for child in self.children:  # type: ignore
                if child.bounds.intersects(item_bounds):
                    child.insert(item_id, item_bounds)

    def remove(self, item_id: Any) -> bool:
        """Remove an item from the quadtree. Returns True if found."""
        if self.is_leaf():
            if item_id in self.items:
                del self.items[item_id]
                return True
            return False
        else:
            found = False
            for child in self.children:  # type: ignore
                if child.remove(item_id):
                    found = True
            return found

    def query(self, query_bounds: Rect) -> Set[Any]:
        """Find all items that intersect the query bounds."""
        result: Set[Any] = set()

        if not self.bounds.intersects(query_bounds):
            return result

        if self.is_leaf():
            for item_id, item_bounds in self.items.items():
                if query_bounds.intersects(item_bounds):
                    result.add(item_id)
        else:
            for child in self.children:  # type: ignore
                result.update(child.query(query_bounds))

        return result

    def clear(self) -> None:
        """Remove all items from this node and children."""
        self.items.clear()
        if self.children:
            for child in self.children:
                child.clear()
        self.children = None


class SpatialIndex:
    """
    Spatial index for canvas items using a quadtree.

    Provides fast O(log n + k) queries for finding items that intersect
    a given rectangle, where n is total items and k is matching items.
    """

    def __init__(
        self,
        world_bounds: Optional[Rect] = None,
        max_items_per_node: int = 8,
        max_depth: int = 10,
    ) -> None:
        """
        Initialize the spatial index.

        Args:
            world_bounds: The bounds of the entire canvas world.
                         If None, uses a large default.
            max_items_per_node: Max items before a node subdivides.
            max_depth: Maximum tree depth to prevent infinite subdivision.
        """
        if world_bounds is None:
            # Default to a large canvas area centered at origin
            world_bounds = Rect(-100000, -100000, 200000, 200000)

        self._root = QuadTreeNode(
            bounds=world_bounds,
            max_items=max_items_per_node,
            max_depth=max_depth,
        )
        # Track item bounds for updates
        self._item_bounds: Dict[Any, Rect] = {}

    def insert(self, item_id: Any, bounds: Rect) -> None:
        """Insert an item with its bounding rectangle."""
        # Remove old entry if updating
        if item_id in self._item_bounds:
            self.remove(item_id)

        self._item_bounds[item_id] = bounds
        self._root.insert(item_id, bounds)

    def remove(self, item_id: Any) -> bool:
        """Remove an item by its ID. Returns True if found."""
        if item_id not in self._item_bounds:
            return False

        del self._item_bounds[item_id]
        return self._root.remove(item_id)

    def update(self, item_id: Any, new_bounds: Rect) -> None:
        """Update an item's bounds (remove + reinsert)."""
        self.remove(item_id)
        self.insert(item_id, new_bounds)

    def query(self, query_bounds: Rect) -> Set[Any]:
        """Find all items that intersect the query bounds."""
        return self._root.query(query_bounds)

    def query_all(self) -> Set[Any]:
        """Return all item IDs in the index."""
        return set(self._item_bounds.keys())

    def clear(self) -> None:
        """Remove all items from the index."""
        self._root.clear()
        self._item_bounds.clear()

    def __len__(self) -> int:
        """Return the number of items in the index."""
        return len(self._item_bounds)

    def __contains__(self, item_id: Any) -> bool:
        """Check if an item is in the index."""
        return item_id in self._item_bounds
