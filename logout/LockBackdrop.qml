// SPDX-License-Identifier: MIT
import QtQuick

Rectangle {
    color: "#17291F"
    Image {
        anchors.fill: parent
        source: "LockWallpaper.jpg"
        fillMode: Image.PreserveAspectCrop
        asynchronous: false
        autoTransform: true
        onStatusChanged: if (status === Image.Error) console.warn("Medical Green confirmation wallpaper failed to load")
    }
}
