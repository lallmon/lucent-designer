import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Lucent

ToolButton {
    id: root
    property string toolName: ""
    property string iconName: ""
    property string tooltipText: ""
    property string activeTool: ""
    property ButtonGroup buttonGroup: null
    // For select tool: treat empty activeTool as selected.
    property bool isDefaultSelect: false
    property string deselectValue: ""
    readonly property SystemPalette themePalette: Lucent.Themed.palette

    signal toolClicked(string nextTool)

    Layout.preferredWidth: Lucent.Styles.height.xlg
    Layout.preferredHeight: Lucent.Styles.height.xlg
    Layout.alignment: Qt.AlignHCenter
    checkable: true
    checked: isDefaultSelect ? (activeTool === toolName || activeTool === "") : activeTool === toolName
    ButtonGroup.group: buttonGroup

    ToolTip.visible: hovered && tooltipText !== ""
    ToolTip.delay: 1000
    ToolTip.text: tooltipText

    contentItem: Item {
        anchors.fill: parent
        Lucent.PhIcon {
            anchors.centerIn: parent
            name: iconName
            color: themePalette.buttonText
        }
    }

    onClicked: {
        toolClicked(checked ? toolName : deselectValue);
    }
}
