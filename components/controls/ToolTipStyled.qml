// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import ".." as Lucent

ToolTip {
    id: root

    readonly property SystemPalette themePalette: Lucent.Themed.palette

    delay: 1000

    background: Rectangle {
        color: themePalette.window
        radius: Lucent.Styles.rad.sm
    }

    contentItem: Label {
        text: root.text
        color: themePalette.text
        font.pixelSize: 11
    }
}
