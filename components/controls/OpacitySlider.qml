import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

Slider {
    id: root

    // Opacity value from 0.0 to 1.0 (bidirectional binding)
    property real opacityValue: 1.0

    // Fires during drag for live preview
    signal valueUpdated(real newOpacity)
    // Fires on release for final commit (useful for undo history)
    signal valueCommitted(real newOpacity)

    readonly property SystemPalette themePalette: Lucent.Themed.palette

    Layout.preferredWidth: 80
    Layout.preferredHeight: Lucent.Styles.height.sm
    implicitHeight: Lucent.Styles.height.sm
    Layout.alignment: Qt.AlignVCenter

    from: 0
    to: 100
    stepSize: 1
    value: Math.round(root.opacityValue * 100)

    onPressedChanged: {
        if (!pressed) {
            root.valueCommitted(value / 100.0);
        }
    }

    onValueChanged: {
        root.opacityValue = value / 100.0;
        root.valueUpdated(value / 100.0);
    }

    Component.onCompleted: {
        value = Math.round(root.opacityValue * 100);
    }

    Binding {
        target: root
        property: "value"
        value: Math.round(root.opacityValue * 100)
        when: !root.pressed
    }

    background: Rectangle {
        x: root.leftPadding
        y: root.topPadding + root.availableHeight / 2 - height / 2
        width: root.availableWidth
        height: Lucent.Styles.height.xxxsm
        implicitWidth: 80
        implicitHeight: Lucent.Styles.height.xxxsm
        radius: Lucent.Styles.rad.sm
        color: root.themePalette.base

        Rectangle {
            width: root.visualPosition * parent.width
            height: parent.height
            color: root.themePalette.highlight
            radius: Lucent.Styles.rad.sm
        }
    }

    handle: Rectangle {
        x: root.leftPadding + root.visualPosition * (root.availableWidth - width)
        y: root.topPadding + root.availableHeight / 2 - height / 2
        width: Lucent.Styles.height.xs
        height: Lucent.Styles.height.xs
        implicitWidth: Lucent.Styles.height.xs
        implicitHeight: Lucent.Styles.height.xs
        radius: Lucent.Styles.rad.lg
        color: root.pressed ? root.themePalette.highlight : root.themePalette.button
        border.color: root.themePalette.mid
        border.width: 1
    }
}
