# Copyright (C) 2026 The Culture List, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

from lucent.selection_state import toggle_selection, union_bounds


class TestToggleSelection:
    def test_single_click_replaces_selection(self):
        assert toggle_selection([1, 2], 3, multi=False) == [3]

    def test_multi_add_and_remove(self):
        sel = toggle_selection([], 1, multi=True)
        assert sel == [1]
        sel = toggle_selection(sel, 2, multi=True)
        assert set(sel) == {1, 2}
        sel = toggle_selection(sel, 1, multi=True)
        assert sel == [2]

    def test_click_empty_no_multi_clears(self):
        assert toggle_selection([1], -1, multi=False) == []

    def test_click_empty_with_multi_keeps(self):
        assert toggle_selection([1], -1, multi=True) == [1]


class TestUnionBounds:
    def test_union_empty_returns_none(self):
        assert union_bounds([]) is None

    def test_union_single(self):
        assert union_bounds([(0, 0, 10, 5)]) == (0, 0, 10, 5)

    def test_union_multiple(self):
        result = union_bounds([(0, 0, 2, 2), (3, 1, 2, 3)])
        assert result == (0, 0, 5, 4)
