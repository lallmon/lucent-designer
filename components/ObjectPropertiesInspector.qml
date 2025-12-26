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

    property var selectedItem: null
    property string originalStrokeColor: ""
    property string originalFillColor: ""
    
    // Helper to check if selected item is a shape with stroke/fill properties
    readonly property bool isShapeSelected: selectedItem !== null && 
        (selectedItem.type === "rectangle" || selectedItem.type === "ellipse")
    
    readonly property int labelSize: 11
    readonly property color labelColor: DV.Theme.colors.textSubtle
    
    function updateProperty(property, value) {
        if (selectedItem && DV.SelectionManager.selectedItemIndex >= 0) {
            canvasModel.updateItem(DV.SelectionManager.selectedItemIndex, {[property]: value})
        }
    }
    
    component PropertySeparator: Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 1
        color: DV.Theme.colors.borderSubtle
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
            color: "white"
            Layout.fillWidth: true
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: DV.Theme.colors.borderSubtle
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.topMargin: 4
            spacing: 8
            visible: root.selectedItem !== null

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                visible: root.selectedItem && root.selectedItem.type === "rectangle"

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

                    Label { text: qsTr("X:"); font.pixelSize: root.labelSize; color: root.labelColor }
                    SpinBox {
                        from: -100000; to: 100000
                        value: root.selectedItem ? Math.round(root.selectedItem.x) : 0
                        editable: true
                        Layout.fillWidth: true
                        onValueModified: root.updateProperty("x", value)
                    }

                    Label { text: qsTr("Y:"); font.pixelSize: root.labelSize; color: root.labelColor }
                    SpinBox {
                        from: -100000; to: 100000
                        value: root.selectedItem ? Math.round(root.selectedItem.y) : 0
                        editable: true
                        Layout.fillWidth: true
                        onValueModified: root.updateProperty("y", value)
                    }

                    Label { text: qsTr("Width:"); font.pixelSize: root.labelSize; color: root.labelColor }
                    SpinBox {
                        from: 0; to: 100000
                        value: root.selectedItem ? Math.round(root.selectedItem.width) : 0
                        editable: true
                        Layout.fillWidth: true
                        onValueModified: root.updateProperty("width", value)
                    }

                    Label { text: qsTr("Height:"); font.pixelSize: root.labelSize; color: root.labelColor }
                    SpinBox {
                        from: 0; to: 100000
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
                visible: root.selectedItem && root.selectedItem.type === "ellipse"

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

                    Label { text: qsTr("Center X:"); font.pixelSize: root.labelSize; color: root.labelColor }
                    SpinBox {
                        from: -100000; to: 100000
                        value: root.selectedItem ? Math.round(root.selectedItem.centerX) : 0
                        editable: true
                        Layout.fillWidth: true
                        onValueModified: root.updateProperty("centerX", value)
                    }

                    Label { text: qsTr("Center Y:"); font.pixelSize: root.labelSize; color: root.labelColor }
                    SpinBox {
                        from: -100000; to: 100000
                        value: root.selectedItem ? Math.round(root.selectedItem.centerY) : 0
                        editable: true
                        Layout.fillWidth: true
                        onValueModified: root.updateProperty("centerY", value)
                    }

                    Label { text: qsTr("Radius X:"); font.pixelSize: root.labelSize; color: root.labelColor }
                    SpinBox {
                        from: 0; to: 100000
                        value: root.selectedItem ? Math.round(root.selectedItem.radiusX) : 0
                        editable: true
                        Layout.fillWidth: true
                        onValueModified: root.updateProperty("radiusX", value)
                    }

                    Label { text: qsTr("Radius Y:"); font.pixelSize: root.labelSize; color: root.labelColor }
                    SpinBox {
                        from: 0; to: 100000
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
                visible: root.selectedItem && root.selectedItem.type === "layer"

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

                    Label { text: qsTr("Name:"); font.pixelSize: root.labelSize; color: root.labelColor }
                    Label {
                        text: root.selectedItem ? root.selectedItem.name : ""
                        font.pixelSize: root.labelSize
                        color: "white"
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

            // Appearance section - only for shapes (rectangle, ellipse)
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                visible: root.isShapeSelected

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

                    Label { text: qsTr("Stroke Width:"); font.pixelSize: root.labelSize; color: root.labelColor }
                    SpinBox {
                        from: 1; to: 1000; stepSize: 1
                        value: root.selectedItem ? Math.round(root.selectedItem.strokeWidth * 10) : 10
                        editable: true
                        Layout.fillWidth: true
                        property real realValue: value / 10.0
                        textFromValue: function(value, locale) {
                            return Number(value / 10.0).toLocaleString(locale, 'f', 1) + " px"
                        }
                        valueFromText: function(text, locale) {
                            return Math.round(Number.fromLocaleString(locale, text.replace(" px", "")) * 10)
                        }
                        onValueModified: root.updateProperty("strokeWidth", realValue)
                    }

                    Label { text: qsTr("Stroke Color:"); font.pixelSize: root.labelSize; color: root.labelColor }
                    RowLayout {
                        spacing: 4
                        Layout.fillWidth: true
                        Button {
                            Layout.preferredWidth: 16
                            Layout.preferredHeight: 16
                            onClicked: {
                                root.originalStrokeColor = root.selectedItem.strokeColor
                                canvasModel.beginTransaction()
                                strokeColorDialog.open()
                            }
                            background: Rectangle {
                                color: root.isShapeSelected ? root.selectedItem.strokeColor : "transparent"
                                border.color: DV.Theme.colors.borderSubtle
                                border.width: 1
                                radius: DV.Theme.sizes.radiusSm
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

                    Label { text: qsTr("Stroke Opacity:"); font.pixelSize: root.labelSize; color: root.labelColor }
                    RowLayout {
                        spacing: 8
                        Layout.fillWidth: true
                        Slider {
                            id: strokeOpacitySlider
                            Layout.fillWidth: true
                            Layout.preferredHeight: DV.Theme.sizes.sliderHeight
                            implicitHeight: DV.Theme.sizes.sliderHeight
                            from: 0; to: 100; stepSize: 1; value: 100

                            onPressedChanged: pressed ? canvasModel.beginTransaction() : canvasModel.endTransaction()
                            onValueChanged: if (pressed) root.updateProperty("strokeOpacity", value / 100.0)
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
                                height: DV.Theme.sizes.sliderTrackHeight
                                implicitWidth: 80
                                implicitHeight: DV.Theme.sizes.sliderTrackHeight
                                radius: DV.Theme.sizes.radiusSm
                                color: DV.Theme.colors.gridMinor
                                Rectangle {
                                    width: strokeOpacitySlider.visualPosition * parent.width
                                    height: parent.height
                                    color: DV.Theme.colors.accent
                                    radius: DV.Theme.sizes.radiusSm
                                }
                            }
                            handle: Rectangle {
                                x: strokeOpacitySlider.leftPadding + strokeOpacitySlider.visualPosition * (strokeOpacitySlider.availableWidth - width)
                                y: strokeOpacitySlider.topPadding + strokeOpacitySlider.availableHeight / 2 - height / 2
                                width: DV.Theme.sizes.sliderHandleSize
                                height: DV.Theme.sizes.sliderHandleSize
                                implicitWidth: DV.Theme.sizes.sliderHandleSize
                                implicitHeight: DV.Theme.sizes.sliderHandleSize
                                radius: DV.Theme.sizes.radiusLg
                                color: strokeOpacitySlider.pressed ? DV.Theme.colors.accent : "#ffffff"
                                border.color: DV.Theme.colors.borderSubtle
                                border.width: 1
                            }
                        }
                        Label {
                            text: Math.round(strokeOpacitySlider.value) + "%"
                            font.pixelSize: 11
                            color: "white"
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

                    Label { text: qsTr("Fill Color:"); font.pixelSize: root.labelSize; color: root.labelColor }
                    RowLayout {
                        spacing: 4
                        Layout.fillWidth: true
                        Button {
                            Layout.preferredWidth: 16
                            Layout.preferredHeight: 16
                            onClicked: {
                                root.originalFillColor = root.selectedItem.fillColor
                                canvasModel.beginTransaction()
                                fillColorDialog.open()
                            }
                            background: Rectangle {
                                color: root.isShapeSelected ? root.selectedItem.fillColor : "transparent"
                                border.color: DV.Theme.colors.borderSubtle
                                border.width: 1
                                radius: DV.Theme.sizes.radiusSm
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

                    Label { text: qsTr("Fill Opacity:"); font.pixelSize: root.labelSize; color: root.labelColor }
                    RowLayout {
                        spacing: 8
                        Layout.fillWidth: true
                        Slider {
                            id: opacitySlider
                            Layout.fillWidth: true
                            Layout.preferredHeight: DV.Theme.sizes.sliderHeight
                            implicitHeight: DV.Theme.sizes.sliderHeight
                            from: 0; to: 100; stepSize: 1; value: 0

                            onPressedChanged: pressed ? canvasModel.beginTransaction() : canvasModel.endTransaction()
                            onValueChanged: if (pressed) root.updateProperty("fillOpacity", value / 100.0)
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
                                height: DV.Theme.sizes.sliderTrackHeight
                                implicitWidth: 80
                                implicitHeight: DV.Theme.sizes.sliderTrackHeight
                                radius: DV.Theme.sizes.radiusSm
                                color: DV.Theme.colors.gridMinor
                                Rectangle {
                                    width: opacitySlider.visualPosition * parent.width
                                    height: parent.height
                                    color: DV.Theme.colors.accent
                                    radius: DV.Theme.sizes.radiusSm
                                }
                            }
                            handle: Rectangle {
                                x: opacitySlider.leftPadding + opacitySlider.visualPosition * (opacitySlider.availableWidth - width)
                                y: opacitySlider.topPadding + opacitySlider.availableHeight / 2 - height / 2
                                width: DV.Theme.sizes.sliderHandleSize
                                height: DV.Theme.sizes.sliderHandleSize
                                implicitWidth: DV.Theme.sizes.sliderHandleSize
                                implicitHeight: DV.Theme.sizes.sliderHandleSize
                                radius: DV.Theme.sizes.radiusLg
                                color: opacitySlider.pressed ? DV.Theme.colors.accent : "#ffffff"
                                border.color: DV.Theme.colors.borderSubtle
                                border.width: 1
                            }
                        }
                        Label {
                            text: Math.round(opacitySlider.value) + "%"
                            font.pixelSize: 11
                            color: "white"
                            Layout.preferredWidth: 40
                        }
                    }
                }

                ColorDialog {
                    id: strokeColorDialog
                    title: qsTr("Choose Stroke Color")
                    selectedColor: root.isShapeSelected ? root.selectedItem.strokeColor : "#ffffff"
                    onSelectedColorChanged: root.updateProperty("strokeColor", selectedColor.toString())
                    onAccepted: canvasModel.endTransaction()
                    onRejected: {
                        root.updateProperty("strokeColor", root.originalStrokeColor)
                        canvasModel.endTransaction()
                    }
                }

                ColorDialog {
                    id: fillColorDialog
                    title: qsTr("Choose Fill Color")
                    selectedColor: root.isShapeSelected ? root.selectedItem.fillColor : "#ffffff"
                    onSelectedColorChanged: root.updateProperty("fillColor", selectedColor.toString())
                    onAccepted: canvasModel.endTransaction()
                    onRejected: {
                        root.updateProperty("fillColor", root.originalFillColor)
                        canvasModel.endTransaction()
                    }
                }
            }
        }

        Label {
            visible: root.selectedItem === null
            text: qsTr("No object selected")
            font.pixelSize: 12
            color: DV.Theme.colors.textSubtle
            Layout.fillWidth: true
            Layout.topMargin: 8
        }

        Item {
            Layout.fillHeight: true
        }
    }
}
