import QtQuick

Rectangle {
    id: about_widget

    width: 320; height: 180

    Text {
        id: app_name
        text: "Count Anywhere"

        y: 0

        anchors.horizontalCenter: about_widget.horizontalCenter

        font.pointSize: 24; font.bold: true
    }
}