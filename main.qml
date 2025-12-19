import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

ApplicationWindow {
    id: root
    width: 1920
    height: 1080
    visible: true
    title: qsTr("DesignVibe")

    // Menu Bar
    menuBar: MenuBar {
        viewport: viewport
    }

    // Status Bar
    footer: StatusBar {
        zoomLevel: viewport.zoomLevel
        cursorX: canvas.cursorX
        cursorY: canvas.cursorY
    }

    // Main layout with tool settings and content
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        
        // Tool Settings Bar
        ToolSettings {
            id: toolSettings
            Layout.fillWidth: true
            Layout.preferredHeight: 32
            activeTool: canvas.drawingMode === "" ? "select" : canvas.drawingMode
        }
        
        // Main content area with toolbar and canvas
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0
            
            // Left toolbar
            ToolBar {
                id: toolBar
                Layout.fillHeight: true
                
                onToolSelected: (toolName) => {
                    canvas.setDrawingMode(toolName)
                }
            }
            
            // Main Viewport with Canvas
            Viewport {
                id: viewport
                Layout.fillWidth: true
                Layout.fillHeight: true
                
                Canvas {
                    id: canvas
                    anchors.fill: parent
                    zoomLevel: viewport.zoomLevel
                    offsetX: viewport.offsetX
                    offsetY: viewport.offsetY
                    rectangleStrokeWidth: toolSettings.rectangleStrokeWidth
                    rectangleStrokeColor: toolSettings.rectangleStrokeColor
                    rectangleFillColor: toolSettings.rectangleFillColor
                    rectangleFillOpacity: toolSettings.rectangleFillOpacity
                    
                    onPanRequested: (dx, dy) => {
                        viewport.pan(dx, dy);
                    }
                }
            }
        }
    }
}
