import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as DV

ToolBar {
    id: root
    height: 48

    property string activeTool: ""
    readonly property SystemPalette themePalette: DV.Themed.palette

    // Expose tool settings for external access (e.g., when creating shapes)
    readonly property var toolSettings: ({
            "rectangle": {
                strokeWidth: rectangleSettings.strokeWidth,
                strokeColor: rectangleSettings.strokeColor,
                strokeOpacity: rectangleSettings.strokeOpacity,
                fillColor: rectangleSettings.fillColor,
                fillOpacity: rectangleSettings.fillOpacity
            },
            "ellipse": {
                strokeWidth: ellipseSettings.strokeWidth,
                strokeColor: ellipseSettings.strokeColor,
                strokeOpacity: ellipseSettings.strokeOpacity,
                fillColor: ellipseSettings.fillColor,
                fillOpacity: ellipseSettings.fillOpacity
            },
            "pen": {
                strokeWidth: penSettings.strokeWidth,
                strokeColor: penSettings.strokeColor,
                strokeOpacity: penSettings.strokeOpacity,
                fillColor: penSettings.fillColor,
                fillOpacity: penSettings.fillOpacity
            },
            "text": {
                fontFamily: textSettings.fontFamily,
                fontSize: textSettings.fontSize,
                textColor: textSettings.textColor,
                textOpacity: textSettings.textOpacity
            }
        })

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 8
        anchors.rightMargin: 8
        spacing: 8

        DV.RectangleToolSettings {
            id: rectangleSettings
            visible: root.activeTool === "rectangle"
        }

        DV.EllipseToolSettings {
            id: ellipseSettings
            visible: root.activeTool === "ellipse"
        }

        DV.PenToolSettings {
            id: penSettings
            visible: root.activeTool === "pen"
        }

        DV.TextToolSettings {
            id: textSettings
            visible: root.activeTool === "text"
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
