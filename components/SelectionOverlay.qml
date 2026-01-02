import QtQuick

// Renders a bounding box for the currently selected item in canvas coordinates.
Rectangle {
    id: selectionOverlay

    property var selectedItem
    property var boundsOverride
    property real zoomLevel: 1.0
    property real selectionPadding: 8
    property color accentColor: "lightblue"

    readonly property bool _hasBounds: boundsOverride !== null && boundsOverride !== undefined

    visible: selectedItem !== null && selectedItem !== undefined

    x: {
        if (!visible)
            return 0;
        if (_hasBounds) {
            return boundsOverride.x - selectionPadding;
        }
        if (selectedItem.type === "rectangle") {
            return selectedItem.x - selectionPadding;
        } else if (selectedItem.type === "ellipse") {
            return selectedItem.centerX - selectedItem.radiusX - selectionPadding;
        }
        return 0;
    }

    y: {
        if (!visible)
            return 0;
        if (_hasBounds) {
            return boundsOverride.y - selectionPadding;
        }
        if (selectedItem.type === "rectangle") {
            return selectedItem.y - selectionPadding;
        } else if (selectedItem.type === "ellipse") {
            return selectedItem.centerY - selectedItem.radiusY - selectionPadding;
        }
        return 0;
    }

    width: {
        if (!visible)
            return 0;
        if (_hasBounds) {
            return boundsOverride.width + selectionPadding * 2;
        }
        if (selectedItem.type === "rectangle") {
            return selectedItem.width + selectionPadding * 2;
        } else if (selectedItem.type === "ellipse") {
            return selectedItem.radiusX * 2 + selectionPadding * 2;
        }
        return 0;
    }

    height: {
        if (!visible)
            return 0;
        if (_hasBounds) {
            return boundsOverride.height + selectionPadding * 2;
        }
        if (selectedItem.type === "rectangle") {
            return selectedItem.height + selectionPadding * 2;
        } else if (selectedItem.type === "ellipse") {
            return selectedItem.radiusY * 2 + selectionPadding * 2;
        }
        return 0;
    }

    color: "transparent"
    border.color: accentColor
    border.width: (zoomLevel > 0 ? 2 / zoomLevel : 0)
}
