import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as DV

Pane {
    id: root

    signal toolSelected(string toolName)
    property string activeTool: ""

    ButtonGroup {
        id: toolButtonGroup
        exclusive: true
    }

    contentItem: ColumnLayout {
        // Selection tool button
        ToolButton {
            id: selButton
            Layout.preferredWidth: DV.Theme.sizes.toolButtonSize
            Layout.preferredHeight: DV.Theme.sizes.toolButtonSize
            Layout.alignment: Qt.AlignHCenter
            checkable: true
            checked: root.activeTool === "select" || root.activeTool === ""
            ButtonGroup.group: toolButtonGroup

            contentItem: Item {
                anchors.fill: parent
                PhIcon {
                    anchors.centerIn: parent
                    name: "hand-pointing"
                    color: "white"
                }
            }

            onClicked: {
                if (checked) {
                    root.activeTool = "select"
                    root.toolSelected("select")
                } else {
                    root.activeTool = ""
                    root.toolSelected("")
                }
            }

            background: Rectangle {
                color: selButton.checked ? DV.Theme.colors.panelActive : (selButton.hovered ? DV.Theme.colors.panelHover : DV.Theme.colors.panelBackground)
                border.color: selButton.checked ? "#ffffff" : DV.Theme.colors.borderDefault
                border.width: 1
                radius: DV.Theme.sizes.radiusMd
            }
        }

        // Rectangle tool button
        ToolButton {
            id: rectButton
            Layout.preferredWidth: DV.Theme.sizes.toolButtonSize
            Layout.preferredHeight: DV.Theme.sizes.toolButtonSize
            Layout.alignment: Qt.AlignHCenter
            checkable: true
            checked: root.activeTool === "rectangle"
            ButtonGroup.group: toolButtonGroup

            contentItem: Item {
                anchors.fill: parent
                PhIcon {
                    anchors.centerIn: parent
                    name: "rectangle"
                    color: "white"
                }
            }
            onClicked: {
                if (checked) {
                    root.activeTool = "rectangle"
                    root.toolSelected("rectangle")
                } else {
                    root.activeTool = ""
                    root.toolSelected("")
                }
            }
            background: Rectangle {
                color: rectButton.checked ? DV.Theme.colors.panelActive : (rectButton.hovered ? DV.Theme.colors.panelHover : DV.Theme.colors.panelBackground)
                border.color: rectButton.checked ? "#ffffff" : DV.Theme.colors.borderDefault
                border.width: 1
                radius: DV.Theme.sizes.radiusMd
            }
        }
        ToolButton {
            id: ellipseButton
            Layout.preferredWidth: DV.Theme.sizes.toolButtonSize
            Layout.preferredHeight: DV.Theme.sizes.toolButtonSize
            Layout.alignment: Qt.AlignHCenter
            checkable: true
            checked: root.activeTool === "ellipse"
            ButtonGroup.group: toolButtonGroup

            contentItem: Item {
                anchors.fill: parent
                PhIcon {
                    anchors.centerIn: parent
                    name: "circle"
                    color: "white"
                }
            }

            onClicked: {
                if (checked) {
                    root.activeTool = "ellipse"
                    root.toolSelected("ellipse")
                } else {
                    root.activeTool = ""
                    root.toolSelected("")
                }
            }

            // Visual feedback for active state
            background: Rectangle {
                color: ellipseButton.checked ? DV.Theme.colors.panelActive : (ellipseButton.hovered ? DV.Theme.colors.panelHover : DV.Theme.colors.panelBackground)
                border.color: ellipseButton.checked ? "#ffffff" : DV.Theme.colors.borderDefault
                border.width: 1
                radius: DV.Theme.sizes.radiusMd
            }
        }
        Item {
            Layout.fillHeight: true
        }
    }
}
