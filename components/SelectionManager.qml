// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

pragma Singleton

import QtQuick

QtObject {
    property int selectedItemIndex: -1
    property var selectedItem: null
    property var selectedIndices: []

    function hasSelection() {
        return ((selectedIndices && selectedIndices.length > 0) || selectedItemIndex >= 0);
    }

    function currentSelectionIndices() {
        var indices = selectedIndices || [];
        if (indices.length > 0) {
            return indices.slice();
        }
        if (selectedItemIndex >= 0) {
            return [selectedItemIndex];
        }
        return [];
    }

    function setSelection(indices) {
        var next = indices ? indices.slice() : [];
        selectedIndices = next;
        var primary = next.length > 0 ? next[next.length - 1] : -1;
        selectedItemIndex = primary;
        selectedItem = primary >= 0 ? canvasModel.getItemData(primary) : null;
    }

    function toggleSelection(index, multi) {
        if (index < 0) {
            if (!multi) {
                setSelection([]);
            }
            return;
        }
        var next = selectedIndices ? selectedIndices.slice() : [];
        if (multi) {
            var pos = next.indexOf(index);
            if (pos >= 0) {
                next.splice(pos, 1);
            } else {
                next.push(index);
            }
        } else {
            next = [index];
        }
        setSelection(next);
    }

    Component.onCompleted: {
        canvasModel.itemModified.connect(function (index, data) {
            if (index === selectedItemIndex) {
                selectedItem = data;
            }
        });

        canvasModel.itemRemoved.connect(function (index) {
            // Adjust multi-selection
            var next = [];
            for (var i = 0; i < selectedIndices.length; i++) {
                var val = selectedIndices[i];
                if (val === index) {
                    continue;
                } else if (val > index) {
                    next.push(val - 1);
                } else {
                    next.push(val);
                }
            }
            selectedIndices = next;

            // Clear selection when the selected item is removed
            if (index === selectedItemIndex) {
                selectedItemIndex = selectedIndices.length > 0 ? selectedIndices[selectedIndices.length - 1] : -1;
                selectedItem = selectedItemIndex >= 0 ? canvasModel.getItemData(selectedItemIndex) : null;
            } else if (index < selectedItemIndex) {
                // Shift selection when a preceding item is removed
                selectedItemIndex = selectedItemIndex - 1;
                selectedItem = selectedItemIndex >= 0 ? canvasModel.getItemData(selectedItemIndex) : null;
            }
        });

        canvasModel.itemsCleared.connect(function () {
            selectedItemIndex = -1;
            selectedItem = null;
            selectedIndices = [];
        });
    }
}
