// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

Item {
    id: delegateRoot

    required property var panel
    required property var container
    required property var flickable
    required property var repeater
    required property var column

    // Model role properties from QAbstractListModel
    required property int index
    required property string name
    required property string itemType
    required property int itemIndex
    required property var itemId
    required property var parentId
    required property bool modelVisible
    required property bool modelLocked

    readonly property SystemPalette themePalette: Lucent.Themed.palette

    // Visual order is reversed so top of the list is highest Z.
    readonly property int displayIndex: repeater.count - 1 - index
    readonly property bool isSelected: Lucent.SelectionManager.selectedIndices && Lucent.SelectionManager.selectedIndices.indexOf(index) !== -1
    readonly property bool isBeingDragged: panel.draggedIndex === index
    property real dragOffsetY: 0
    readonly property bool hasParent: !!parentId
    readonly property bool isContainer: itemType === "layer" || itemType === "group"

    // Hide selection highlights during drag so drop hints are visible
    readonly property bool showAsSelected: isSelected && panel.draggedIndex < 0
    readonly property color itemTextColor: showAsSelected ? themePalette.highlightedText : themePalette.text
    readonly property var typeIconInfo: {
        switch (itemType) {
        case "layer":
            return {
                name: "stack-fill",
                weight: "fill"
            };
        case "group":
            return {
                name: "folders-fill",
                weight: "fill"
            };
        case "rectangle":
            return {
                name: "rectangle",
                weight: "regular"
            };
        case "ellipse":
            return {
                name: "circle",
                weight: "regular"
            };
        case "path":
            return {
                name: "pen-nib",
                weight: "regular"
            };
        case "text":
            return {
                name: "text-t",
                weight: "regular"
            };
        default:
            return {
                name: "shapes-fill",
                weight: "fill"
            };
        }
    }

    function resetDragState() {
        dragOffsetY = 0;
        panel.draggedIndex = -1;
        panel.draggedItemType = "";
        panel.dropTargetContainerId = "";
        panel.draggedItemParentId = null;
        panel.dropTargetParentId = null;
        panel.dropInsertIndex = -1;
    }

    function deleteItem() {
        Lucent.SelectionManager.selectedIndices = [index];
        Lucent.SelectionManager.selectedItemIndex = index;
        Lucent.SelectionManager.selectedItem = canvasModel.getItemData(index);
        canvasModel.removeItem(index);
    }

    function selectItemAt(newIndex) {
        Lucent.SelectionManager.selectedIndices = [newIndex];
        Lucent.SelectionManager.selectedItemIndex = newIndex;
        Lucent.SelectionManager.selectedItem = canvasModel.getItemData(newIndex);
    }

    anchors.left: parent ? parent.left : undefined
    anchors.right: parent ? parent.right : undefined
    height: container.itemHeight
    y: displayIndex * (container.itemHeight + container.itemSpacing)

    transform: Translate {
        y: delegateRoot.dragOffsetY
    }
    z: isBeingDragged ? 100 : 0

    readonly property bool isDropTarget: isContainer && panel.draggedIndex >= 0 && panel.draggedItemType !== "layer" && panel.dropTargetContainerId === itemId

    Rectangle {
        id: background
        anchors.fill: parent
        radius: Lucent.Styles.rad.sm
        color: delegateRoot.isDropTarget ? themePalette.highlight : delegateRoot.showAsSelected ? themePalette.highlight : nameHoverHandler.hovered ? themePalette.midlight : "transparent"
        border.width: delegateRoot.isDropTarget ? 2 : 0
        border.color: themePalette.highlight

        Rectangle {
            // Separator between items; thickens and highlights when this is the insertion target
            property bool isInsertTarget: delegateRoot.displayIndex === panel.dropInsertIndex
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: isInsertTarget ? 3 : 1
            color: isInsertTarget ? themePalette.highlight : themePalette.mid
            visible: delegateRoot.displayIndex > 0 || isInsertTarget
        }

        Rectangle {
            // Bottom indicator for dropping after the last item in the list
            property bool isLastItem: delegateRoot.displayIndex === repeater.count - 1
            property bool isBottomDropTarget: isLastItem && panel.dropInsertIndex === repeater.count
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: isBottomDropTarget ? 3 : 0
            color: themePalette.highlight
            visible: isBottomDropTarget
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: delegateRoot.hasParent ? 6 : 0
            anchors.rightMargin: 8
            spacing: 4

            Item {
                id: dragHandle
                Layout.preferredWidth: 28
                Layout.fillHeight: true

                Lucent.PhIcon {
                    anchors.centerIn: parent
                    name: delegateRoot.typeIconInfo.name
                    weight: delegateRoot.typeIconInfo.weight
                    size: 18
                    color: delegateRoot.itemTextColor
                }

                DragHandler {
                    id: dragHandler
                    target: null
                    yAxis.enabled: true
                    xAxis.enabled: false

                    onActiveChanged: {
                        try {
                            if (active) {
                                panel.draggedIndex = delegateRoot.index;
                                panel.draggedItemType = delegateRoot.itemType;
                                panel.draggedItemParentId = delegateRoot.parentId;
                                container.dragStartContentY = flickable.contentY;
                                container.dragActive = true;
                                panel.autoScrollTimer.start();
                            } else {
                                container.dragActive = false;
                                panel.autoScrollTimer.stop();
                                if (panel.draggedIndex >= 0) {
                                    // Guard against empty model or stale indices after a reset
                                    if (repeater.count <= 0) {
                                        delegateRoot.resetDragState();
                                        return;
                                    }
                                    let totalItemHeight = container.itemHeight + container.itemSpacing;
                                    let indexDelta = Math.round(delegateRoot.dragOffsetY / totalItemHeight);
                                    let targetDisplayIndex = panel.dropInsertIndex >= 0 ? panel.dropInsertIndex : delegateRoot.displayIndex + indexDelta;
                                    let rowCount = repeater.count;
                                    targetDisplayIndex = Math.max(0, Math.min(rowCount - 1, targetDisplayIndex));
                                    let targetModelIndex = panel.modelIndexForDisplay(targetDisplayIndex);
                                    if (targetModelIndex < 0 || targetModelIndex >= rowCount) {
                                        delegateRoot.resetDragState();
                                        return;
                                    }

                                    // Adjust target for removal-insertion semantics when moving down in display
                                    // (from higher model index to lower). The removal doesn't shift items
                                    // below, so we need to insert one position higher.
                                    // Exception: when dropping at the very bottom (dropInsertIndex === rowCount),
                                    // no adjustment needed since we're at the edge.
                                    const isBottomEdgeDrop = panel.dropInsertIndex === rowCount;
                                    if (panel.draggedIndex > targetModelIndex && !isBottomEdgeDrop) {
                                        targetModelIndex = Math.min(targetModelIndex + 1, rowCount - 1);
                                    }

                                    let didMove = false;
                                    const draggedParent = panel.draggedItemParentId || "";
                                    const isLayer = panel.draggedItemType === "layer";

                                    if (isLayer) {
                                        // Layers can only be reordered at top level, not reparented
                                        if (targetModelIndex !== panel.draggedIndex) {
                                            canvasModel.moveItem(panel.draggedIndex, targetModelIndex);
                                            didMove = true;
                                        }
                                    } else if (panel.dropTargetContainerId !== "") {
                                        if (panel.dropTargetContainerId !== draggedParent) {
                                            canvasModel.reparentItem(panel.draggedIndex, panel.dropTargetContainerId, -1);
                                            didMove = true;
                                        } else if (targetModelIndex !== panel.draggedIndex) {
                                            canvasModel.moveItem(panel.draggedIndex, targetModelIndex);
                                            didMove = true;
                                        }
                                    } else {
                                        const targetParent = panel.dropTargetParentId || "";
                                        if (draggedParent === targetParent) {
                                            if (targetModelIndex !== panel.draggedIndex) {
                                                canvasModel.moveItem(panel.draggedIndex, targetModelIndex);
                                                didMove = true;
                                            }
                                        } else {
                                            canvasModel.reparentItem(panel.draggedIndex, targetParent, targetModelIndex);
                                            didMove = true;
                                        }
                                    }

                                    if (didMove) {
                                        delegateRoot.selectItemAt(targetModelIndex);
                                    }
                                }
                                delegateRoot.resetDragState();
                            }
                        } catch (e) {
                            console.warn("LayerListItem drag error:", e);
                            delegateRoot.resetDragState();
                        }
                    }

                    onTranslationChanged: {
                        if (active) {
                            let compensatedY = translation.y + (flickable.contentY - container.dragStartContentY);
                            delegateRoot.dragOffsetY = compensatedY;
                            updateDropTarget();
                            const p = delegateRoot.mapToItem(flickable, 0, dragHandler.centroid.position.y);
                            panel.lastDragYInFlick = p.y;
                        }
                    }

                    function updateDropTarget() {
                        if (repeater.count === 0)
                            return;
                        if (!dragHandler.centroid || !dragHandler.centroid.position)
                            return;

                        const totalItemHeight = container.itemHeight + container.itemSpacing;
                        const rowCount = repeater.count;
                        const p = delegateRoot.mapToItem(column, 0, dragHandler.centroid.position.y);
                        let yInColumn = Math.max(0, Math.min(column.contentHeight - 1, p.y));

                        let targetDisplayIndex = Math.floor(yInColumn / totalItemHeight);
                        targetDisplayIndex = Math.max(0, Math.min(rowCount - 1, targetDisplayIndex));

                        const positionInRow = yInColumn / totalItemHeight;
                        const fractionalPart = positionInRow - Math.floor(positionInRow);
                        const isContainerCenterZone = fractionalPart > 0.25 && fractionalPart < 0.75;

                        const targetModelIndex = panel.modelIndexForDisplay(targetDisplayIndex);
                        const targetItem = repeater.itemAt(targetModelIndex);

                        if (targetItem && targetItem.isContainer && panel.draggedItemType !== "layer" && isContainerCenterZone) {
                            // Hovering on container center - show as drop target for parenting
                            panel.dropTargetContainerId = targetItem.itemId;
                            panel.dropTargetParentId = null;
                            panel.dropInsertIndex = -1;
                        } else {
                            // Edge zone - show insertion indicator
                            panel.dropTargetContainerId = "";
                            panel.dropTargetParentId = targetItem ? targetItem.parentId : null;
                            panel.dropInsertIndex = fractionalPart >= 0.5 ? Math.min(targetDisplayIndex + 1, rowCount) : targetDisplayIndex;

                            // Hide indicator when over self or adjacent (no move would occur)
                            const draggedDisplayIndex = delegateRoot.displayIndex;
                            if (panel.dropInsertIndex === draggedDisplayIndex || panel.dropInsertIndex === draggedDisplayIndex + 1) {
                                panel.dropInsertIndex = -1;
                            }
                        }
                    }
                }

                HoverHandler {
                    cursorShape: Qt.OpenHandCursor
                }
            }

            Item {
                id: nameEditor
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                Layout.minimumWidth: 80
                Layout.preferredWidth: 120
                implicitWidth: Math.max(80, nameLabel.implicitWidth)
                implicitHeight: nameLabel.implicitHeight
                property bool isEditing: false
                property string draftName: delegateRoot.name
                property string originalName: delegateRoot.name

                function startEditing() {
                    originalName = delegateRoot.name;
                    draftName = delegateRoot.name;
                    isEditing = true;
                    nameField.text = draftName;
                    nameField.selectAll();
                    nameField.forceActiveFocus();
                }

                function commitEditing() {
                    if (!isEditing)
                        return;
                    draftName = nameField.text;
                    isEditing = false;
                    if (draftName !== delegateRoot.name) {
                        canvasModel.renameItem(delegateRoot.index, draftName);
                    }
                    // Return focus to the list so global shortcuts (undo/redo) work
                    nameField.focus = false;
                    flickable.forceActiveFocus();
                }

                function cancelEditing() {
                    if (!isEditing)
                        return;
                    isEditing = false;
                    draftName = originalName;
                    nameField.text = originalName;
                    nameField.focus = false;
                    flickable.forceActiveFocus();
                }

                HoverHandler {
                    id: nameHoverHandler
                }

                MouseArea {
                    anchors.fill: parent
                    enabled: !nameEditor.isEditing
                    hoverEnabled: true
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    preventStealing: true
                    onClicked: function (mouse) {
                        if (mouse.button === Qt.RightButton) {
                            panel.setSelectionFromDelegate(delegateRoot.index, false);
                            itemContextMenu.popup();
                        } else {
                            panel.setSelectionFromDelegate(delegateRoot.index, mouse.modifiers & Qt.ControlModifier);
                        }
                    }
                    onDoubleClicked: function (mouse) {
                        panel.setSelectionFromDelegate(delegateRoot.index, mouse.modifiers & Qt.ControlModifier);
                        nameEditor.startEditing();
                    }

                    Menu {
                        id: itemContextMenu

                        Action {
                            text: qsTr("Rename")
                            onTriggered: nameEditor.startEditing()
                        }

                        Action {
                            text: qsTr("Export Layer...")
                            enabled: delegateRoot.itemType === "layer"
                            onTriggered: appController.openExportDialog(delegateRoot.itemId, delegateRoot.name || "Layer")
                        }

                        Action {
                            text: qsTr("Ungroup")
                            enabled: delegateRoot.itemType === "group"
                            onTriggered: canvasModel.ungroup(delegateRoot.index)
                        }

                        MenuSeparator {}

                        Action {
                            text: qsTr("Delete")
                            onTriggered: delegateRoot.deleteItem()
                        }
                    }
                }

                Label {
                    id: nameLabel
                    visible: !nameEditor.isEditing
                    text: delegateRoot.name
                    font.pixelSize: 11
                    color: delegateRoot.itemTextColor
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                    Layout.minimumWidth: 40
                }

                TextField {
                    id: nameField
                    visible: nameEditor.isEditing
                    text: nameEditor.draftName
                    font.pixelSize: 11
                    color: delegateRoot.itemTextColor
                    horizontalAlignment: Text.AlignLeft
                    verticalAlignment: TextInput.AlignVCenter
                    padding: 0
                    Layout.fillWidth: true
                    background: Rectangle {
                        color: "transparent"
                        border.color: "transparent"
                    }

                    Keys.onEscapePressed: nameEditor.cancelEditing()
                    onAccepted: nameEditor.commitEditing()
                    onActiveFocusChanged: {
                        if (!activeFocus && nameEditor.isEditing) {
                            nameEditor.cancelEditing();
                        }
                    }
                    onTextChanged: nameEditor.draftName = text
                    Keys.onPressed: function (event) {
                        if (nameEditor.isEditing)
                            return;
                        if (event.matches(StandardKey.Undo)) {
                            if (canvasModel) {
                                canvasModel.undo();
                            }
                            event.accepted = true;
                        } else if (event.matches(StandardKey.Redo)) {
                            if (canvasModel) {
                                canvasModel.redo();
                            }
                            event.accepted = true;
                        }
                    }
                }
            }

            Lucent.IconButton {
                iconName: delegateRoot.modelVisible ? "eye-fill" : "eye-slash-fill"
                iconBaseColor: delegateRoot.itemTextColor
                iconSize: 18
                onClicked: canvasModel.toggleVisibility(delegateRoot.index)
            }

            Lucent.IconButton {
                iconName: delegateRoot.modelLocked ? "lock-simple-fill" : "lock-simple-open-fill"
                iconBaseColor: delegateRoot.itemTextColor
                iconSize: 18
                onClicked: canvasModel.toggleLocked(delegateRoot.index)
            }

            Lucent.IconButton {
                iconName: "trash-simple-fill"
                iconBaseColor: delegateRoot.itemTextColor
                iconSize: 18
                onClicked: delegateRoot.deleteItem()
            }
        }
    }

    Behavior on dragOffsetY {
        enabled: !delegateRoot.isBeingDragged
        NumberAnimation {
            duration: 100
        }
    }
}
