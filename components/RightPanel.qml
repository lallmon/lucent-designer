import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as DV

Pane {
    id: root
    padding: 0

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Properties section
        Pane {
            Layout.fillWidth: true
            Layout.preferredHeight: parent.height * 0.35
            Layout.minimumHeight: 150
            padding: DV.Theme.sizes.rightPanelPadding

            ObjectPropertiesInspector {
                id: propertiesInspector
                anchors.fill: parent
                
                Binding {
                    target: propertiesInspector
                    property: "selectedItem"
                    value: DV.SelectionManager.selectedItem
                    restoreMode: Binding.RestoreNone
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: DV.Theme.colors.borderSubtle
        }

        // Layers section
        Pane {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 150
            padding: DV.Theme.sizes.rightPanelPadding

            LayerPanel {
                anchors.fill: parent
            }
        }
    }
}
