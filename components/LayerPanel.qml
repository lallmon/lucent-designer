import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as DV

Item {
    id: root

    property int draggedIndex: -1

    ColumnLayout {
        anchors.fill: parent
        spacing: 8

        Label {
            text: qsTr("Layers")
            font.pixelSize: 12
            font.bold: true
            color: "white"
            Layout.fillWidth: true
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: DV.Theme.colors.borderSubtle
        }

        Item {
            id: layerContainer
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            property int itemHeight: 28
            property int itemSpacing: 2

            Column {
                id: layerColumn
                width: parent.width
                spacing: layerContainer.itemSpacing

                Repeater {
                    id: layerRepeater
                    model: canvasModel

                    delegate: Item {
                        id: delegateRoot
                        width: layerColumn.width
                        height: layerContainer.itemHeight

                        // Model role properties (auto-bound from QAbstractListModel)
                        required property int index
                        required property string name
                        required property string itemType
                        required property int itemIndex

                        // Use layerRepeater.count (reactive property) not canvasModel.rowCount() (method)
                        // Methods don't trigger binding updates; properties do
                        property int displayIndex: layerRepeater.count - 1 - index
                        property bool isSelected: displayIndex === DV.SelectionManager.selectedItemIndex
                        property bool isBeingDragged: root.draggedIndex === displayIndex
                        property real dragOffsetY: 0

                        transform: Translate { y: delegateRoot.dragOffsetY }
                        z: isBeingDragged ? 100 : 0

                        Rectangle {
                            id: background
                            anchors.fill: parent
                            radius: DV.Theme.sizes.radiusSm
                            color: delegateRoot.isSelected ? DV.Theme.colors.accent 
                                 : hoverHandler.hovered ? DV.Theme.colors.panelHover 
                                 : "transparent"

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 4
                                anchors.rightMargin: 8
                                spacing: 4

                                Item {
                                    id: dragHandle
                                    Layout.preferredWidth: 24
                                    Layout.fillHeight: true

                                    Column {
                                        anchors.centerIn: parent
                                        spacing: 2
                                        Repeater {
                                            model: 3
                                            Rectangle {
                                                width: 10
                                                height: 2
                                                radius: 1
                                                color: DV.Theme.colors.textSubtle
                                            }
                                        }
                                    }

                                    DragHandler {
                                        id: dragHandler
                                        target: null
                                        yAxis.enabled: true
                                        xAxis.enabled: false

                                        onActiveChanged: {
                                            try {
                                                if (active) {
                                                    root.draggedIndex = delegateRoot.displayIndex
                                                } else {
                                                    if (root.draggedIndex >= 0) {
                                                        let totalItemHeight = layerContainer.itemHeight + layerContainer.itemSpacing
                                                        let indexDelta = Math.round(delegateRoot.dragOffsetY / totalItemHeight)
                                                        let newListIndex = delegateRoot.index + indexDelta
                                                        let rowCount = layerRepeater.count
                                                        newListIndex = Math.max(0, Math.min(rowCount - 1, newListIndex))
                                                        let newItemIndex = rowCount - 1 - newListIndex

                                                        if (newItemIndex !== root.draggedIndex) {
                                                            canvasModel.moveItem(root.draggedIndex, newItemIndex)
                                                        }
                                                    }
                                                    delegateRoot.dragOffsetY = 0
                                                    root.draggedIndex = -1
                                                }
                                            } catch (e) {
                                                // Delegate being destroyed during model update, ignore
                                            }
                                        }

                                        onTranslationChanged: {
                                            if (active) {
                                                delegateRoot.dragOffsetY = translation.y
                                            }
                                        }
                                    }

                                    HoverHandler {
                                        cursorShape: Qt.OpenHandCursor
                                    }
                                }

                                Label {
                                    text: delegateRoot.name
                                    font.pixelSize: 11
                                    color: delegateRoot.isSelected ? "white" : DV.Theme.colors.textSubtle
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true

                                    TapHandler {
                                        onTapped: {
                                            DV.SelectionManager.selectedItemIndex = delegateRoot.displayIndex
                                            DV.SelectionManager.selectedItem = canvasModel.getItemData(delegateRoot.displayIndex)
                                        }
                                    }

                                    HoverHandler {
                                        id: hoverHandler
                                    }
                                }
                            }
                        }

                        Behavior on dragOffsetY {
                            enabled: !delegateRoot.isBeingDragged
                            NumberAnimation { duration: 100 }
                        }
                    }
                }
            }

            Label {
                anchors.centerIn: parent
                visible: layerRepeater.count === 0
                text: qsTr("No objects")
                font.pixelSize: 11
                color: DV.Theme.colors.textSubtle
            }
        }
    }
}
