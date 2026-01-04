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

    // Resize state tracking
    property bool isResizing: false
    property bool justFinishedResizing: false
    property real resizeStartX: 0
    property real resizeStartY: 0
    property real resizeStartWidth: 0
    property real resizeStartHeight: 0

    // Text editing container (shown after box is created)
    Rectangle {
        id: textEditContainer
        visible: tool.isEditing

        x: tool.boxX
        y: tool.boxY
        width: tool.boxWidth
        height: Math.max(tool.boxHeight, textEdit.contentHeight + tool.textPadding * 2)

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
            focus: tool.isEditing && !tool.isResizing
            cursorVisible: tool.isEditing && !tool.isResizing

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

        // Resize handle (bottom-right corner)
        Rectangle {
            id: resizeHandle
            width: 10 / tool.zoomLevel
            height: 10 / tool.zoomLevel
            radius: 5 / tool.zoomLevel
            color: DV.PaletteBridge.active.highlight
            border.color: DV.PaletteBridge.active.base
            border.width: 1 / tool.zoomLevel

            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.rightMargin: -5 / tool.zoomLevel
            anchors.bottomMargin: -5 / tool.zoomLevel

            MouseArea {
                id: resizeMouseArea
                anchors.fill: parent
                anchors.margins: -6 / tool.zoomLevel  // Larger hit area for hover
                cursorShape: Qt.SizeFDiagCursor
                hoverEnabled: true
                // Don't accept press - let it pass through to Canvas
                acceptedButtons: Qt.NoButton
            }
        }
    }

    // Check if a canvas position is within the resize handle area
    function isInResizeHandle(canvasX, canvasY) {
        if (!tool.isEditing)
            return false;

        var handleSize = 16 / tool.zoomLevel;  // Generous hit area
        var handleX = tool.boxX + tool.boxWidth - handleSize / 2;
        var handleY = tool.boxY + textEditContainer.height - handleSize / 2;

        return canvasX >= handleX && canvasX <= handleX + handleSize && canvasY >= handleY && canvasY <= handleY + handleSize;
    }

    // Handle mouse press (for resize detection)
    function handleMousePress(canvasX, canvasY, button, modifiers) {
        if (!tool.active || !tool.isEditing)
            return;

        if (isInResizeHandle(canvasX, canvasY)) {
            tool.isResizing = true;
            tool.resizeStartX = canvasX;
            tool.resizeStartY = canvasY;
            tool.resizeStartWidth = tool.boxWidth;
            tool.resizeStartHeight = tool.boxHeight;
        }
    }

    // Handle clicks for text box creation
    function handleClick(canvasX, canvasY) {
        if (!tool.active)
            return;

        if (tool.isEditing) {
            // Check if click is inside the text box
            var insideX = canvasX >= tool.boxX && canvasX <= tool.boxX + tool.boxWidth;
            var insideY = canvasY >= tool.boxY && canvasY <= tool.boxY + textEditContainer.height;

            if (insideX && insideY) {
                // Click inside: position cursor at click location
                // Convert canvas coords to TextEdit local coords
                var localX = canvasX - tool.boxX - tool.textPadding;
                var localY = canvasY - tool.boxY - tool.textPadding;
                var pos = textEdit.positionAt(localX, localY);
                textEdit.cursorPosition = pos;
                textEdit.forceActiveFocus();
                tool.justFinishedResizing = false;
                return;
            }

            // Skip commit if we just finished resizing (avoid accidental commit)
            if (tool.justFinishedResizing) {
                tool.justFinishedResizing = false;
                return;
            }

            // Clicking outside: commit and potentially start new
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
        if (!tool.active)
            return;

        // Handle resize dragging
        if (tool.isResizing) {
            var deltaX = canvasX - tool.resizeStartX;
            var deltaY = canvasY - tool.resizeStartY;
            tool.boxWidth = Math.max(50, tool.resizeStartWidth + deltaX);
            tool.boxHeight = Math.max(30, tool.resizeStartHeight + deltaY);
            return;
        }

        if (!helper.isDrawing)
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

    // Handle mouse release (for resize completion)
    function handleMouseRelease(canvasX, canvasY) {
        if (tool.isResizing) {
            tool.isResizing = false;
            tool.justFinishedResizing = true;
            textEdit.forceActiveFocus();
        }
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
