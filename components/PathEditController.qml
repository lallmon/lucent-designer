// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import "." as Lucent

// Handles path point and handle editing operations
QtObject {
    id: controller

    // Path edit mode state (derived from SelectionManager)
    readonly property bool editModeActive: Lucent.SelectionManager.editModeActive

    readonly property var geometry: {
        if (!editModeActive)
            return null;
        var item = Lucent.SelectionManager.selectedItem;
        if (item && item.type === "path" && item.geometry)
            return item.geometry;
        return null;
    }

    readonly property var transform: {
        if (!editModeActive)
            return null;
        var item = Lucent.SelectionManager.selectedItem;
        if (item && item.transform)
            return item.transform;
        return {};
    }

    readonly property var selectedPointIndices: Lucent.SelectionManager.selectedPointIndices

    // Handle point click with optional multi-select
    function handlePointClicked(index, modifiers) {
        var multi = modifiers & Qt.ShiftModifier;
        Lucent.SelectionManager.selectPoint(index, multi);
    }

    // Move a path point (and any selected points if dragged point is selected)
    function handlePointMoved(index, x, y) {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx < 0)
            return;

        var item = Lucent.SelectionManager.selectedItem;
        if (!item || item.type !== "path")
            return;

        var draggedPt = item.geometry.points[index];
        var dx = x - draggedPt.x;
        var dy = y - draggedPt.y;

        var selectedIndices = Lucent.SelectionManager.selectedPointIndices || [];
        var isDraggedSelected = selectedIndices.indexOf(index) >= 0;

        var newPoints = [];
        for (var i = 0; i < item.geometry.points.length; i++) {
            var pt = item.geometry.points[i];
            var shouldMove = (i === index) || (isDraggedSelected && selectedIndices.indexOf(i) >= 0);

            if (shouldMove) {
                var newPt = {
                    x: pt.x + dx,
                    y: pt.y + dy
                };
                if (pt.handleIn)
                    newPt.handleIn = {
                        x: pt.handleIn.x + dx,
                        y: pt.handleIn.y + dy
                    };
                if (pt.handleOut)
                    newPt.handleOut = {
                        x: pt.handleOut.x + dx,
                        y: pt.handleOut.y + dy
                    };
                newPoints.push(newPt);
            } else {
                newPoints.push(pt);
            }
        }

        canvasModel.updateItem(idx, {
            geometry: {
                points: newPoints,
                closed: item.geometry.closed
            }
        });
    }

    // Move a bezier handle with symmetric mirroring (both angle and length)
    function handleHandleMoved(index, handleType, x, y, modifiers) {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx < 0)
            return;

        var item = Lucent.SelectionManager.selectedItem;
        if (!item || item.type !== "path")
            return;

        var breakSymmetry = !!(modifiers & Qt.AltModifier);

        var newPoints = [];
        for (var i = 0; i < item.geometry.points.length; i++) {
            var pt = item.geometry.points[i];
            if (i === index) {
                var newPt = {
                    x: pt.x,
                    y: pt.y
                };

                if (handleType === "handleIn") {
                    newPt.handleIn = {
                        x: x,
                        y: y
                    };
                    if (pt.handleOut) {
                        if (breakSymmetry) {
                            newPt.handleOut = {
                                x: pt.handleOut.x,
                                y: pt.handleOut.y
                            };
                        } else {
                            // Mirror both angle and length symmetrically
                            var dx = x - pt.x;
                            var dy = y - pt.y;
                            newPt.handleOut = {
                                x: pt.x - dx,
                                y: pt.y - dy
                            };
                        }
                    }
                } else if (handleType === "handleOut") {
                    newPt.handleOut = {
                        x: x,
                        y: y
                    };
                    if (pt.handleIn) {
                        if (breakSymmetry) {
                            newPt.handleIn = {
                                x: pt.handleIn.x,
                                y: pt.handleIn.y
                            };
                        } else {
                            // Mirror both angle and length symmetrically
                            var dx = x - pt.x;
                            var dy = y - pt.y;
                            newPt.handleIn = {
                                x: pt.x - dx,
                                y: pt.y - dy
                            };
                        }
                    }
                }

                newPoints.push(newPt);
            } else {
                newPoints.push(pt);
            }
        }

        canvasModel.updateItem(idx, {
            geometry: {
                points: newPoints,
                closed: item.geometry.closed
            }
        });
    }

    // Delete selected points from the path
    function deleteSelectedPoints() {
        var idx = Lucent.SelectionManager.selectedItemIndex;
        if (idx < 0)
            return;

        var item = Lucent.SelectionManager.selectedItem;
        if (!item || item.type !== "path")
            return;

        var selectedIndices = Lucent.SelectionManager.selectedPointIndices;
        if (!selectedIndices || selectedIndices.length === 0)
            return;

        var newPoints = [];
        for (var i = 0; i < item.geometry.points.length; i++) {
            if (selectedIndices.indexOf(i) < 0) {
                newPoints.push(item.geometry.points[i]);
            }
        }

        if (newPoints.length < 2) {
            // Path too short, remove entire item
            canvasModel.removeItem(idx);
            Lucent.SelectionManager.exitEditMode();
        } else {
            canvasModel.updateItem(idx, {
                geometry: {
                    points: newPoints,
                    closed: item.geometry.closed && newPoints.length >= 3
                }
            });
            Lucent.SelectionManager.clearPointSelection();
        }
    }
}
