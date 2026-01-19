// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform as Platform
import ".." as Lucent

Dialog {
    id: root
    title: qsTr("Export Artboard")
    modal: true
    standardButtons: Dialog.Cancel
    padding: 16

    property string artboardId: ""
    property string artboardName: "Artboard"

    // Document DPI controls print scaling; screen exports are 1:1.
    readonly property int documentDPI: documentManager ? documentManager.documentDPI : 72

    // Get selected DPI value from combo box
    readonly property int selectedDPI: {
        if (dpiCombo.currentIndex >= 0 && dpiCombo.model.count > 0)
            return dpiCombo.model.get(dpiCombo.currentIndex).value;
        return 72;
    }

    readonly property real printBaseDPI: {
        if (unitSettings && unitSettings.displayUnit !== "px")
            return unitSettings.previewDPI;
        return documentDPI;
    }

    readonly property real computedWidth: {
        if (!canvasModel || !artboardId)
            return 0;
        var bounds = canvasModel.getArtboardBounds(artboardId);
        var scale = exportModeCombo.currentIndex === 1 ? selectedDPI / printBaseDPI : 1.0;
        return (bounds.width + paddingInput.value * 2) * scale;
    }

    readonly property real computedHeight: {
        if (!canvasModel || !artboardId)
            return 0;
        var bounds = canvasModel.getArtboardBounds(artboardId);
        var scale = exportModeCombo.currentIndex === 1 ? selectedDPI / printBaseDPI : 1.0;
        return (bounds.height + paddingInput.value * 2) * scale;
    }

    width: 360
    implicitHeight: contentLayout.implicitHeight + footerBox.implicitHeight + topPadding + bottomPadding

    Platform.FileDialog {
        id: saveDialog
        title: qsTr("Export As")
        fileMode: Platform.FileDialog.SaveFile
        nameFilters: formatCombo.currentIndex === 0 ? ["PNG files (*.png)"] : formatCombo.currentIndex === 1 ? ["SVG files (*.svg)"] : formatCombo.currentIndex === 2 ? ["JPG files (*.jpg *.jpeg)"] : ["PDF files (*.pdf)"]
        defaultSuffix: formatCombo.currentIndex === 0 ? "png" : formatCombo.currentIndex === 1 ? "svg" : formatCombo.currentIndex === 2 ? "jpg" : "pdf"
        onAccepted: {
            if (documentManager) {
                var bg = transparentCheck.checked ? "" : bgColorPicker.color.toString();
                var filePath = saveDialog.file.toString();
                var exportDpi = exportModeCombo.currentIndex === 1 ? root.selectedDPI : root.documentDPI;
                console.log("Exporting to:", filePath, "DPI:", exportDpi);
                var result = documentManager.exportArtboard(root.artboardId, filePath, exportDpi, paddingInput.value, bg);
                console.log("Export result:", result);
            }
            root.close();
        }
    }

    contentItem: ColumnLayout {
        id: contentLayout
        spacing: 12

        Label {
            text: qsTr("Exporting: %1").arg(root.artboardName)
            font.bold: true
        }

        GridLayout {
            columns: 2
            columnSpacing: 12
            rowSpacing: 8
            Layout.fillWidth: true

            Label {
                text: qsTr("Format:")
            }
            ComboBox {
                id: formatCombo
                model: ["PNG", "SVG", "JPG", "PDF"]
                Layout.fillWidth: true
                onCurrentIndexChanged: {
                    if (currentIndex === 1) {
                        transparentCheck.checked = true;
                    } else if (currentIndex === 2) {
                        transparentCheck.checked = false;
                    }
                }
            }

            Label {
                text: qsTr("Export mode:")
                visible: formatCombo.currentIndex === 0 || formatCombo.currentIndex === 2 || formatCombo.currentIndex === 3
            }
            ComboBox {
                id: exportModeCombo
                visible: formatCombo.currentIndex === 0 || formatCombo.currentIndex === 2 || formatCombo.currentIndex === 3
                model: [qsTr("Screen (1×)"), qsTr("Print (DPI)")]
                currentIndex: 0
                Layout.fillWidth: true
            }

            Label {
                text: qsTr("Resolution:")
                visible: (formatCombo.currentIndex === 0 || formatCombo.currentIndex === 2 || formatCombo.currentIndex === 3) && exportModeCombo.currentIndex === 1
            }
            ComboBox {
                id: dpiCombo
                visible: (formatCombo.currentIndex === 0 || formatCombo.currentIndex === 2 || formatCombo.currentIndex === 3) && exportModeCombo.currentIndex === 1
                model: ListModel {
                    ListElement {
                        text: "72 DPI (Screen)"
                        value: 72
                    }
                    ListElement {
                        text: "144 DPI (Retina)"
                        value: 144
                    }
                    ListElement {
                        text: "300 DPI (Print)"
                        value: 300
                    }
                }
                textRole: "text"
                valueRole: "value"
                currentIndex: 0
                Layout.fillWidth: true
            }

            Label {
                text: qsTr("Padding:")
            }
            SpinBox {
                id: paddingInput
                from: 0
                to: 500
                value: 0
                editable: true
                Layout.fillWidth: true
            }

            Label {
                text: qsTr("Background:")
            }
            RowLayout {
                Layout.fillWidth: true
                CheckBox {
                    id: transparentCheck
                    text: qsTr("Transparent")
                    checked: true
                    enabled: formatCombo.currentIndex !== 2
                }
                Lucent.ColorPickerButton {
                    id: bgColorPicker
                    color: "#ffffff"
                    visible: !transparentCheck.checked
                    Layout.preferredWidth: 24
                    Layout.preferredHeight: 24
                    onColorPicked: newColor => color = newColor
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: palette.mid
        }

        Label {
            text: qsTr("Output size: %1 × %2 px").arg(Math.round(root.computedWidth)).arg(Math.round(root.computedHeight))
            visible: formatCombo.currentIndex === 0 || formatCombo.currentIndex === 2 || formatCombo.currentIndex === 3
            color: palette.text
        }

        Item {
            Layout.fillHeight: true
        }
    }

    footer: DialogButtonBox {
        id: footerBox
        standardButtons: Dialog.Cancel
        Button {
            text: qsTr("Export...")
            DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            onClicked: saveDialog.open()
        }
    }
}
