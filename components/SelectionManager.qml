pragma Singleton

import QtQuick

QtObject {
    property int selectedItemIndex: -1
    property var selectedItem: null
    
    Component.onCompleted: {
        canvasModel.itemModified.connect(function(index, data) {
            if (index === selectedItemIndex) {
                selectedItem = data
            }
        })

        canvasModel.itemRemoved.connect(function(index) {
            // Clear selection when the selected item is removed
            if (index === selectedItemIndex) {
                selectedItemIndex = -1
                selectedItem = null
            } else if (index < selectedItemIndex) {
                // Shift selection when a preceding item is removed
                selectedItemIndex = selectedItemIndex - 1
            }
        })

        canvasModel.itemsCleared.connect(function() {
            selectedItemIndex = -1
            selectedItem = null
        })
    }
}

