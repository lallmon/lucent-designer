// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import CanvasRendering 1.0

// GPU-accelerated rendering layer using SceneGraphRenderer
Item {
    id: renderLayer

    anchors.centerIn: parent
    width: 0
    height: 0

    // Required properties from parent Canvas
    required property real zoomLevel
    required property real offsetX
    required property real offsetY
    required property real viewportWidth
    required property real viewportHeight

    function setPreviewItem(itemData) {
        gpuRenderer.setPreviewItem(itemData);
    }

    function clearPreview() {
        gpuRenderer.clearPreview();
    }

    // Single SceneGraphRenderer covering the canvas
    SceneGraphRenderer {
        id: gpuRenderer

        // Cover a large canvas area for rendering all items
        width: 16384
        height: 16384
        x: -width / 2
        y: -height / 2

        zoomLevel: renderLayer.zoomLevel
        tileOriginX: 0
        tileOriginY: 0

        Component.onCompleted: setModel(canvasModel)
    }
}
