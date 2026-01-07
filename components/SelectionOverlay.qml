import QtQuick
import "." as Lucent

// Renders a bounding box for the currently selected item in canvas coordinates.
Rectangle {
    id: selectionOverlay

    property var selectedItem
    property var boundsOverride
    property real zoomLevel: 1.0
    property real selectionPadding: 0
    property color accentColor: Lucent.Themed.selector

    readonly property bool _hasBounds: boundsOverride !== null && boundsOverride !== undefined
    readonly property var _geom: selectedItem ? selectedItem.geometry : null

    visible: selectedItem !== null && selectedItem !== undefined

    x: {
        if (!visible)
            return 0;
        if (_hasBounds) {
            return boundsOverride.x - selectionPadding;
        }
        if (_geom && selectedItem.type === "rectangle") {
            return _geom.x - selectionPadding;
        } else if (_geom && selectedItem.type === "ellipse") {
            return _geom.centerX - _geom.radiusX - selectionPadding;
        }
        return 0;
    }

    y: {
        if (!visible)
            return 0;
        if (_hasBounds) {
            return boundsOverride.y - selectionPadding;
        }
        if (_geom && selectedItem.type === "rectangle") {
            return _geom.y - selectionPadding;
        } else if (_geom && selectedItem.type === "ellipse") {
            return _geom.centerY - _geom.radiusY - selectionPadding;
        }
        return 0;
    }

    width: {
        if (!visible)
            return 0;
        if (_hasBounds) {
            return boundsOverride.width + selectionPadding * 2;
        }
        if (_geom && selectedItem.type === "rectangle") {
            return _geom.width + selectionPadding * 2;
        } else if (_geom && selectedItem.type === "ellipse") {
            return _geom.radiusX * 2 + selectionPadding * 2;
        }
        return 0;
    }

    height: {
        if (!visible)
            return 0;
        if (_hasBounds) {
            return boundsOverride.height + selectionPadding * 2;
        }
        if (_geom && selectedItem.type === "rectangle") {
            return _geom.height + selectionPadding * 2;
        } else if (_geom && selectedItem.type === "ellipse") {
            return _geom.radiusY * 2 + selectionPadding * 2;
        }
        return 0;
    }

    color: "transparent"
    border.color: accentColor
    border.width: (zoomLevel > 0 ? 1 / zoomLevel : 0)
}
