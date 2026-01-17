// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import ".." as Lucent

// Rectangle drawing tool component
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
    property var currentRect: null
    property real mouseX: 0
    property real mouseY: 0
    readonly property bool hasUnitSettings: typeof unitSettings !== "undefined" && unitSettings !== null

    signal itemCompleted(var itemData)

    onCurrentRectChanged: updatePreview()

    function updatePreview() {
        if (!currentRect || currentRect.width <= 0 || currentRect.height <= 0) {
            if (clearPreviewCallback)
                clearPreviewCallback();
            return;
        }
        if (!setPreviewCallback)
            return;

        var style = helper.extractStyle(settings);
        var geom = {
            x: currentRect.x,
            y: currentRect.y,
            width: currentRect.width,
            height: currentRect.height
        };
        if (settings) {
            if (settings.singleRadiusMode) {
                geom.cornerRadius = settings.cornerRadius || 0;
            } else {
                geom.cornerRadiusTL = settings.cornerRadiusTL || 0;
                geom.cornerRadiusTR = settings.cornerRadiusTR || 0;
                geom.cornerRadiusBR = settings.cornerRadiusBR || 0;
                geom.cornerRadiusBL = settings.cornerRadiusBL || 0;
            }
        }
        setPreviewCallback({
            type: "rectangle",
            geometry: geom,
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
                    order: style.strokeOrder
                }
            ]
        });
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
            var geom = {
                x: currentRect.x,
                y: currentRect.y,
                width: currentRect.width,
                height: currentRect.height
            };
            if (settings) {
                if (settings.singleRadiusMode) {
                    geom.cornerRadius = settings.cornerRadius || 0;
                } else {
                    geom.cornerRadiusTL = settings.cornerRadiusTL || 0;
                    geom.cornerRadiusTR = settings.cornerRadiusTR || 0;
                    geom.cornerRadiusBR = settings.cornerRadiusBR || 0;
                    geom.cornerRadiusBL = settings.cornerRadiusBL || 0;
                }
            }
            itemCompleted({
                type: "rectangle",
                geometry: geom,
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
                        order: style.strokeOrder
                    }
                ]
            });
        }

        if (clearPreviewCallback)
            clearPreviewCallback();
        currentRect = null;
        helper.reset();
    }

    function handleMouseMove(canvasX, canvasY, modifiers) {
        mouseX = canvasX;
        mouseY = canvasY;

        if (!tool.active || !helper.isDrawing)
            return;

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

        // Calculate position based on Ctrl (center mode) or corner mode
        var rectX, rectY;
        if (modifiers & Qt.ControlModifier) {
            // Ctrl: draw from center - double the dimensions
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

    function reset() {
        helper.reset();
        if (clearPreviewCallback)
            clearPreviewCallback();
        currentRect = null;
    }
}
