// SPDX-FileCopyrightText: 2026 Xinyan
// SPDX-License-Identifier: MIT
import QtQuick
import org.kde.plasma.plasmoid

WallpaperItem {
    id: root
    loading: picture.status !== Image.Ready

    Rectangle { anchors.fill: parent; color: "#F4F7F2" }
    Image {
        id: picture
        anchors.fill: parent
        source: root.configuration.Image || ""
        fillMode: root.configuration.FillMode === undefined ? Image.PreserveAspectCrop : root.configuration.FillMode
        asynchronous: true
        autoTransform: true
        onStatusChanged: if (status === Image.Error) console.warn("Medical Green lock-screen image failed to load")
    }
    // Paint only a background behind the native footer. Authentication and
    // all interactive controls are supplied by the unchanged KDE greeter.
    Rectangle {
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: Math.min(parent.height * 0.18, 176)
        gradient: Gradient {
            GradientStop { position: 0; color: "#00F4F7F2" }
            GradientStop { position: 0.45; color: "#99F4F7F2" }
            GradientStop { position: 0.8; color: "#EEF4F7F2" }
            GradientStop { position: 1; color: "#FFF4F7F2" }
        }
    }
}
