import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as DV

Item {
    id: root
    readonly property SystemPalette themePalette: DV.Themed.palette

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

    function setSelectionFromDelegate(modelIndex, multi) {
        DV.SelectionManager.toggleSelection(modelIndex, multi);
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            spacing: 0

            Label {
                text: qsTr("Layers")
                font.pixelSize: 12
                font.bold: true
                color: themePalette.text
                Layout.fillWidth: true
            }

            RowLayout {
                spacing: 4

                Rectangle {
                    id: addLayerButton
                    Layout.preferredWidth: 24
                    Layout.preferredHeight: 24
                    radius: DV.Styles.rad.sm
                    color: addLayerHover.hovered ? themePalette.midlight : "transparent"

                    DV.PhIcon {
                        anchors.centerIn: parent
                        name: "stack-plus"
                        size: 18
                        color: themePalette.text
                    }

                    HoverHandler {
                        id: addLayerHover
                        cursorShape: Qt.PointingHandCursor
                    }

                    TapHandler {
                        onTapped: canvasModel.addLayer()
                    }
                }

                Rectangle {
                    id: addGroupButton
                    Layout.preferredWidth: 24
                    Layout.preferredHeight: 24
                    radius: DV.Styles.rad.sm
                    color: addGroupHover.hovered ? themePalette.midlight : "transparent"

                    DV.PhIcon {
                        anchors.centerIn: parent
                        name: "folder-simple-plus"
                        size: 18
                        color: themePalette.text
                    }

                    HoverHandler {
                        id: addGroupHover
                        cursorShape: Qt.PointingHandCursor
                    }

                    TapHandler {
                        onTapped: {
                            canvasModel.addItem({
                                "type": "group"
                            });
                            const idx = canvasModel.count() - 1;
                            DV.SelectionManager.setSelection([idx]);
                        }
                    }
                }

                Rectangle {
                    id: addGroupFromSelectionButton
                    Layout.preferredWidth: 24
                    Layout.preferredHeight: 24
                    radius: DV.Styles.rad.sm
                    color: addGroupFromSelectionHover.hovered ? themePalette.midlight : "transparent"

                    DV.PhIcon {
                        anchors.centerIn: parent
                        name: "folders"
                        size: 18
                        color: themePalette.text
                    }

                    HoverHandler {
                        id: addGroupFromSelectionHover
                        cursorShape: Qt.PointingHandCursor
                    }

                    TapHandler {
                        onTapped: {
                            var indices = DV.SelectionManager.currentSelectionIndices();
                            if (indices.length === 0)
                                return;
                            var finalGroupIndex = canvasModel.groupItems(indices);
                            if (finalGroupIndex >= 0) {
                                DV.SelectionManager.setSelection([finalGroupIndex]);
                            }
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: themePalette.mid
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

                        delegate: Item {
                            id: delegateRoot
                            anchors.left: parent.left
                            anchors.right: parent.right
                            height: layerContainer.itemHeight
                            y: displayIndex * (layerContainer.itemHeight + layerContainer.itemSpacing)

                            // Model role properties (auto-bound from QAbstractListModel)
                            required property int index
                            required property string name
                            required property string itemType
                            required property int itemIndex
                            required property var itemId      // Layer's unique ID (null for shapes)
                            required property var parentId    // Parent layer ID (null for top-level items)
                            required property bool modelVisible
                            required property bool modelLocked

                            // Model index is the source-of-truth for data operations.
                            property int modelIndex: index
                            // Visual order is reversed so top of the list is highest Z.
                            property int displayIndex: layerRepeater.count - 1 - modelIndex
                            property bool isSelected: DV.SelectionManager.selectedIndices && DV.SelectionManager.selectedIndices.indexOf(modelIndex) !== -1
                            property bool isBeingDragged: root.draggedIndex === modelIndex
                            property real dragOffsetY: 0
                            property bool hasParent: !!parentId
                            property bool isLayer: itemType === "layer"
                            property bool isGroup: itemType === "group"
                            property bool isContainer: isLayer || isGroup

                            transform: Translate {
                                y: delegateRoot.dragOffsetY
                            }
                            z: isBeingDragged ? 100 : 0

                            property bool isDropTarget: delegateRoot.isContainer && root.draggedIndex >= 0 && root.draggedItemType !== "layer" && root.dropTargetContainerId === delegateRoot.itemId

                            Rectangle {
                                id: background
                                anchors.fill: parent
                                radius: DV.Styles.rad.sm
                                color: delegateRoot.isDropTarget ? themePalette.highlight : delegateRoot.isSelected ? themePalette.highlight : nameHoverHandler.hovered ? themePalette.midlight : "transparent"
                                border.width: delegateRoot.isDropTarget ? 2 : 0
                                border.color: themePalette.highlight

                                Rectangle {
                                    // Separator between items; thickens and highlights when this is the insertion target
                                    property bool isInsertTarget: delegateRoot.displayIndex === root.dropInsertIndex
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    anchors.top: parent.top
                                    height: isInsertTarget ? 3 : 1
                                    color: isInsertTarget ? themePalette.highlight : themePalette.mid
                                    visible: delegateRoot.displayIndex > 0 || isInsertTarget
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

                                        DV.PhIcon {
                                            anchors.centerIn: parent
                                            name: {
                                                if (delegateRoot.itemType === "layer")
                                                    return "stack";
                                                if (delegateRoot.itemType === "group")
                                                    return "folder-simple";
                                                if (delegateRoot.itemType === "rectangle")
                                                    return "rectangle";
                                                if (delegateRoot.itemType === "ellipse")
                                                    return "circle";
                                                if (delegateRoot.itemType === "path")
                                                    return "pen-nib";
                                                if (delegateRoot.itemType === "text")
                                                    return "text-t";
                                                return "shapes";
                                            }
                                            size: 18
                                            color: delegateRoot.isSelected ? themePalette.highlightedText : themePalette.text
                                        }

                                        DragHandler {
                                            id: dragHandler
                                            target: null
                                            yAxis.enabled: true
                                            xAxis.enabled: false

                                            onActiveChanged: {
                                                try {
                                                    if (active) {
                                                        root.draggedIndex = delegateRoot.modelIndex;
                                                        root.draggedItemType = delegateRoot.itemType;
                                                        root.draggedItemParentId = delegateRoot.parentId;
                                                        layerContainer.dragStartContentY = layerFlickable.contentY;
                                                        layerContainer.dragActive = true;
                                                        autoScrollTimer.start();
                                                    } else {
                                                        layerContainer.dragActive = false;
                                                        autoScrollTimer.stop();
                                                        if (root.draggedIndex >= 0) {
                                                            // Guard against empty model or stale indices after a reset
                                                            if (layerRepeater.count <= 0) {
                                                                delegateRoot.dragOffsetY = 0;
                                                                root.draggedIndex = -1;
                                                                root.draggedItemType = "";
                                                                root.dropTargetContainerId = "";
                                                                root.draggedItemParentId = null;
                                                                root.dropTargetParentId = null;
                                                                root.dropInsertIndex = -1;
                                                                return;
                                                            }
                                                            // Calculate target model index for potential reordering
                                                            let totalItemHeight = layerContainer.itemHeight + layerContainer.itemSpacing;
                                                            let indexDelta = Math.round(delegateRoot.dragOffsetY / totalItemHeight);
                                                            let targetDisplayIndex = root.dropInsertIndex >= 0 ? root.dropInsertIndex : delegateRoot.displayIndex + indexDelta;
                                                            let rowCount = layerRepeater.count;
                                                            targetDisplayIndex = Math.max(0, Math.min(rowCount - 1, targetDisplayIndex));
                                                            let targetModelIndex = root.modelIndexForDisplay(targetDisplayIndex);
                                                            if (targetModelIndex < 0 || targetModelIndex >= rowCount) {
                                                                delegateRoot.dragOffsetY = 0;
                                                                root.draggedIndex = -1;
                                                                root.draggedItemType = "";
                                                                root.dropTargetContainerId = "";
                                                                root.draggedItemParentId = null;
                                                                root.dropTargetParentId = null;
                                                                root.dropInsertIndex = -1;
                                                                return;
                                                            }

                                                            // Determine the action based on drag context
                                                            if (root.dropTargetContainerId !== "" && root.draggedItemType !== "layer") {
                                                                // Check if dropping onto the SAME parent (sibling reorder, not reparent)
                                                                if (root.dropTargetContainerId === root.draggedItemParentId) {
                                                                    // Same parent - just reorder within the container
                                                                    if (targetModelIndex !== root.draggedIndex) {
                                                                        canvasModel.moveItem(root.draggedIndex, targetModelIndex);
                                                                    }
                                                                } else {
                                                                    // Different container - reparent to that container
                                                                    let insertModelIndex = targetModelIndex;
                                                                    canvasModel.reparentItem(root.draggedIndex, root.dropTargetContainerId, insertModelIndex);
                                                                }
                                                            } else if (root.dropTargetParentId && root.draggedItemType !== "layer") {
                                                                // Dropping onto a gap between children of a layer
                                                                const isSameParent = root.draggedItemParentId === root.dropTargetParentId;
                                                                let insertModelIndex = targetModelIndex;
                                                                if (isSameParent) {
                                                                    if (insertModelIndex !== root.draggedIndex) {
                                                                        canvasModel.moveItem(root.draggedIndex, insertModelIndex);
                                                                    }
                                                                } else {
                                                                    canvasModel.reparentItem(root.draggedIndex, root.dropTargetParentId, insertModelIndex);
                                                                }
                                                            } else if (root.draggedItemParentId && root.dropTargetParentId === root.draggedItemParentId) {
                                                                // Dropping onto a sibling (same parent) - just reorder, keep parent
                                                                if (targetModelIndex !== root.draggedIndex) {
                                                                    canvasModel.moveItem(root.draggedIndex, targetModelIndex);
                                                                }
                                                            } else if (root.draggedItemParentId && !root.dropTargetParentId && root.dropTargetContainerId === "") {
                                                                // Dropping a child onto a top-level item - unparent
                                                                canvasModel.reparentItem(root.draggedIndex, "", targetModelIndex);
                                                            } else {
                                                                // Normal z-order reordering for top-level items
                                                                if (targetModelIndex !== root.draggedIndex) {
                                                                    canvasModel.moveItem(root.draggedIndex, targetModelIndex);
                                                                }
                                                            }
                                                        }
                                                        delegateRoot.dragOffsetY = 0;
                                                        root.draggedIndex = -1;
                                                        root.draggedItemType = "";
                                                        root.dropTargetContainerId = "";
                                                        root.draggedItemParentId = null;
                                                        root.dropTargetParentId = null;
                                                        root.dropInsertIndex = -1;
                                                    }
                                                } catch (e) {
                                                    console.warn("LayerPanel drag error:", e);
                                                    // Reset state - guard against delegate destruction during model reset
                                                    if (typeof delegateRoot !== 'undefined' && delegateRoot) {
                                                        delegateRoot.dragOffsetY = 0;
                                                    }
                                                    if (typeof root !== 'undefined' && root) {
                                                        root.draggedIndex = -1;
                                                        root.draggedItemType = "";
                                                        root.dropTargetContainerId = "";
                                                        root.dropTargetContainerId = "";
                                                        root.draggedItemParentId = null;
                                                        root.dropTargetParentId = null;
                                                        root.dropInsertIndex = -1;
                                                    }
                                                }
                                            }

                                            onTranslationChanged: {
                                                if (active) {
                                                    // Compensate for flickable contentY changes during auto-scroll
                                                    let compensatedY = translation.y + (layerFlickable.contentY - layerContainer.dragStartContentY);
                                                    delegateRoot.dragOffsetY = compensatedY;
                                                    // Calculate which item we're hovering over
                                                    updateDropTarget();
                                                    // Auto-scroll handled via timer using scene position
                                                    const p = delegateRoot.mapToItem(layerFlickable, 0, dragHandler.centroid.position.y);
                                                    root.lastDragYInFlick = p.y;
                                                }
                                            }

                                            function updateDropTarget() {
                                                if (layerRepeater.count === 0)
                                                    return;
                                                if (!dragHandler.centroid || !dragHandler.centroid.position)
                                                    return;

                                                // Use pointer position within the list to determine target row
                                                const totalItemHeight = layerContainer.itemHeight + layerContainer.itemSpacing;
                                                const rowCount = layerRepeater.count;
                                                const p = delegateRoot.mapToItem(layerColumn, 0, dragHandler.centroid.position.y);
                                                let yInColumn = p.y;
                                                // Clamp to column bounds
                                                yInColumn = Math.max(0, Math.min(layerColumn.contentHeight - 1, yInColumn));

                                                let targetDisplayIndex = Math.floor(yInColumn / totalItemHeight);
                                                targetDisplayIndex = Math.max(0, Math.min(rowCount - 1, targetDisplayIndex));

                                                // Calculate fractional position within the target row using absolute pointer
                                                const positionInRow = yInColumn / totalItemHeight;
                                                const fractionalPart = positionInRow - Math.floor(positionInRow);
                                                const isLayerParentingZone = fractionalPart > 0.25 && fractionalPart < 0.75;

                                                const targetModelIndex = root.modelIndexForDisplay(targetDisplayIndex);
                                                const targetItem = layerRepeater.itemAt(targetModelIndex);
                                                if (targetItem && targetItem.isContainer && root.draggedItemType !== "layer" && isLayerParentingZone) {
                                                    // Center of a container - show as drop target for parenting
                                                    root.dropTargetContainerId = targetItem.itemId;
                                                    root.dropTargetParentId = null;
                                                    root.dropInsertIndex = -1;
                                                } else {
                                                    // Edge zone - show insertion indicator
                                                    root.dropTargetContainerId = "";
                                                    root.dropTargetParentId = targetItem ? targetItem.parentId : null;
                                                    // Insert indicator shows on the item below the insertion gap
                                                    if (fractionalPart >= 0.5) {
                                                        // Dropping below target row, indicator on next item
                                                        root.dropInsertIndex = Math.min(targetDisplayIndex + 1, rowCount - 1);
                                                    } else {
                                                        // Dropping above target row, indicator on target item
                                                        root.dropInsertIndex = targetDisplayIndex;
                                                    }
                                                    // Hide indicator when dragging over self or adjacent position (no move would occur)
                                                    const draggedDisplayIndex = delegateRoot.displayIndex;
                                                    if (root.dropInsertIndex === draggedDisplayIndex || root.dropInsertIndex === draggedDisplayIndex + 1) {
                                                        root.dropInsertIndex = -1;
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
                                                canvasModel.renameItem(delegateRoot.modelIndex, draftName);
                                            }
                                            // Return focus to the list so global shortcuts (undo/redo) work
                                            nameField.focus = false;
                                            layerFlickable.forceActiveFocus();
                                        }

                                        function cancelEditing() {
                                            if (!isEditing)
                                                return;
                                            isEditing = false;
                                            draftName = originalName;
                                            nameField.text = originalName;
                                            nameField.focus = false;
                                            layerFlickable.forceActiveFocus();
                                        }

                                        HoverHandler {
                                            id: nameHoverHandler
                                        }

                                        MouseArea {
                                            anchors.fill: parent
                                            enabled: !nameEditor.isEditing
                                            hoverEnabled: true
                                            acceptedButtons: Qt.LeftButton
                                            preventStealing: true
                                            onClicked: function (mouse) {
                                                root.setSelectionFromDelegate(delegateRoot.modelIndex, mouse.modifiers & Qt.ControlModifier);
                                            }
                                            onDoubleClicked: function (mouse) {
                                                root.setSelectionFromDelegate(delegateRoot.modelIndex, mouse.modifiers & Qt.ControlModifier);
                                                nameEditor.startEditing();
                                            }
                                        }

                                        Label {
                                            id: nameLabel
                                            visible: !nameEditor.isEditing
                                            text: delegateRoot.name
                                            font.pixelSize: 11
                                            color: delegateRoot.isSelected ? themePalette.highlightedText : themePalette.text
                                            elide: Text.ElideRight
                                            Layout.fillWidth: true
                                            Layout.minimumWidth: 40
                                        }

                                        TextField {
                                            id: nameField
                                            visible: nameEditor.isEditing
                                            text: nameEditor.draftName
                                            font.pixelSize: 11
                                            color: delegateRoot.isSelected ? themePalette.highlightedText : themePalette.text
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

                                    Item {
                                        id: visibilityButton
                                        Layout.preferredWidth: 28
                                        Layout.fillHeight: true

                                        HoverHandler {
                                            id: visibilityHover
                                        }

                                        MouseArea {
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            acceptedButtons: Qt.LeftButton
                                            preventStealing: true
                                            onClicked: {
                                                canvasModel.toggleVisibility(delegateRoot.modelIndex);
                                            }
                                        }

                                        Rectangle {
                                            anchors.fill: parent
                                            color: visibilityHover.hovered ? themePalette.midlight : "transparent"
                                            radius: DV.Styles.rad.sm

                                            DV.PhIcon {
                                                anchors.centerIn: parent
                                                name: delegateRoot.modelVisible ? "eye" : "eye-closed"
                                                size: 16
                                                color: delegateRoot.isSelected ? themePalette.highlightedText : themePalette.text
                                            }
                                        }
                                    }

                                    Item {
                                        id: lockButton
                                        Layout.preferredWidth: 28
                                        Layout.fillHeight: true

                                        HoverHandler {
                                            id: lockHover
                                        }

                                        MouseArea {
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            acceptedButtons: Qt.LeftButton
                                            preventStealing: true
                                            onClicked: {
                                                canvasModel.toggleLocked(delegateRoot.modelIndex);
                                            }
                                        }

                                        Rectangle {
                                            anchors.fill: parent
                                            color: lockHover.hovered ? themePalette.midlight : "transparent"
                                            radius: DV.Styles.rad.sm

                                            DV.PhIcon {
                                                anchors.centerIn: parent
                                                name: delegateRoot.modelLocked ? "lock" : "lock-open"
                                                size: 16
                                                color: delegateRoot.isSelected ? themePalette.highlightedText : themePalette.text
                                            }
                                        }
                                    }

                                    Item {
                                        id: deleteButton
                                        Layout.preferredWidth: 28
                                        Layout.fillHeight: true

                                        HoverHandler {
                                            id: deleteHover
                                        }

                                        MouseArea {
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            acceptedButtons: Qt.LeftButton
                                            preventStealing: true
                                            onClicked: {
                                                // Ensure selection reflects the target being deleted
                                                DV.SelectionManager.selectedIndices = [delegateRoot.modelIndex];
                                                DV.SelectionManager.selectedItemIndex = delegateRoot.modelIndex;
                                                DV.SelectionManager.selectedItem = canvasModel.getItemData(delegateRoot.modelIndex);
                                                canvasModel.removeItem(delegateRoot.modelIndex);
                                            }
                                        }

                                        Rectangle {
                                            anchors.fill: parent
                                            color: deleteHover.hovered ? themePalette.midlight : "transparent"
                                            radius: DV.Styles.rad.sm

                                            DV.PhIcon {
                                                anchors.centerIn: parent
                                                name: "trash"
                                                size: 16
                                                color: delegateRoot.isSelected ? themePalette.highlightedText : themePalette.text
                                            }
                                        }
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
                    }
                }

                Label {
                    anchors.centerIn: parent
                    visible: layerRepeater.count === 0
                    text: qsTr("No objects")
                    font.pixelSize: 11
                    color: themePalette.text
                }
            }
        }
    }
}
