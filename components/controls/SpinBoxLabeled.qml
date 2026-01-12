// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

// Reusable labeled SpinBox for transform panels and tool settings
RowLayout {
    id: root

    property string label: ""
    property int labelSize: 10
    property color labelColor: Lucent.Themed.palette.text

    property alias value: spinBox.value
    property alias from: spinBox.from
    property alias to: spinBox.to
    property alias editable: spinBox.editable
    property alias stepSize: spinBox.stepSize
    property int decimals: 3

    signal valueModified(int newValue)

    spacing: 4

    Label {
        text: root.label
        font.pixelSize: root.labelSize
        color: root.labelColor
        visible: root.label !== ""
    }

    SpinBox {
        id: spinBox
        Layout.fillWidth: true
        editable: true
        // SpinBox in Controls 6/QtQuick does not support decimals; we expose the
        // property but do not bind it here to avoid binding errors. Decimal support
        // is handled externally where supported.

        onValueModified: root.valueModified(value)
    }
}
