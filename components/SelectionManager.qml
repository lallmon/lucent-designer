pragma Singleton

import QtQuick

QtObject {
    property int selectedItemIndex: -1
    property var selectedItem: null
    property var selectedIndices: []

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
