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
    // Keep the original image: no tint, brightness overlay, or gradients.
}
