// Copyright (C) 2026 The Culture List, Inc.
// SPDX-License-Identifier: GPL-3.0-or-later

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

ToolBar {
    id: root
    implicitHeight: 32
    property real zoomLevel: 1.0
    signal zoomRequested(real value)
    property real cursorX: 0
    property real cursorY: 0

    readonly property bool hasUnitSettings: typeof unitSettings !== "undefined" && unitSettings !== null
    readonly property real displayCursorX: hasUnitSettings ? unitSettings.canvasToDisplay(root.cursorX) : root.cursorX
    readonly property real displayCursorY: hasUnitSettings ? unitSettings.canvasToDisplay(root.cursorY) : root.cursorY
    readonly property string displayUnitLabel: hasUnitSettings ? unitSettings.displayUnit : "px"

    RowLayout {
        anchors.fill: parent
        spacing: 12
        Layout.alignment: Qt.AlignVCenter

        // Left cluster: unit + DPI controls
        RowLayout {
            spacing: 8
            Layout.alignment: Qt.AlignVCenter
            Layout.leftMargin: 10

            RowLayout {
                spacing: 4
                Label {
                    text: qsTr("Unit")
                    color: "white"
                }
                ComboBox {
                    id: unitPicker
                    visible: root.hasUnitSettings
                    implicitHeight: 24
                    background: Rectangle {
                        color: root.palette.window
                        border.color: root.palette.mid
                        radius: 2
                    }
                    model: [
                        {
                            label: qsTr("Inches"),
                            value: "in"
                        },
                        {
                            label: qsTr("Millimeters"),
                            value: "mm"
                        },
                        {
                            label: qsTr("Pixels"),
                            value: "px"
                        }
                    ]
                    textRole: "label"
                    valueRole: "value"
                    implicitWidth: 72
                    currentIndex: Math.max(0, model.findIndex(m => m.value === (root.hasUnitSettings ? unitSettings.displayUnit : "px")))
                    onActivated: index => {
                        if (index >= 0) {
                            unitSettings.displayUnit = model[index].value;
                        }
                    }
                }
            }

            Lucent.VerticalDivider {}

            RowLayout {
                spacing: 4
                Label {
                    text: qsTr("Preview DPI")
                    color: "white"
                }
                ComboBox {
                    id: dpiPicker
                    visible: root.hasUnitSettings
                    implicitHeight: 24
                    background: Rectangle {
                        color: root.palette.window
                        border.color: root.palette.mid
                        radius: 2
                    }
                    model: [300, 96, 72]
                    implicitWidth: 72
                    currentIndex: {
                        var dpiVal = root.hasUnitSettings ? unitSettings.previewDPI : 96;
                        var i = model.indexOf(dpiVal);
                        return i >= 0 ? i : 1; // default to 96 if not matched
                    }
                    onActivated: index => {
                        if (!root.hasUnitSettings || index < 0)
                            return;
                        var val = model[index];
                        unitSettings.previewDPI = val;
                    }
                }
            }
        }

        Item {
            Layout.fillWidth: true
        }

        // Cursor readout (center)
        RowLayout {
            Layout.alignment: Qt.AlignVCenter
            spacing: 6
            Lucent.PhIcon {
                name: "crosshair-simple"
                size: 16
                color: "white"
            }
            Label {
                text: qsTr("X: %1  Y: %2 %3").arg(root.displayCursorX.toFixed(1)).arg(root.displayCursorY.toFixed(1)).arg(displayUnitLabel)
                horizontalAlignment: Text.AlignHCenter
            }
        }

        Item {
            Layout.fillWidth: true
        }

        // Zoom readout
        RowLayout {
            spacing: 6
            Lucent.PhIcon {
                name: "magnifying-glass"
                size: 16
                color: "white"
            }
            ComboBox {
                id: zoomPicker
                implicitHeight: 24
                implicitWidth: 60
                background: Rectangle {
                    color: root.palette.window
                    border.color: root.palette.mid
                    radius: 2
                }
                model: [25, 50, 75, 100, 125, 150, 175, 200]
                textRole: ""
                valueRole: ""
                currentIndex: {
                    // Snap to nearest option
                    var z = Math.round(root.zoomLevel * 100);
                    var best = 0;
                    var bestDiff = 9999;
                    for (var i = 0; i < model.length; i++) {
                        var d = Math.abs(model[i] - z);
                        if (d < bestDiff) {
                            bestDiff = d;
                            best = i;
                        }
                    }
                    return best;
                }
                delegate: ItemDelegate {
                    width: zoomPicker.width
                    text: modelData + "%"
                }
                contentItem: Label {
                    text: Math.round(root.zoomLevel * 100) + "%"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    color: "white"
                    elide: Text.ElideRight
                }
                onActivated: index => {
                    if (index >= 0) {
                        var val = model[index] / 100.0;
                        zoomRequested(val);
                    }
                }
            }
        }
    }
}
