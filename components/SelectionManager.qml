pragma Singleton

import QtQuick

// Singleton for managing object selection state across the application
QtObject {
    // Index of the currently selected item (-1 means no selection)
    property int selectedItemIndex: -1
    
    // The actual selected item object (null when no selection)
    property var selectedItem: null
}



