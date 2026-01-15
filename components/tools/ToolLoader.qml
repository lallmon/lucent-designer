// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick

// Dynamically loads drawing tools based on the current drawing mode.
// Handles property binding and signal connection for loaded tools.
Item {
    id: root

    // Input properties from Canvas
    property string drawingMode: ""
    property real zoomLevel: 1.0
    property var toolSettings: null
    property real viewportWidth: 0
    property real viewportHeight: 0

    // Preview rendering callbacks from Canvas
    property var setPreviewCallback: null
    property var clearPreviewCallback: null

    // Expose the loaded tool for mouse event forwarding
    readonly property var currentTool: loader.item

    // Whether the loader is active (has a tool loaded)
    readonly property bool active: loader.active && loader.item !== null

    // Emitted when a tool completes drawing an item
    signal itemCompleted(var itemData)

    // Tool name to QML file mapping
    readonly property var toolMap: ({
            "rectangle": "RectangleTool.qml",
            "ellipse": "EllipseTool.qml",
            "pen": "PenTool.qml",
            "text": "TextTool.qml"
        })

    Loader {
        id: loader
        active: root.drawingMode !== "" && root.drawingMode !== "select"

        source: root.toolMap[root.drawingMode] || ""

        onLoaded: {
            if (item) {
                // Bind required properties
                item.zoomLevel = Qt.binding(function () {
                    return root.zoomLevel;
                });
                item.active = Qt.binding(function () {
                    return root.drawingMode !== "" && root.drawingMode !== "select";
                });
                item.settings = Qt.binding(function () {
                    return root.toolSettings ? root.toolSettings[root.drawingMode] : null;
                });

                // Bind optional viewport dimensions if the tool supports them
                if (item.hasOwnProperty("viewportWidth")) {
                    item.viewportWidth = Qt.binding(function () {
                        return root.viewportWidth;
                    });
                }
                if (item.hasOwnProperty("viewportHeight")) {
                    item.viewportHeight = Qt.binding(function () {
                        return root.viewportHeight;
                    });
                }

                // Bind preview callbacks if the tool supports them
                if (item.hasOwnProperty("setPreviewCallback")) {
                    item.setPreviewCallback = root.setPreviewCallback;
                }
                if (item.hasOwnProperty("clearPreviewCallback")) {
                    item.clearPreviewCallback = root.clearPreviewCallback;
                }

                // Connect tool's itemCompleted to our signal
                item.itemCompleted.connect(root.itemCompleted);
            }
        }
    }

    // Reset the current tool's state
    function reset() {
        if (loader.item && loader.item.reset) {
            loader.item.reset();
        }
    }
}
