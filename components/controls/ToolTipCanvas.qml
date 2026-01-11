// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import ".." as Lucent

// Tooltip that follows cursor position on canvas, scaling with zoom
Rectangle {
    id: root

    required property real zoomLevel
    required property real cursorX
    required property real cursorY
    required property string text

    readonly property SystemPalette themePalette: Lucent.Themed.palette

    x: cursorX + (16 / zoomLevel)
    y: cursorY - height - (8 / zoomLevel)

    width: label.width + (12 / zoomLevel)
    height: label.height + (6 / zoomLevel)
    radius: Lucent.Styles.rad.sm / zoomLevel

    color: themePalette.window
    border.color: themePalette.mid
    border.width: 1 / zoomLevel

    Label {
        id: label
        anchors.centerIn: parent
        font.pixelSize: 11 / root.zoomLevel
        color: root.themePalette.text
        text: root.text
    }
}
