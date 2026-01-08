import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

Pane {
    id: root
    width: 48
    padding: Lucent.Styles.pad.md

    signal toolSelected(string toolName)
    property string activeTool: ""
    readonly property SystemPalette themePalette: Lucent.Themed.palette

    ButtonGroup {
        id: toolButtonGroup
        exclusive: true
    }

    contentItem: ColumnLayout {
        Lucent.ToolIconButton {
            id: selButton
            toolName: "select"
            iconName: "hand-pointing"
            tooltipText: ""
            activeTool: root.activeTool
            buttonGroup: toolButtonGroup
            isDefaultSelect: true
            deselectValue: ""
            onToolClicked: function (nextTool) {
                root.toolSelected(nextTool);
            }
        }

        Lucent.ToolIconButton {
            id: rectButton
            toolName: "rectangle"
            iconName: "rectangle"
            tooltipText: "Rectangle Tool\n\nShift: Constrain to square\nAlt: Draw from center"
            activeTool: root.activeTool
            buttonGroup: toolButtonGroup
            onToolClicked: function (nextTool) {
                root.toolSelected(nextTool);
            }
        }

        Lucent.ToolIconButton {
            id: ellipseButton
            toolName: "ellipse"
            iconName: "circle"
            tooltipText: "Ellipse Tool\n\nShift: Constrain to circle\nAlt: Draw from center"
            activeTool: root.activeTool
            buttonGroup: toolButtonGroup
            onToolClicked: function (nextTool) {
                root.toolSelected(nextTool);
            }
        }

        Lucent.ToolIconButton {
            id: penButton
            toolName: "pen"
            iconName: "pen-nib"
            tooltipText: "Pen Tool\n\nClick to add points, click first point to close"
            activeTool: root.activeTool
            buttonGroup: toolButtonGroup
            onToolClicked: function (nextTool) {
                root.toolSelected(nextTool);
            }
        }

        Lucent.ToolIconButton {
            id: textButton
            toolName: "text"
            iconName: "text-t"
            tooltipText: "Text Tool\n\nClick to place text, type, then press Enter to confirm"
            activeTool: root.activeTool
            buttonGroup: toolButtonGroup
            onToolClicked: function (nextTool) {
                root.toolSelected(nextTool);
            }
        }

        Item {
            Layout.fillHeight: true
        }
    }
}
