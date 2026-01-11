# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Render query utilities for canvas items.

This module provides pure functions for querying items for rendering
and hit testing without Qt dependencies, making them easily testable.
"""

from typing import List, Any, Callable, Dict


def get_render_items(
    items: List[Any],
    is_container: Callable[[Any], bool],
    is_renderable: Callable[[Any], bool],
    is_visible: Callable[[int], bool],
) -> List[Any]:
    """Get items in render order (bottom to top) skipping containers.

    Model order is treated as bottom-to-top z-order: lower indices are
    beneath higher indices. Rendering should iterate this list in order
    so later items naturally paint over earlier ones.

    Args:
        items: List of all canvas items.
        is_container: Predicate to identify container items (Layer, Group).
        is_renderable: Predicate to identify renderable items.
        is_visible: Predicate to check if item at index is effectively visible.

    Returns:
        List of renderable, visible items in render order.
    """
    ordered: List[Any] = []
    for idx, item in enumerate(items):
        # Skip non-rendering containers but keep model ordering of shapes
        if is_container(item):
            continue
        if is_renderable(item):
            if not is_visible(idx):
                continue
            ordered.append(item)
    return ordered


def get_hit_test_items(
    items: List[Any],
    is_visible: Callable[[int], bool],
    item_to_dict: Callable[[Any], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Get items for hit testing with model indices.

    Args:
        items: List of all canvas items.
        is_visible: Predicate to check if item at index is effectively visible.
        item_to_dict: Function to convert item to dictionary.

    Returns:
        List of item dictionaries with modelIndex attached.
    """
    visible_items: List[Dict[str, Any]] = []
    for idx, item in enumerate(items):
        if is_visible(idx):
            item_dict = item_to_dict(item)
            item_dict["modelIndex"] = idx
            visible_items.append(item_dict)
    return visible_items
