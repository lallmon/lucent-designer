import QtQuick
import QtQuick.Shapes
import ".." as Lucent

// Renders a bounding box for the currently selected item in canvas coordinates.
// The overlay transforms with the shape (translate, rotate, scale around origin).
// Uses Shape/ShapePath for better thin line rendering at all zoom levels.
Shape {
    id: selectionOverlay

    property var geometryBounds  // Object with x, y, width, height (untransformed)
    property var itemTransform   // Transform object with rotate, translateX, scaleX, etc.
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
    readonly property real _scaleX: itemTransform ? (itemTransform.scaleX || 1) : 1
    readonly property real _scaleY: itemTransform ? (itemTransform.scaleY || 1) : 1
    readonly property real _originX: itemTransform ? (itemTransform.originX || 0) : 0
    readonly property real _originY: itemTransform ? (itemTransform.originY || 0) : 0

    visible: geometryBounds !== null && geometryBounds !== undefined

    x: _geomX - selectionPadding + _translateX
    y: _geomY - selectionPadding + _translateY
    width: _geomWidth + selectionPadding * 2
    height: _geomHeight + selectionPadding * 2

    transform: [
        Scale {
            origin.x: selectionOverlay.width * selectionOverlay._originX
            origin.y: selectionOverlay.height * selectionOverlay._originY
            xScale: selectionOverlay._scaleX
            yScale: selectionOverlay._scaleY
        },
        Rotation {
            origin.x: selectionOverlay.width * selectionOverlay._originX
            origin.y: selectionOverlay.height * selectionOverlay._originY
            angle: selectionOverlay._rotation
        }
    ]

    // ShapePath provides better thin line rendering than Rectangle border
    ShapePath {
        strokeColor: selectionOverlay.accentColor
        strokeWidth: selectionOverlay.zoomLevel > 0 ? 1 / selectionOverlay.zoomLevel : 0
        fillColor: "transparent"
        joinStyle: ShapePath.MiterJoin
        capStyle: ShapePath.FlatCap

        // Draw closed rectangle path
        startX: 0
        startY: 0
        PathLine {
            x: selectionOverlay.width
            y: 0
        }
        PathLine {
            x: selectionOverlay.width
            y: selectionOverlay.height
        }
        PathLine {
            x: 0
            y: selectionOverlay.height
        }
        PathLine {
            x: 0
            y: 0
        }
    }
}
