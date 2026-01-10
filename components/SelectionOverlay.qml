import QtQuick
import QtQuick.Shapes
import "." as Lucent

Shape {
    id: selectionOverlay

    property var geometryBounds
    property var itemTransform
    property real zoomLevel: 1.0
    property real selectionPadding: 0
    property color accentColor: Lucent.Themed.selector

    // Cursor position in canvas coordinates (passed from Canvas)
    property real cursorX: 0
    property real cursorY: 0

    signal resizeRequested(var newBounds)
    signal rotateRequested(real angle)

    property bool shiftPressed: false
    property bool isRotating: false

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

    readonly property real handleSize: 8 / zoomLevel
    readonly property real rotationArmLength: 30 / zoomLevel
    property bool isResizing: false

    ShapePath {
        strokeColor: selectionOverlay.accentColor
        strokeWidth: selectionOverlay.zoomLevel > 0 ? 1 / selectionOverlay.zoomLevel : 0
        fillColor: "transparent"
        joinStyle: ShapePath.MiterJoin
        capStyle: ShapePath.FlatCap

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

    // Rotation arm line from center-top upward
    ShapePath {
        strokeColor: selectionOverlay.accentColor
        strokeWidth: selectionOverlay.zoomLevel > 0 ? 1 / selectionOverlay.zoomLevel : 0
        fillColor: "transparent"

        startX: selectionOverlay.width / 2
        startY: 0
        PathLine {
            x: selectionOverlay.width / 2
            y: -selectionOverlay.rotationArmLength
        }
    }

    // Rotation grip at end of arm
    Rectangle {
        id: rotationGrip
        x: selectionOverlay.width / 2 - selectionOverlay.handleSize / 2
        y: -selectionOverlay.rotationArmLength - selectionOverlay.handleSize / 2
        width: selectionOverlay.handleSize
        height: selectionOverlay.handleSize
        radius: selectionOverlay.handleSize / 2
        color: selectionOverlay.accentColor

        property real startAngle: 0

        DragHandler {
            id: rotationDragHandler
            target: null

            onActiveChanged: {
                selectionOverlay.isRotating = active;
                if (active) {
                    rotationGrip.startAngle = selectionOverlay._rotation;
                }
            }

            onTranslationChanged: {
                if (!active)
                    return;

                // Shape center in canvas coordinates
                var centerX = selectionOverlay._geomX + selectionOverlay._geomWidth / 2;
                var centerY = selectionOverlay._geomY + selectionOverlay._geomHeight / 2;

                // Angle from center to cursor (atan2 with -dy because up is negative Y)
                var dx = selectionOverlay.cursorX - centerX;
                var dy = selectionOverlay.cursorY - centerY;
                var rawAngle = Math.atan2(dx, -dy) * 180 / Math.PI;

                // Snap to 15 degrees if Shift held
                if (selectionOverlay.shiftPressed) {
                    rawAngle = Math.round(rawAngle / 15) * 15;
                }

                selectionOverlay.rotateRequested(rawAngle);
            }
        }
    }

    Repeater {
        model: [
            {
                x: 0,
                y: 0,
                type: "tl"
            },
            {
                x: 0.5,
                y: 0,
                type: "t"
            },
            {
                x: 1,
                y: 0,
                type: "tr"
            },
            {
                x: 1,
                y: 0.5,
                type: "r"
            },
            {
                x: 1,
                y: 1,
                type: "br"
            },
            {
                x: 0.5,
                y: 1,
                type: "b"
            },
            {
                x: 0,
                y: 1,
                type: "bl"
            },
            {
                x: 0,
                y: 0.5,
                type: "l"
            }
        ]

        Rectangle {
            id: handle
            required property var modelData
            required property int index

            x: selectionOverlay.width * modelData.x - selectionOverlay.handleSize / 2
            y: selectionOverlay.height * modelData.y - selectionOverlay.handleSize / 2
            width: selectionOverlay.handleSize
            height: selectionOverlay.handleSize
            radius: selectionOverlay.handleSize / 2
            color: selectionOverlay.accentColor

            property var startBounds: null
            property real startCursorX: 0
            property real startCursorY: 0

            DragHandler {
                id: dragHandler
                target: null

                onActiveChanged: {
                    selectionOverlay.isResizing = active;
                    if (active) {
                        handle.startBounds = {
                            x: selectionOverlay._geomX,
                            y: selectionOverlay._geomY,
                            width: selectionOverlay._geomWidth,
                            height: selectionOverlay._geomHeight
                        };
                        handle.startCursorX = selectionOverlay.cursorX;
                        handle.startCursorY = selectionOverlay.cursorY;
                    }
                }

                onTranslationChanged: {
                    if (!active || !handle.startBounds)
                        return;

                    // Use cursor delta in canvas coordinates for 1:1 movement
                    var dx = selectionOverlay.cursorX - handle.startCursorX;
                    var dy = selectionOverlay.cursorY - handle.startCursorY;
                    var b = handle.startBounds;
                    var t = handle.modelData.type;
                    var newBounds = {
                        x: b.x,
                        y: b.y,
                        width: b.width,
                        height: b.height
                    };

                    // Horizontal resize
                    if (t === "l" || t === "tl" || t === "bl") {
                        newBounds.x = b.x + dx;
                        newBounds.width = Math.max(1, b.width - dx);
                    } else if (t === "r" || t === "tr" || t === "br") {
                        newBounds.width = Math.max(1, b.width + dx);
                    }

                    // Vertical resize
                    if (t === "t" || t === "tl" || t === "tr") {
                        newBounds.y = b.y + dy;
                        newBounds.height = Math.max(1, b.height - dy);
                    } else if (t === "b" || t === "bl" || t === "br") {
                        newBounds.height = Math.max(1, b.height + dy);
                    }

                    selectionOverlay.resizeRequested(newBounds);
                }
            }
        }
    }
}
