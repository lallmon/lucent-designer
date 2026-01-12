// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Shapes
import ".." as Lucent

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
    property real mouseX: 0
    property real mouseY: 0
    readonly property bool hasUnitSettings: typeof unitSettings !== "undefined" && unitSettings !== null

    signal itemCompleted(var itemData)

    // Preview rectangle using Shape for better performance
    Shape {
        id: previewRect

        visible: tool.currentRect !== null && tool.currentRect.width > 0 && tool.currentRect.height > 0

        x: tool.currentRect ? tool.currentRect.x : 0
        y: tool.currentRect ? tool.currentRect.y : 0
        width: tool.currentRect ? tool.currentRect.width : 0
        height: tool.currentRect ? tool.currentRect.height : 0

        ShapePath {
            strokeWidth: (settings ? settings.strokeWidth : 1) / tool.zoomLevel
            strokeColor: {
                if (!settings)
                    return Lucent.Themed.palette.text;
                var c = Qt.color(settings.strokeColor);
                c.a = settings.strokeOpacity !== undefined ? settings.strokeOpacity : 1.0;
                return c;
            }
            fillColor: {
                if (!settings)
                    return "transparent";
                var c = Qt.color(settings.fillColor);
                c.a = settings.fillOpacity;
                return c;
            }
            joinStyle: ShapePath.MiterJoin

            startX: 0
            startY: 0
            PathLine {
                x: previewRect.width
                y: 0
            }
            PathLine {
                x: previewRect.width
                y: previewRect.height
            }
            PathLine {
                x: 0
                y: previewRect.height
            }
            PathLine {
                x: 0
                y: 0
            }
        }
    }

    Lucent.ToolTipCanvas {
        visible: helper.isDrawing && tool.currentRect !== null
        zoomLevel: tool.zoomLevel
        cursorX: tool.mouseX
        cursorY: tool.mouseY
        text: {
            if (!tool.currentRect)
                return "";
            var w = tool.currentRect.width;
            var h = tool.currentRect.height;
            if (tool.hasUnitSettings) {
                w = unitSettings.canvasToDisplay(w);
                h = unitSettings.canvasToDisplay(h);
            }
            var unitLabel = tool.hasUnitSettings ? unitSettings.displayUnit : "px";
            var places = 1;
            if (tool.hasUnitSettings) {
                if (unitSettings.displayUnit === "in")
                    places = 3;
                else if (unitSettings.displayUnit === "mm")
                    places = 2;
                else if (unitSettings.displayUnit === "pt")
                    places = 2;
            }
            return w.toFixed(places) + " × " + h.toFixed(places) + " " + unitLabel;
        }
    }

    function handleMousePress(canvasX, canvasY, button, modifiers) {
        if (!tool.active || button !== Qt.LeftButton)
            return;

        helper.begin(canvasX, canvasY);
        currentRect = {
            x: helper.startX,
            y: helper.startY,
            width: 1,
            height: 1
        };
    }

    function handleMouseRelease(canvasX, canvasY) {
        if (!tool.active || !helper.isDrawing)
            return;

        if (helper.hasSize(currentRect)) {
            var style = helper.extractStyle(settings);
            itemCompleted({
                type: "rectangle",
                geometry: {
                    x: currentRect.x,
                    y: currentRect.y,
                    width: currentRect.width,
                    height: currentRect.height
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
            });
        }

        currentRect = null;
        helper.reset();
    }

    // Update preview during mouse movement
    function handleMouseMove(canvasX, canvasY, modifiers) {
        mouseX = canvasX;
        mouseY = canvasY;

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
