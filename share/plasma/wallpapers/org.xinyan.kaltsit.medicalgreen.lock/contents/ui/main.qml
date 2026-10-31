// SPDX-FileCopyrightText: 2026 Xinyan
// SPDX-License-Identifier: MIT
import QtQuick
import org.kde.plasma.plasmoid

WallpaperItem {
    id: root
    loading: picture.status === Image.Loading

    Rectangle { anchors.fill: parent; color: "#17291F" }
    Image {
        id: picture
        anchors.fill: parent
        source: root.configuration.Image || ""
        fillMode: root.configuration.FillMode === undefined ? Image.PreserveAspectCrop : root.configuration.FillMode
        asynchronous: true
        autoTransform: true
        onStatusChanged: if (status === Image.Error) console.warn("Medical Green lock-screen image failed to load")
    }
    // A restrained green veil keeps highlights comfortable. The native dark
    // complementary palette dims, rather than brightens, the password view.
    Rectangle { anchors.fill: parent; color: "#4017291F" }
    Rectangle {
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: parent.height * 0.42
        gradient: Gradient {
            GradientStop { position: 0; color: "#B317291F" }
            GradientStop { position: 0.65; color: "#8017291F" }
            GradientStop { position: 1; color: "#0017291F" }
        }
    }
    // Paint only a background behind the native footer. Authentication and
    // all interactive controls are supplied by the unchanged KDE greeter.
    Rectangle {
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: Math.min(parent.height * 0.18, 176)
        gradient: Gradient {
            GradientStop { position: 0; color: "#0017291F" }
            GradientStop { position: 0.45; color: "#9917291F" }
            GradientStop { position: 0.8; color: "#EE17291F" }
            GradientStop { position: 1; color: "#FF17291F" }
        }
    }
}
