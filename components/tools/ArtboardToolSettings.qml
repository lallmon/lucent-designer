// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

// Artboard tool settings - background color control
RowLayout {
    id: root

    property bool editMode: false
    property var selectedItem: null
    property color _defaultBackgroundColor: "#ffffff"

    readonly property color backgroundColor: {
        if (editMode && selectedItem && selectedItem.backgroundColor)
            return selectedItem.backgroundColor;
        return _defaultBackgroundColor;
    }

    function updateBackgroundColor(value) {
        var colorString = value && value.toString ? value.toString() : value;
        _defaultBackgroundColor = colorString;
        if (editMode && Lucent.SelectionManager.selectedItemIndex >= 0) {
            canvasModel.updateItem(Lucent.SelectionManager.selectedItemIndex, {
                "backgroundColor": colorString
            });
        }
    }

    Layout.fillHeight: true
    Layout.alignment: Qt.AlignVCenter
    spacing: 6

    Label {
        text: qsTr("Background:")
        font.pixelSize: 12
        Layout.alignment: Qt.AlignVCenter
    }

    Lucent.ColorPickerButton {
        id: backgroundPicker
        color: root.backgroundColor
        Layout.alignment: Qt.AlignVCenter
        dialogTitle: qsTr("Choose Artboard Background")
        onDialogOpened: canvasModel.beginTransaction()
        onDialogClosed: canvasModel.endTransaction()
        onColorPreview: previewColor => root.updateBackgroundColor(previewColor)
        onColorPicked: newColor => root.updateBackgroundColor(newColor)
    }
}
