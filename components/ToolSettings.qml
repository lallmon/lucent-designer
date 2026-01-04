import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import "." as DV

ToolBar {
    id: root
    height: 48
    property ToolDefaults toolDefaults: ToolDefaults {}

    property string activeTool: ""  // Current tool ("select", "rectangle", "ellipse", etc.)
    readonly property SystemPalette palette: DV.PaletteBridge.active

    property real rectangleStrokeWidth: 1
    property color rectangleStrokeColor: toolDefaults.defaultStrokeColor
    property real rectangleStrokeOpacity: 1.0
    property color rectangleFillColor: toolDefaults.defaultFillColor
    property real rectangleFillOpacity: toolDefaults.defaultFillOpacity

    property real ellipseStrokeWidth: 1
    property color ellipseStrokeColor: toolDefaults.defaultStrokeColor
    property real ellipseStrokeOpacity: 1.0
    property color ellipseFillColor: toolDefaults.defaultFillColor
    property real ellipseFillOpacity: toolDefaults.defaultFillOpacity

    property real penStrokeWidth: 1
    property color penStrokeColor: toolDefaults.defaultStrokeColor
    property real penStrokeOpacity: 1.0
    property color penFillColor: toolDefaults.defaultFillColor
    property real penFillOpacity: toolDefaults.defaultFillOpacity

    property string textFontFamily: "Sans Serif"
    property real textFontSize: 16
    property color textColor: toolDefaults.defaultStrokeColor
    property real textOpacity: 1.0

    readonly property var toolSettings: ({
            "rectangle": {
                strokeWidth: rectangleStrokeWidth,
                strokeColor: rectangleStrokeColor,
                strokeOpacity: rectangleStrokeOpacity,
                fillColor: rectangleFillColor,
                fillOpacity: rectangleFillOpacity
            },
            "ellipse": {
                strokeWidth: ellipseStrokeWidth,
                strokeColor: ellipseStrokeColor,
                strokeOpacity: ellipseStrokeOpacity,
                fillColor: ellipseFillColor,
                fillOpacity: ellipseFillOpacity
            },
            "pen": {
                strokeWidth: penStrokeWidth,
                strokeColor: penStrokeColor,
                strokeOpacity: penStrokeOpacity,
                fillColor: penFillColor,
                fillOpacity: penFillOpacity
            },
            "text": {
                fontFamily: textFontFamily,
                fontSize: textFontSize,
                textColor: textColor,
                textOpacity: textOpacity
            }
        })

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 8
        anchors.rightMargin: 8
        spacing: 8

        // Rectangle tool settings
        RowLayout {
            id: rectangleSettings
            visible: root.activeTool === "rectangle"
            Layout.fillHeight: true
            Layout.alignment: Qt.AlignVCenter
            spacing: 6

            Label {
                text: qsTr("Stroke Width:")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            TextField {
                id: strokeWidthInput
                Layout.preferredWidth: 50
                Layout.preferredHeight: DV.Styles.height.md
                Layout.alignment: Qt.AlignVCenter
                text: root.rectangleStrokeWidth.toString()
                horizontalAlignment: TextInput.AlignHCenter
                font.pixelSize: 11
                validator: DoubleValidator {
                    bottom: 0.1
                    top: 100.0
                    decimals: 1
                }

                function commitValue() {
                    var value = parseFloat(text);
                    if (!isNaN(value) && value >= 0.1 && value <= 100.0) {
                        root.rectangleStrokeWidth = value;
                    } else {
                        // Reset to current value if invalid
                        text = root.rectangleStrokeWidth.toString();
                    }
                }

                onEditingFinished: {
                    commitValue();
                }

                onActiveFocusChanged: {
                    if (!activeFocus) {
                        commitValue();
                    }
                }

                background: Rectangle {
                    color: palette.base
                    border.color: strokeWidthInput.activeFocus ? palette.highlight : palette.mid
                    border.width: 1
                    radius: DV.Styles.rad.sm
                }

                color: palette.text
            }

            Label {
                text: qsTr("px")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            // Separator
            Rectangle {
                Layout.preferredWidth: 1
                Layout.preferredHeight: 16
                Layout.alignment: Qt.AlignVCenter
                Layout.leftMargin: 6
                Layout.rightMargin: 6
                color: palette.mid
            }

            Label {
                text: qsTr("Stroke Color:")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            Button {
                id: strokeColorButton
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16
                Layout.alignment: Qt.AlignVCenter

                onClicked: {
                    strokeColorDialog.open();
                }

                background: Rectangle {
                    color: root.rectangleStrokeColor
                    border.color: palette.mid
                    border.width: 1
                    radius: DV.Styles.rad.sm
                }
            }

            Label {
                text: qsTr("Opacity:")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            Slider {
                id: strokeOpacitySlider
                Layout.preferredWidth: 80
                Layout.preferredHeight: DV.Styles.height.sm
                implicitHeight: DV.Styles.height.sm
                Layout.alignment: Qt.AlignVCenter
                from: 0
                to: 100
                stepSize: 1
                value: 100

                onPressedChanged: {
                    if (!pressed) {
                        root.rectangleStrokeOpacity = value / 100.0;
                    }
                }

                onValueChanged: {
                    root.rectangleStrokeOpacity = value / 100.0;
                }

                Component.onCompleted: {
                    value = Math.round(root.rectangleStrokeOpacity * 100);
                }

                Binding {
                    target: strokeOpacitySlider
                    property: "value"
                    value: Math.round(root.rectangleStrokeOpacity * 100)
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
                    color: palette.base

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
                    color: strokeOpacitySlider.pressed ? palette.highlight : palette.button
                    border.color: palette.mid
                    border.width: 1
                }
            }

            TextField {
                id: strokeOpacityInput
                Layout.preferredWidth: 35
                Layout.preferredHeight: DV.Styles.height.md
                Layout.alignment: Qt.AlignVCenter
                text: Math.round(root.rectangleStrokeOpacity * 100).toString()
                horizontalAlignment: TextInput.AlignHCenter
                font.pixelSize: 11
                validator: IntValidator {
                    bottom: 0
                    top: 100
                }

                function commitValue() {
                    var value = parseInt(text);
                    if (!isNaN(value) && value >= 0 && value <= 100) {
                        root.rectangleStrokeOpacity = value / 100.0;
                        console.log("Stroke opacity set to:", root.rectangleStrokeOpacity);
                    } else {
                        text = Math.round(root.rectangleStrokeOpacity * 100).toString();
                    }
                }

                onEditingFinished: {
                    commitValue();
                }

                onActiveFocusChanged: {
                    if (!activeFocus) {
                        commitValue();
                    }
                }

                Connections {
                    target: root
                    function onRectangleStrokeOpacityChanged() {
                        if (!strokeOpacityInput.activeFocus) {
                            strokeOpacityInput.text = Math.round(root.rectangleStrokeOpacity * 100).toString();
                        }
                    }
                }

                background: Rectangle {
                    color: palette.base
                    border.color: strokeOpacityInput.activeFocus ? palette.highlight : palette.mid
                    border.width: 1
                    radius: DV.Styles.rad.sm
                }

                color: palette.text
            }

            Label {
                text: qsTr("%")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            // Separator
            Rectangle {
                Layout.preferredWidth: 1
                Layout.preferredHeight: 16
                Layout.alignment: Qt.AlignVCenter
                Layout.leftMargin: 6
                Layout.rightMargin: 6
                color: palette.mid
            }

            Label {
                text: qsTr("Fill Color:")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            Button {
                id: fillColorButton
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16
                Layout.alignment: Qt.AlignVCenter

                onClicked: {
                    fillColorDialog.open();
                }

                background: Rectangle {
                    border.color: palette.mid
                    border.width: 1
                    radius: DV.Styles.rad.sm
                    color: "transparent"
                    clip: true

                    // Checkerboard pattern to show transparency
                    Canvas {
                        anchors.fill: parent
                        z: 0
                        property color checkerLight: palette.midlight
                        property color checkerDark: palette.mid
                        onCheckerLightChanged: requestPaint()
                        onCheckerDarkChanged: requestPaint()
                        onPaint: {
                            var ctx = getContext("2d");
                            ctx.clearRect(0, 0, width, height);

                            // Draw checkerboard
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

                    // Fill color with opacity applied
                    Rectangle {
                        anchors.fill: parent
                        z: 1
                        color: root.rectangleFillColor
                        opacity: root.rectangleFillOpacity
                    }
                }
            }

            Label {
                text: qsTr("Opacity:")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            Slider {
                id: opacitySlider
                Layout.preferredWidth: 80
                // When we customize handle/background, the Slider can lose its implicit height,
                // which causes RowLayout to give it ~0 height (no hit area). Explicitly size it.
                Layout.preferredHeight: DV.Styles.height.sm
                implicitHeight: DV.Styles.height.sm
                Layout.alignment: Qt.AlignVCenter
                from: 0
                to: 100
                stepSize: 1
                value: 0

                onPressedChanged: {
                    if (!pressed) {
                        // Update property when slider is released
                        root.rectangleFillOpacity = value / 100.0;
                    }
                }

                onValueChanged: {
                    // Update property as slider moves
                    root.rectangleFillOpacity = value / 100.0;
                }

                Component.onCompleted: {
                    value = Math.round(root.rectangleFillOpacity * 100);
                }

                Binding {
                    target: opacitySlider
                    property: "value"
                    value: Math.round(root.rectangleFillOpacity * 100)
                    when: !opacitySlider.pressed
                }

                background: Rectangle {
                    x: opacitySlider.leftPadding
                    y: opacitySlider.topPadding + opacitySlider.availableHeight / 2 - height / 2
                    width: opacitySlider.availableWidth
                    height: DV.Styles.height.xxxsm
                    // Provide implicit sizes so the control has a non-zero implicitHeight/Width in layouts
                    implicitWidth: 80
                    implicitHeight: DV.Styles.height.xxxsm
                    radius: DV.Styles.rad.sm
                    color: palette.base

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
                    color: opacitySlider.pressed ? palette.highlight : palette.button
                    border.color: palette.mid
                    border.width: 1
                }
            }

            TextField {
                id: opacityInput
                Layout.preferredWidth: 35
                Layout.preferredHeight: DV.Styles.height.md
                Layout.alignment: Qt.AlignVCenter
                text: Math.round(root.rectangleFillOpacity * 100).toString()
                horizontalAlignment: TextInput.AlignHCenter
                font.pixelSize: 11
                validator: IntValidator {
                    bottom: 0
                    top: 100
                }

                function commitValue() {
                    var value = parseInt(text);
                    if (!isNaN(value) && value >= 0 && value <= 100) {
                        root.rectangleFillOpacity = value / 100.0;
                    } else {
                        // Reset to current value if invalid
                        text = Math.round(root.rectangleFillOpacity * 100).toString();
                    }
                }

                onEditingFinished: {
                    commitValue();
                }

                onActiveFocusChanged: {
                    if (!activeFocus) {
                        commitValue();
                    }
                }

                // Update text when property changes externally
                Connections {
                    target: root
                    function onRectangleFillOpacityChanged() {
                        if (!opacityInput.activeFocus) {
                            opacityInput.text = Math.round(root.rectangleFillOpacity * 100).toString();
                        }
                    }
                }

                background: Rectangle {
                    color: palette.base
                    border.color: opacityInput.activeFocus ? palette.highlight : palette.mid
                    border.width: 1
                    radius: DV.Styles.rad.sm
                }

                color: palette.text
            }

            Label {
                text: qsTr("%")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }
        }

        // Pen tool settings
        RowLayout {
            id: penSettings
            visible: root.activeTool === "pen"
            Layout.fillHeight: true
            Layout.alignment: Qt.AlignVCenter
            spacing: 6

            Label {
                text: qsTr("Stroke Width:")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            TextField {
                id: penStrokeWidthInput
                Layout.preferredWidth: 50
                Layout.preferredHeight: DV.Styles.height.md
                Layout.alignment: Qt.AlignVCenter
                text: root.penStrokeWidth.toString()
                horizontalAlignment: TextInput.AlignHCenter
                font.pixelSize: 11
                validator: DoubleValidator {
                    bottom: 0.1
                    top: 100.0
                    decimals: 1
                }

                function commitValue() {
                    var value = parseFloat(text);
                    if (!isNaN(value) && value >= 0.1 && value <= 100.0) {
                        root.penStrokeWidth = value;
                    } else {
                        text = root.penStrokeWidth.toString();
                    }
                }

                onEditingFinished: commitValue()
                onActiveFocusChanged: {
                    if (!activeFocus) {
                        commitValue();
                    }
                }

                background: Rectangle {
                    color: palette.base
                    border.color: penStrokeWidthInput.activeFocus ? palette.highlight : palette.mid
                    border.width: 1
                    radius: DV.Styles.rad.sm
                }
                color: palette.text
            }

            Label {
                text: qsTr("px")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            Rectangle {
                Layout.preferredWidth: 1
                Layout.preferredHeight: 16
                Layout.alignment: Qt.AlignVCenter
                Layout.leftMargin: 6
                Layout.rightMargin: 6
                color: palette.mid
            }

            Label {
                text: qsTr("Stroke Color:")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            Button {
                id: penStrokeColorButton
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16
                Layout.alignment: Qt.AlignVCenter

                onClicked: penStrokeColorDialog.open()

                background: Rectangle {
                    color: root.penStrokeColor
                    border.color: palette.mid
                    border.width: 1
                    radius: DV.Styles.rad.sm
                }
            }

            Label {
                text: qsTr("Opacity:")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            Slider {
                id: penStrokeOpacitySlider
                Layout.preferredWidth: 80
                Layout.preferredHeight: DV.Styles.height.sm
                implicitHeight: DV.Styles.height.sm
                Layout.alignment: Qt.AlignVCenter
                from: 0
                to: 100
                stepSize: 1
                value: 100

                onPressedChanged: {
                    if (!pressed) {
                        root.penStrokeOpacity = value / 100.0;
                    }
                }

                onValueChanged: root.penStrokeOpacity = value / 100.0

                Component.onCompleted: value = Math.round(root.penStrokeOpacity * 100)

                Binding {
                    target: penStrokeOpacitySlider
                    property: "value"
                    value: Math.round(root.penStrokeOpacity * 100)
                    when: !penStrokeOpacitySlider.pressed
                }

                background: Rectangle {
                    x: penStrokeOpacitySlider.leftPadding
                    y: penStrokeOpacitySlider.topPadding + penStrokeOpacitySlider.availableHeight / 2 - height / 2
                    width: penStrokeOpacitySlider.availableWidth
                    height: DV.Styles.height.xxxsm
                    implicitWidth: 80
                    implicitHeight: DV.Styles.height.xxxsm
                    radius: DV.Styles.rad.sm
                    color: palette.base

                    Rectangle {
                        width: penStrokeOpacitySlider.visualPosition * parent.width
                        height: parent.height
                        color: palette.highlight
                        radius: DV.Styles.rad.sm
                    }
                }

                handle: Rectangle {
                    x: penStrokeOpacitySlider.leftPadding + penStrokeOpacitySlider.visualPosition * (penStrokeOpacitySlider.availableWidth - width)
                    y: penStrokeOpacitySlider.topPadding + penStrokeOpacitySlider.availableHeight / 2 - height / 2
                    width: DV.Styles.height.xs
                    height: DV.Styles.height.xs
                    implicitWidth: DV.Styles.height.xs
                    implicitHeight: DV.Styles.height.xs
                    radius: DV.Styles.rad.lg
                    color: penStrokeOpacitySlider.pressed ? palette.highlight : palette.button
                    border.color: palette.mid
                    border.width: 1
                }
            }

            TextField {
                id: penStrokeOpacityInput
                Layout.preferredWidth: 35
                Layout.preferredHeight: DV.Styles.height.md
                Layout.alignment: Qt.AlignVCenter
                text: Math.round(root.penStrokeOpacity * 100).toString()
                horizontalAlignment: TextInput.AlignHCenter
                font.pixelSize: 11
                validator: IntValidator {
                    bottom: 0
                    top: 100
                }

                function commitValue() {
                    var value = parseInt(text);
                    if (!isNaN(value) && value >= 0 && value <= 100) {
                        root.penStrokeOpacity = value / 100.0;
                    } else {
                        text = Math.round(root.penStrokeOpacity * 100).toString();
                    }
                }

                onEditingFinished: commitValue()
                onActiveFocusChanged: {
                    if (!activeFocus) {
                        commitValue();
                    }
                }

                Connections {
                    target: root
                    function onPenStrokeOpacityChanged() {
                        if (!penStrokeOpacityInput.activeFocus) {
                            penStrokeOpacityInput.text = Math.round(root.penStrokeOpacity * 100).toString();
                        }
                    }
                }

                background: Rectangle {
                    color: palette.base
                    border.color: penStrokeOpacityInput.activeFocus ? palette.highlight : palette.mid
                    border.width: 1
                    radius: DV.Styles.rad.sm
                }
                color: palette.text
            }

            Label {
                text: qsTr("%")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            // Separator
            Rectangle {
                Layout.preferredWidth: 1
                Layout.preferredHeight: 16
                Layout.alignment: Qt.AlignVCenter
                Layout.leftMargin: 6
                Layout.rightMargin: 6
                color: palette.mid
            }

            Label {
                text: qsTr("Fill Color:")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            Button {
                id: penFillColorButton
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16
                Layout.alignment: Qt.AlignVCenter

                onClicked: penFillColorDialog.open()

                background: Rectangle {
                    border.color: palette.mid
                    border.width: 1
                    radius: DV.Styles.rad.sm
                    color: "transparent"
                    clip: true

                    // Checkerboard
                    Canvas {
                        anchors.fill: parent
                        z: 0
                        property color checkerLight: palette.midlight
                        property color checkerDark: palette.mid
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

                    Rectangle {
                        anchors.fill: parent
                        z: 1
                        color: root.penFillColor
                        opacity: root.penFillOpacity
                    }
                }
            }

            Label {
                text: qsTr("Fill Opacity:")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            Slider {
                id: penFillOpacitySlider
                Layout.preferredWidth: 80
                Layout.preferredHeight: DV.Styles.height.sm
                implicitHeight: DV.Styles.height.sm
                Layout.alignment: Qt.AlignVCenter
                from: 0
                to: 100
                stepSize: 1
                value: 0

                onPressedChanged: {
                    if (!pressed) {
                        root.penFillOpacity = value / 100.0;
                    }
                }

                onValueChanged: root.penFillOpacity = value / 100.0

                Component.onCompleted: value = Math.round(root.penFillOpacity * 100)

                Binding {
                    target: penFillOpacitySlider
                    property: "value"
                    value: Math.round(root.penFillOpacity * 100)
                    when: !penFillOpacitySlider.pressed
                }

                background: Rectangle {
                    x: penFillOpacitySlider.leftPadding
                    y: penFillOpacitySlider.topPadding + penFillOpacitySlider.availableHeight / 2 - height / 2
                    width: penFillOpacitySlider.availableWidth
                    height: DV.Styles.height.xxxsm
                    implicitWidth: 80
                    implicitHeight: DV.Styles.height.xxxsm
                    radius: DV.Styles.rad.sm
                    color: palette.base

                    Rectangle {
                        width: penFillOpacitySlider.visualPosition * parent.width
                        height: parent.height
                        color: palette.highlight
                        radius: DV.Styles.rad.sm
                    }
                }

                handle: Rectangle {
                    x: penFillOpacitySlider.leftPadding + penFillOpacitySlider.visualPosition * (penFillOpacitySlider.availableWidth - width)
                    y: penFillOpacitySlider.topPadding + penFillOpacitySlider.availableHeight / 2 - height / 2
                    width: DV.Styles.height.xs
                    height: DV.Styles.height.xs
                    implicitWidth: DV.Styles.height.xs
                    implicitHeight: DV.Styles.height.xs
                    radius: DV.Styles.rad.lg
                    color: penFillOpacitySlider.pressed ? palette.highlight : palette.button
                    border.color: palette.mid
                    border.width: 1
                }
            }

            TextField {
                id: penFillOpacityInput
                Layout.preferredWidth: 35
                Layout.preferredHeight: DV.Styles.height.md
                Layout.alignment: Qt.AlignVCenter
                text: Math.round(root.penFillOpacity * 100).toString()
                horizontalAlignment: TextInput.AlignHCenter
                font.pixelSize: 11
                validator: IntValidator {
                    bottom: 0
                    top: 100
                }

                function commitValue() {
                    var value = parseInt(text);
                    if (!isNaN(value) && value >= 0 && value <= 100) {
                        root.penFillOpacity = value / 100.0;
                    } else {
                        text = Math.round(root.penFillOpacity * 100).toString();
                    }
                }

                onEditingFinished: commitValue()
                onActiveFocusChanged: {
                    if (!activeFocus)
                        commitValue();
                }

                Connections {
                    target: root
                    function onPenFillOpacityChanged() {
                        if (!penFillOpacityInput.activeFocus) {
                            penFillOpacityInput.text = Math.round(root.penFillOpacity * 100).toString();
                        }
                    }
                }

                background: Rectangle {
                    color: palette.base
                    border.color: penFillOpacityInput.activeFocus ? palette.highlight : palette.mid
                    border.width: 1
                    radius: DV.Styles.rad.sm
                }
                color: palette.text
            }

            Label {
                text: qsTr("%")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }
        }

        // Stroke color picker dialog
        ColorDialog {
            id: strokeColorDialog
            title: qsTr("Choose Stroke Color")
            selectedColor: root.rectangleStrokeColor

            onAccepted: {
                root.rectangleStrokeColor = selectedColor;
            }
        }

        // Fill color picker dialog
        ColorDialog {
            id: fillColorDialog
            title: qsTr("Choose Fill Color")
            selectedColor: root.rectangleFillColor

            onAccepted: {
                root.rectangleFillColor = selectedColor;
            }
        }

        // Ellipse tool settings
        RowLayout {
            id: ellipseSettings
            visible: root.activeTool === "ellipse"
            Layout.fillHeight: true
            Layout.alignment: Qt.AlignVCenter
            spacing: 6

            Label {
                text: qsTr("Stroke Width:")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            TextField {
                id: ellipseStrokeWidthInput
                Layout.preferredWidth: 50
                Layout.preferredHeight: DV.Styles.height.md
                Layout.alignment: Qt.AlignVCenter
                text: root.ellipseStrokeWidth.toString()
                horizontalAlignment: TextInput.AlignHCenter
                font.pixelSize: 11
                validator: DoubleValidator {
                    bottom: 0.1
                    top: 100.0
                    decimals: 1
                }

                function commitValue() {
                    var value = parseFloat(text);
                    if (!isNaN(value) && value >= 0.1 && value <= 100.0) {
                        root.ellipseStrokeWidth = value;
                    } else {
                        // Reset to current value if invalid
                        text = root.ellipseStrokeWidth.toString();
                    }
                }

                onEditingFinished: {
                    commitValue();
                }

                onActiveFocusChanged: {
                    if (!activeFocus) {
                        commitValue();
                    }
                }

                background: Rectangle {
                    color: palette.base
                    border.color: ellipseStrokeWidthInput.activeFocus ? palette.highlight : palette.mid
                    border.width: 1
                    radius: DV.Styles.rad.sm
                }

                color: palette.text
            }

            Label {
                text: qsTr("px")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            // Separator
            Rectangle {
                Layout.preferredWidth: 1
                Layout.preferredHeight: 16
                Layout.alignment: Qt.AlignVCenter
                Layout.leftMargin: 6
                Layout.rightMargin: 6
                color: palette.mid
            }

            Label {
                text: qsTr("Stroke Color:")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            Button {
                id: ellipseStrokeColorButton
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16
                Layout.alignment: Qt.AlignVCenter

                onClicked: {
                    ellipseStrokeColorDialog.open();
                }

                background: Rectangle {
                    color: root.ellipseStrokeColor
                    border.color: palette.mid
                    border.width: 1
                    radius: DV.Styles.rad.sm
                }
            }

            Label {
                text: qsTr("Opacity:")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            Slider {
                id: ellipseStrokeOpacitySlider
                Layout.preferredWidth: 80
                Layout.preferredHeight: DV.Styles.height.sm
                implicitHeight: DV.Styles.height.sm
                Layout.alignment: Qt.AlignVCenter
                from: 0
                to: 100
                stepSize: 1
                value: 100

                onPressedChanged: {
                    if (!pressed) {
                        root.ellipseStrokeOpacity = value / 100.0;
                    }
                }

                onValueChanged: {
                    root.ellipseStrokeOpacity = value / 100.0;
                }

                Component.onCompleted: {
                    value = Math.round(root.ellipseStrokeOpacity * 100);
                }

                Binding {
                    target: ellipseStrokeOpacitySlider
                    property: "value"
                    value: Math.round(root.ellipseStrokeOpacity * 100)
                    when: !ellipseStrokeOpacitySlider.pressed
                }

                background: Rectangle {
                    x: ellipseStrokeOpacitySlider.leftPadding
                    y: ellipseStrokeOpacitySlider.topPadding + ellipseStrokeOpacitySlider.availableHeight / 2 - height / 2
                    width: ellipseStrokeOpacitySlider.availableWidth
                    height: DV.Styles.height.xxxsm
                    implicitWidth: 80
                    implicitHeight: DV.Styles.height.xxxsm
                    radius: DV.Styles.rad.sm
                    color: palette.base

                    Rectangle {
                        width: ellipseStrokeOpacitySlider.visualPosition * parent.width
                        height: parent.height
                        color: palette.highlight
                        radius: DV.Styles.rad.sm
                    }
                }

                handle: Rectangle {
                    x: ellipseStrokeOpacitySlider.leftPadding + ellipseStrokeOpacitySlider.visualPosition * (ellipseStrokeOpacitySlider.availableWidth - width)
                    y: ellipseStrokeOpacitySlider.topPadding + ellipseStrokeOpacitySlider.availableHeight / 2 - height / 2
                    width: DV.Styles.height.xs
                    height: DV.Styles.height.xs
                    implicitWidth: DV.Styles.height.xs
                    implicitHeight: DV.Styles.height.xs
                    radius: DV.Styles.rad.lg
                    color: ellipseStrokeOpacitySlider.pressed ? palette.highlight : palette.button
                    border.color: palette.mid
                    border.width: 1
                }
            }

            TextField {
                id: ellipseStrokeOpacityInput
                Layout.preferredWidth: 35
                Layout.preferredHeight: DV.Styles.height.md
                Layout.alignment: Qt.AlignVCenter
                text: Math.round(root.ellipseStrokeOpacity * 100).toString()
                horizontalAlignment: TextInput.AlignHCenter
                font.pixelSize: 11
                validator: IntValidator {
                    bottom: 0
                    top: 100
                }

                function commitValue() {
                    var value = parseInt(text);
                    if (!isNaN(value) && value >= 0 && value <= 100) {
                        root.ellipseStrokeOpacity = value / 100.0;
                        console.log("Ellipse stroke opacity set to:", root.ellipseStrokeOpacity);
                    } else {
                        text = Math.round(root.ellipseStrokeOpacity * 100).toString();
                    }
                }

                onEditingFinished: {
                    commitValue();
                }

                onActiveFocusChanged: {
                    if (!activeFocus) {
                        commitValue();
                    }
                }

                Connections {
                    target: root
                    function onEllipseStrokeOpacityChanged() {
                        if (!ellipseStrokeOpacityInput.activeFocus) {
                            ellipseStrokeOpacityInput.text = Math.round(root.ellipseStrokeOpacity * 100).toString();
                        }
                    }
                }

                background: Rectangle {
                    color: palette.base
                    border.color: ellipseStrokeOpacityInput.activeFocus ? palette.highlight : palette.mid
                    border.width: 1
                    radius: DV.Styles.rad.sm
                }

                color: palette.text
            }

            Label {
                text: qsTr("%")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            // Separator
            Rectangle {
                Layout.preferredWidth: 1
                Layout.preferredHeight: 16
                Layout.alignment: Qt.AlignVCenter
                Layout.leftMargin: 6
                Layout.rightMargin: 6
                color: palette.mid
            }

            Label {
                text: qsTr("Fill Color:")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            Button {
                id: ellipseFillColorButton
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16
                Layout.alignment: Qt.AlignVCenter

                onClicked: {
                    ellipseFillColorDialog.open();
                }

                background: Rectangle {
                    border.color: palette.mid
                    border.width: 1
                    radius: DV.Styles.rad.sm
                    color: "transparent"
                    clip: true

                    // Checkerboard pattern to show transparency
                    Canvas {
                        anchors.fill: parent
                        z: 0
                        property color checkerLight: palette.midlight
                        property color checkerDark: palette.mid
                        onCheckerLightChanged: requestPaint()
                        onCheckerDarkChanged: requestPaint()
                        onPaint: {
                            var ctx = getContext("2d");
                            ctx.clearRect(0, 0, width, height);

                            // Draw checkerboard
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

                    // Fill color with opacity applied
                    Rectangle {
                        anchors.fill: parent
                        z: 1
                        color: root.ellipseFillColor
                        opacity: root.ellipseFillOpacity
                    }
                }
            }

            Label {
                text: qsTr("Opacity:")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            Slider {
                id: ellipseOpacitySlider
                Layout.preferredWidth: 80
                Layout.preferredHeight: DV.Styles.height.sm
                implicitHeight: DV.Styles.height.sm
                Layout.alignment: Qt.AlignVCenter
                from: 0
                to: 100
                stepSize: 1
                value: 0

                onPressedChanged: {
                    if (!pressed) {
                        // Update property when slider is released
                        root.ellipseFillOpacity = value / 100.0;
                    }
                }

                onValueChanged: {
                    // Update property as slider moves
                    root.ellipseFillOpacity = value / 100.0;
                }

                Component.onCompleted: {
                    value = Math.round(root.ellipseFillOpacity * 100);
                }

                Binding {
                    target: ellipseOpacitySlider
                    property: "value"
                    value: Math.round(root.ellipseFillOpacity * 100)
                    when: !ellipseOpacitySlider.pressed
                }

                background: Rectangle {
                    x: ellipseOpacitySlider.leftPadding
                    y: ellipseOpacitySlider.topPadding + ellipseOpacitySlider.availableHeight / 2 - height / 2
                    width: ellipseOpacitySlider.availableWidth
                    height: DV.Styles.height.xxxsm
                    implicitWidth: 80
                    implicitHeight: DV.Styles.height.xxxsm
                    radius: DV.Styles.rad.sm
                    color: palette.base

                    Rectangle {
                        width: ellipseOpacitySlider.visualPosition * parent.width
                        height: parent.height
                        color: palette.highlight
                        radius: DV.Styles.rad.sm
                    }
                }

                handle: Rectangle {
                    x: ellipseOpacitySlider.leftPadding + ellipseOpacitySlider.visualPosition * (ellipseOpacitySlider.availableWidth - width)
                    y: ellipseOpacitySlider.topPadding + ellipseOpacitySlider.availableHeight / 2 - height / 2
                    width: DV.Styles.height.xs
                    height: DV.Styles.height.xs
                    implicitWidth: DV.Styles.height.xs
                    implicitHeight: DV.Styles.height.xs
                    radius: DV.Styles.rad.lg
                    color: ellipseOpacitySlider.pressed ? palette.highlight : palette.button
                    border.color: palette.mid
                    border.width: 1
                }
            }

            TextField {
                id: ellipseOpacityInput
                Layout.preferredWidth: 35
                Layout.preferredHeight: DV.Styles.height.md
                Layout.alignment: Qt.AlignVCenter
                text: Math.round(root.ellipseFillOpacity * 100).toString()
                horizontalAlignment: TextInput.AlignHCenter
                font.pixelSize: 11
                validator: IntValidator {
                    bottom: 0
                    top: 100
                }

                function commitValue() {
                    var value = parseInt(text);
                    if (!isNaN(value) && value >= 0 && value <= 100) {
                        root.ellipseFillOpacity = value / 100.0;
                    } else {
                        // Reset to current value if invalid
                        text = Math.round(root.ellipseFillOpacity * 100).toString();
                    }
                }

                onEditingFinished: {
                    commitValue();
                }

                onActiveFocusChanged: {
                    if (!activeFocus) {
                        commitValue();
                    }
                }

                // Update text when property changes externally
                Connections {
                    target: root
                    function onEllipseFillOpacityChanged() {
                        if (!ellipseOpacityInput.activeFocus) {
                            ellipseOpacityInput.text = Math.round(root.ellipseFillOpacity * 100).toString();
                        }
                    }
                }

                background: Rectangle {
                    color: palette.base
                    border.color: ellipseOpacityInput.activeFocus ? palette.highlight : palette.mid
                    border.width: 1
                    radius: DV.Styles.rad.sm
                }

                color: palette.text
            }

            Label {
                text: qsTr("%")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }
        }

        // Ellipse stroke color picker dialog
        ColorDialog {
            id: ellipseStrokeColorDialog
            title: qsTr("Choose Ellipse Stroke Color")
            selectedColor: root.ellipseStrokeColor

            onAccepted: {
                root.ellipseStrokeColor = selectedColor;
            }
        }

        // Ellipse fill color picker dialog
        ColorDialog {
            id: ellipseFillColorDialog
            title: qsTr("Choose Ellipse Fill Color")
            selectedColor: root.ellipseFillColor

            onAccepted: {
                root.ellipseFillColor = selectedColor;
            }
        }

        // Pen stroke color picker dialog
        ColorDialog {
            id: penStrokeColorDialog
            title: qsTr("Choose Pen Stroke Color")
            selectedColor: root.penStrokeColor

            onAccepted: {
                root.penStrokeColor = selectedColor;
            }
        }

        // Pen fill color picker dialog
        ColorDialog {
            id: penFillColorDialog
            title: qsTr("Choose Pen Fill Color")
            selectedColor: root.penFillColor

            onAccepted: {
                root.penFillColor = selectedColor;
            }
        }

        // Text tool settings
        RowLayout {
            id: textSettings
            visible: root.activeTool === "text"
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
                currentIndex: fontProvider ? fontProvider.indexOf(root.textFontFamily) : 0

                onCurrentTextChanged: {
                    if (currentText && currentText.length > 0) {
                        root.textFontFamily = currentText;
                    }
                }

                Component.onCompleted: {
                    // Set default font if not already set
                    if (fontProvider && (!root.textFontFamily || root.textFontFamily === "Sans Serif")) {
                        root.textFontFamily = fontProvider.defaultFont();
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

            // Separator
            Rectangle {
                Layout.preferredWidth: 1
                Layout.preferredHeight: 16
                Layout.alignment: Qt.AlignVCenter
                Layout.leftMargin: 6
                Layout.rightMargin: 6
                color: palette.mid
            }

            Label {
                text: qsTr("Size:")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            ComboBox {
                id: textFontSizeCombo
                Layout.preferredWidth: 70
                Layout.preferredHeight: DV.Styles.height.md
                Layout.alignment: Qt.AlignVCenter
                editable: true
                model: [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 64, 72, 96, 128]

                // Find current index or -1 for custom values
                currentIndex: {
                    var idx = model.indexOf(Math.round(root.textFontSize));
                    return idx >= 0 ? idx : -1;
                }

                // Update text field to show current size
                Component.onCompleted: {
                    editText = Math.round(root.textFontSize).toString();
                }

                onCurrentIndexChanged: {
                    if (currentIndex >= 0) {
                        root.textFontSize = model[currentIndex];
                    }
                }

                onAccepted: {
                    var value = parseFloat(editText);
                    if (!isNaN(value) && value >= 8 && value <= 200) {
                        root.textFontSize = Math.round(value);
                    }
                    editText = Math.round(root.textFontSize).toString();
                }

                // Sync editText when textFontSize changes externally
                Connections {
                    target: root
                    function onTextFontSizeChanged() {
                        if (!textFontSizeCombo.activeFocus) {
                            textFontSizeCombo.editText = Math.round(root.textFontSize).toString();
                        }
                    }
                }

                validator: IntValidator {
                    bottom: 8
                    top: 200
                }

                background: Rectangle {
                    color: palette.base
                    border.color: textFontSizeCombo.activeFocus ? palette.highlight : palette.mid
                    border.width: 1
                    radius: DV.Styles.rad.sm
                }

                contentItem: TextInput {
                    text: textFontSizeCombo.editText
                    font.pixelSize: 11
                    color: palette.text
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    leftPadding: 6
                    rightPadding: 6
                    selectByMouse: true
                    validator: textFontSizeCombo.validator

                    onTextChanged: textFontSizeCombo.editText = text
                    onAccepted: textFontSizeCombo.accepted()
                }
            }

            Label {
                text: qsTr("pt")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            // Separator
            Rectangle {
                Layout.preferredWidth: 1
                Layout.preferredHeight: 16
                Layout.alignment: Qt.AlignVCenter
                Layout.leftMargin: 6
                Layout.rightMargin: 6
                color: palette.mid
            }

            Label {
                text: qsTr("Color:")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            Button {
                id: textColorButton
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16
                Layout.alignment: Qt.AlignVCenter

                onClicked: textColorDialog.open()

                background: Rectangle {
                    color: root.textColor
                    border.color: palette.mid
                    border.width: 1
                    radius: DV.Styles.rad.sm
                }
            }

            Label {
                text: qsTr("Opacity:")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }

            Slider {
                id: textOpacitySlider
                Layout.preferredWidth: 80
                Layout.preferredHeight: DV.Styles.height.sm
                implicitHeight: DV.Styles.height.sm
                Layout.alignment: Qt.AlignVCenter
                from: 0
                to: 100
                stepSize: 1
                value: 100

                onPressedChanged: {
                    if (!pressed) {
                        root.textOpacity = value / 100.0;
                    }
                }

                onValueChanged: root.textOpacity = value / 100.0

                Component.onCompleted: value = Math.round(root.textOpacity * 100)

                Binding {
                    target: textOpacitySlider
                    property: "value"
                    value: Math.round(root.textOpacity * 100)
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
                    color: palette.base

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
                    color: textOpacitySlider.pressed ? palette.highlight : palette.button
                    border.color: palette.mid
                    border.width: 1
                }
            }

            TextField {
                id: textOpacityInput
                Layout.preferredWidth: 35
                Layout.preferredHeight: DV.Styles.height.md
                Layout.alignment: Qt.AlignVCenter
                text: Math.round(root.textOpacity * 100).toString()
                horizontalAlignment: TextInput.AlignHCenter
                font.pixelSize: 11
                validator: IntValidator {
                    bottom: 0
                    top: 100
                }

                function commitValue() {
                    var value = parseInt(text);
                    if (!isNaN(value) && value >= 0 && value <= 100) {
                        root.textOpacity = value / 100.0;
                    } else {
                        text = Math.round(root.textOpacity * 100).toString();
                    }
                }

                onEditingFinished: commitValue()
                onActiveFocusChanged: {
                    if (!activeFocus) {
                        commitValue();
                    }
                }

                Connections {
                    target: root
                    function onTextOpacityChanged() {
                        if (!textOpacityInput.activeFocus) {
                            textOpacityInput.text = Math.round(root.textOpacity * 100).toString();
                        }
                    }
                }

                background: Rectangle {
                    color: palette.base
                    border.color: textOpacityInput.activeFocus ? palette.highlight : palette.mid
                    border.width: 1
                    radius: DV.Styles.rad.sm
                }
                color: palette.text
            }

            Label {
                text: qsTr("%")
                font.pixelSize: 11
                Layout.alignment: Qt.AlignVCenter
            }
        }

        // Text color picker dialog
        ColorDialog {
            id: textColorDialog
            title: qsTr("Choose Text Color")
            selectedColor: root.textColor

            onAccepted: {
                root.textColor = selectedColor;
            }
        }

        // Select tool settings (empty for now)
        Item {
            visible: root.activeTool === "select" || root.activeTool === ""
            Layout.fillHeight: true
            Layout.fillWidth: true
        }

        // Spacer
        Item {
            Layout.fillWidth: true
        }
    }
}
