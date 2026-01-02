"""
Selection state helpers for multi-select logic.
"""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple


def toggle_selection(
    selected_indices: Sequence[int], hit_index: int, multi: bool
) -> List[int]:
    """
    Update selection set given a hit index and multi-select flag.

    Args:
        selected_indices: current selection indices
        hit_index: index that was clicked/hit
        multi: whether multi-select (toggle) behavior is requested
    """
    current = list(selected_indices)
    if hit_index < 0:
        return [] if not multi else current
    if not multi:
        return [hit_index]
    if hit_index in current:
        current = [i for i in current if i != hit_index]
    else:
        current.append(hit_index)
    return current


def union_bounds(bounds_list: Iterable[Tuple[float, float, float, float]]):
    """Compute axis-aligned union bounds for a list of (x, y, w, h) tuples."""
    iterator = iter(bounds_list)
    try:
        first = next(iterator)
    except StopIteration:
        return None
    min_x, min_y, w, h = first
    max_x = min_x + w
    max_y = min_y + h
    for x, y, width, height in iterator:
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x + width)
        max_y = max(max_y, y + height)
    return (min_x, min_y, max_x - min_x, max_y - min_y)
