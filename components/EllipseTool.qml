import QtQuick
import QtQuick.Controls

// Ellipse drawing tool component
Item {
    id: tool

    // Properties passed from Canvas
    property real zoomLevel: 1.0
    property bool active: false
    property var settings: null  // Tool settings object

    TwoPointToolHelper {
        id: helper
    }
    property var currentEllipse: null

    // Signal emitted when an item is completed
    signal itemCompleted(var itemData)

    // Starting point indicator (black dot shown during ellipse drawing)
    Rectangle {
        id: startPointIndicator
        visible: helper.isDrawing
        x: helper.startX - (6 / tool.zoomLevel)
        y: helper.startY - (6 / tool.zoomLevel)
        width: 12 / tool.zoomLevel
        height: 12 / tool.zoomLevel
        radius: 6 / tool.zoomLevel
        color: "black"
        border.color: "white"
        border.width: 1 / tool.zoomLevel
    }

    // Preview ellipse (shown while drawing)
    Item {
        id: previewEllipse

        // Enable layer smoothing to match QPainter antialiasing
        layer.enabled: true
        layer.smooth: true

        property real strokeW: (settings ? settings.strokeWidth : 1) / tool.zoomLevel
        property real halfStroke: strokeW / 2

        visible: tool.currentEllipse !== null && tool.currentEllipse !== undefined && tool.currentEllipse.width > 0 && tool.currentEllipse.height > 0

        // Position accounts for stroke extending outward
        x: (tool.currentEllipse ? tool.currentEllipse.x : 0) - halfStroke
        y: (tool.currentEllipse ? tool.currentEllipse.y : 0) - halfStroke
        width: (tool.currentEllipse ? tool.currentEllipse.width : 0) + strokeW
        height: (tool.currentEllipse ? tool.currentEllipse.height : 0) + strokeW

        // Ellipse drawn with Canvas
        Canvas {
            id: dashedCanvas
            anchors.fill: parent

            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height);

                if (width > 0 && height > 0 && settings) {
                    var centerX = width / 2;
                    var centerY = height / 2;
                    // Radii account for the stroke width being part of the parent size
                    var radiusX = (width - previewEllipse.strokeW) / 2;
                    var radiusY = (height - previewEllipse.strokeW) / 2;

                    ctx.save();
                    ctx.translate(centerX, centerY);
                    ctx.scale(radiusX, radiusY);
                    ctx.beginPath();
                    ctx.arc(0, 0, 1, 0, 2 * Math.PI, false);
                    ctx.restore();

                    var fillColor = Qt.color(settings.fillColor);
                    fillColor.a = settings.fillOpacity;
                    ctx.fillStyle = fillColor;
                    ctx.fill();

                    var strokeColor = Qt.color(settings.strokeColor);
                    strokeColor.a = settings.strokeOpacity !== undefined ? settings.strokeOpacity : 1.0;
                    ctx.strokeStyle = strokeColor;
                    ctx.lineWidth = previewEllipse.strokeW;
                    ctx.stroke();
                }
            }

            Component.onCompleted: requestPaint()

            Connections {
                target: previewEllipse
                function onWidthChanged() {
                    dashedCanvas.requestPaint();
                }
                function onHeightChanged() {
                    dashedCanvas.requestPaint();
                }
                function onVisibleChanged() {
                    if (previewEllipse.visible)
                        dashedCanvas.requestPaint();
                }
            }

            Connections {
                target: tool
                function onZoomLevelChanged() {
                    dashedCanvas.requestPaint();
                }
                function onSettingsChanged() {
                    dashedCanvas.requestPaint();
                }
            }
        }
    }

    // Handle clicks for ellipse drawing (two-click pattern like rectangle tool)
    function handleClick(canvasX, canvasY) {
        if (!tool.active)
            return;

        if (!helper.isDrawing) {
            // First click: Start drawing an ellipse
            helper.begin(canvasX, canvasY);

            // Initialize ellipse at start point with minimal size
            currentEllipse = {
                x: helper.startX,
                y: helper.startY,
                width: 1,
                height: 1
            };
        } else {
            // Second click: Finalize the ellipse
            if (helper.hasSize(currentEllipse)) {
                // Convert bounding box to center and radii
                var centerX = currentEllipse.x + currentEllipse.width / 2;
                var centerY = currentEllipse.y + currentEllipse.height / 2;
                var radiusX = currentEllipse.width / 2;
                var radiusY = currentEllipse.height / 2;

                var style = helper.extractStyle(settings);
                // Create complete item data object with new format
                var itemData = {
                    type: "ellipse",
                    geometry: {
                        centerX: centerX,
                        centerY: centerY,
                        radiusX: radiusX,
                        radiusY: radiusY
                    },
                    appearances: [
                        {
                            type: "fill",
                            color: style.fillColor,
                            opacity: style.fillOpacity,
                            visible: true
                        },
                        {
                            type: "stroke",
                            color: style.strokeColor,
                            width: style.strokeWidth,
                            opacity: style.strokeOpacity,
                            visible: true
                        }
                    ]
                };

                // Emit signal with complete item data
                itemCompleted(itemData);
            }

            // Clear current ellipse and reset drawing state
            currentEllipse = null;
            helper.reset();
        }
    }

    // Update preview during mouse movement
    function handleMouseMove(canvasX, canvasY, modifiers) {
        if (!tool.active || !helper.isDrawing)
            return;

        // Calculate distance from start point to current point
        var deltaX = canvasX - helper.startX;
        var deltaY = canvasY - helper.startY;
        var ellipseWidth = Math.abs(deltaX);
        var ellipseHeight = Math.abs(deltaY);

        // Constrain to circle when Shift is held
        if (modifiers & Qt.ShiftModifier) {
            var size = Math.max(ellipseWidth, ellipseHeight);
            ellipseWidth = size;
            ellipseHeight = size;
        }

        // Calculate position based on Alt (center mode) or corner mode
        var ellipseX, ellipseY;
        if (modifiers & Qt.AltModifier) {
            // Alt: draw from center - double the dimensions
            ellipseWidth *= 2;
            ellipseHeight *= 2;
            ellipseX = helper.startX - ellipseWidth / 2;
            ellipseY = helper.startY - ellipseHeight / 2;
        } else {
            // Normal: draw from corner
            ellipseX = deltaX >= 0 ? helper.startX : helper.startX - ellipseWidth;
            ellipseY = deltaY >= 0 ? helper.startY : helper.startY - ellipseHeight;
        }

        // Update current ellipse (create new object to trigger binding)
        currentEllipse = {
            x: ellipseX,
            y: ellipseY,
            width: ellipseWidth,
            height: ellipseHeight
        };
    }

    // Reset tool state (called when switching tools)
    function reset() {
        helper.reset();
        currentEllipse = null;
    }
}
