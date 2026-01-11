// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

Item {
    id: root
    readonly property SystemPalette themePalette: Lucent.Themed.palette

    // Map between visual order (top-to-bottom) and model order (append order).
    // Top of the list should correspond to the highest Z on canvas, so visual
    // index 0 maps to model index (count - 1).
    function modelIndexForDisplay(displayIndex) {
        return layerRepeater.count - 1 - displayIndex;
    }

    property int draggedIndex: -1
    property string draggedItemType: ""
    property string dropTargetContainerId: ""
    property var draggedItemParentId: null
    property var dropTargetParentId: null
    property int dropInsertIndex: -1
    property real lastDragYInFlick: 0

    property alias autoScrollTimer: autoScrollTimer

    function setSelectionFromDelegate(modelIndex, multi) {
        Lucent.SelectionManager.toggleSelection(modelIndex, multi);
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: Lucent.Styles.pad.xsm
            Layout.rightMargin: Lucent.Styles.pad.xsm

            Label {
                text: qsTr("Layers")
                font.pixelSize: 12
                color: themePalette.text
                Layout.fillWidth: true
            }

            RowLayout {
                spacing: 2

                Lucent.IconButton {
                    iconName: "stack-plus-fill"
                    tooltipText: qsTr("Add Layer")
                    onClicked: canvasModel.addLayer()
                }

                Lucent.IconButton {
                    iconName: "folder-plus-fill"
                    tooltipText: qsTr("Add Group")
                    onClicked: {
                        canvasModel.addItem({
                            "type": "group"
                        });
                        const idx = canvasModel.count() - 1;
                        Lucent.SelectionManager.setSelection([idx]);
                    }
                }

                Lucent.IconButton {
                    iconName: "folders-fill"
                    tooltipText: qsTr("Group Selection")
                    onClicked: {
                        var indices = Lucent.SelectionManager.currentSelectionIndices();
                        if (indices.length === 0)
                            return;
                        var finalGroupIndex = canvasModel.groupItems(indices);
                        if (finalGroupIndex >= 0) {
                            Lucent.SelectionManager.setSelection([finalGroupIndex]);
                        }
                    }
                }
            }
        }

        ToolSeparator {
            Layout.fillWidth: true
            orientation: Qt.Horizontal
            contentItem: Rectangle {
                implicitHeight: 1
                color: themePalette.mid
            }
        }

        Item {
            id: layerContainer
            Layout.fillWidth: true
            Layout.fillHeight: true
            width: root.width
            clip: true

            property int itemHeight: 28
            property int itemSpacing: 2
            property real dragStartContentY: 0
            property bool dragActive: false

            Flickable {
                id: layerFlickable
                anchors.fill: parent
                // Ensure content area is at least viewport height so empty-state label can center vertically
                contentHeight: Math.max(layerColumn.contentHeight, height)
                property real autoScrollStep: 8
                interactive: root.draggedIndex < 0
                boundsBehavior: Flickable.StopAtBounds
                clip: true

                function autoScrollScene(yInFlickable) {
                    if (contentHeight <= height)
                        return;
                    const edge = 24;
                    if (yInFlickable < edge) {
                        contentY = Math.max(0, contentY - autoScrollStep);
                    } else if (yInFlickable > height - edge) {
                        const maxY = Math.max(0, contentHeight - height);
                        contentY = Math.min(maxY, contentY + autoScrollStep);
                    }
                }

                Timer {
                    id: autoScrollTimer
                    interval: 30
                    running: layerContainer.dragActive
                    repeat: true
                    onTriggered: {
                        if (!layerContainer.dragActive)
                            return;
                        layerFlickable.autoScrollScene(root.lastDragYInFlick);
                    }
                }

                Item {
                    id: layerColumn
                    width: layerFlickable.width
                    property real contentHeight: {
                        const count = layerRepeater.count;
                        if (count <= 0)
                            return 0;
                        return count * layerContainer.itemHeight + Math.max(0, count - 1) * layerContainer.itemSpacing;
                    }

                    Repeater {
                        id: layerRepeater
                        model: canvasModel

                        delegate: LayerListItem {
                            panel: root
                            container: layerContainer
                            flickable: layerFlickable
                            repeater: layerRepeater
                            column: layerColumn
                        }
                    }
                }

                Label {
                    anchors.centerIn: parent
                    visible: layerRepeater.count === 0
                    text: qsTr("Empty")
                    font.pixelSize: 12
                    color: themePalette.text
                }
            }
        }
    }
}
