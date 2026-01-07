import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform as Platform
import "." as Lucent

Dialog {
    id: root
    title: qsTr("Export Layer")
    modal: true
    standardButtons: Dialog.Cancel

    property string layerId: ""
    property string layerName: "Layer"

    // Document DPI is always 72 (points = pixels at 1:1)
    readonly property int documentDPI: 72

    // Get selected DPI value from combo box
    readonly property int selectedDPI: {
        if (dpiCombo.currentIndex >= 0 && dpiCombo.model.count > 0)
            return dpiCombo.model.get(dpiCombo.currentIndex).value;
        return 72;
    }

    readonly property real computedWidth: {
        if (!canvasModel || !layerId)
            return 0;
        var bounds = canvasModel.getLayerBounds(layerId);
        var scale = selectedDPI / documentDPI;
        return (bounds.width + paddingInput.value * 2) * scale;
    }

    readonly property real computedHeight: {
        if (!canvasModel || !layerId)
            return 0;
        var bounds = canvasModel.getLayerBounds(layerId);
        var scale = selectedDPI / documentDPI;
        return (bounds.height + paddingInput.value * 2) * scale;
    }

    width: 360
    height: 320

    Platform.FileDialog {
        id: saveDialog
        title: qsTr("Export As")
        fileMode: Platform.FileDialog.SaveFile
        nameFilters: formatCombo.currentIndex === 0 ? ["PNG files (*.png)"] : ["SVG files (*.svg)"]
        defaultSuffix: formatCombo.currentIndex === 0 ? "png" : "svg"
        onAccepted: {
            if (documentManager) {
                var bg = transparentCheck.checked ? "" : bgColorPicker.color.toString();
                var filePath = saveDialog.file.toString();
                console.log("Exporting to:", filePath, "DPI:", root.selectedDPI);
                var result = documentManager.exportLayer(root.layerId, filePath, root.selectedDPI, paddingInput.value, bg);
                console.log("Export result:", result);
            }
            root.close();
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        Label {
            text: qsTr("Exporting: %1").arg(root.layerName)
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
                model: ["PNG", "SVG"]
                Layout.fillWidth: true
            }

            Label {
                text: qsTr("Resolution:")
                visible: formatCombo.currentIndex === 0
            }
            ComboBox {
                id: dpiCombo
                visible: formatCombo.currentIndex === 0
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
            visible: formatCombo.currentIndex === 0
            color: palette.text
        }

        Item {
            Layout.fillHeight: true
        }

        Button {
            text: qsTr("Export...")
            Layout.alignment: Qt.AlignRight
            onClicked: saveDialog.open()
        }
    }
}
