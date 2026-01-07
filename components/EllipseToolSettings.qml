import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as Lucent

RowLayout {
    id: root

    // Edit mode: when true, we're editing a selected item instead of setting defaults
    property bool editMode: false
    property var selectedItem: null

    // Internal defaults for creation mode
    property real _defaultStrokeWidth: 1
    property color _defaultStrokeColor: Lucent.Themed.palette.text
    property real _defaultStrokeOpacity: 1.0
    property color _defaultFillColor: Lucent.Themed.palette.text
    property real _defaultFillOpacity: 0.0

    // Exposed properties: read from selectedItem in edit mode, defaults in creation mode
    readonly property real strokeWidth: editMode && selectedItem ? selectedItem.strokeWidth : _defaultStrokeWidth
    readonly property color strokeColor: editMode && selectedItem ? selectedItem.strokeColor : _defaultStrokeColor
    readonly property real strokeOpacity: editMode && selectedItem ? selectedItem.strokeOpacity : _defaultStrokeOpacity
    readonly property color fillColor: editMode && selectedItem ? selectedItem.fillColor : _defaultFillColor
    readonly property real fillOpacity: editMode && selectedItem ? selectedItem.fillOpacity : _defaultFillOpacity

    // Update helper: always updates defaults, and also updates selected item in edit mode
    function updateProperty(propName, value) {
        // Always update defaults so new shapes use the last-used settings
        if (propName === "strokeWidth")
            _defaultStrokeWidth = value;
        else if (propName === "strokeColor")
            _defaultStrokeColor = value;
        else if (propName === "strokeOpacity")
            _defaultStrokeOpacity = value;
        else if (propName === "fillColor")
            _defaultFillColor = value;
        else if (propName === "fillOpacity")
            _defaultFillOpacity = value;

        // Also update selected item if in edit mode
        if (editMode && Lucent.SelectionManager.selectedItemIndex >= 0) {
            var props = {};
            props[propName] = value;
            canvasModel.updateItem(Lucent.SelectionManager.selectedItemIndex, props);
        }
    }

    Layout.fillHeight: true
    Layout.alignment: Qt.AlignVCenter
    spacing: 6

    Lucent.LabeledNumericField {
        labelText: qsTr("Stroke Width:")
        value: root.strokeWidth
        minimum: 0.1
        maximum: 100.0
        decimals: 1
        suffix: qsTr("pt")
        onCommitted: newValue => root.updateProperty("strokeWidth", newValue)
    }

    ToolSeparator {}

    Label {
        text: qsTr("Stroke Color:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    Lucent.ColorPickerButton {
        color: root.strokeColor
        colorOpacity: root.strokeOpacity
        dialogTitle: qsTr("Choose Stroke Color")
        onColorPicked: newColor => root.updateProperty("strokeColor", newColor.toString())
    }

    Label {
        text: qsTr("Opacity:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    Lucent.OpacitySlider {
        opacityValue: root.strokeOpacity
        onValueUpdated: newOpacity => root.updateProperty("strokeOpacity", newOpacity)
    }

    Lucent.LabeledNumericField {
        labelText: ""
        value: Math.round(root.strokeOpacity * 100)
        minimum: 0
        maximum: 100
        decimals: 0
        fieldWidth: 35
        suffix: qsTr("%")
        onCommitted: newValue => root.updateProperty("strokeOpacity", newValue / 100.0)
    }

    ToolSeparator {}

    Label {
        text: qsTr("Fill Color:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    Lucent.ColorPickerButton {
        color: root.fillColor
        colorOpacity: root.fillOpacity
        dialogTitle: qsTr("Choose Fill Color")
        onColorPicked: newColor => root.updateProperty("fillColor", newColor.toString())
    }

    Label {
        text: qsTr("Opacity:")
        font.pixelSize: 11
        Layout.alignment: Qt.AlignVCenter
    }

    Lucent.OpacitySlider {
        opacityValue: root.fillOpacity
        onValueUpdated: newOpacity => root.updateProperty("fillOpacity", newOpacity)
    }

    Lucent.LabeledNumericField {
        labelText: ""
        value: Math.round(root.fillOpacity * 100)
        minimum: 0
        maximum: 100
        decimals: 0
        fieldWidth: 35
        suffix: qsTr("%")
        onCommitted: newValue => root.updateProperty("fillOpacity", newValue / 100.0)
    }
}
