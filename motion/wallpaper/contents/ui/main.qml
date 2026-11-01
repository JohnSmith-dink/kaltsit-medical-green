// SPDX-FileCopyrightText: 2026 Xinyan
// SPDX-License-Identifier: MIT
import QtQuick
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import "Defaults.js" as Defaults

WallpaperItem {
    id: root
    property url defaultPoster: Qt.resolvedUrl("../../../../../wallpapers/KaltsitMedicalGreenMotion/contents/images/poster.jpg")
    loading: surface.posterLoading
    contextualActions: [pauseAction]

    function localVideo(value) {
        const text = String(value || "");
        if (text.startsWith("file://")) return text;
        if (text.startsWith("/")) return "file://" + text.split("/").map(encodeURIComponent).join("/");
        return "";
    }
    VideoSurface {
        id: surface
        anchors.fill: parent
        videoSource: root.localVideo(root.configuration.Video || Defaults.video)
        posterSource: root.configuration.Image || root.defaultPoster
        paused: root.configuration.Paused || !root.visible
        fillMode: root.configuration.FillMode === undefined ? 2 : root.configuration.FillMode
    }
    PlasmaCore.Action {
        id: pauseAction
        text: root.configuration.Paused ? qsTr("继续动态壁纸") : qsTr("暂停动态壁纸")
        icon.name: root.configuration.Paused ? "media-playback-start" : "media-playback-pause"
        onTriggered: {
            root.configuration.Paused = !root.configuration.Paused;
            root.configuration.writeConfig();
        }
    }
}
