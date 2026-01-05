import QtQuick
import QtQuick.Controls
import "." as DV

// Rectangle drawing tool component
Item {
    id: tool

    // Properties passed from Canvas
    property real zoomLevel: 1.0
    property bool active: false
    property var settings: null  // Tool settings object

    TwoPointToolHelper {
        id: helper
    }
    property var currentRect: null

    // Signal emitted when an item is completed
    signal itemCompleted(var itemData)

    // Starting point indicator (black dot shown during rectangle drawing)
    Rectangle {
        id: startPointIndicator
        visible: helper.isDrawing
        x: helper.startX - (6 / tool.zoomLevel)
        y: helper.startY - (6 / tool.zoomLevel)
        width: 12 / tool.zoomLevel
        height: 12 / tool.zoomLevel
        radius: 6 / tool.zoomLevel
        color: DV.Themed.palette.text
        border.color: DV.Themed.palette.base
        border.width: 1 / tool.zoomLevel
    }

    // Preview rectangle (shown while drawing) - using explicit rectangles for reliable rendering
    Item {
        id: previewRect

        // Enable layer smoothing to match QPainter antialiasing
        layer.enabled: true
        layer.smooth: true

        property real strokeW: (settings ? settings.strokeWidth : 1) / tool.zoomLevel
        property color strokeColor: {
            if (!settings)
                return DV.Themed.palette.text;
            var c = Qt.color(settings.strokeColor);
            c.a = settings.strokeOpacity !== undefined ? settings.strokeOpacity : 1.0;
            return c;
        }
        property color fillColor: {
            if (!settings)
                return "transparent";
            var c = Qt.color(settings.fillColor);
            c.a = settings.fillOpacity;
            return c;
        }

        visible: tool.currentRect !== null && tool.currentRect !== undefined && tool.currentRect.width > 0 && tool.currentRect.height > 0

        x: tool.currentRect ? tool.currentRect.x : 0
        y: tool.currentRect ? tool.currentRect.y : 0
        width: tool.currentRect ? tool.currentRect.width : 0
        height: tool.currentRect ? tool.currentRect.height : 0

        // Fill rectangle
        Rectangle {
            anchors.fill: parent
            color: previewRect.fillColor
        }

        // Top border
        Rectangle {
            x: -previewRect.strokeW / 2
            y: -previewRect.strokeW / 2
            width: parent.width + previewRect.strokeW
            height: previewRect.strokeW
            color: previewRect.strokeColor
            radius: 0.5
            antialiasing: true
        }

        // Bottom border
        Rectangle {
            x: -previewRect.strokeW / 2
            y: parent.height - previewRect.strokeW / 2
            width: parent.width + previewRect.strokeW
            height: previewRect.strokeW
            color: previewRect.strokeColor
            radius: 0.5
            antialiasing: true
        }

        // Left border
        Rectangle {
            x: -previewRect.strokeW / 2
            y: previewRect.strokeW / 2
            width: previewRect.strokeW
            height: parent.height - previewRect.strokeW
            color: previewRect.strokeColor
            radius: 0.5
            antialiasing: true
        }

        // Right border
        Rectangle {
            x: parent.width - previewRect.strokeW / 2
            y: previewRect.strokeW / 2
            width: previewRect.strokeW
            height: parent.height - previewRect.strokeW
            color: previewRect.strokeColor
            radius: 0.5
            antialiasing: true
        }
    }

    // Handle clicks for rectangle drawing
    function handleClick(canvasX, canvasY) {
        if (!tool.active)
            return;

        if (!helper.isDrawing) {
            // First click: Start drawing a rectangle
            helper.begin(canvasX, canvasY);

            // Initialize rectangle at start point with minimal size
            currentRect = {
                x: helper.startX,
                y: helper.startY,
                width: 1,
                height: 1
            };
        } else {
            // Second click: Finalize the rectangle
            if (helper.hasSize(currentRect)) {
                var style = helper.extractStyle(settings);
                itemCompleted({
                    type: "rectangle",
                    x: currentRect.x,
                    y: currentRect.y,
                    width: currentRect.width,
                    height: currentRect.height,
                    strokeWidth: style.strokeWidth,
                    strokeColor: style.strokeColor,
                    strokeOpacity: style.strokeOpacity,
                    fillColor: style.fillColor,
                    fillOpacity: style.fillOpacity
                });
            }

            // Clear current rectangle and reset drawing state
            currentRect = null;
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
        var rectWidth = Math.abs(deltaX);
        var rectHeight = Math.abs(deltaY);

        // Constrain to square when Shift is held
        if (modifiers & Qt.ShiftModifier) {
            var size = Math.max(rectWidth, rectHeight);
            rectWidth = size;
            rectHeight = size;
        }

        // Calculate position based on Alt (center mode) or corner mode
        var rectX, rectY;
        if (modifiers & Qt.AltModifier) {
            // Alt: draw from center - double the dimensions
            rectWidth *= 2;
            rectHeight *= 2;
            rectX = helper.startX - rectWidth / 2;
            rectY = helper.startY - rectHeight / 2;
        } else {
            // Normal: draw from corner
            rectX = deltaX >= 0 ? helper.startX : helper.startX - rectWidth;
            rectY = deltaY >= 0 ? helper.startY : helper.startY - rectHeight;
        }

        // Update current rectangle (create new object to trigger binding)
        currentRect = {
            x: rectX,
            y: rectY,
            width: rectWidth,
            height: rectHeight
        };
    }

    // Reset tool state (called when switching tools)
    function reset() {
        helper.reset();
        currentRect = null;
    }
}
