// SPDX-FileCopyrightText: 2026 Xinyan
// SPDX-License-Identifier: MIT
import QtQuick
import QtMultimedia
import org.kde.plasma.workspace.dbus as DBus

Item {
    id: root
    property url videoSource
    property url posterSource
    property bool paused: false
    property string batteryPolicy: "pause"
    property bool onBattery: false
    property bool sessionLocked: false
    property bool batteryKnown: false
    property bool lockKnown: false
    readonly property bool powerServiceAvailable: powerService.registered
    readonly property bool lockServiceAvailable: lockService.registered
    readonly property bool automaticallyPaused: sessionLocked || (batteryPolicy !== "ignore" && onBattery)
    property int powerRevision: 0
    property int lockRevision: 0
    property int fillMode: VideoOutput.PreserveAspectCrop
    property bool failed: false
    property bool hasFrame: false
    // Internal timing seam for native tests, not a persisted setting or CLI option.
    property int retryIntervalMs: 60000
    property int retryAttempts: 0
    property bool retrying: false
    property url mediaSource
    readonly property bool videoRenderingSupported: GraphicsInfo.api !== GraphicsInfo.Software && GraphicsInfo.api !== GraphicsInfo.Unknown
    readonly property bool playbackAllowed: videoRenderingSupported && visible && !paused && !automaticallyPaused && videoSource.toString().length > 0
    readonly property bool wantsPlayback: playbackAllowed && (!failed || retrying)
    readonly property bool showingVideo: videoRenderingSupported && hasFrame && !failed
    readonly property int playbackState: player.playbackState
    readonly property int duration: player.duration
    readonly property string errorString: player.errorString
    readonly property bool posterLoading: poster.status === Image.Loading
    property alias position: player.position

    function refreshPower() {
        const revision = ++powerRevision;
        if (!powerService.registered) {
            console.warn("Medical Green: battery signal unavailable; retaining last known state");
            return;
        }
        DBus.SessionBus.asyncCall({ service: powerService.watchedService,
            path: "/org/freedesktop/PowerManagement", iface: powerService.watchedService,
            member: "GetPowerSaveStatus" }, reply => {
                if (revision !== powerRevision || !powerService.registered) return;
                if (typeof reply.value === "boolean") {
                    onBattery = reply.value;
                    batteryKnown = true;
                }
            }, () => console.warn("Medical Green: battery query unavailable; retaining last known state"));
    }
    function refreshLock() {
        const revision = ++lockRevision;
        if (!lockService.registered) {
            console.warn("Medical Green: lock signal unavailable; retaining last known state");
            return;
        }
        DBus.SessionBus.asyncCall({ service: lockService.watchedService,
            path: "/ScreenSaver", iface: lockService.watchedService, member: "GetActive" }, reply => {
                if (revision !== lockRevision || !lockService.registered) return;
                if (typeof reply.value === "boolean") {
                    sessionLocked = reply.value;
                    lockKnown = true;
                }
            }, () => console.warn("Medical Green: lock query unavailable; retaining last known state"));
    }
    DBus.DBusServiceWatcher {
        id: powerService
        watchedService: "org.freedesktop.PowerManagement"
        onRegisteredChanged: root.refreshPower()
    }
    DBus.DBusServiceWatcher {
        id: lockService
        watchedService: "org.freedesktop.ScreenSaver"
        onRegisteredChanged: root.refreshLock()
    }
    DBus.SignalWatcher {
        service: powerService.watchedService
        path: "/org/freedesktop/PowerManagement"
        iface: service
        function dbusPowerSaveStatusChanged(value) {
            if (!powerService.registered || typeof value !== "boolean") return;
            ++root.powerRevision;
            root.onBattery = value;
            root.batteryKnown = true;
        }
    }
    DBus.SignalWatcher {
        service: lockService.watchedService
        path: "/ScreenSaver"
        iface: service
        function dbusActiveChanged(value) {
            if (!lockService.registered || typeof value !== "boolean") return;
            ++root.lockRevision;
            root.sessionLocked = value;
            root.lockKnown = true;
        }
    }
    Timer {
        interval: root.retryIntervalMs
        // Stopping the timer on pause discards elapsed time. Resume waits a full interval.
        running: root.failed && root.playbackAllowed && !root.retrying && root.retryAttempts < 3
        repeat: false
        onTriggered: {
            ++root.retryAttempts;
            root.retrying = true;
            root.hasFrame = false;
            root.mediaSource = "";
            output.clearOutput();
            const source = root.videoSource.toString();
            const attempt = root.retryAttempts;
            Qt.callLater(() => {
                if (source !== root.videoSource.toString() || attempt !== root.retryAttempts) return;
                if (!root.playbackAllowed) { root.retrying = false; return; }
                root.mediaSource = source;
                root.synchronize();
            });
        }
    }

    function synchronize() {
        if (wantsPlayback) {
            player.play();
        } else if (player.playbackState === MediaPlayer.PlayingState) {
            player.pause();
        }
    }
    onWantsPlaybackChanged: Qt.callLater(synchronize)
    onVideoSourceChanged: {
        retryAttempts = 0;
        retrying = false;
        failed = false;
        hasFrame = false;
        mediaSource = videoSource;
        if (output) output.clearOutput();
        Qt.callLater(synchronize);
    }
    Component.onCompleted: {
        refreshPower();
        refreshLock();
        Qt.callLater(synchronize);
    }
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
            if (player.playbackState === MediaPlayer.PlayingState && root.mediaSource.toString() === root.videoSource.toString()
                && output.videoSink.videoSize.width > 0 && output.videoSink.videoSize.height > 0) {
                root.hasFrame = true;
                root.failed = false;
                root.retrying = false;
            }
        }
    }
    MediaPlayer {
        id: player
        source: root.mediaSource
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
            if (!root.mediaSource.toString()) return;
            root.failed = true;
            root.retrying = false;
            console.warn("Medical Green video unavailable; keeping still image:", message);
            if (root.retryAttempts >= 3) console.warn("Medical Green: retry limit reached (3); keeping still image until source changes");
        }
    }
}
