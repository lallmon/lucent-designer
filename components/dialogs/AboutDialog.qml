// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

Dialog {
    id: root
    modal: true
    focus: true
    standardButtons: Dialog.Ok
    readonly property SystemPalette themePalette: Lucent.Themed.palette

    contentItem: Item {
        implicitWidth: column.implicitWidth + 28
        implicitHeight: column.implicitHeight + 28

        Column {
            id: column
            anchors.fill: parent
            anchors.margins: 14
            spacing: 8

            Label {
                text: qsTr("Lucent Designer")
                font.bold: true
            }
            Label {
                text: qsTr("Copyright (C) 2026 The Culture List, Inc.")
            }

            Label {
                text: qsTr("Version: %1").arg(appInfo ? appInfo.appVersion : "unknown")
            }

            Label {
                text: qsTr("Renderer: %1 (%2)").arg(appInfo ? appInfo.rendererBackend : "unknown").arg(appInfo ? appInfo.rendererType : "unknown")
            }

            Label {
                text: qsTr("Graphics: %1").arg(appInfo ? appInfo.glVendor : "unknown")
                visible: appInfo && appInfo.rendererBackend === "opengl"
            }
        }
    }
}
