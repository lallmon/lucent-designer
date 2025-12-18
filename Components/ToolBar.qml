import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Vertical toolbar for drawing tools
Rectangle {
    id: root
    width: 48
    color: "#3c3c3c"
    
    // Signal emitted when a tool is selected
    signal toolSelected(string toolName)
    
    // Current active tool
    property string activeTool: ""
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 8
        
        // Selection tool button
        Button {
            id: selButton
            Layout.preferredWidth: 32
            Layout.preferredHeight: 32
            Layout.alignment: Qt.AlignHCenter
            
            text: ""
            checkable: true
            checked: root.activeTool === "select" || root.activeTool === ""
            
            contentItem: Item {
                anchors.fill: parent
                PhIcon {
                    anchors.centerIn: parent
                    name: "hand-pointing"
                    size: 20
                    color: "white"
                }
            }
            
            onClicked: {
                if (checked) {
                    root.activeTool = "select"
                    rectButton.checked = false
                    root.toolSelected("select")
                } else {
                    root.activeTool = ""
                    root.toolSelected("")
                }
            }
            
            // Visual feedback for active state
            background: Rectangle {
                color: selButton.checked ? "#5c5c5c" : (selButton.hovered ? "#4c4c4c" : "#3c3c3c")
                border.color: selButton.checked ? "#ffffff" : "#6c6c6c"
                border.width: 1
                radius: 4
            }
        }
        
        // Rectangle tool button
        Button {
            id: rectButton
            Layout.preferredWidth: 32
            Layout.preferredHeight: 32
            Layout.alignment: Qt.AlignHCenter
            
            text: ""
            checkable: true
            checked: root.activeTool === "rectangle"
            
            contentItem: Item {
                anchors.fill: parent
                PhIcon {
                    anchors.centerIn: parent
                    name: "rectangle"
                    size: 20
                    color: "white"
                }
            }
            
            onClicked: {
                if (checked) {
                    root.activeTool = "rectangle"
                    selButton.checked = false
                    root.toolSelected("rectangle")
                } else {
                    root.activeTool = ""
                    root.toolSelected("")
                }
            }
            
            // Visual feedback for active state
            background: Rectangle {
                color: rectButton.checked ? "#5c5c5c" : (rectButton.hovered ? "#4c4c4c" : "#3c3c3c")
                border.color: rectButton.checked ? "#ffffff" : "#6c6c6c"
                border.width: 1
                radius: 4
            }
        }
        
        // Spacer to push tools to the top
        Item {
            Layout.fillHeight: true
        }
    }
}

