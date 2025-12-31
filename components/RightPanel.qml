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
                // Direct binding avoids binding loop warnings seen with Binding element
                selectedItem: DV.SelectionManager.selectedItem
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
