import QtQuick
import org.kde.kirigami as Kirigami

Item {
    id: iconRoot
    anchors.fill: parent

    property string customIcon: ""
    property bool activeIcon: false

    Kirigami.Icon {
        anchors.centerIn: parent
        width: Math.min(parent.height, parent.width)
        height: width

        source: (iconRoot.customIcon && iconRoot.customIcon !== "icon")
        ? iconRoot.customIcon
        : Qt.resolvedUrl("../icons/icon.svg")

        active: iconRoot.activeIcon
        isMask: true
    }
}
