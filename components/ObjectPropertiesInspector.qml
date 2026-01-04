import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import "." as DV

// Inspector component displaying properties of selected object
ScrollView {
    id: root
    clip: true
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
    readonly property SystemPalette palette: DV.PaletteBridge.active

    property var selectedItem: null
    property string originalStrokeColor: ""
    property string originalFillColor: ""

    // Helper to check if selected item is a shape with stroke/fill properties
    readonly property bool isShapeSelected: !!selectedItem && (selectedItem.type === "rectangle" || selectedItem.type === "ellipse")
    readonly property bool isPathSelected: !!selectedItem && selectedItem.type === "path"
    readonly property bool isTextSelected: !!selectedItem && selectedItem.type === "text"

    // Helper to check if selected item is effectively locked (own state or parent layer locked)
    readonly property bool isLocked: (DV.SelectionManager.selectedItemIndex >= 0) && canvasModel && canvasModel.isEffectivelyLocked(DV.SelectionManager.selectedItemIndex)

    readonly property int labelSize: 11
    readonly property color labelColor: palette.text

    function updateProperty(property, value) {
        if (selectedItem && DV.SelectionManager.selectedItemIndex >= 0) {
            canvasModel.updateItem(DV.SelectionManager.selectedItemIndex, {
                [property]: value
            });
        }
    }

    component PropertySeparator: Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 1
        color: palette.mid
        Layout.topMargin: 4
        Layout.bottomMargin: 4
    }

    ColumnLayout {
        width: root.availableWidth
        spacing: 8

        Label {
            text: qsTr("Properties")
            font.pixelSize: 12
            font.bold: true
            color: palette.text
            Layout.fillWidth: true
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: palette.mid
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.topMargin: 4
            spacing: 8
            visible: !!root.selectedItem

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                visible: !!root.selectedItem && root.selectedItem.type === "rectangle"

                Label {
                    text: qsTr("Rectangle")
                    font.pixelSize: 12
                    font.bold: true
                    color: root.labelColor
                }

                GridLayout {
                    columns: 2
                    rowSpacing: 4
                    columnSpacing: 8
                    Layout.fillWidth: true
                    enabled: !root.isLocked

                    Label {
                        text: qsTr("X:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    SpinBox {
                        from: -100000
                        to: 100000
                        value: root.selectedItem ? Math.round(root.selectedItem.x) : 0
                        editable: true
                        Layout.fillWidth: true
                        onValueModified: root.updateProperty("x", value)
                    }

                    Label {
                        text: qsTr("Y:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    SpinBox {
                        from: -100000
                        to: 100000
                        value: root.selectedItem ? Math.round(root.selectedItem.y) : 0
                        editable: true
                        Layout.fillWidth: true
                        onValueModified: root.updateProperty("y", value)
                    }

                    Label {
                        text: qsTr("Width:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    SpinBox {
                        from: 0
                        to: 100000
                        value: root.selectedItem ? Math.round(root.selectedItem.width) : 0
                        editable: true
                        Layout.fillWidth: true
                        onValueModified: root.updateProperty("width", value)
                    }

                    Label {
                        text: qsTr("Height:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    SpinBox {
                        from: 0
                        to: 100000
                        value: root.selectedItem ? Math.round(root.selectedItem.height) : 0
                        editable: true
                        Layout.fillWidth: true
                        onValueModified: root.updateProperty("height", value)
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                visible: !!root.selectedItem && root.selectedItem.type === "ellipse"

                Label {
                    text: qsTr("Ellipse")
                    font.pixelSize: 12
                    font.bold: true
                    color: root.labelColor
                }

                GridLayout {
                    columns: 2
                    rowSpacing: 4
                    columnSpacing: 8
                    Layout.fillWidth: true
                    enabled: !root.isLocked

                    Label {
                        text: qsTr("Center X:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    SpinBox {
                        from: -100000
                        to: 100000
                        value: root.selectedItem ? Math.round(root.selectedItem.centerX) : 0
                        editable: true
                        Layout.fillWidth: true
                        onValueModified: root.updateProperty("centerX", value)
                    }

                    Label {
                        text: qsTr("Center Y:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    SpinBox {
                        from: -100000
                        to: 100000
                        value: root.selectedItem ? Math.round(root.selectedItem.centerY) : 0
                        editable: true
                        Layout.fillWidth: true
                        onValueModified: root.updateProperty("centerY", value)
                    }

                    Label {
                        text: qsTr("Radius X:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    SpinBox {
                        from: 0
                        to: 100000
                        value: root.selectedItem ? Math.round(root.selectedItem.radiusX) : 0
                        editable: true
                        Layout.fillWidth: true
                        onValueModified: root.updateProperty("radiusX", value)
                    }

                    Label {
                        text: qsTr("Radius Y:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    SpinBox {
                        from: 0
                        to: 100000
                        value: root.selectedItem ? Math.round(root.selectedItem.radiusY) : 0
                        editable: true
                        Layout.fillWidth: true
                        onValueModified: root.updateProperty("radiusY", value)
                    }
                }
            }

            // Layer section - shown when a layer is selected
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                visible: !!root.selectedItem && root.selectedItem.type === "layer"

                Label {
                    text: qsTr("Layer")
                    font.pixelSize: 12
                    font.bold: true
                    color: root.labelColor
                }

                GridLayout {
                    columns: 2
                    rowSpacing: 4
                    columnSpacing: 8
                    Layout.fillWidth: true

                    Label {
                        text: qsTr("Name:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    Label {
                        text: root.selectedItem ? root.selectedItem.name : ""
                        font.pixelSize: root.labelSize
                        color: palette.text
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }
                }

                Label {
                    text: qsTr("Layers are used to organize items.")
                    font.pixelSize: 10
                    color: root.labelColor
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                    Layout.topMargin: 8
                }
            }

            // Path section - shown when a path is selected
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                visible: !!root.selectedItem && root.selectedItem.type === "path"

                Label {
                    text: qsTr("Path")
                    font.pixelSize: 12
                    font.bold: true
                    color: root.labelColor
                }

                GridLayout {
                    columns: 2
                    rowSpacing: 4
                    columnSpacing: 8
                    Layout.fillWidth: true
                    enabled: !root.isLocked

                    Label {
                        text: qsTr("Stroke Width:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    RowLayout {
                        spacing: 6
                        Layout.fillWidth: true

                        TextField {
                            id: pathStrokeWidthInput
                            Layout.fillWidth: true
                            text: root.isPathSelected && root.selectedItem.strokeWidth !== undefined ? root.selectedItem.strokeWidth.toString() : "1"
                            font.pixelSize: 10
                            inputMethodHints: Qt.ImhFormattedNumbersOnly
                            validator: DoubleValidator {
                                bottom: 0.1
                                top: 1000.0
                                decimals: 2
                            }
                            onEditingFinished: {
                                var v = parseFloat(text);
                                if (!isNaN(v) && v >= 0.1 && v <= 1000.0) {
                                    root.updateProperty("strokeWidth", v);
                                } else {
                                    text = root.selectedItem ? root.selectedItem.strokeWidth.toString() : "1";
                                }
                            }
                        }

                        Label {
                            text: qsTr("px")
                            font.pixelSize: root.labelSize
                            color: root.labelColor
                            Layout.alignment: Qt.AlignVCenter
                        }
                    }

                    Label {
                        text: qsTr("Stroke Color:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    RowLayout {
                        spacing: 6
                        Layout.fillWidth: true

                        Rectangle {
                            width: 28
                            height: 16
                            radius: 2
                            color: root.isPathSelected ? root.selectedItem.strokeColor : "transparent"
                            border.color: palette.mid
                            border.width: 1
                            Layout.alignment: Qt.AlignVCenter
                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    root.originalStrokeColor = root.selectedItem.strokeColor;
                                    canvasModel.beginTransaction();
                                    pathStrokeColorDialog.open();
                                }
                            }
                        }

                        TextField {
                            text: root.isPathSelected ? root.selectedItem.strokeColor : ""
                            font.pixelSize: 10
                            Layout.fillWidth: true
                            selectByMouse: true
                            onEditingFinished: root.updateProperty("strokeColor", text)
                        }
                    }

                    Label {
                        text: qsTr("Stroke Opacity:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        Slider {
                            id: pathStrokeOpacitySlider
                            Layout.fillWidth: true
                            Layout.preferredHeight: DV.Styles.height.sm
                            from: 0
                            to: 100
                            stepSize: 1
                            onPressedChanged: pressed ? canvasModel.beginTransaction() : canvasModel.endTransaction()
                            onValueChanged: if (pressed)
                                root.updateProperty("strokeOpacity", value / 100.0)
                            Component.onCompleted: value = root.selectedItem && root.selectedItem.strokeOpacity !== undefined ? Math.round(root.selectedItem.strokeOpacity * 100) : 100

                            Binding {
                                target: pathStrokeOpacitySlider
                                property: "value"
                                value: root.selectedItem && root.selectedItem.strokeOpacity !== undefined ? Math.round(root.selectedItem.strokeOpacity * 100) : 100
                                when: !pathStrokeOpacitySlider.pressed
                            }

                            background: Rectangle {
                                x: pathStrokeOpacitySlider.leftPadding
                                y: pathStrokeOpacitySlider.topPadding + pathStrokeOpacitySlider.availableHeight / 2 - height / 2
                                width: pathStrokeOpacitySlider.availableWidth
                                height: DV.Styles.height.xxxsm
                                implicitWidth: 80
                                implicitHeight: DV.Styles.height.xxxsm
                                radius: DV.Styles.rad.sm
                                color: palette.midlight

                                Rectangle {
                                    width: pathStrokeOpacitySlider.visualPosition * parent.width
                                    height: parent.height
                                    color: palette.highlight
                                    radius: DV.Styles.rad.sm
                                }
                            }

                            handle: Rectangle {
                                x: pathStrokeOpacitySlider.leftPadding + pathStrokeOpacitySlider.visualPosition * (pathStrokeOpacitySlider.availableWidth - width)
                                y: pathStrokeOpacitySlider.topPadding + pathStrokeOpacitySlider.availableHeight / 2 - height / 2
                                width: DV.Styles.height.xs
                                height: DV.Styles.height.xs
                                implicitWidth: DV.Styles.height.xs
                                implicitHeight: DV.Styles.height.xs
                                radius: DV.Styles.rad.lg
                                color: pathStrokeOpacitySlider.pressed ? palette.highlight : palette.text
                                border.color: palette.mid
                                border.width: 1
                            }
                        }

                        Label {
                            text: Math.round(pathStrokeOpacitySlider.value) + "%"
                            font.pixelSize: 11
                            color: palette.text
                            Layout.alignment: Qt.AlignVCenter
                        }
                    }

                    Label {
                        text: qsTr("Fill Color:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    RowLayout {
                        spacing: 6
                        Layout.fillWidth: true

                        Rectangle {
                            width: 28
                            height: 16
                            radius: 2
                            color: root.isPathSelected ? root.selectedItem.fillColor : "transparent"
                            border.color: palette.mid
                            border.width: 1
                            Layout.alignment: Qt.AlignVCenter
                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    root.originalFillColor = root.selectedItem.fillColor;
                                    canvasModel.beginTransaction();
                                    pathFillColorDialog.open();
                                }
                            }
                        }

                        TextField {
                            text: root.isPathSelected ? root.selectedItem.fillColor : ""
                            font.pixelSize: 10
                            Layout.fillWidth: true
                            selectByMouse: true
                            onEditingFinished: root.updateProperty("fillColor", text)
                        }
                    }

                    Label {
                        text: qsTr("Fill Opacity:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        Slider {
                            id: pathFillOpacitySlider
                            Layout.fillWidth: true
                            Layout.preferredHeight: DV.Styles.height.sm
                            from: 0
                            to: 100
                            stepSize: 1
                            onPressedChanged: pressed ? canvasModel.beginTransaction() : canvasModel.endTransaction()
                            onValueChanged: if (pressed)
                                root.updateProperty("fillOpacity", value / 100.0)
                            Component.onCompleted: value = root.selectedItem ? Math.round((root.selectedItem.fillOpacity || 0) * 100) : 0

                            Binding {
                                target: pathFillOpacitySlider
                                property: "value"
                                value: root.selectedItem ? Math.round((root.selectedItem.fillOpacity || 0) * 100) : 0
                                when: !pathFillOpacitySlider.pressed
                            }

                            background: Rectangle {
                                x: pathFillOpacitySlider.leftPadding
                                y: pathFillOpacitySlider.topPadding + pathFillOpacitySlider.availableHeight / 2 - height / 2
                                width: pathFillOpacitySlider.availableWidth
                                height: DV.Styles.height.xxxsm
                                implicitWidth: 80
                                implicitHeight: DV.Styles.height.xxxsm
                                radius: DV.Styles.rad.sm
                                color: palette.midlight

                                Rectangle {
                                    width: pathFillOpacitySlider.visualPosition * parent.width
                                    height: parent.height
                                    color: palette.highlight
                                    radius: DV.Styles.rad.sm
                                }
                            }

                            handle: Rectangle {
                                x: pathFillOpacitySlider.leftPadding + pathFillOpacitySlider.visualPosition * (pathFillOpacitySlider.availableWidth - width)
                                y: pathFillOpacitySlider.topPadding + pathFillOpacitySlider.availableHeight / 2 - height / 2
                                width: DV.Styles.height.xs
                                height: DV.Styles.height.xs
                                implicitWidth: DV.Styles.height.xs
                                implicitHeight: DV.Styles.height.xs
                                radius: DV.Styles.rad.lg
                                color: pathFillOpacitySlider.pressed ? palette.highlight : palette.text
                                border.color: palette.mid
                                border.width: 1
                            }
                        }

                        Label {
                            text: Math.round(pathFillOpacitySlider.value) + "%"
                            font.pixelSize: 11
                            color: palette.text
                            Layout.alignment: Qt.AlignVCenter
                        }
                    }
                }
            }

            // Text section - shown when a text item is selected
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                visible: root.isTextSelected

                Label {
                    text: qsTr("Text")
                    font.pixelSize: 12
                    font.bold: true
                    color: root.labelColor
                }

                GridLayout {
                    columns: 2
                    rowSpacing: 4
                    columnSpacing: 8
                    Layout.fillWidth: true
                    enabled: !root.isLocked

                    Label {
                        text: qsTr("X:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    SpinBox {
                        from: -100000
                        to: 100000
                        value: root.selectedItem ? Math.round(root.selectedItem.x) : 0
                        editable: true
                        Layout.fillWidth: true
                        onValueModified: root.updateProperty("x", value)
                    }

                    Label {
                        text: qsTr("Y:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    SpinBox {
                        from: -100000
                        to: 100000
                        value: root.selectedItem ? Math.round(root.selectedItem.y) : 0
                        editable: true
                        Layout.fillWidth: true
                        onValueModified: root.updateProperty("y", value)
                    }

                    Label {
                        text: qsTr("Text:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    TextField {
                        Layout.fillWidth: true
                        text: root.isTextSelected ? root.selectedItem.text : ""
                        font.pixelSize: 10
                        selectByMouse: true
                        onEditingFinished: root.updateProperty("text", text)
                    }

                    Label {
                        text: qsTr("Font:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    ComboBox {
                        id: fontFamilyCombo
                        Layout.fillWidth: true
                        model: fontProvider ? fontProvider.fonts : []
                        currentIndex: root.isTextSelected && fontProvider ? fontProvider.indexOf(root.selectedItem.fontFamily) : 0
                        onActivated: root.updateProperty("fontFamily", model[currentIndex])

                        contentItem: Text {
                            text: fontFamilyCombo.displayText
                            color: palette.text
                            font.pixelSize: 10
                            font.family: fontFamilyCombo.displayText
                            verticalAlignment: Text.AlignVCenter
                            leftPadding: 6
                            elide: Text.ElideRight
                        }
                    }

                    Label {
                        text: qsTr("Size:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    RowLayout {
                        spacing: 6
                        Layout.fillWidth: true

                        ComboBox {
                            id: textFontSizeCombo
                            Layout.fillWidth: true
                            editable: true
                            model: [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 64, 72, 96, 128]

                            currentIndex: {
                                if (!root.isTextSelected)
                                    return 6; // Default to 16
                                var idx = model.indexOf(Math.round(root.selectedItem.fontSize));
                                return idx >= 0 ? idx : -1;
                            }

                            Component.onCompleted: {
                                editText = root.isTextSelected ? Math.round(root.selectedItem.fontSize).toString() : "16";
                            }

                            onCurrentIndexChanged: {
                                if (currentIndex >= 0 && root.isTextSelected) {
                                    root.updateProperty("fontSize", model[currentIndex]);
                                }
                            }

                            onAccepted: {
                                var value = parseFloat(editText);
                                if (!isNaN(value) && value >= 8 && value <= 200 && root.isTextSelected) {
                                    root.updateProperty("fontSize", Math.round(value));
                                }
                                editText = root.isTextSelected ? Math.round(root.selectedItem.fontSize).toString() : "16";
                            }

                            Connections {
                                target: root
                                function onSelectedItemChanged() {
                                    if (root.isTextSelected) {
                                        textFontSizeCombo.editText = Math.round(root.selectedItem.fontSize).toString();
                                    }
                                }
                            }

                            validator: IntValidator {
                                bottom: 8
                                top: 200
                            }

                            contentItem: TextInput {
                                text: textFontSizeCombo.editText
                                font.pixelSize: 10
                                color: palette.text
                                verticalAlignment: Text.AlignVCenter
                                horizontalAlignment: Text.AlignLeft
                                leftPadding: 6
                                selectByMouse: true
                                validator: textFontSizeCombo.validator

                                onTextChanged: textFontSizeCombo.editText = text
                                onAccepted: textFontSizeCombo.accepted()
                            }
                        }

                        Label {
                            text: qsTr("pt")
                            font.pixelSize: root.labelSize
                            color: root.labelColor
                            Layout.alignment: Qt.AlignVCenter
                        }
                    }

                    Label {
                        text: qsTr("Color:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    RowLayout {
                        spacing: 6
                        Layout.fillWidth: true

                        Rectangle {
                            width: 28
                            height: 16
                            radius: 2
                            color: root.isTextSelected ? root.selectedItem.textColor : "transparent"
                            border.color: palette.mid
                            border.width: 1
                            Layout.alignment: Qt.AlignVCenter
                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    canvasModel.beginTransaction();
                                    textColorDialog.open();
                                }
                            }
                        }

                        TextField {
                            text: root.isTextSelected ? root.selectedItem.textColor : ""
                            font.pixelSize: 10
                            Layout.fillWidth: true
                            selectByMouse: true
                            onEditingFinished: root.updateProperty("textColor", text)
                        }
                    }

                    Label {
                        text: qsTr("Opacity:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        Slider {
                            id: textOpacitySlider
                            Layout.fillWidth: true
                            Layout.preferredHeight: DV.Styles.height.sm
                            from: 0
                            to: 100
                            stepSize: 1
                            onPressedChanged: pressed ? canvasModel.beginTransaction() : canvasModel.endTransaction()
                            onValueChanged: if (pressed)
                                root.updateProperty("textOpacity", value / 100.0)
                            Component.onCompleted: value = root.selectedItem && root.selectedItem.textOpacity !== undefined ? Math.round(root.selectedItem.textOpacity * 100) : 100

                            Binding {
                                target: textOpacitySlider
                                property: "value"
                                value: root.selectedItem && root.selectedItem.textOpacity !== undefined ? Math.round(root.selectedItem.textOpacity * 100) : 100
                                when: !textOpacitySlider.pressed
                            }

                            background: Rectangle {
                                x: textOpacitySlider.leftPadding
                                y: textOpacitySlider.topPadding + textOpacitySlider.availableHeight / 2 - height / 2
                                width: textOpacitySlider.availableWidth
                                height: DV.Styles.height.xxxsm
                                implicitWidth: 80
                                implicitHeight: DV.Styles.height.xxxsm
                                radius: DV.Styles.rad.sm
                                color: palette.midlight

                                Rectangle {
                                    width: textOpacitySlider.visualPosition * parent.width
                                    height: parent.height
                                    color: palette.highlight
                                    radius: DV.Styles.rad.sm
                                }
                            }

                            handle: Rectangle {
                                x: textOpacitySlider.leftPadding + textOpacitySlider.visualPosition * (textOpacitySlider.availableWidth - width)
                                y: textOpacitySlider.topPadding + textOpacitySlider.availableHeight / 2 - height / 2
                                width: DV.Styles.height.xs
                                height: DV.Styles.height.xs
                                implicitWidth: DV.Styles.height.xs
                                implicitHeight: DV.Styles.height.xs
                                radius: DV.Styles.rad.lg
                                color: textOpacitySlider.pressed ? palette.highlight : palette.text
                                border.color: palette.mid
                                border.width: 1
                            }
                        }

                        Label {
                            text: Math.round(textOpacitySlider.value) + "%"
                            font.pixelSize: 11
                            color: palette.text
                            Layout.alignment: Qt.AlignVCenter
                        }
                    }
                }

                ColorDialog {
                    id: textColorDialog
                    title: qsTr("Choose Text Color")
                    onVisibleChanged: {
                        if (visible) {
                            selectedColor = root.isTextSelected ? root.selectedItem.textColor : palette.text;
                        }
                    }
                    onSelectedColorChanged: root.updateProperty("textColor", selectedColor.toString())
                    onAccepted: canvasModel.endTransaction()
                    onRejected: canvasModel.endTransaction()
                }
            }

            // Appearance section - only for shapes (rectangle, ellipse)
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                visible: root.isShapeSelected
                enabled: !root.isLocked

                PropertySeparator {}

                Label {
                    text: qsTr("Appearance")
                    font.pixelSize: 12
                    font.bold: true
                    color: root.labelColor
                }

                GridLayout {
                    columns: 2
                    rowSpacing: 4
                    columnSpacing: 8
                    Layout.fillWidth: true

                    Label {
                        text: qsTr("Stroke Width:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    SpinBox {
                        from: 1
                        to: 1000
                        stepSize: 1
                        value: root.selectedItem ? Math.round(root.selectedItem.strokeWidth * 10) : 10
                        editable: true
                        Layout.fillWidth: true
                        property real realValue: value / 10.0
                        textFromValue: function (value, locale) {
                            return Number(value / 10.0).toLocaleString(locale, 'f', 1) + " px";
                        }
                        valueFromText: function (text, locale) {
                            return Math.round(Number.fromLocaleString(locale, text.replace(" px", "")) * 10);
                        }
                        onValueModified: root.updateProperty("strokeWidth", realValue)
                    }

                    Label {
                        text: qsTr("Stroke Color:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    RowLayout {
                        spacing: 4
                        Layout.fillWidth: true
                        Button {
                            Layout.preferredWidth: 16
                            Layout.preferredHeight: 16
                            onClicked: {
                                root.originalStrokeColor = root.selectedItem.strokeColor;
                                canvasModel.beginTransaction();
                                strokeColorDialog.open();
                            }
                            background: Rectangle {
                                color: root.isShapeSelected ? root.selectedItem.strokeColor : "transparent"
                                border.color: palette.mid
                                border.width: 1
                                radius: DV.Styles.rad.sm
                            }
                        }
                        TextField {
                            text: root.isShapeSelected ? root.selectedItem.strokeColor : ""
                            font.pixelSize: 10
                            Layout.fillWidth: true
                            selectByMouse: true
                            onEditingFinished: root.updateProperty("strokeColor", text)
                        }
                    }

                    Label {
                        text: qsTr("Stroke Opacity:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    RowLayout {
                        spacing: 8
                        Layout.fillWidth: true
                        Slider {
                            id: strokeOpacitySlider
                            Layout.fillWidth: true
                            Layout.preferredHeight: DV.Styles.height.sm
                            implicitHeight: DV.Styles.height.sm
                            from: 0
                            to: 100
                            stepSize: 1
                            value: 100

                            onPressedChanged: pressed ? canvasModel.beginTransaction() : canvasModel.endTransaction()
                            onValueChanged: if (pressed)
                                root.updateProperty("strokeOpacity", value / 100.0)
                            Component.onCompleted: value = root.selectedItem && root.selectedItem.strokeOpacity !== undefined ? Math.round(root.selectedItem.strokeOpacity * 100) : 100

                            Binding {
                                target: strokeOpacitySlider
                                property: "value"
                                value: root.selectedItem && root.selectedItem.strokeOpacity !== undefined ? Math.round(root.selectedItem.strokeOpacity * 100) : 100
                                when: !strokeOpacitySlider.pressed
                            }

                            background: Rectangle {
                                x: strokeOpacitySlider.leftPadding
                                y: strokeOpacitySlider.topPadding + strokeOpacitySlider.availableHeight / 2 - height / 2
                                width: strokeOpacitySlider.availableWidth
                                height: DV.Styles.height.xxxsm
                                implicitWidth: 80
                                implicitHeight: DV.Styles.height.xxxsm
                                radius: DV.Styles.rad.sm
                                color: palette.midlight
                                Rectangle {
                                    width: strokeOpacitySlider.visualPosition * parent.width
                                    height: parent.height
                                    color: palette.highlight
                                    radius: DV.Styles.rad.sm
                                }
                            }
                            handle: Rectangle {
                                x: strokeOpacitySlider.leftPadding + strokeOpacitySlider.visualPosition * (strokeOpacitySlider.availableWidth - width)
                                y: strokeOpacitySlider.topPadding + strokeOpacitySlider.availableHeight / 2 - height / 2
                                width: DV.Styles.height.xs
                                height: DV.Styles.height.xs
                                implicitWidth: DV.Styles.height.xs
                                implicitHeight: DV.Styles.height.xs
                                radius: DV.Styles.rad.lg
                                color: strokeOpacitySlider.pressed ? palette.highlight : palette.text
                                border.color: palette.mid
                                border.width: 1
                            }
                        }
                        Label {
                            text: Math.round(strokeOpacitySlider.value) + "%"
                            font.pixelSize: 11
                            color: palette.text
                            Layout.preferredWidth: 40
                        }
                    }
                }

                PropertySeparator {}

                GridLayout {
                    columns: 2
                    rowSpacing: 4
                    columnSpacing: 8
                    Layout.fillWidth: true

                    Label {
                        text: qsTr("Fill Color:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    RowLayout {
                        spacing: 4
                        Layout.fillWidth: true
                        Button {
                            Layout.preferredWidth: 16
                            Layout.preferredHeight: 16
                            onClicked: {
                                root.originalFillColor = root.selectedItem.fillColor;
                                canvasModel.beginTransaction();
                                fillColorDialog.open();
                            }
                            background: Rectangle {
                                color: root.isShapeSelected ? root.selectedItem.fillColor : "transparent"
                                border.color: palette.mid
                                border.width: 1
                                radius: DV.Styles.rad.sm
                            }
                        }
                        TextField {
                            text: root.isShapeSelected ? root.selectedItem.fillColor : ""
                            font.pixelSize: 10
                            Layout.fillWidth: true
                            selectByMouse: true
                            onEditingFinished: root.updateProperty("fillColor", text)
                        }
                    }

                    Label {
                        text: qsTr("Fill Opacity:")
                        font.pixelSize: root.labelSize
                        color: root.labelColor
                    }
                    RowLayout {
                        spacing: 8
                        Layout.fillWidth: true
                        Slider {
                            id: opacitySlider
                            Layout.fillWidth: true
                            Layout.preferredHeight: DV.Styles.height.sm
                            implicitHeight: DV.Styles.height.sm
                            from: 0
                            to: 100
                            stepSize: 1
                            value: 0

                            onPressedChanged: pressed ? canvasModel.beginTransaction() : canvasModel.endTransaction()
                            onValueChanged: if (pressed)
                                root.updateProperty("fillOpacity", value / 100.0)
                            Component.onCompleted: value = root.selectedItem ? Math.round(root.selectedItem.fillOpacity * 100) : 0

                            Binding {
                                target: opacitySlider
                                property: "value"
                                value: root.selectedItem ? Math.round(root.selectedItem.fillOpacity * 100) : 0
                                when: !opacitySlider.pressed
                            }

                            background: Rectangle {
                                x: opacitySlider.leftPadding
                                y: opacitySlider.topPadding + opacitySlider.availableHeight / 2 - height / 2
                                width: opacitySlider.availableWidth
                                height: DV.Styles.height.xxxsm
                                implicitWidth: 80
                                implicitHeight: DV.Styles.height.xxxsm
                                radius: DV.Styles.rad.sm
                                color: palette.midlight
                                Rectangle {
                                    width: opacitySlider.visualPosition * parent.width
                                    height: parent.height
                                    color: palette.highlight
                                    radius: DV.Styles.rad.sm
                                }
                            }
                            handle: Rectangle {
                                x: opacitySlider.leftPadding + opacitySlider.visualPosition * (opacitySlider.availableWidth - width)
                                y: opacitySlider.topPadding + opacitySlider.availableHeight / 2 - height / 2
                                width: DV.Styles.height.xs
                                height: DV.Styles.height.xs
                                implicitWidth: DV.Styles.height.xs
                                implicitHeight: DV.Styles.height.xs
                                radius: DV.Styles.rad.lg
                                color: opacitySlider.pressed ? palette.highlight : palette.text
                                border.color: palette.mid
                                border.width: 1
                            }
                        }
                        Label {
                            text: Math.round(opacitySlider.value) + "%"
                            font.pixelSize: 11
                            color: palette.text
                            Layout.preferredWidth: 40
                        }
                    }
                }

                ColorDialog {
                    id: strokeColorDialog
                    title: qsTr("Choose Stroke Color")
                    selectedColor: root.isShapeSelected ? root.selectedItem.strokeColor : palette.text
                    onSelectedColorChanged: root.updateProperty("strokeColor", selectedColor.toString())
                    onAccepted: canvasModel.endTransaction()
                    onRejected: {
                        root.updateProperty("strokeColor", root.originalStrokeColor);
                        canvasModel.endTransaction();
                    }
                }

                ColorDialog {
                    id: pathStrokeColorDialog
                    title: qsTr("Choose Stroke Color")
                    onVisibleChanged: {
                        if (visible) {
                            selectedColor = root.isPathSelected ? root.selectedItem.strokeColor : palette.text;
                        }
                    }
                    onSelectedColorChanged: root.updateProperty("strokeColor", selectedColor.toString())
                    onAccepted: canvasModel.endTransaction()
                    onRejected: {
                        root.updateProperty("strokeColor", root.originalStrokeColor);
                        canvasModel.endTransaction();
                    }
                }

                ColorDialog {
                    id: pathFillColorDialog
                    title: qsTr("Choose Fill Color")
                    onVisibleChanged: {
                        if (visible) {
                            selectedColor = root.isPathSelected ? root.selectedItem.fillColor : palette.text;
                        }
                    }
                    onSelectedColorChanged: root.updateProperty("fillColor", selectedColor.toString())
                    onAccepted: canvasModel.endTransaction()
                    onRejected: {
                        root.updateProperty("fillColor", root.originalFillColor);
                        canvasModel.endTransaction();
                    }
                }

                ColorDialog {
                    id: fillColorDialog
                    title: qsTr("Choose Fill Color")
                    selectedColor: root.isShapeSelected ? root.selectedItem.fillColor : palette.text
                    onSelectedColorChanged: root.updateProperty("fillColor", selectedColor.toString())
                    onAccepted: canvasModel.endTransaction()
                    onRejected: {
                        root.updateProperty("fillColor", root.originalFillColor);
                        canvasModel.endTransaction();
                    }
                }
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredHeight: root.availableHeight
            visible: root.selectedItem === null

            Label {
                anchors.centerIn: parent
                text: qsTr("No object selected")
                font.pixelSize: 12
                color: palette.text
            }
        }

        Item {
            Layout.fillHeight: true
            visible: root.selectedItem !== null
        }
    }
}
