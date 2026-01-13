// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

ToolBar {
    id: root
    implicitHeight: 32
    property real cursorX: 0
    property real cursorY: 0
    property string activeTool: "select"

    readonly property bool hasUnitSettings: typeof unitSettings !== "undefined" && unitSettings !== null
    readonly property real displayCursorX: hasUnitSettings ? unitSettings.canvasToDisplay(root.cursorX) : root.cursorX
    readonly property real displayCursorY: hasUnitSettings ? unitSettings.canvasToDisplay(root.cursorY) : root.cursorY
    readonly property string displayUnitLabel: hasUnitSettings ? unitSettings.displayUnit : "px"

    RowLayout {
        anchors.fill: parent
        spacing: 12
        Layout.alignment: Qt.AlignVCenter

        // Tool instructions (left side)
        Label {
            Layout.leftMargin: 10
            Layout.fillWidth: true
            text: Lucent.ToolRegistry.getInstruction(root.activeTool)
            color: palette.text
            font.pixelSize: 11
            elide: Text.ElideRight
        }

        // Cursor readout (right side)
        RowLayout {
            Layout.alignment: Qt.AlignVCenter
            Layout.rightMargin: 10
            spacing: 6
            Lucent.PhIcon {
                name: "crosshair-simple"
                size: 16
                color: "white"
            }
            Label {
                text: qsTr("X: %1  Y: %2 %3").arg(root.displayCursorX.toFixed(1)).arg(root.displayCursorY.toFixed(1)).arg(displayUnitLabel)
                horizontalAlignment: Text.AlignRight
            }
        }
    }
}
