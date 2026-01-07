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

    // Extract geometry bounds (from model via Canvas)
    readonly property real _geomX: geometryBounds ? geometryBounds.x : 0
    readonly property real _geomY: geometryBounds ? geometryBounds.y : 0
    readonly property real _geomWidth: geometryBounds ? geometryBounds.width : 0
    readonly property real _geomHeight: geometryBounds ? geometryBounds.height : 0

    // Transform values
    readonly property real _rotation: itemTransform ? (itemTransform.rotate || 0) : 0
    readonly property real _translateX: itemTransform ? (itemTransform.translateX || 0) : 0
    readonly property real _translateY: itemTransform ? (itemTransform.translateY || 0) : 0

    visible: geometryBounds !== null && geometryBounds !== undefined

    // Position at geometry bounds (will be adjusted by transform)
    x: _geomX - selectionPadding + _translateX
    y: _geomY - selectionPadding + _translateY
    width: _geomWidth + selectionPadding * 2
    height: _geomHeight + selectionPadding * 2

    color: "transparent"
    border.color: accentColor
    border.width: (zoomLevel > 0 ? 1 / zoomLevel : 0)

    // Apply rotation around the center of the geometry
    transform: Rotation {
        origin.x: selectionOverlay.width / 2
        origin.y: selectionOverlay.height / 2
        angle: selectionOverlay._rotation
    }
}
