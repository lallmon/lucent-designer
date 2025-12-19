import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import "." as DV

// Tool Settings Bar - displays settings for the currently active tool
ToolBar {
    id: root
    height: 48
    
    // Properties
    property string activeTool: ""  // Current tool ("select", "rectangle", "ellipse", etc.)
    
    // Tool-specific settings - Rectangle
    property real rectangleStrokeWidth: 1
    property color rectangleStrokeColor: "#ffffff"
    property color rectangleFillColor: "#ffffff"
    property real rectangleFillOpacity: 0.0
    
    // Tool-specific settings - Ellipse
    property real ellipseStrokeWidth: 1
    property color ellipseStrokeColor: "#ffffff"
    property color ellipseFillColor: "#ffffff"
    property real ellipseFillOpacity: 0.0
    
    // Construct toolSettings object from individual properties
    readonly property var toolSettings: ({
        "rectangle": {
            strokeWidth: rectangleStrokeWidth,
            strokeColor: rectangleStrokeColor,
            fillColor: rectangleFillColor,
            fillOpacity: rectangleFillOpacity
        },
        "ellipse": {
            strokeWidth: ellipseStrokeWidth,
            strokeColor: ellipseStrokeColor,
            fillColor: ellipseFillColor,
            fillOpacity: ellipseFillOpacity
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
                Layout.preferredWidth: DV.Theme.sizes.settingsStrokeWidthFieldWidth
                Layout.preferredHeight: DV.Theme.sizes.settingsFieldHeight
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
                        console.log("Stroke width set to:", value);
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
                    color: DV.Theme.colors.gridMinor
                    border.color: strokeWidthInput.activeFocus ? DV.Theme.colors.accent : DV.Theme.colors.borderSubtle
                    border.width: 1
                    radius: DV.Theme.sizes.radiusSm
                }
                
                color: "#ffffff"
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
                color: DV.Theme.colors.borderSubtle
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
                    border.color: DV.Theme.colors.borderSubtle
                    border.width: 1
                    radius: DV.Theme.sizes.radiusSm
                }
            }
            
            // Separator
            Rectangle {
                Layout.preferredWidth: 1
                Layout.preferredHeight: 16
                Layout.alignment: Qt.AlignVCenter
                Layout.leftMargin: 6
                Layout.rightMargin: 6
                color: DV.Theme.colors.borderSubtle
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
                    border.color: DV.Theme.colors.borderSubtle
                    border.width: 1
                    radius: DV.Theme.sizes.radiusSm
                    color: "transparent"
                    clip: true
                    
                    // Checkerboard pattern to show transparency
                    Canvas {
                        anchors.fill: parent
                        z: 0
                        onPaint: {
                            var ctx = getContext("2d");
                            ctx.clearRect(0, 0, width, height);
                            
                            // Draw checkerboard
                            var size = 4;
                            for (var y = 0; y < height; y += size) {
                                for (var x = 0; x < width; x += size) {
                                    if ((Math.floor(x/size) + Math.floor(y/size)) % 2 === 0) {
                                        ctx.fillStyle = "#999999";
                                    } else {
                                        ctx.fillStyle = "#666666";
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
                Layout.preferredHeight: DV.Theme.sizes.sliderHeight
                implicitHeight: DV.Theme.sizes.sliderHeight
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
                    height: DV.Theme.sizes.sliderTrackHeight
                    // Provide implicit sizes so the control has a non-zero implicitHeight/Width in layouts
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
            
            TextField {
                id: opacityInput
                Layout.preferredWidth: DV.Theme.sizes.settingsOpacityFieldWidth
                Layout.preferredHeight: DV.Theme.sizes.settingsFieldHeight
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
                        console.log("Fill opacity set to:", root.rectangleFillOpacity);
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
                    color: DV.Theme.colors.gridMinor
                    border.color: opacityInput.activeFocus ? DV.Theme.colors.accent : DV.Theme.colors.borderSubtle
                    border.width: 1
                    radius: DV.Theme.sizes.radiusSm
                }
                
                color: "#ffffff"
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
                console.log("Stroke color set to:", selectedColor);
            }
        }
        
        // Fill color picker dialog
        ColorDialog {
            id: fillColorDialog
            title: qsTr("Choose Fill Color")
            selectedColor: root.rectangleFillColor
            
            onAccepted: {
                root.rectangleFillColor = selectedColor;
                console.log("Fill color set to:", selectedColor);
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
                Layout.preferredWidth: DV.Theme.sizes.settingsStrokeWidthFieldWidth
                Layout.preferredHeight: DV.Theme.sizes.settingsFieldHeight
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
                        console.log("Ellipse stroke width set to:", value);
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
                    color: DV.Theme.colors.gridMinor
                    border.color: ellipseStrokeWidthInput.activeFocus ? DV.Theme.colors.accent : DV.Theme.colors.borderSubtle
                    border.width: 1
                    radius: DV.Theme.sizes.radiusSm
                }
                
                color: "#ffffff"
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
                color: DV.Theme.colors.borderSubtle
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
                    border.color: DV.Theme.colors.borderSubtle
                    border.width: 1
                    radius: DV.Theme.sizes.radiusSm
                }
            }
            
            // Separator
            Rectangle {
                Layout.preferredWidth: 1
                Layout.preferredHeight: 16
                Layout.alignment: Qt.AlignVCenter
                Layout.leftMargin: 6
                Layout.rightMargin: 6
                color: DV.Theme.colors.borderSubtle
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
                    border.color: DV.Theme.colors.borderSubtle
                    border.width: 1
                    radius: DV.Theme.sizes.radiusSm
                    color: "transparent"
                    clip: true
                    
                    // Checkerboard pattern to show transparency
                    Canvas {
                        anchors.fill: parent
                        z: 0
                        onPaint: {
                            var ctx = getContext("2d");
                            ctx.clearRect(0, 0, width, height);
                            
                            // Draw checkerboard
                            var size = 4;
                            for (var y = 0; y < height; y += size) {
                                for (var x = 0; x < width; x += size) {
                                    if ((Math.floor(x/size) + Math.floor(y/size)) % 2 === 0) {
                                        ctx.fillStyle = "#999999";
                                    } else {
                                        ctx.fillStyle = "#666666";
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
                Layout.preferredHeight: DV.Theme.sizes.sliderHeight
                implicitHeight: DV.Theme.sizes.sliderHeight
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
                    height: DV.Theme.sizes.sliderTrackHeight
                    implicitWidth: 80
                    implicitHeight: DV.Theme.sizes.sliderTrackHeight
                    radius: DV.Theme.sizes.radiusSm
                    color: DV.Theme.colors.gridMinor
                    
                    Rectangle {
                        width: ellipseOpacitySlider.visualPosition * parent.width
                        height: parent.height
                        color: DV.Theme.colors.accent
                        radius: DV.Theme.sizes.radiusSm
                    }
                }
                
                handle: Rectangle {
                    x: ellipseOpacitySlider.leftPadding + ellipseOpacitySlider.visualPosition * (ellipseOpacitySlider.availableWidth - width)
                    y: ellipseOpacitySlider.topPadding + ellipseOpacitySlider.availableHeight / 2 - height / 2
                    width: DV.Theme.sizes.sliderHandleSize
                    height: DV.Theme.sizes.sliderHandleSize
                    implicitWidth: DV.Theme.sizes.sliderHandleSize
                    implicitHeight: DV.Theme.sizes.sliderHandleSize
                    radius: DV.Theme.sizes.radiusLg
                    color: ellipseOpacitySlider.pressed ? DV.Theme.colors.accent : "#ffffff"
                    border.color: DV.Theme.colors.borderSubtle
                    border.width: 1
                }
            }
            
            TextField {
                id: ellipseOpacityInput
                Layout.preferredWidth: DV.Theme.sizes.settingsOpacityFieldWidth
                Layout.preferredHeight: DV.Theme.sizes.settingsFieldHeight
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
                        console.log("Ellipse fill opacity set to:", root.ellipseFillOpacity);
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
                    color: DV.Theme.colors.gridMinor
                    border.color: ellipseOpacityInput.activeFocus ? DV.Theme.colors.accent : DV.Theme.colors.borderSubtle
                    border.width: 1
                    radius: DV.Theme.sizes.radiusSm
                }
                
                color: "#ffffff"
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
                console.log("Ellipse stroke color set to:", selectedColor);
            }
        }
        
        // Ellipse fill color picker dialog
        ColorDialog {
            id: ellipseFillColorDialog
            title: qsTr("Choose Ellipse Fill Color")
            selectedColor: root.ellipseFillColor
            
            onAccepted: {
                root.ellipseFillColor = selectedColor;
                console.log("Ellipse fill color set to:", selectedColor);
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

