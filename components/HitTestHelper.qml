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
            } else if (item.type === "path") {
                // Precise polyline hit test with stroke tolerance
                if (item.points && item.points.length >= 2) {
                    var tolerance = Math.max(1.5, (item.strokeWidth || 1) * 0.6);
                    if (_hitTestPath(item.points, canvasX, canvasY, tolerance, item.closed === true)) {
                        return i;
                    }
                }
            } else if (item.type === "group" || item.type === "layer") {
                if (boundingBoxCallback) {
                    var bounds = boundingBoxCallback(i);
                    if (bounds && bounds.width >= 0 && bounds.height >= 0) {
                        // Expand bounds slightly to account for stroke width
                        var expand = item.strokeWidth ? item.strokeWidth * 0.5 : 1;
                        if (canvasX >= bounds.x - expand && canvasX <= bounds.x + bounds.width + expand && canvasY >= bounds.y - expand && canvasY <= bounds.y + bounds.height + expand) {
                            return i;
                        }
                    }
                }
            }
        }
        return -1;
    }

    // Distance from point to segment helper
    function _pointToSegmentDistance(px, py, x1, y1, x2, y2) {
        var dx = x2 - x1;
        var dy = y2 - y1;
        if (dx === 0 && dy === 0) {
            dx = px - x1;
            dy = py - y1;
            return Math.sqrt(dx * dx + dy * dy);
        }
        var t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy);
        t = Math.max(0, Math.min(1, t));
        var projX = x1 + t * dx;
        var projY = y1 + t * dy;
        var ddx = px - projX;
        var ddy = py - projY;
        return Math.sqrt(ddx * ddx + ddy * ddy);
    }

    function _hitTestPath(points, px, py, tolerance, closed) {
        var count = points.length;
        for (var j = 0; j < count - 1; j++) {
            var p1 = points[j];
            var p2 = points[j + 1];
            if (_pointToSegmentDistance(px, py, p1.x, p1.y, p2.x, p2.y) <= tolerance) {
                return true;
            }
        }
        if (closed && count > 2) {
            var pFirst = points[0];
            var pLast = points[count - 1];
            if (_pointToSegmentDistance(px, py, pLast.x, pLast.y, pFirst.x, pFirst.y) <= tolerance) {
                return true;
            }
        }
        return false;
    }

    function applySelection(selectionManager, canvasModel, index) {
        if (!selectionManager || !canvasModel)
            return;

        selectionManager.selectedItemIndex = index;
        selectionManager.selectedItem = (index >= 0) ? canvasModel.getItemData(index) : null;
    }
}
