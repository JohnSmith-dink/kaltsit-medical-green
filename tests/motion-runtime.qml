// Real Qt Multimedia / KDE DBus module, private controllable service.
import QtQuick
import QtQuick.Window
import QtMultimedia
import org.kde.plasma.workspace.dbus as DBus

Window {
    id: root
    width: 640; height: 360; visible: true
    property var args: [] // MOTION_TEST_ARGUMENTS
    property int phase: 0
    property real phaseAt: Date.now()
    property bool entered: false
    property bool restoredPaused: false
    property var results: ({})
    property var steps: []
    property int savedPosition: 0
    function fail(message) { console.error("MOTION_TEST_FAIL", phase, message); Qt.exit(1); }
    function control(member, value) {
        const message = {service: "org.kaltsit.MotionTest", path: "/Test", iface: "org.kaltsit.MotionTest", member: member};
        if (value !== undefined) message.arguments = [new DBus.bool(value)];
        DBus.SessionBus.asyncCall(message, () => {}, e => root.fail(member + ": " + e.error.message));
    }
    function stopped(s) { return s.playbackState !== MediaPlayer.PlayingState && !s.wantsPlayback; }
    function playing(s) { return s.showingVideo && s.playbackState === MediaPlayer.PlayingState && s.wantsPlayback; }
    function step(name, setup, ready, delay) { return {name:name, setup:setup, ready:ready, delay:delay || 0}; }
    function finish() {
        timer.stop();
        root.contentItem.grabToImage(result => {
            if (!result.saveToFile(root.args[3])) { root.fail("capture failed"); return; }
            console.log("MOTION_TEST_PASS", JSON.stringify(root.results));
            Qt.quit();
        });
    }
    Loader {
        id: video
        anchors.fill: parent
        source: root.args[0]
        onLoaded: {
            item.paused = root.restoredPaused;
            item.videoSource = root.args[1];
            item.posterSource = root.args[2];
            item.retryIntervalMs = 700;
        }
        onStatusChanged: if (status === Loader.Error) root.fail("component did not load")
    }
    Component.onCompleted: {
        steps = [
            step("unknown_services_do_not_guess", s => {}, s => !s.batteryKnown && !s.lockKnown && playing(s), 500),
            step("initial_queries", s => control("Connect"), s => s.batteryKnown && s.lockKnown && !s.onBattery && !s.sessionLocked),
            step("manual_pause_preserves_frame", s => { root.savedPosition=s.position; s.paused=true; }, s => stopped(s) && s.showingVideo && Math.abs(s.position-root.savedPosition)<150, 700),
            step("resume_advances", s => s.paused=false, s => playing(s) && s.position>root.savedPosition+250),
            step("hidden_surface_pauses", s => {root.savedPosition=s.position; s.visible=false;}, s => stopped(s) && Math.abs(s.position-root.savedPosition)<150, 700),
            step("loop_keeps_visible_frame", s => {s.visible=true; s.position=s.duration-350;}, s => playing(s) && s.position<1500, 500),
            step("battery_pauses", s => control("Battery",true), s => s.onBattery && stopped(s)),
            step("battery_resumes", s => control("Battery",false), s => !s.onBattery && playing(s)),
            step("battery_manual_priority", s => {s.paused=true; control("Battery",true);}, s => s.onBattery && stopped(s)),
            step("battery_release_keeps_manual", s => control("Battery",false), s => !s.onBattery && s.paused && stopped(s), 500),
            step("battery_ignore", s => {s.paused=false; s.batteryPolicy="ignore"; control("Battery",true);}, s => s.onBattery && playing(s)),
            step("battery_policy_pause", s => s.batteryPolicy="pause", s => stopped(s)),
            step("power_loss_keeps_last", s => control("DropPower"), s => !s.powerServiceAvailable && s.onBattery && stopped(s), 500),
            step("power_reconnect_refreshes", s => control("ReconnectPower"), s => s.powerServiceAvailable && !s.onBattery && playing(s)),
            step("lock_pauses", s => control("Locked",true), s => s.sessionLocked && stopped(s)),
            step("lock_resumes", s => control("Locked",false), s => !s.sessionLocked && playing(s)),
            step("lock_manual_priority", s => {s.paused=true; control("Locked",true);}, s => s.sessionLocked && stopped(s)),
            step("lock_release_keeps_manual", s => control("Locked",false), s => !s.sessionLocked && s.paused && stopped(s), 500),
            step("conditions_combine", s => {s.paused=false; control("Locked",true); control("Battery",true);}, s => s.onBattery && s.sessionLocked && stopped(s)),
            step("one_condition_remains", s => control("Battery",false), s => !s.onBattery && s.sessionLocked && stopped(s)),
            step("lock_loss_keeps_last", s => control("DropLock"), s => !s.lockServiceAvailable && s.sessionLocked && stopped(s), 500),
            step("lock_reconnect_refreshes", s => control("ReconnectLock"), s => s.lockServiceAvailable && !s.sessionLocked && playing(s)),
            step("invalid_video_falls_back", s => s.videoSource=root.args[5], s => s.failed && !s.showingVideo),
            step("manual_pause_blocks_retry", s => s.paused=true, s => s.retryAttempts===0 && s.failed && !s.retrying, 1100),
            step("hidden_blocks_retry", s => {s.visible=false; s.paused=false;}, s => s.retryAttempts===0 && s.failed, 1100),
            step("lock_blocks_retry", s => control("Locked",true), s => s.sessionLocked),
            step("visible_locked_no_retry", s => s.visible=true, s => s.retryAttempts===0 && s.failed, 1100),
            step("battery_blocks_retry", s => {control("Battery",true); control("Locked",false);}, s => s.onBattery && !s.sessionLocked && s.retryAttempts===0, 1100),
            step("resume_waits_full_interval", s => control("Battery",false), s => !s.onBattery && s.retryAttempts===0 && s.failed, 250),
            step("three_retries_exhausted", s => {}, s => s.retryAttempts===3 && s.failed && !s.retrying),
            step("retry_limit_stays_bounded", s => {}, s => s.retryAttempts===3 && s.failed && !s.retrying, 1100),
            step("source_change_resets_budget", s => s.videoSource=root.args[1], s => playing(s) && s.retryAttempts===0 && !s.failed),
            step("same_source_retry_started", s => s.videoSource=root.args[6], s => s.retryAttempts===1 && s.failed && !s.retrying),
            step("same_source_retry_recovers", s => control("Repair"), s => playing(s) && !s.failed && s.retryAttempts===2 && s.videoSource.toString()===root.args[6]),
            step("recreate_with_persisted_pause", s => {root.restoredPaused=true; video.active=false; video.active=true;}, s => s.paused && stopped(s), 800)
        ];
    }
    Timer {
        id: timer
        interval: 50; repeat: true; running: true
        onTriggered: {
            const s=video.item;
            if (!s) return;
            if (s.failed && s.showingVideo) {root.fail("failed/retrying frame flashed"); return;}
            if (root.args[4] === "software") {
                if (Date.now()-root.phaseAt<1000 || s.posterLoading) return;
                if (s.showingVideo || s.wantsPlayback || s.playbackState===MediaPlayer.PlayingState) {root.fail("software fallback decoded continuously"); return;}
                root.results.software_backend_static_fallback=true;
                root.finish(); return;
            }
            if (root.phase>=root.steps.length) {root.finish(); return;}
            const current=root.steps[root.phase];
            if (!root.entered) {
                root.entered=true; root.phaseAt=Date.now(); current.setup(s); return;
            }
            if (Date.now()-root.phaseAt>12000) {root.fail(current.name+" timed out"); return;}
            if (Date.now()-root.phaseAt>=current.delay && current.ready(s)) {
                root.results[current.name]=true;
                console.log("MOTION_STEP", current.name);
                root.phase++; root.entered=false;
            }
        }
    }
}
