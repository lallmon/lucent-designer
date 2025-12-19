import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as DV

// Inspector component displaying properties of selected object
ScrollView {
    id: root
    clip: true
    
    // Property to receive selected item data
    property var selectedItem: null
    
    ColumnLayout {
        width: parent.width
        spacing: 12
        
        // Panel header
        Label {
            text: qsTr("Properties")
            font.pixelSize: 14
            font.bold: true
            color: "white"
            Layout.fillWidth: true
        }
        
        // Separator
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: DV.Theme.colors.borderSubtle
        }
        
        // Properties content
        ColumnLayout {
            Layout.fillWidth: true
            Layout.topMargin: 4
            spacing: 8
            
            // Show properties if item is selected
            visible: root.selectedItem !== null
            
            // Rectangle properties
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: rectanglePropsLayout.implicitHeight
                visible: root.selectedItem && root.selectedItem.type === "rectangle"
                
                ColumnLayout {
                    id: rectanglePropsLayout
                    anchors.fill: parent
                    spacing: 6
                    
                    Label {
                        text: qsTr("Rectangle")
                        font.pixelSize: 12
                        font.bold: true
                        color: DV.Theme.colors.textSubtle
                    }
                    
                    // Position
                    GridLayout {
                        columns: 2
                        rowSpacing: 4
                        columnSpacing: 8
                        Layout.fillWidth: true
                        
                        Label {
                            text: qsTr("X:")
                            font.pixelSize: 11
                            color: DV.Theme.colors.textSubtle
                        }
                        Label {
                            text: root.selectedItem ? root.selectedItem.x.toFixed(1) : ""
                            font.pixelSize: 11
                            color: "white"
                        }
                        
                        Label {
                            text: qsTr("Y:")
                            font.pixelSize: 11
                            color: DV.Theme.colors.textSubtle
                        }
                        Label {
                            text: root.selectedItem ? root.selectedItem.y.toFixed(1) : ""
                            font.pixelSize: 11
                            color: "white"
                        }
                        
                        Label {
                            text: qsTr("Width:")
                            font.pixelSize: 11
                            color: DV.Theme.colors.textSubtle
                        }
                        Label {
                            text: root.selectedItem ? root.selectedItem.width.toFixed(1) : ""
                            font.pixelSize: 11
                            color: "white"
                        }
                        
                        Label {
                            text: qsTr("Height:")
                            font.pixelSize: 11
                            color: DV.Theme.colors.textSubtle
                        }
                        Label {
                            text: root.selectedItem ? root.selectedItem.height.toFixed(1) : ""
                            font.pixelSize: 11
                            color: "white"
                        }
                    }
                    
                    // Stroke properties
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: DV.Theme.colors.borderSubtle
                        Layout.topMargin: 4
                        Layout.bottomMargin: 4
                    }
                    
                    GridLayout {
                        columns: 2
                        rowSpacing: 4
                        columnSpacing: 8
                        Layout.fillWidth: true
                        
                        Label {
                            text: qsTr("Stroke Width:")
                            font.pixelSize: 11
                            color: DV.Theme.colors.textSubtle
                        }
                        Label {
                            text: root.selectedItem ? root.selectedItem.strokeWidth.toFixed(1) + " px" : ""
                            font.pixelSize: 11
                            color: "white"
                        }
                        
                        Label {
                            text: qsTr("Stroke Color:")
                            font.pixelSize: 11
                            color: DV.Theme.colors.textSubtle
                        }
                        RowLayout {
                            spacing: 4
                            Rectangle {
                                width: 16
                                height: 16
                                color: root.selectedItem ? root.selectedItem.strokeColor : "transparent"
                                border.color: DV.Theme.colors.borderSubtle
                                border.width: 1
                            }
                            Label {
                                text: root.selectedItem ? root.selectedItem.strokeColor : ""
                                font.pixelSize: 10
                                color: "white"
                            }
                        }
                    }
                    
                    // Fill properties
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: DV.Theme.colors.borderSubtle
                        Layout.topMargin: 4
                        Layout.bottomMargin: 4
                    }
                    
                    GridLayout {
                        columns: 2
                        rowSpacing: 4
                        columnSpacing: 8
                        Layout.fillWidth: true
                        
                        Label {
                            text: qsTr("Fill Color:")
                            font.pixelSize: 11
                            color: DV.Theme.colors.textSubtle
                        }
                        RowLayout {
                            spacing: 4
                            Rectangle {
                                width: 16
                                height: 16
                                color: root.selectedItem ? root.selectedItem.fillColor : "transparent"
                                border.color: DV.Theme.colors.borderSubtle
                                border.width: 1
                            }
                            Label {
                                text: root.selectedItem ? root.selectedItem.fillColor : ""
                                font.pixelSize: 10
                                color: "white"
                            }
                        }
                        
                        Label {
                            text: qsTr("Fill Opacity:")
                            font.pixelSize: 11
                            color: DV.Theme.colors.textSubtle
                        }
                        Label {
                            text: root.selectedItem ? Math.round(root.selectedItem.fillOpacity * 100) + "%" : ""
                            font.pixelSize: 11
                            color: "white"
                        }
                    }
                }
            }
            
            // Ellipse properties
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: ellipsePropsLayout.implicitHeight
                visible: root.selectedItem && root.selectedItem.type === "ellipse"
                
                ColumnLayout {
                    id: ellipsePropsLayout
                    anchors.fill: parent
                    spacing: 6
                    
                    Label {
                        text: qsTr("Ellipse")
                        font.pixelSize: 12
                        font.bold: true
                        color: DV.Theme.colors.textSubtle
                    }
                    
                    // Position and radii
                    GridLayout {
                        columns: 2
                        rowSpacing: 4
                        columnSpacing: 8
                        Layout.fillWidth: true
                        
                        Label {
                            text: qsTr("Center X:")
                            font.pixelSize: 11
                            color: DV.Theme.colors.textSubtle
                        }
                        Label {
                            text: root.selectedItem ? root.selectedItem.centerX.toFixed(1) : ""
                            font.pixelSize: 11
                            color: "white"
                        }
                        
                        Label {
                            text: qsTr("Center Y:")
                            font.pixelSize: 11
                            color: DV.Theme.colors.textSubtle
                        }
                        Label {
                            text: root.selectedItem ? root.selectedItem.centerY.toFixed(1) : ""
                            font.pixelSize: 11
                            color: "white"
                        }
                        
                        Label {
                            text: qsTr("Radius X:")
                            font.pixelSize: 11
                            color: DV.Theme.colors.textSubtle
                        }
                        Label {
                            text: root.selectedItem ? root.selectedItem.radiusX.toFixed(1) : ""
                            font.pixelSize: 11
                            color: "white"
                        }
                        
                        Label {
                            text: qsTr("Radius Y:")
                            font.pixelSize: 11
                            color: DV.Theme.colors.textSubtle
                        }
                        Label {
                            text: root.selectedItem ? root.selectedItem.radiusY.toFixed(1) : ""
                            font.pixelSize: 11
                            color: "white"
                        }
                    }
                    
                    // Stroke properties
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: DV.Theme.colors.borderSubtle
                        Layout.topMargin: 4
                        Layout.bottomMargin: 4
                    }
                    
                    GridLayout {
                        columns: 2
                        rowSpacing: 4
                        columnSpacing: 8
                        Layout.fillWidth: true
                        
                        Label {
                            text: qsTr("Stroke Width:")
                            font.pixelSize: 11
                            color: DV.Theme.colors.textSubtle
                        }
                        Label {
                            text: root.selectedItem ? root.selectedItem.strokeWidth.toFixed(1) + " px" : ""
                            font.pixelSize: 11
                            color: "white"
                        }
                        
                        Label {
                            text: qsTr("Stroke Color:")
                            font.pixelSize: 11
                            color: DV.Theme.colors.textSubtle
                        }
                        RowLayout {
                            spacing: 4
                            Rectangle {
                                width: 16
                                height: 16
                                color: root.selectedItem ? root.selectedItem.strokeColor : "transparent"
                                border.color: DV.Theme.colors.borderSubtle
                                border.width: 1
                            }
                            Label {
                                text: root.selectedItem ? root.selectedItem.strokeColor : ""
                                font.pixelSize: 10
                                color: "white"
                            }
                        }
                    }
                    
                    // Fill properties
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: DV.Theme.colors.borderSubtle
                        Layout.topMargin: 4
                        Layout.bottomMargin: 4
                    }
                    
                    GridLayout {
                        columns: 2
                        rowSpacing: 4
                        columnSpacing: 8
                        Layout.fillWidth: true
                        
                        Label {
                            text: qsTr("Fill Color:")
                            font.pixelSize: 11
                            color: DV.Theme.colors.textSubtle
                        }
                        RowLayout {
                            spacing: 4
                            Rectangle {
                                width: 16
                                height: 16
                                color: root.selectedItem ? root.selectedItem.fillColor : "transparent"
                                border.color: DV.Theme.colors.borderSubtle
                                border.width: 1
                            }
                            Label {
                                text: root.selectedItem ? root.selectedItem.fillColor : ""
                                font.pixelSize: 10
                                color: "white"
                            }
                        }
                        
                        Label {
                            text: qsTr("Fill Opacity:")
                            font.pixelSize: 11
                            color: DV.Theme.colors.textSubtle
                        }
                        Label {
                            text: root.selectedItem ? Math.round(root.selectedItem.fillOpacity * 100) + "%" : ""
                            font.pixelSize: 11
                            color: "white"
                        }
                    }
                }
            }
        }
        
        // No selection message
        Label {
            visible: root.selectedItem === null
            text: qsTr("No object selected")
            font.pixelSize: 12
            color: DV.Theme.colors.textSubtle
            Layout.fillWidth: true
            Layout.topMargin: 8
        }
        
        // Spacer to push content to top
        Item {
            Layout.fillHeight: true
        }
    }
}

