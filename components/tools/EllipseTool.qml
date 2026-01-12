// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Shapes
import ".." as Lucent

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
    property real mouseX: 0
    property real mouseY: 0

    signal itemCompleted(var itemData)

    // Preview ellipse using Shape for better performance
    Shape {
        id: previewEllipse

        visible: tool.currentEllipse !== null && tool.currentEllipse.width > 0 && tool.currentEllipse.height > 0

        x: tool.currentEllipse ? tool.currentEllipse.x : 0
        y: tool.currentEllipse ? tool.currentEllipse.y : 0
        width: tool.currentEllipse ? tool.currentEllipse.width : 0
        height: tool.currentEllipse ? tool.currentEllipse.height : 0

        ShapePath {
            id: ellipsePath
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

            // Draw ellipse using two arcs (top half and bottom half)
            startX: previewEllipse.width / 2
            startY: 0
            PathArc {
                x: previewEllipse.width / 2
                y: previewEllipse.height
                radiusX: previewEllipse.width / 2
                radiusY: previewEllipse.height / 2
                useLargeArc: true
            }
            PathArc {
                x: previewEllipse.width / 2
                y: 0
                radiusX: previewEllipse.width / 2
                radiusY: previewEllipse.height / 2
                useLargeArc: true
            }
        }
    }

    Lucent.ToolTipCanvas {
        visible: helper.isDrawing && tool.currentEllipse !== null
        zoomLevel: tool.zoomLevel
        cursorX: tool.mouseX
        cursorY: tool.mouseY
        text: {
            if (!tool.currentEllipse)
                return "";
            var w = tool.currentEllipse.width;
            var h = tool.currentEllipse.height;
            var label = "px";
            if (tool.hasUnitSettings) {
                w = unitSettings.canvasToDisplay(w);
                h = unitSettings.canvasToDisplay(h);
                label = unitSettings.displayUnit;
            }
            return Math.round(w) + " × " + Math.round(h) + " " + label;
        }
    }

    function handleMousePress(canvasX, canvasY, button, modifiers) {
        if (!tool.active || button !== Qt.LeftButton)
            return;

        helper.begin(canvasX, canvasY);
        currentEllipse = {
            x: helper.startX,
            y: helper.startY,
            width: 1,
            height: 1
        };
    }

    function handleMouseRelease(canvasX, canvasY) {
        if (!tool.active || !helper.isDrawing)
            return;

        if (helper.hasSize(currentEllipse)) {
            var centerX = currentEllipse.x + currentEllipse.width / 2;
            var centerY = currentEllipse.y + currentEllipse.height / 2;
            var radiusX = currentEllipse.width / 2;
            var radiusY = currentEllipse.height / 2;

            var style = helper.extractStyle(settings);
            itemCompleted({
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
            });
        }

        currentEllipse = null;
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
