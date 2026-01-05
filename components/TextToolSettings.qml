import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as DV

RowLayout {
    id: root

    // Tool settings properties with theme-aware defaults
    property string fontFamily: "Sans Serif"
    property real fontSize: 16
    property color textColor: DV.Themed.palette.text
    property real textOpacity: 1.0

    Layout.fillHeight: true
    Layout.alignment: Qt.AlignVCenter
    spacing: 6

    Label {
        text: qsTr("Font:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    ComboBox {
        id: fontFamilyCombo
        Layout.preferredWidth: 160
        Layout.preferredHeight: DV.Styles.height.md
        Layout.alignment: Qt.AlignVCenter
        model: fontProvider ? fontProvider.fonts : []
        currentIndex: fontProvider ? fontProvider.indexOf(root.fontFamily) : 0

        onCurrentTextChanged: {
            if (currentText && currentText.length > 0) {
                root.fontFamily = currentText;
            }
        }

        Component.onCompleted: {
            if (fontProvider && (!root.fontFamily || root.fontFamily === "Sans Serif")) {
                root.fontFamily = fontProvider.defaultFont();
            }
        }

        background: Rectangle {
            color: palette.base
            border.color: fontFamilyCombo.activeFocus ? palette.highlight : palette.mid
            border.width: 1
            radius: DV.Styles.rad.sm
        }

        contentItem: Text {
            text: fontFamilyCombo.displayText
            color: palette.text
            font.pixelSize: 11
            font.family: fontFamilyCombo.displayText
            verticalAlignment: Text.AlignVCenter
            leftPadding: 6
            elide: Text.ElideRight
        }
    }

    ToolSeparator {}

    Label {
        text: qsTr("Size:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    ComboBox {
        id: fontSizeCombo
        Layout.preferredWidth: 70
        Layout.preferredHeight: DV.Styles.height.md
        Layout.alignment: Qt.AlignVCenter
        editable: true
        model: [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 64, 72, 96, 128]

        currentIndex: {
            var idx = model.indexOf(Math.round(root.fontSize));
            return idx >= 0 ? idx : -1;
        }

        Component.onCompleted: {
            editText = Math.round(root.fontSize).toString();
        }

        onCurrentIndexChanged: {
            if (currentIndex >= 0) {
                root.fontSize = model[currentIndex];
            }
        }

        onAccepted: {
            var value = parseFloat(editText);
            if (!isNaN(value) && value >= 8 && value <= 200) {
                root.fontSize = Math.round(value);
            }
            editText = Math.round(root.fontSize).toString();
        }

        Connections {
            target: root
            function onFontSizeChanged() {
                if (!fontSizeCombo.activeFocus) {
                    fontSizeCombo.editText = Math.round(root.fontSize).toString();
                }
            }
        }

        validator: IntValidator {
            bottom: 8
            top: 200
        }

        background: Rectangle {
            color: palette.base
            border.color: fontSizeCombo.activeFocus ? palette.highlight : palette.mid
            border.width: 1
            radius: DV.Styles.rad.sm
        }

        contentItem: TextInput {
            text: fontSizeCombo.editText
            font.pixelSize: 11
            color: palette.text
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            leftPadding: 6
            rightPadding: 6
            selectByMouse: true
            validator: fontSizeCombo.validator

            onTextChanged: fontSizeCombo.editText = text
            onAccepted: fontSizeCombo.accepted()
        }
    }

    Label {
        text: qsTr("pt")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    ToolSeparator {}

    Label {
        text: qsTr("Color:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    DV.ColorPickerButton {
        color: root.textColor
        colorOpacity: root.textOpacity
        dialogTitle: qsTr("Choose Text Color")
        onColorPicked: newColor => root.textColor = newColor
    }

    Label {
        text: qsTr("Opacity:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    DV.OpacitySlider {
        opacityValue: root.textOpacity
        onValueUpdated: newOpacity => root.textOpacity = newOpacity
    }

    DV.LabeledNumericField {
        labelText: ""
        value: Math.round(root.textOpacity * 100)
        minimum: 0
        maximum: 100
        decimals: 0
        fieldWidth: 35
        suffix: qsTr("%")
        onCommitted: newValue => root.textOpacity = newValue / 100.0
    }
}
