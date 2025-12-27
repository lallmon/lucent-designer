import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as DV

Item {
    id: root

    property int draggedIndex: -1
    property string draggedItemType: ""      // Type of item being dragged
    property string dropTargetLayerId: ""    // Layer ID we're hovering over for drop
    property var draggedItemParentId: null   // Parent ID of the item being dragged
    property var dropTargetParentId: null    // Parent ID of the item we're hovering over

    ColumnLayout {
        anchors.fill: parent
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 4

            Label {
                text: qsTr("Layers")
                font.pixelSize: 12
                font.bold: true
                color: "white"
                Layout.fillWidth: true
            }

            Rectangle {
                id: addLayerButton
                Layout.preferredWidth: 24
                Layout.preferredHeight: 24
                radius: DV.Theme.sizes.radiusSm
                color: addLayerHover.hovered ? DV.Theme.colors.panelHover : "transparent"

                DV.PhIcon {
                    anchors.centerIn: parent
                    name: "stack-plus"
                    size: 18
                    color: DV.Theme.colors.textSubtle
                }

                HoverHandler {
                    id: addLayerHover
                    cursorShape: Qt.PointingHandCursor
                }

                TapHandler {
                    onTapped: canvasModel.addLayer()
                }
            }
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
                        required property var itemId      // Layer's unique ID (null for shapes)
                        required property var parentId    // Parent layer ID (null for top-level items)

                        // Use layerRepeater.count (reactive property) not canvasModel.rowCount() (method)
                        // Methods don't trigger binding updates; properties do
                        property int displayIndex: layerRepeater.count - 1 - index
                        // Use model index for selection comparison (not displayIndex)
                        property bool isSelected: index === DV.SelectionManager.selectedItemIndex
                        property bool isBeingDragged: root.draggedIndex === index
                        property real dragOffsetY: 0
                        property bool hasParent: parentId !== null && parentId !== undefined && parentId !== ""
                        property bool isLayer: itemType === "layer"

                        transform: Translate { y: delegateRoot.dragOffsetY }
                        z: isBeingDragged ? 100 : 0

                        // Track if this layer is a valid drop target
                        property bool isDropTarget: delegateRoot.isLayer && 
                                                    root.draggedIndex >= 0 && 
                                                    root.draggedItemType !== "layer" &&
                                                    root.dropTargetLayerId === delegateRoot.itemId

                        Rectangle {
                            id: background
                            anchors.fill: parent
                            radius: DV.Theme.sizes.radiusSm
                            color: delegateRoot.isDropTarget ? DV.Theme.colors.accentHover
                                 : delegateRoot.isSelected ? DV.Theme.colors.accent 
                                 : nameHoverHandler.hovered ? DV.Theme.colors.panelHover 
                                 : "transparent"
                            border.width: delegateRoot.isDropTarget ? 2 : 0
                            border.color: DV.Theme.colors.accent

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: delegateRoot.hasParent ? 20 : 4  // Indent children
                                anchors.rightMargin: 8
                                spacing: 4

                                Item {
                                    id: dragHandle
                                    Layout.preferredWidth: 28
                                    Layout.fillHeight: true

                                    // Icon indicating item type: stack for layers, specific tool icon for shapes
                                    DV.PhIcon {
                                        anchors.centerIn: parent
                                        name: {
                                            if (delegateRoot.itemType === "layer") return "stack"
                                            if (delegateRoot.itemType === "rectangle") return "rectangle"
                                            if (delegateRoot.itemType === "ellipse") return "circle"
                                            return "shapes"
                                        }
                                        size: 18
                                        color: delegateRoot.isSelected ? "white" : DV.Theme.colors.textSubtle
                                    }

                                    DragHandler {
                                        id: dragHandler
                                        target: null
                                        yAxis.enabled: true
                                        xAxis.enabled: false

                                        onActiveChanged: {
                                            try {
                                                if (active) {
                                                    // Use model index (not displayIndex) for model operations
                                                    root.draggedIndex = delegateRoot.index
                                                    root.draggedItemType = delegateRoot.itemType
                                                    root.draggedItemParentId = delegateRoot.parentId
                                                } else {
                                                    if (root.draggedIndex >= 0) {
                                                        // Calculate target model index for potential reordering
                                                        let totalItemHeight = layerContainer.itemHeight + layerContainer.itemSpacing
                                                        let indexDelta = Math.round(delegateRoot.dragOffsetY / totalItemHeight)
                                                        let targetModelIndex = delegateRoot.index + indexDelta
                                                        let rowCount = layerRepeater.count
                                                        targetModelIndex = Math.max(0, Math.min(rowCount - 1, targetModelIndex))
                                                        
                                                        // Determine the action based on drag context
                                                        if (root.dropTargetLayerId !== "" && root.draggedItemType !== "layer") {
                                                            // Check if dropping onto the SAME parent layer (sibling reorder, not reparent)
                                                            if (root.dropTargetLayerId === root.draggedItemParentId) {
                                                                // Same parent - just reorder within the layer
                                                                if (targetModelIndex !== root.draggedIndex) {
                                                                    canvasModel.moveItem(root.draggedIndex, targetModelIndex)
                                                                }
                                                            } else {
                                                                // Different layer - reparent to that layer
                                                                canvasModel.reparentItem(root.draggedIndex, root.dropTargetLayerId)
                                                            }
                                                        } else if (root.draggedItemParentId && root.dropTargetParentId === root.draggedItemParentId) {
                                                            // Dropping onto a sibling (same parent) - just reorder, keep parent
                                                            if (targetModelIndex !== root.draggedIndex) {
                                                                canvasModel.moveItem(root.draggedIndex, targetModelIndex)
                                                            }
                                                        } else if (root.draggedItemParentId && !root.dropTargetParentId && root.dropTargetLayerId === "") {
                                                            // Dropping a child onto a top-level item - unparent
                                                            canvasModel.reparentItem(root.draggedIndex, "")
                                                        } else {
                                                            // Normal z-order reordering for top-level items
                                                            if (targetModelIndex !== root.draggedIndex) {
                                                                canvasModel.moveItem(root.draggedIndex, targetModelIndex)
                                                            }
                                                        }
                                                    }
                                                    delegateRoot.dragOffsetY = 0
                                                    root.draggedIndex = -1
                                                    root.draggedItemType = ""
                                                    root.dropTargetLayerId = ""
                                                    root.draggedItemParentId = null
                                                    root.dropTargetParentId = null
                                                }
                                            } catch (e) {
                                                console.warn("LayerPanel drag error:", e)
                                                // Reset state - guard against delegate destruction during model reset
                                                if (typeof delegateRoot !== 'undefined' && delegateRoot) {
                                                    delegateRoot.dragOffsetY = 0
                                                }
                                                if (typeof root !== 'undefined' && root) {
                                                    root.draggedIndex = -1
                                                    root.draggedItemType = ""
                                                    root.dropTargetLayerId = ""
                                                    root.draggedItemParentId = null
                                                    root.dropTargetParentId = null
                                                }
                                            }
                                        }

                                        onTranslationChanged: {
                                            if (active) {
                                                delegateRoot.dragOffsetY = translation.y
                                                // Calculate which item we're hovering over
                                                updateDropTarget()
                                            }
                                        }

                                        function updateDropTarget() {
                                            // Find which row we're over based on drag offset
                                            let totalItemHeight = layerContainer.itemHeight + layerContainer.itemSpacing
                                            let indexDelta = Math.round(delegateRoot.dragOffsetY / totalItemHeight)
                                            let targetListIndex = delegateRoot.index + indexDelta
                                            let rowCount = layerRepeater.count
                                            targetListIndex = Math.max(0, Math.min(rowCount - 1, targetListIndex))

                                            // Get the item at target position
                                            let targetItem = layerRepeater.itemAt(targetListIndex)
                                            if (targetItem && targetItem.isLayer && root.draggedItemType !== "layer") {
                                                root.dropTargetLayerId = targetItem.itemId
                                                root.dropTargetParentId = null
                                            } else {
                                                root.dropTargetLayerId = ""
                                                root.dropTargetParentId = targetItem ? targetItem.parentId : null
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
                                        originalName = delegateRoot.name
                                        draftName = delegateRoot.name
                                        isEditing = true
                                        nameField.text = draftName
                                        nameField.selectAll()
                                        nameField.forceActiveFocus()
                                    }

                                    function commitEditing() {
                                        if (!isEditing)
                                            return
                                        draftName = nameField.text
                                        isEditing = false
                                        if (draftName !== delegateRoot.name) {
                                            canvasModel.renameItem(delegateRoot.index, draftName)
                                        }
                                    }

                                    function cancelEditing() {
                                        if (!isEditing)
                                            return
                                        isEditing = false
                                        draftName = originalName
                                        nameField.text = originalName
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
                                        cursorShape: Qt.IBeamCursor
                                        onClicked: {
                                            DV.SelectionManager.selectedItemIndex = delegateRoot.index
                                            DV.SelectionManager.selectedItem = canvasModel.getItemData(delegateRoot.index)
                                        }
                                        onDoubleClicked: {
                                            DV.SelectionManager.selectedItemIndex = delegateRoot.index
                                            DV.SelectionManager.selectedItem = canvasModel.getItemData(delegateRoot.index)
                                            nameEditor.startEditing()
                                        }
                                    }

                                    Label {
                                        id: nameLabel
                                        visible: !nameEditor.isEditing
                                        text: delegateRoot.name
                                        font.pixelSize: 11
                                        color: delegateRoot.isSelected ? "white" : DV.Theme.colors.textSubtle
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                        Layout.minimumWidth: 40
                                    }

                                    TextField {
                                        id: nameField
                                        visible: nameEditor.isEditing
                                        text: nameEditor.draftName
                                        font.pixelSize: 11
                                        color: delegateRoot.isSelected ? "white" : DV.Theme.colors.textSubtle
                                        horizontalAlignment: Text.AlignLeft
                                        verticalAlignment: TextInput.AlignVCenter
                                        padding: 0
                                        Layout.fillWidth: true
                                        background: Rectangle { color: "transparent"; border.color: "transparent" }

                                        Keys.onEscapePressed: nameEditor.cancelEditing()
                                        onAccepted: nameEditor.commitEditing()
                                        onActiveFocusChanged: {
                                            if (!activeFocus && nameEditor.isEditing) {
                                                nameEditor.cancelEditing()
                                            }
                                        }
                                        onTextChanged: nameEditor.draftName = text
                                    }
                                }

                                Item {
                                    id: deleteButton
                                    Layout.preferredWidth: 28
                                    Layout.fillHeight: true

                                    HoverHandler { id: deleteHover }

                                    MouseArea {
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        acceptedButtons: Qt.LeftButton
                                        preventStealing: true
                                        onClicked: {
                                            // Ensure selection reflects the target being deleted
                                            DV.SelectionManager.selectedItemIndex = delegateRoot.index
                                            DV.SelectionManager.selectedItem = canvasModel.getItemData(delegateRoot.index)
                                            canvasModel.removeItem(delegateRoot.index)
                                        }
                                    }

                                    Rectangle {
                                        anchors.fill: parent
                                        color: deleteHover.hovered ? DV.Theme.colors.panelHover : "transparent"
                                        radius: DV.Theme.sizes.radiusSm

                                        DV.PhIcon {
                                            anchors.centerIn: parent
                                            name: "trash"
                                            size: 16
                                            color: delegateRoot.isSelected ? "white" : DV.Theme.colors.textSubtle
                                        }
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
