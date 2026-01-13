// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick

// Toggle with F12
Rectangle {
    id: root
    width: 100
    height: contentColumn.height + 16
    color: "#CC000000"
    radius: 4
    visible: false

    property int frameCount: 0
    property real fps: 0

    FrameAnimation {
        running: root.visible
        onTriggered: root.frameCount++
    }

    Timer {
        interval: 1000
        running: root.visible
        repeat: true
        onTriggered: {
            root.fps = root.frameCount;
            root.frameCount = 0;
        }
    }

    Column {
        id: contentColumn
        anchors.centerIn: parent
        spacing: 4

        Row {
            spacing: 6

            Text {
                text: "FPS:"
                color: "#AAAAAA"
                font.pixelSize: 11
                font.family: "monospace"
            }

            Text {
                text: root.fps.toFixed(0)
                color: root.fps < 30 ? "#FF6B6B" : root.fps < 55 ? "#FFE66D" : "#4ECDC4"
                font.pixelSize: 11
                font.bold: true
                font.family: "monospace"
            }
        }
    }
}
