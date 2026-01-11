# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Hierarchy helper functions for canvas item parent-child relationships.

This module provides pure functions for working with container hierarchies
(layers, groups) without Qt dependencies, making them easily testable.
"""

from typing import List, Optional, Callable, Any


def get_container_by_id(
    items: List[Any],
    container_id: Optional[str],
    is_container: Callable[[Any], bool],
) -> Optional[Any]:
    """Find a container item by its ID.

    Args:
        items: List of canvas items to search.
        container_id: The ID to search for, or None.
        is_container: Predicate to check if an item is a container.

    Returns:
        The container item if found, None otherwise.
    """
    if not container_id:
        return None
    for candidate in items:
        if is_container(candidate) and getattr(candidate, "id", None) == container_id:
            return candidate
    return None


def get_direct_children_indices(
    items: List[Any],
    container_id: str,
) -> List[int]:
    """Get indices of items that are direct children of a container.

    Args:
        items: List of canvas items.
        container_id: The parent container ID.

    Returns:
        List of indices of direct children.
    """
    return [
        i
        for i, child in enumerate(items)
        if getattr(child, "parent_id", None) == container_id
    ]


def get_descendant_indices(
    items: List[Any],
    container_id: str,
    is_container: Callable[[Any], bool],
) -> List[int]:
    """Get indices of all descendants (any depth) of a container.

    Args:
        items: List of canvas items.
        container_id: The ancestor container ID.
        is_container: Predicate to check if an item is a container.

    Returns:
        List of indices of all descendants.
    """
    result: List[int] = []
    queue = list(get_direct_children_indices(items, container_id))
    while queue:
        idx = queue.pop(0)
        result.append(idx)
        child = items[idx]
        child_id = getattr(child, "id", None)
        if is_container(child) and child_id:
            queue.extend(get_direct_children_indices(items, child_id))
    return result


def is_descendant_of(
    items: List[Any],
    candidate_id: Optional[str],
    ancestor_id: str,
    is_container: Callable[[Any], bool],
) -> bool:
    """Check if a container is a descendant of another container.

    Args:
        items: List of canvas items.
        candidate_id: ID of the potential descendant container.
        ancestor_id: ID of the potential ancestor container.
        is_container: Predicate to check if an item is a container.

    Returns:
        True if candidate is a descendant of ancestor, False otherwise.
    """
    current = get_container_by_id(items, candidate_id, is_container)
    visited: set[str] = set()
    while current and getattr(current, "id", None) not in visited:
        current_id = getattr(current, "id", None)
        if current_id:
            visited.add(current_id)
        parent_id = getattr(current, "parent_id", None)
        if parent_id == ancestor_id:
            return True
        current = get_container_by_id(items, parent_id, is_container)
    return False


def is_effectively_visible(
    items: List[Any],
    index: int,
    is_container: Callable[[Any], bool],
) -> bool:
    """Check if an item is visible considering parent visibility.

    An item is effectively visible if it and all its ancestors are visible.

    Args:
        items: List of canvas items.
        index: Index of the item to check.
        is_container: Predicate to check if an item is a container.

    Returns:
        True if the item is effectively visible, False otherwise.
    """
    if not (0 <= index < len(items)):
        return False
    item = items[index]
    if not getattr(item, "visible", True):
        return False
    parent_id = getattr(item, "parent_id", None)
    if not parent_id:
        return True
    parent = get_container_by_id(items, parent_id, is_container)
    if not parent:
        return True
    try:
        parent_index = items.index(parent)
    except ValueError:
        return True
    return is_effectively_visible(items, parent_index, is_container)


def is_effectively_locked(
    items: List[Any],
    index: int,
    is_container: Callable[[Any], bool],
) -> bool:
    """Check if an item is locked considering parent lock status.

    An item is effectively locked if it or any of its ancestors is locked.

    Args:
        items: List of canvas items.
        index: Index of the item to check.
        is_container: Predicate to check if an item is a container.

    Returns:
        True if the item is effectively locked, False otherwise.
    """
    if not (0 <= index < len(items)):
        return False
    item = items[index]
    if getattr(item, "locked", False):
        return True
    parent_id = getattr(item, "parent_id", None)
    if not parent_id:
        return False
    parent = get_container_by_id(items, parent_id, is_container)
    if not parent:
        return False
    try:
        parent_index = items.index(parent)
    except ValueError:
        return False
    return is_effectively_locked(items, parent_index, is_container)
