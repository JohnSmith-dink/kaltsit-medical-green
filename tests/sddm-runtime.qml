// Isolated UI behavior with mock SDDM models. This does not authenticate.
import QtQuick
import QtQuick.Window
import QtQuick.Controls.Basic
Window {
    id: root
    width: 1280; height: 800; visible: true
    property var args: [] // SDDM_TEST_ARGUMENTS
    property alias sddm: proxy
    property alias userModel: users
    property alias sessionModel: sessions
    property alias keyboard: layout
    property int phase: 0
    property real started: Date.now()
    property var results: ({})
    QtObject {
        id: proxy
        property bool canPowerOff: false
        property bool canReboot: false
        property bool received: false
        signal loginFailed()
        signal loginSucceeded()
        function login(user, credential, index) {
            // Check synthetic input in memory only. Do not include it in output.
            received = user === "fixture" && credential.length === 14 && index === 0;
            Qt.callLater(() => proxy.loginFailed());
        }
        function powerOff() { root.fail("Unexpected power call"); }
        function reboot() { root.fail("Unexpected reboot call"); }
    }
    ListModel { id: users; property int lastIndex: 0; property string lastUser: "fixture"; ListElement { name: "fixture" } }
    ListModel { id: sessions; property int lastIndex: 0; ListElement { name: "Test session" } }
    QtObject { id: layout; property int currentLayout: 0; property var layouts: [{shortName: "us"}] }
    function find(item, name) {
        if (item.objectName === name) return item;
        for (let child of item.children || []) { let result=find(child,name); if(result) return result; }
        return null;
    }
    function fail(message) { console.error("SDDM_UI_FAIL",message); Qt.exit(1); }
    Loader { id: theme; anchors.fill: parent; source: root.args[0]; onStatusChanged: if(status===Loader.Error) root.fail("load") }
    Timer {
        id: timer
        interval: 100; repeat: true; running: true
        onTriggered: {
            if(Date.now()-root.started>10000) {root.fail("timeout");return;}
            if(!theme.item || Date.now()-root.started<500) return;
            let password=root.find(theme.item,"password");
            let username=root.find(theme.item,"username");
            let button=root.find(theme.item,"loginButton");
            let error=root.find(theme.item,"loginError");
            if(!password || !username || !button || !error) {root.fail("required controls");return;}
            if(root.phase===0) {
                if(username.text!=="fixture" || !password.activeFocus) {root.fail("initial focus");return;}
                if(root.find(theme.item,"shutdownButton").enabled || root.find(theme.item,"rebootButton").enabled) {root.fail("power capability ignored");return;}
                root.results.initial_focus_and_power_capability=true;
                password.text="synthetic-only";
                if(password.echoMode!==TextInput.Password || password.displayText===password.text) {root.fail("password visible");return;}
                root.results.password_masked=true;
                theme.item.login();
                if(password.text.length!==0 || !theme.item.busy) {root.fail("credential retained after submit");return;}
                root.results.submit_clears_field=true;
                root.phase=1;
            } else if(root.phase===1 && !theme.item.busy) {
                if(!proxy.received || password.text.length || !password.activeFocus || !error.visible || !error.text.length) {root.fail("error focus/clearing");return;}
                root.results.error_message_and_refocus=true;
                username.text="";
                root.phase=2;
            } else if(root.phase===2) {
                if(button.enabled) {root.fail("empty username accepted");return;}
                root.results.empty_username_blocks_submit=true;
                timer.stop();
                root.contentItem.grabToImage(result => {
                    if(!result.saveToFile(root.args[1])) {root.fail("capture");return;}
                    console.log("SDDM_UI_PASS",JSON.stringify(root.results));Qt.quit();
                });
            }
        }
    }
}
