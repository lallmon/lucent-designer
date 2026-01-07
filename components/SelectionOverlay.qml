import QtQuick
import "." as Lucent

// Renders a bounding box for the currently selected item in canvas coordinates.
// The overlay rotates with the shape's transform.
Rectangle {
    id: selectionOverlay

    property var geometryBounds  // Object with x, y, width, height (untransformed)
    property var itemTransform   // Transform object with rotate, translateX, etc.
    property real zoomLevel: 1.0
    property real selectionPadding: 0
    property color accentColor: Lucent.Themed.selector

    readonly property real _geomX: geometryBounds ? geometryBounds.x : 0
    readonly property real _geomY: geometryBounds ? geometryBounds.y : 0
    readonly property real _geomWidth: geometryBounds ? geometryBounds.width : 0
    readonly property real _geomHeight: geometryBounds ? geometryBounds.height : 0

    readonly property real _rotation: itemTransform ? (itemTransform.rotate || 0) : 0
    readonly property real _translateX: itemTransform ? (itemTransform.translateX || 0) : 0
    readonly property real _translateY: itemTransform ? (itemTransform.translateY || 0) : 0
    readonly property real _originX: itemTransform ? (itemTransform.originX || 0) : 0
    readonly property real _originY: itemTransform ? (itemTransform.originY || 0) : 0

    visible: geometryBounds !== null && geometryBounds !== undefined

    x: _geomX - selectionPadding + _translateX
    y: _geomY - selectionPadding + _translateY
    width: _geomWidth + selectionPadding * 2
    height: _geomHeight + selectionPadding * 2

    color: "transparent"
    border.color: accentColor
    border.width: (zoomLevel > 0 ? 1 / zoomLevel : 0)

    transform: Rotation {
        origin.x: selectionOverlay.width * selectionOverlay._originX
        origin.y: selectionOverlay.height * selectionOverlay._originY
        angle: selectionOverlay._rotation
    }
}
