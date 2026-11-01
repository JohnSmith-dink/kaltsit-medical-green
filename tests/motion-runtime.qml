// Native Qt Multimedia behavior checks in a private/offscreen process.
import QtQuick
import QtQuick.Window
import QtMultimedia

Window {
    id: root
    width: 640; height: 360; visible: true
    property var args: [] // MOTION_TEST_ARGUMENTS
    property int phase: 0
    property real phaseAt: Date.now()
    property int savedPosition: 0
    property var results: ({})
    function fail(message) { console.error("MOTION_TEST_FAIL", phase, message); Qt.exit(1); }
    function next() { phase++; phaseAt = Date.now(); }

    Loader {
        id: video
        anchors.fill: parent
        source: root.args[0]
        onLoaded: {
            item.videoSource = root.args[1];
            item.posterSource = root.args[2];
        }
        onStatusChanged: if (status === Loader.Error) root.fail("component did not load")
    }
    Timer {
        interval: 100; repeat: true; running: true
        onTriggered: {
            if (Date.now() - root.phaseAt > 20000) { root.fail("phase timed out"); return; }
            const surface = video.item;
            if (!surface) return;
            if (root.args[4] === "software" && root.phase === 0 && Date.now() - root.phaseAt > 1000 && !surface.posterLoading) {
                if (surface.showingVideo || surface.wantsPlayback || surface.playbackState === MediaPlayer.PlayingState) {
                    root.fail("software backend must show the still without continuous decoding"); return;
                }
                root.next();
                root.contentItem.grabToImage(function(result) {
                    if (!result.saveToFile(root.args[3])) { root.fail("fallback frame capture failed"); return; }
                    console.log("MOTION_TEST_PASS", JSON.stringify({software_backend_static_fallback: true}));
                    Qt.quit();
                });
                return;
            }
            if (root.phase === 0 && surface.showingVideo && surface.position > 350) {
                root.results.playback_started = true;
                root.savedPosition = surface.position;
                surface.paused = true;
                root.next();
            } else if (root.phase === 1 && Date.now() - root.phaseAt > 700) {
                if (Math.abs(surface.position - root.savedPosition) > 150) { root.fail("manual pause moved"); return; }
                root.results.manual_pause_preserves_frame = surface.showingVideo;
                surface.paused = false;
                root.next();
            } else if (root.phase === 2 && surface.position > root.savedPosition + 250) {
                root.results.resume_advances = true;
                root.savedPosition = surface.position;
                surface.visible = false;
                root.next();
            } else if (root.phase === 3 && Date.now() - root.phaseAt > 700) {
                if (Math.abs(surface.position - root.savedPosition) > 150) { root.fail("hidden surface kept playing"); return; }
                root.results.hidden_surface_pauses = true;
                surface.visible = true;
                surface.position = surface.duration - 350;
                root.next();
            } else if (root.phase === 4 && Date.now() - root.phaseAt > 500 && surface.position < 1500) {
                root.results.loop_keeps_visible_frame = surface.showingVideo;
                surface.videoSource = "file:///tmp/kaltsit-missing-video-for-runtime-test.mp4";
                root.next();
            } else if (root.phase === 5 && surface.failed && !surface.posterLoading) {
                if (surface.showingVideo) { root.fail("error did not fall back to still"); return; }
                root.results.invalid_video_falls_back = true;
                surface.videoSource = root.args[1];
                root.next();
            } else if (root.phase === 6 && surface.showingVideo && surface.position > 350 && !surface.failed) {
                root.results.valid_source_recovers = true;
                for (const key in root.results) if (root.results[key] !== true) { root.fail(key); return; }
                root.next();
                root.contentItem.grabToImage(function(result) {
                    if (!result.saveToFile(root.args[3])) { root.fail("frame capture failed"); return; }
                    console.log("MOTION_TEST_PASS", JSON.stringify(root.results));
                    Qt.quit();
                });
            }
        }
    }
}
