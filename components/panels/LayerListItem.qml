import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

// Individual row item for the layer list
Item {
    id: delegateRoot

    // Parent references for accessing shared state
    required property var panel        // LayerPanel root
    required property var container    // layerContainer
    required property var flickable    // layerFlickable
    required property var repeater     // layerRepeater
    required property var column       // layerColumn

    // Model role properties (auto-bound from QAbstractListModel)
    required property int index
    required property string name
    required property string itemType
    required property int itemIndex
    required property var itemId      // Layer's unique ID (null for shapes)
    required property var parentId    // Parent layer ID (null for top-level items)
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

    // Computed colors and icons based on state
    // Hide all selection highlights during any drag so drop hints are clearly visible
    readonly property bool showAsSelected: isSelected && panel.draggedIndex < 0
    readonly property color itemTextColor: showAsSelected ? themePalette.highlightedText : themePalette.text
    readonly property string typeIcon: {
        switch (itemType) {
        case "layer":
            return "stack";
        case "group":
            return "folder-simple";
        case "rectangle":
            return "rectangle";
        case "ellipse":
            return "circle";
        case "path":
            return "pen-nib";
        case "text":
            return "text-t";
        default:
            return "shapes";
        }
    }

    // Reset all drag-related state
    function resetDragState() {
        dragOffsetY = 0;
        panel.draggedIndex = -1;
        panel.draggedItemType = "";
        panel.dropTargetContainerId = "";
        panel.draggedItemParentId = null;
        panel.dropTargetParentId = null;
        panel.dropInsertIndex = -1;
    }

    // Delete this item with proper selection update
    function deleteItem() {
        Lucent.SelectionManager.selectedIndices = [index];
        Lucent.SelectionManager.selectedItemIndex = index;
        Lucent.SelectionManager.selectedItem = canvasModel.getItemData(index);
        canvasModel.removeItem(index);
    }

    // Select the item at the given index after a drag-drop
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
            anchors.leftMargin: delegateRoot.hasParent ? 20 : 4
            anchors.rightMargin: 8
            spacing: 4

            Item {
                id: dragHandle
                Layout.preferredWidth: 28
                Layout.fillHeight: true

                Lucent.PhIcon {
                    anchors.centerIn: parent
                    name: delegateRoot.typeIcon
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
                                    // Calculate target model index for potential reordering
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

                                    // Determine the action based on drag context
                                    let didMove = false;
                                    if (panel.dropTargetContainerId !== "" && panel.draggedItemType !== "layer") {
                                        // Check if dropping onto the SAME parent (sibling reorder, not reparent)
                                        if (panel.dropTargetContainerId === panel.draggedItemParentId) {
                                            // Same parent - just reorder within the container
                                            if (targetModelIndex !== panel.draggedIndex) {
                                                canvasModel.moveItem(panel.draggedIndex, targetModelIndex);
                                                didMove = true;
                                            }
                                        } else {
                                            // Different container - reparent to that container
                                            canvasModel.reparentItem(panel.draggedIndex, panel.dropTargetContainerId, targetModelIndex);
                                            didMove = true;
                                        }
                                    } else if (panel.dropTargetParentId && panel.draggedItemType !== "layer") {
                                        // Dropping onto a gap between children of a layer
                                        const isSameParent = panel.draggedItemParentId === panel.dropTargetParentId;
                                        if (isSameParent) {
                                            if (targetModelIndex !== panel.draggedIndex) {
                                                canvasModel.moveItem(panel.draggedIndex, targetModelIndex);
                                                didMove = true;
                                            }
                                        } else {
                                            canvasModel.reparentItem(panel.draggedIndex, panel.dropTargetParentId, targetModelIndex);
                                            didMove = true;
                                        }
                                    } else if (panel.draggedItemParentId && panel.dropTargetParentId === panel.draggedItemParentId) {
                                        // Dropping onto a sibling (same parent) - just reorder, keep parent
                                        if (targetModelIndex !== panel.draggedIndex) {
                                            canvasModel.moveItem(panel.draggedIndex, targetModelIndex);
                                            didMove = true;
                                        }
                                    } else if (panel.draggedItemParentId && !panel.dropTargetParentId && panel.dropTargetContainerId === "") {
                                        // Dropping a child onto a top-level item - unparent
                                        canvasModel.reparentItem(panel.draggedIndex, "", targetModelIndex);
                                        didMove = true;
                                    } else {
                                        // Normal z-order reordering for top-level items
                                        if (targetModelIndex !== panel.draggedIndex) {
                                            canvasModel.moveItem(panel.draggedIndex, targetModelIndex);
                                            didMove = true;
                                        }
                                    }

                                    // Select the dropped item
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
                            // Compensate for flickable contentY changes during auto-scroll
                            let compensatedY = translation.y + (flickable.contentY - container.dragStartContentY);
                            delegateRoot.dragOffsetY = compensatedY;
                            // Calculate which item we're hovering over
                            updateDropTarget();
                            // Auto-scroll handled via timer using scene position
                            const p = delegateRoot.mapToItem(flickable, 0, dragHandler.centroid.position.y);
                            panel.lastDragYInFlick = p.y;
                        }
                    }

                    function updateDropTarget() {
                        if (repeater.count === 0)
                            return;
                        if (!dragHandler.centroid || !dragHandler.centroid.position)
                            return;

                        // Use pointer position within the list to determine target row
                        const totalItemHeight = container.itemHeight + container.itemSpacing;
                        const rowCount = repeater.count;
                        const p = delegateRoot.mapToItem(column, 0, dragHandler.centroid.position.y);
                        let yInColumn = p.y;
                        // Clamp to column bounds
                        yInColumn = Math.max(0, Math.min(column.contentHeight - 1, yInColumn));

                        let targetDisplayIndex = Math.floor(yInColumn / totalItemHeight);
                        targetDisplayIndex = Math.max(0, Math.min(rowCount - 1, targetDisplayIndex));

                        // Calculate fractional position within the target row using absolute pointer
                        const positionInRow = yInColumn / totalItemHeight;
                        const fractionalPart = positionInRow - Math.floor(positionInRow);
                        const isLayerParentingZone = fractionalPart > 0.25 && fractionalPart < 0.75;

                        const targetModelIndex = panel.modelIndexForDisplay(targetDisplayIndex);
                        const targetItem = repeater.itemAt(targetModelIndex);
                        if (targetItem && targetItem.isContainer && panel.draggedItemType !== "layer" && isLayerParentingZone) {
                            // Center of a container - show as drop target for parenting
                            panel.dropTargetContainerId = targetItem.itemId;
                            panel.dropTargetParentId = null;
                            panel.dropInsertIndex = -1;
                        } else {
                            // Edge zone - show insertion indicator
                            panel.dropTargetContainerId = "";
                            panel.dropTargetParentId = targetItem ? targetItem.parentId : null;
                            // Insert indicator shows on the item below the insertion gap
                            if (fractionalPart >= 0.5) {
                                // Dropping below target row, indicator on next item
                                // Allow rowCount as valid value for "after last item"
                                panel.dropInsertIndex = Math.min(targetDisplayIndex + 1, rowCount);
                            } else {
                                // Dropping above target row, indicator on target item
                                panel.dropInsertIndex = targetDisplayIndex;
                            }
                            // Hide indicator when dragging over self or adjacent position (no move would occur)
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
                iconName: delegateRoot.modelVisible ? "eye" : "eye-closed"
                iconBaseColor: delegateRoot.itemTextColor
                size: 28
                iconSize: 16
                onClicked: canvasModel.toggleVisibility(delegateRoot.index)
            }

            Lucent.IconButton {
                iconName: delegateRoot.modelLocked ? "lock" : "lock-open"
                iconBaseColor: delegateRoot.itemTextColor
                size: 28
                iconSize: 16
                onClicked: canvasModel.toggleLocked(delegateRoot.index)
            }

            Lucent.IconButton {
                iconName: "trash"
                iconBaseColor: delegateRoot.itemTextColor
                size: 28
                iconSize: 16
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
