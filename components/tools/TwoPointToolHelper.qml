import QtQuick

// Shared helper for two-click drawing tools (rectangle, ellipse, etc.)
QtObject {
    id: helper

    property bool isDrawing: false
    property real startX: 0
    property real startY: 0

    function begin(x, y) {
        isDrawing = true;
        startX = x;
        startY = y;
    }

    function reset() {
        isDrawing = false;
    }

    function extractStyle(settings) {
        // Force evaluation to plain values to avoid unintended bindings; settings must be provided
        return {
            strokeWidth: settings ? settings.strokeWidth : 1,
            strokeColor: settings ? settings.strokeColor.toString() : "",
            strokeOpacity: settings ? (settings.strokeOpacity !== undefined ? settings.strokeOpacity : 1.0) : 1.0,
            fillColor: settings ? settings.fillColor.toString() : "",
            fillOpacity: settings ? settings.fillOpacity : 1.0
        };
    }

    function hasSize(rect) {
        return rect && rect.width > 1 && rect.height > 1;
    }
}
