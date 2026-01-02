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

            if (item.type === "rectangle") {
                if (canvasX >= item.x && canvasX <= item.x + item.width && canvasY >= item.y && canvasY <= item.y + item.height) {
                    return i;
                }
            } else if (item.type === "ellipse") {
                var dx = (canvasX - item.centerX) / item.radiusX;
                var dy = (canvasY - item.centerY) / item.radiusY;
                if (dx * dx + dy * dy <= 1.0) {
                    return i;
                }
            } else if (item.type === "group" || item.type === "layer") {
                if (boundingBoxCallback) {
                    var bounds = boundingBoxCallback(i);
                    if (bounds && bounds.width >= 0 && bounds.height >= 0) {
                        if (canvasX >= bounds.x && canvasX <= bounds.x + bounds.width && canvasY >= bounds.y && canvasY <= bounds.y + bounds.height) {
                            return i;
                        }
                    }
                }
            }
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
