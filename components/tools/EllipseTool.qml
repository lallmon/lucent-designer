// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import ".." as Lucent

// Ellipse drawing tool component
Item {
    id: tool

    // Properties passed from Canvas
    property real zoomLevel: 1.0
    property bool active: false
    property var settings: null  // Tool settings object

    // Preview callbacks from ToolLoader
    property var setPreviewCallback: null
    property var clearPreviewCallback: null

    TwoPointToolHelper {
        id: helper
    }
    property var currentEllipse: null
    property real mouseX: 0
    property real mouseY: 0
    readonly property bool hasUnitSettings: typeof unitSettings !== "undefined" && unitSettings !== null

    signal itemCompleted(var itemData)

    onCurrentEllipseChanged: updatePreview()

    function updatePreview() {
        if (!currentEllipse || currentEllipse.width <= 0 || currentEllipse.height <= 0) {
            if (clearPreviewCallback)
                clearPreviewCallback();
            return;
        }
        if (!setPreviewCallback)
            return;

        var centerX = currentEllipse.x + currentEllipse.width / 2;
        var centerY = currentEllipse.y + currentEllipse.height / 2;
        var radiusX = currentEllipse.width / 2;
        var radiusY = currentEllipse.height / 2;
        var style = helper.extractStyle(settings);

        setPreviewCallback({
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
                    visible: style.strokeVisible,
                    cap: style.strokeCap,
                    align: style.strokeAlign,
                    order: style.strokeOrder,
                    scaleWithObject: style.strokeScaleWithObject
                }
            ]
        });
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
                        visible: style.strokeVisible,
                        cap: style.strokeCap,
                        align: style.strokeAlign,
                        order: style.strokeOrder,
                        scaleWithObject: style.strokeScaleWithObject
                    }
                ]
            });
        }

        if (clearPreviewCallback)
            clearPreviewCallback();
        currentEllipse = null;
        helper.reset();
    }

    function handleMouseMove(canvasX, canvasY, modifiers) {
        mouseX = canvasX;
        mouseY = canvasY;

        if (!tool.active || !helper.isDrawing)
            return;

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

        // Calculate position based on Ctrl (center mode) or corner mode
        var ellipseX, ellipseY;
        if (modifiers & Qt.ControlModifier) {
            // Ctrl: draw from center - double the dimensions
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

    function reset() {
        helper.reset();
        if (clearPreviewCallback)
            clearPreviewCallback();
        currentEllipse = null;
    }
}
