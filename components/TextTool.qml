import QtQuick
import QtQuick.Controls
import "." as DV

// Text tool component for creating text boxes on the canvas
Item {
    id: tool

    // Properties passed from Canvas
    property real zoomLevel: 1.0
    property bool active: false
    property var settings: null  // Tool settings object

    // Two-point helper for click-drag box creation
    TwoPointToolHelper {
        id: helper
    }

    // Current text box being drawn
    property var currentBox: null

    // State for text editing (after box is created)
    property bool isEditing: false
    property real boxX: 0
    property real boxY: 0
    property real boxWidth: 100
    property real boxHeight: 0

    // Signal emitted when a text item is completed
    signal itemCompleted(var itemData)

    // Placeholder text constant
    readonly property string placeholderText: "Type here..."

    // Padding inside the text edit container (in canvas coordinates)
    readonly property real textPadding: 4

    // Box preview rectangle (shown while drawing)
    Rectangle {
        id: boxPreview
        visible: helper.isDrawing && currentBox !== null && currentBox.width > 1 && currentBox.height > 1

        x: currentBox ? currentBox.x : 0
        y: currentBox ? currentBox.y : 0
        width: currentBox ? currentBox.width : 0
        height: currentBox ? currentBox.height : 0

        color: "transparent"
        border.color: DV.PaletteBridge.active.highlight
        border.width: 2 / tool.zoomLevel

        // Dashed border effect using inner rectangle
        Rectangle {
            anchors.fill: parent
            anchors.margins: 1 / tool.zoomLevel
            color: "transparent"
            border.color: DV.PaletteBridge.active.base
            border.width: 1 / tool.zoomLevel
            opacity: 0.5
        }
    }

    // Text editing container (shown after box is created)
    Rectangle {
        id: textEditContainer
        visible: tool.isEditing

        x: tool.boxX
        y: tool.boxY
        width: tool.boxWidth
        height: Math.max(tool.boxHeight, textEdit.contentHeight)

        color: "transparent"
        border.color: DV.PaletteBridge.active.highlight
        border.width: 2 / tool.zoomLevel
        radius: 2 / tool.zoomLevel

        TextEdit {
            id: textEdit
            anchors.fill: parent
            anchors.margins: tool.textPadding

            // Ensure no internal padding for precise positioning
            leftPadding: 0
            rightPadding: 0
            topPadding: 0
            bottomPadding: 0

            font.family: settings ? settings.fontFamily : "Sans Serif"
            font.pointSize: settings ? settings.fontSize : 16
            color: {
                if (!settings)
                    return DV.PaletteBridge.active.text;
                var c = Qt.color(settings.textColor);
                c.a = settings.textOpacity !== undefined ? settings.textOpacity : 1.0;
                return c;
            }
            selectionColor: DV.PaletteBridge.active.highlight

            wrapMode: TextEdit.Wrap
            selectByMouse: true
            focus: tool.isEditing
            cursorVisible: tool.isEditing

            // Start with placeholder text selected
            text: tool.placeholderText

            Component.onCompleted: {
                if (tool.isEditing) {
                    selectAll();
                    forceActiveFocus();
                }
            }

            onActiveFocusChanged: {
                if (activeFocus && text === tool.placeholderText) {
                    selectAll();
                }
            }

            Keys.onReturnPressed: function (event) {
                if (event.modifiers & Qt.ShiftModifier) {
                    // Shift+Enter: Insert newline manually to maintain cursor
                    textEdit.insert(textEdit.cursorPosition, "\n");
                    textEdit.forceActiveFocus();
                    textEdit.cursorVisible = true;
                    event.accepted = true;
                } else {
                    // Enter: Commit text
                    tool.commitText();
                    event.accepted = true;
                }
            }

            Keys.onEnterPressed: function (event) {
                if (event.modifiers & Qt.ShiftModifier) {
                    // Shift+Enter: Insert newline manually to maintain cursor
                    textEdit.insert(textEdit.cursorPosition, "\n");
                    textEdit.forceActiveFocus();
                    textEdit.cursorVisible = true;
                    event.accepted = true;
                } else {
                    tool.commitText();
                    event.accepted = true;
                }
            }

            Keys.onEscapePressed: {
                tool.cancelText();
            }
        }
    }

    // Handle clicks for text box creation
    function handleClick(canvasX, canvasY) {
        if (!tool.active)
            return;

        if (tool.isEditing) {
            // If clicking outside current edit, commit and potentially start new
            var insideX = canvasX >= tool.boxX && canvasX <= tool.boxX + tool.boxWidth;
            var insideY = canvasY >= tool.boxY && canvasY <= tool.boxY + tool.boxHeight;
            if (!insideX || !insideY) {
                if (textEdit.text.trim().length > 0 && textEdit.text !== tool.placeholderText) {
                    tool.commitText();
                } else {
                    tool.cancelText();
                }
                // Start drawing new box
                helper.begin(canvasX, canvasY);
                currentBox = {
                    x: canvasX,
                    y: canvasY,
                    width: 1,
                    height: 1
                };
            }
            return;
        }

        if (!helper.isDrawing) {
            // First click: Start drawing the text box
            helper.begin(canvasX, canvasY);
            currentBox = {
                x: canvasX,
                y: canvasY,
                width: 1,
                height: 1
            };
        } else {
            // Second click: Finalize box and start editing
            if (currentBox && currentBox.width > 10 && currentBox.height > 10) {
                tool.boxX = currentBox.x;
                tool.boxY = currentBox.y;
                tool.boxWidth = currentBox.width;
                tool.boxHeight = currentBox.height;
                tool.isEditing = true;

                // Initialize with placeholder and select it
                textEdit.text = tool.placeholderText;
                textEdit.selectAll();
                textEdit.forceActiveFocus();
            }
            currentBox = null;
            helper.reset();
        }
    }

    // Update preview during mouse movement
    function handleMouseMove(canvasX, canvasY, modifiers) {
        if (!tool.active || !helper.isDrawing)
            return;

        // Calculate box dimensions from start to current point
        var deltaX = canvasX - helper.startX;
        var deltaY = canvasY - helper.startY;
        var boxWidth = Math.abs(deltaX);
        var boxHeight = Math.abs(deltaY);

        // Constrain to square when Shift is held
        if (modifiers & Qt.ShiftModifier) {
            var size = Math.max(boxWidth, boxHeight);
            boxWidth = size;
            boxHeight = size;
        }

        // Calculate position based on drag direction
        var boxX = deltaX >= 0 ? helper.startX : helper.startX - boxWidth;
        var boxY = deltaY >= 0 ? helper.startY : helper.startY - boxHeight;

        // Update current box
        currentBox = {
            x: boxX,
            y: boxY,
            width: boxWidth,
            height: boxHeight
        };
    }

    // Commit the text as a canvas item
    function commitText() {
        var finalText = textEdit.text.trim();

        // Don't commit placeholder or empty text
        if (finalText.length === 0 || finalText === tool.placeholderText) {
            tool.cancelText();
            return;
        }

        var fontFamily = settings ? settings.fontFamily : "Sans Serif";
        var fontSize = settings ? settings.fontSize : 16;
        var textColor = settings ? settings.textColor : "#ffffff";
        var textOpacity = settings ? (settings.textOpacity !== undefined ? settings.textOpacity : 1.0) : 1.0;

        itemCompleted({
            type: "text",
            x: tool.boxX + tool.textPadding,
            y: tool.boxY + tool.textPadding,
            width: tool.boxWidth - (tool.textPadding * 2),
            height: tool.boxHeight - (tool.textPadding * 2),
            text: finalText,
            fontFamily: fontFamily,
            fontSize: fontSize,
            textColor: textColor.toString(),
            textOpacity: textOpacity
        });

        // Reset state
        tool.isEditing = false;
        textEdit.text = "";
    }

    // Cancel text input without creating an item
    function cancelText() {
        tool.isEditing = false;
        textEdit.text = "";
        currentBox = null;
        helper.reset();
    }

    // Reset tool state (called when switching tools)
    function reset() {
        if (tool.isEditing) {
            var finalText = textEdit.text.trim();
            if (finalText.length > 0 && finalText !== tool.placeholderText) {
                tool.commitText();
            } else {
                tool.cancelText();
            }
        }
        currentBox = null;
        helper.reset();
    }
}
