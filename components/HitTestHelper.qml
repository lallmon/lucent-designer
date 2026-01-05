import QtQuick

// Stateless helper for canvas hit-testing and selection updates.
QtObject {
    id: helper

    function hitTest(items, canvasX, canvasY, boundingBoxCallback) {
        if (!items)
            return -1;

        // Iterate backwards so topmost items hit first.
        for (var i = items.length - 1; i >= 0; i--) {
            var item = items[i];
            if (!item || !item.type)
                continue;

            // Use modelIndex from item if available, otherwise fall back to array index
            var resultIndex = (item.modelIndex !== undefined) ? item.modelIndex : i;
            // For boundingBoxCallback, always use modelIndex since it expects model indices
            var bbIndex = (item.modelIndex !== undefined) ? item.modelIndex : i;

            if (item.type === "rectangle") {
                if (canvasX >= item.x && canvasX <= item.x + item.width && canvasY >= item.y && canvasY <= item.y + item.height) {
                    return resultIndex;
                }
            } else if (item.type === "ellipse") {
                var dx = (canvasX - item.centerX) / item.radiusX;
                var dy = (canvasY - item.centerY) / item.radiusY;
                if (dx * dx + dy * dy <= 1.0) {
                    return resultIndex;
                }
            } else if (item.type === "path") {
                // Hit test path using bounding box (consistent with text/group/layer)
                if (boundingBoxCallback) {
                    var pathBounds = boundingBoxCallback(bbIndex);
                    if (pathBounds && pathBounds.width >= 0 && pathBounds.height >= 0) {
                        var pathExpand = (item.strokeWidth || 1) * 0.5 + 2;
                        if (canvasX >= pathBounds.x - pathExpand && canvasX <= pathBounds.x + pathBounds.width + pathExpand && canvasY >= pathBounds.y - pathExpand && canvasY <= pathBounds.y + pathBounds.height + pathExpand) {
                            return resultIndex;
                        }
                    }
                }
            } else if (item.type === "text") {
                // Hit test text using bounding box from model
                if (boundingBoxCallback) {
                    var textBounds = boundingBoxCallback(bbIndex);
                    if (textBounds && textBounds.width >= 0 && textBounds.height >= 0) {
                        if (canvasX >= textBounds.x && canvasX <= textBounds.x + textBounds.width && canvasY >= textBounds.y && canvasY <= textBounds.y + textBounds.height) {
                            return resultIndex;
                        }
                    }
                }
            }
            // Groups and layers are not hit-testable on canvas - select via Layer Panel
            // This allows clicking on shapes inside groups to select them directly
        }
        return -1;
    }

    function applySelection(selectionManager, canvasModel, index) {
        if (!selectionManager || !canvasModel)
            return;

        selectionManager.selectedItemIndex = index;
        selectionManager.selectedItem = (index >= 0) ? canvasModel.getItemData(index) : null;
    }
}
