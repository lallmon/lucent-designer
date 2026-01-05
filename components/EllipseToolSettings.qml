import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as DV

RowLayout {
    id: root

    // Tool settings properties with theme-aware defaults
    property real strokeWidth: 1
    property color strokeColor: DV.Themed.palette.text
    property real strokeOpacity: 1.0
    property color fillColor: DV.Themed.palette.text
    property real fillOpacity: 0.0

    Layout.fillHeight: true
    Layout.alignment: Qt.AlignVCenter
    spacing: 6

    DV.LabeledNumericField {
        labelText: qsTr("Stroke Width:")
        value: root.strokeWidth
        minimum: 0.1
        maximum: 100.0
        decimals: 1
        suffix: qsTr("px")
        onCommitted: newValue => root.strokeWidth = newValue
    }

    ToolSeparator {}

    Label {
        text: qsTr("Stroke Color:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    DV.ColorPickerButton {
        color: root.strokeColor
        colorOpacity: root.strokeOpacity
        dialogTitle: qsTr("Choose Stroke Color")
        onColorPicked: newColor => root.strokeColor = newColor
    }

    Label {
        text: qsTr("Opacity:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    DV.OpacitySlider {
        opacityValue: root.strokeOpacity
        onValueUpdated: newOpacity => root.strokeOpacity = newOpacity
    }

    DV.LabeledNumericField {
        labelText: ""
        value: Math.round(root.strokeOpacity * 100)
        minimum: 0
        maximum: 100
        decimals: 0
        fieldWidth: 35
        suffix: qsTr("%")
        onCommitted: newValue => root.strokeOpacity = newValue / 100.0
    }

    ToolSeparator {}

    Label {
        text: qsTr("Fill Color:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    DV.ColorPickerButton {
        color: root.fillColor
        colorOpacity: root.fillOpacity
        dialogTitle: qsTr("Choose Fill Color")
        onColorPicked: newColor => root.fillColor = newColor
    }

    Label {
        text: qsTr("Opacity:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    DV.OpacitySlider {
        opacityValue: root.fillOpacity
        onValueUpdated: newOpacity => root.fillOpacity = newOpacity
    }

    DV.LabeledNumericField {
        labelText: ""
        value: Math.round(root.fillOpacity * 100)
        minimum: 0
        maximum: 100
        decimals: 0
        fieldWidth: 35
        suffix: qsTr("%")
        onCommitted: newValue => root.fillOpacity = newValue / 100.0
    }
}
