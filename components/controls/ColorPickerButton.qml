// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import ".." as Lucent

Button {
    id: root

    property color color: "black"
    property real colorOpacity: 1.0
    property string dialogTitle: qsTr("Choose Color")

    signal colorPicked(color newColor)
    signal opacityPicked(real newOpacity)
    signal colorPreview(color previewColor)
    signal opacityPreview(real previewOpacity)

    readonly property SystemPalette themePalette: Lucent.Themed.palette
    readonly property real buttonHeight: 16

    Layout.preferredWidth: buttonHeight * 2
    Layout.preferredHeight: buttonHeight
    Layout.alignment: Qt.AlignVCenter

    onClicked: {
        // Set initial color with alpha only when opening (not as binding to avoid loops)
        colorDialog.selectedColor = Qt.rgba(root.color.r, root.color.g, root.color.b, root.colorOpacity);
        colorDialog.open();
    }

    background: Rectangle {
        border.color: root.themePalette.mid
        border.width: 1
        radius: Lucent.Styles.rad.sm
        color: "transparent"
        clip: true

        // Checkerboard pattern to show transparency
        Canvas {
            anchors.fill: parent
            z: 0
            property color checkerLight: root.themePalette.midlight
            property color checkerDark: root.themePalette.mid
            onCheckerLightChanged: requestPaint()
            onCheckerDarkChanged: requestPaint()
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height);
                var size = 4;
                for (var y = 0; y < height; y += size) {
                    for (var x = 0; x < width; x += size) {
                        if ((Math.floor(x / size) + Math.floor(y / size)) % 2 === 0) {
                            ctx.fillStyle = checkerLight;
                        } else {
                            ctx.fillStyle = checkerDark;
                        }
                        ctx.fillRect(x, y, size, size);
                    }
                }
            }
            Component.onCompleted: requestPaint()
        }

        // Color overlay with opacity applied
        Rectangle {
            anchors.fill: parent
            z: 1
            color: root.color
            opacity: root.colorOpacity
        }
    }

    ColorDialog {
        id: colorDialog
        title: root.dialogTitle
        options: ColorDialog.ShowAlphaChannel | ColorDialog.DontUseNativeDialog
        modality: Qt.NonModal

        // Live preview while picking (color and opacity)
        onSelectedColorChanged: {
            if (visible) {
                root.colorPreview(selectedColor);
                root.opacityPreview(selectedColor.a);
            }
        }

        onAccepted: {
            root.colorPicked(selectedColor);
            root.opacityPicked(selectedColor.a);
        }

        onRejected: {
            // Restore original color and opacity on cancel
            root.colorPreview(root.color);
            root.opacityPreview(root.colorOpacity);
        }
    }
}
