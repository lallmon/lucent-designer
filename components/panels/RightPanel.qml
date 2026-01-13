// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

Pane {
    id: root
    padding: 0

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        TransformPanel {
            id: transformPanel
            Layout.fillWidth: true
        }

        ToolSeparator {
            Layout.fillWidth: true
            orientation: Qt.Horizontal
            contentItem: Rectangle {
                implicitHeight: 1
                color: Lucent.Themed.palette.mid
            }
        }

        LayerPanel {
            id: layerPanel
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 150
        }
    }
}
