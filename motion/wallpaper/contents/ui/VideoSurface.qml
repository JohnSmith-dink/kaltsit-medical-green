// SPDX-FileCopyrightText: 2026 Xinyan
// SPDX-License-Identifier: MIT
import QtQuick
import QtMultimedia

Item {
    id: root
    property url videoSource
    property url posterSource
    property bool paused: false
    property int fillMode: VideoOutput.PreserveAspectCrop
    property bool failed: false
    property bool hasFrame: false
    readonly property bool videoRenderingSupported: GraphicsInfo.api !== GraphicsInfo.Software && GraphicsInfo.api !== GraphicsInfo.Unknown
    readonly property bool wantsPlayback: videoRenderingSupported && visible && !paused && !failed && videoSource.toString().length > 0
    readonly property bool showingVideo: videoRenderingSupported && hasFrame && !failed
    readonly property int playbackState: player.playbackState
    readonly property int duration: player.duration
    readonly property string errorString: player.errorString
    readonly property bool posterLoading: poster.status === Image.Loading
    property alias position: player.position

    function synchronize() {
        if (wantsPlayback) {
            player.play();
        } else if (player.playbackState === MediaPlayer.PlayingState) {
            player.pause();
        }
    }
    onWantsPlaybackChanged: Qt.callLater(synchronize)
    onVideoSourceChanged: {
        failed = false;
        hasFrame = false;
        if (output) output.clearOutput();
        Qt.callLater(synchronize);
    }
    Component.onCompleted: Qt.callLater(synchronize)
    Component.onDestruction: player.stop()

    Rectangle { anchors.fill: parent; color: "#17291F" }
    Image {
        id: poster
        anchors.fill: parent
        source: root.posterSource
        fillMode: root.fillMode
        asynchronous: true
        autoTransform: true
        visible: !root.showingVideo
    }
    VideoOutput {
        id: output
        anchors.fill: parent
        fillMode: root.fillMode
        endOfStreamPolicy: VideoOutput.KeepLastFrame
        visible: root.showingVideo
    }
    Connections {
        target: output.videoSink
        function onVideoFrameChanged() {
            if (output.videoSink.videoSize.width > 0 && output.videoSink.videoSize.height > 0) {
                root.hasFrame = true;
            }
        }
        function onVideoSizeChanged() {
            if (output.videoSink.videoSize.width > 0 && output.videoSink.videoSize.height > 0) {
                root.hasFrame = true;
            }
        }
    }
    MediaPlayer {
        id: player
        source: root.videoSource
        videoOutput: output
        loops: MediaPlayer.Infinite
        activeAudioTrack: -1
        activeSubtitleTrack: -1
        // No AudioOutput is constructed: wallpaper playback is always silent.
        onMediaStatusChanged: {
            if (mediaStatus === MediaPlayer.LoadedMedia || mediaStatus === MediaPlayer.BufferedMedia) {
                Qt.callLater(root.synchronize);
            }
        }
        onErrorOccurred: (error, message) => {
            root.failed = true;
            console.warn("Medical Green video unavailable; keeping still image:", message);
        }
    }
}
