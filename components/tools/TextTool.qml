import QtQuick
import QtQuick.Controls
import QtQuick.Shapes
import ".." as Lucent

// Text tool component for creating text boxes on the canvas
Item {
    id: tool

    // Properties passed from Canvas
    property real zoomLevel: 1.0
    property bool active: false
    property var settings: null  // Tool settings object

    // Default text box size
    readonly property real defaultBoxWidth: 200
    readonly property real defaultBoxHeight: 80

    // State for text editing
    property bool isEditing: false
    property real boxX: 0
    property real boxY: 0
    property real boxWidth: defaultBoxWidth
    property real boxHeight: defaultBoxHeight

    // Signal emitted when a text item is completed
    signal itemCompleted(var itemData)

    readonly property string placeholderText: "Type here..."
    readonly property real textPadding: 4

    // Resize state
    property bool isResizing: false
    property bool skipNextClick: false
    property real resizeStartX: 0
    property real resizeStartY: 0
    property real resizeStartWidth: 0
    property real resizeStartHeight: 0

    // Text selection state
    property bool isSelectingText: false
    property int selectionAnchor: 0

    Item {
        id: textEditContainer
        visible: tool.isEditing

        x: tool.boxX
        y: tool.boxY
        width: tool.boxWidth
        height: Math.max(tool.boxHeight, textEdit.contentHeight + tool.textPadding * 2)

        // Use Shape for better thin line rendering at all zoom levels
        Shape {
            anchors.fill: parent

            ShapePath {
                strokeColor: Lucent.Themed.selector
                strokeWidth: tool.zoomLevel > 0 ? 1 / tool.zoomLevel : 1
                fillColor: "transparent"
                joinStyle: ShapePath.MiterJoin
                capStyle: ShapePath.FlatCap

                startX: 0
                startY: 0
                PathLine {
                    x: textEditContainer.width
                    y: 0
                }
                PathLine {
                    x: textEditContainer.width
                    y: textEditContainer.height
                }
                PathLine {
                    x: 0
                    y: textEditContainer.height
                }
                PathLine {
                    x: 0
                    y: 0
                }
            }
        }

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
                    return Lucent.Themed.palette.text;
                var c = Qt.color(settings.textColor);
                c.a = settings.textOpacity !== undefined ? settings.textOpacity : 1.0;
                return c;
            }
            selectionColor: Lucent.Themed.palette.highlight

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

            function handleEnterKey(event) {
                if (event.modifiers & Qt.ShiftModifier) {
                    textEdit.insert(textEdit.cursorPosition, "\n");
                    textEdit.forceActiveFocus();
                    textEdit.cursorVisible = true;
                } else {
                    tool.commitText();
                }
                event.accepted = true;
            }

            Keys.onReturnPressed: event => handleEnterKey(event)
            Keys.onEnterPressed: event => handleEnterKey(event)
            Keys.onEscapePressed: tool.cancelText()
        }

        // Resize handle (bottom-right corner)
        Rectangle {
            id: resizeHandle
            width: 10 / tool.zoomLevel
            height: 10 / tool.zoomLevel
            radius: 5 / tool.zoomLevel
            color: Lucent.Themed.selector
            border.color: Lucent.Themed.palette.base
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

    function isInResizeHandle(canvasX, canvasY) {
        if (!tool.isEditing)
            return false;

        var handleSize = 16 / tool.zoomLevel;  // Generous hit area
        var handleX = tool.boxX + tool.boxWidth - handleSize / 2;
        var handleY = tool.boxY + textEditContainer.height - handleSize / 2;

        return canvasX >= handleX && canvasX <= handleX + handleSize && canvasY >= handleY && canvasY <= handleY + handleSize;
    }

    function isInTextArea(canvasX, canvasY) {
        if (!tool.isEditing)
            return false;

        var insideX = canvasX >= tool.boxX && canvasX <= tool.boxX + tool.boxWidth;
        var insideY = canvasY >= tool.boxY && canvasY <= tool.boxY + textEditContainer.height;

        return insideX && insideY && !isInResizeHandle(canvasX, canvasY);
    }

    function handleMousePress(canvasX, canvasY, button, modifiers) {
        if (!tool.active || !tool.isEditing)
            return;

        if (isInResizeHandle(canvasX, canvasY)) {
            tool.isResizing = true;
            tool.resizeStartX = canvasX;
            tool.resizeStartY = canvasY;
            tool.resizeStartWidth = tool.boxWidth;
            tool.resizeStartHeight = tool.boxHeight;
        } else if (isInTextArea(canvasX, canvasY)) {
            var localX = canvasX - tool.boxX - tool.textPadding;
            var localY = canvasY - tool.boxY - tool.textPadding;
            var pos = textEdit.positionAt(localX, localY);
            tool.isSelectingText = true;
            tool.selectionAnchor = pos;
            textEdit.cursorPosition = pos;
            textEdit.forceActiveFocus();
        }
    }

    function handleClick(canvasX, canvasY) {
        if (!tool.active)
            return;

        if (tool.isEditing) {
            if (tool.skipNextClick) {
                tool.skipNextClick = false;
                return;
            }

            var insideX = canvasX >= tool.boxX && canvasX <= tool.boxX + tool.boxWidth;
            var insideY = canvasY >= tool.boxY && canvasY <= tool.boxY + textEditContainer.height;

            if (insideX && insideY) {
                var localX = canvasX - tool.boxX - tool.textPadding;
                var localY = canvasY - tool.boxY - tool.textPadding;
                textEdit.cursorPosition = textEdit.positionAt(localX, localY);
                textEdit.forceActiveFocus();
                return;
            }

            // Click outside: commit or cancel, then create new box at click position
            if (textEdit.text.trim().length > 0 && textEdit.text !== tool.placeholderText) {
                tool.commitText();
            } else {
                tool.cancelText();
            }
            // Create new text box at click position
            createTextBox(canvasX, canvasY);
            return;
        }

        // Not editing: create new text box at click position
        createTextBox(canvasX, canvasY);
    }

    function createTextBox(canvasX, canvasY) {
        tool.boxX = canvasX;
        tool.boxY = canvasY;
        tool.boxWidth = defaultBoxWidth;
        tool.boxHeight = defaultBoxHeight;
        tool.isEditing = true;
        textEdit.text = tool.placeholderText;
        textEdit.selectAll();
        textEdit.forceActiveFocus();
    }

    function handleMouseMove(canvasX, canvasY, modifiers) {
        if (!tool.active)
            return;

        if (tool.isResizing) {
            tool.boxWidth = Math.max(50, tool.resizeStartWidth + canvasX - tool.resizeStartX);
            tool.boxHeight = Math.max(30, tool.resizeStartHeight + canvasY - tool.resizeStartY);
            return;
        }

        if (tool.isSelectingText) {
            var localX = canvasX - tool.boxX - tool.textPadding;
            var localY = canvasY - tool.boxY - tool.textPadding;
            var pos = textEdit.positionAt(localX, localY);
            var start = Math.min(tool.selectionAnchor, pos);
            var end = Math.max(tool.selectionAnchor, pos);
            textEdit.select(start, end);
            return;
        }
    }

    function handleMouseRelease(canvasX, canvasY) {
        if (tool.isResizing) {
            tool.isResizing = false;
            tool.skipNextClick = true;
            textEdit.forceActiveFocus();
        }
        if (tool.isSelectingText) {
            tool.isSelectingText = false;
            if (textEdit.selectedText.length > 0)
                tool.skipNextClick = true;
        }
    }

    function commitText() {
        var finalText = textEdit.text.trim();
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
            height: textEditContainer.height - (tool.textPadding * 2),
            text: finalText,
            fontFamily: fontFamily,
            fontSize: fontSize,
            textColor: textColor.toString(),
            textOpacity: textOpacity
        });

        tool.isEditing = false;
        textEdit.text = "";
    }

    function cancelText() {
        tool.isEditing = false;
        textEdit.text = "";
    }

    function reset() {
        if (tool.isEditing) {
            var finalText = textEdit.text.trim();
            if (finalText.length > 0 && finalText !== tool.placeholderText)
                tool.commitText();
            else
                tool.cancelText();
        }
    }
}
