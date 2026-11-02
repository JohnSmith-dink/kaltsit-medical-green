// Real Qt key/mouse events against fake SDDM models. Never authenticates.
import QtQuick
import QtQuick.Window
import QtQuick.Controls.Basic
import QtTest

Item {
    id: root
    property var args: [] // SDDM_TEST_ARGUMENTS
    width: Math.ceil(args[2] / args[4]); height: Math.ceil(args[3] / args[4])
    visible: true
    property alias sddm: proxy
    property alias userModel: users
    property alias sessionModel: sessions
    property alias keyboard: layout
    QtObject {
        id: proxy
        property bool canPowerOff: false
        property bool canReboot: false
        property int loginCalls: 0
        property int powerCalls: 0
        property int rebootCalls: 0
        property int credentialLength: 0
        property string submittedUser: ""
        property int submittedSession: -1
        signal loginFailed()
        signal loginSucceeded()
        function login(user, credential, index) {
            ++loginCalls; submittedUser = user; submittedSession = index;
            // Only a length is retained, never a credential or its hash.
            credentialLength = credential.length;
        }
        function powerOff() { ++powerCalls; }
        function reboot() { ++rebootCalls; }
    }
    ListModel { id: users; property int lastIndex: 0; property string lastUser: "fixture" }
    ListModel { id: sessions; property int lastIndex: 0 }
    QtObject { id: layout; property int currentLayout: 0; property var layouts: [{shortName: "us"}] }
    Item {
        id: stage
        width: root.args[2] / root.args[4]; height: root.args[3] / root.args[4]
        Loader { id: theme; anchors.fill: parent }
    }
    TestCase {
        id: test
        name: "SddmV2"
        when: windowShown
        function item(name) {
            let result = findChild(theme.item, name);
            verify(result !== null, "Missing control " + name);
            return result;
        }
        function focusControl(name) { item(name).forceActiveFocus(); tryCompare(item(name), "activeFocus", true); }
        function reset(names, remembered, sessionNames) {
            theme.source = "";
            tryCompare(theme, "item", null);
            users.clear(); sessions.clear();
            for (let name of names) users.append({name: name});
            for (let name of sessionNames) sessions.append({name: name});
            users.lastUser = remembered;
            users.lastIndex = Math.max(0, names.indexOf(remembered));
            sessions.lastIndex = sessionNames.length ? 0 : -1;
            proxy.canPowerOff = false; proxy.canReboot = false;
            proxy.loginCalls = 0; proxy.powerCalls = 0; proxy.rebootCalls = 0;
            proxy.credentialLength = 0; proxy.submittedUser = ""; proxy.submittedSession = -1;
            theme.source = root.args[0];
            tryCompare(theme, "status", Loader.Ready);
            root.Window.window.requestActivate();
            wait(40);
        }
        function init() { reset(["fixture"], "fixture", ["Test session"]); }
        function cleanup() { theme.source = ""; }
        function openUserMenu() {
            focusControl(theme.item.manualUser ? "manualUserMenu" : "userSelection");
            keyClick(Qt.Key_Return);
            tryCompare(item("userPopup"), "opened", true);
        }
        function capture(name) {
            let finished = false;
            // Popups live in the window Overlay, outside the loaded theme item.
            verify(root.Window.window.contentItem.grabToImage(result => {
                verify(result.saveToFile(root.args[1] + "/" + name + ".png"), "Save native capture");
                finished = true;
            }, Qt.size(stage.width, stage.height)));
            tryVerify(() => finished, 5000);
        }
        function inside(control) {
            let pos = control.mapToItem(stage, 0, 0);
            verify(pos.x >= -0.1 && pos.y >= -0.1, "Top/left in bounds");
            verify(pos.x + control.width <= stage.width + 0.1, "Right in bounds");
            verify(pos.y + control.height <= stage.height + 0.1, "Bottom in bounds");
        }
        function test_initial_single_user_and_capabilities() {
            compare(theme.item.manualUser, false);
            compare(theme.item.loginUser, "fixture");
            verify(!item("username").visible);
            verify(item("calendarDate").text.indexOf("星期") >= 0);
            tryCompare(item("password"), "activeFocus", true);
            verify(!item("shutdownButton").enabled && !item("rebootButton").enabled);
            compare(item("password").echoMode, TextInput.Password);
            item("password").text = "synthetic-only";
            verify(item("password").displayText !== item("password").text);
        }
        function test_tab_and_backtab_cycle() {
            proxy.canPowerOff = true; proxy.canReboot = true;
            focusControl("password");
            for (let name of ["loginButton", "sessionSelection", "shutdownButton", "rebootButton", "userSelection", "password"]) {
                keyClick(Qt.Key_Tab); tryCompare(item(name), "activeFocus", true);
            }
            keyClick(Qt.Key_Backtab, Qt.ShiftModifier);
            tryCompare(item("userSelection"), "activeFocus", true);
            keyClick(Qt.Key_Return); tryCompare(item("userPopup"), "opened", true);
            keyClick(Qt.Key_Escape); tryCompare(item("userPopup"), "opened", false);
            tryCompare(item("userSelection"), "activeFocus", true);
            compare(proxy.loginCalls, 0);
        }
        function test_single_user_other_and_back() {
            openUserMenu();
            keyClick(Qt.Key_Down); keyClick(Qt.Key_Return);
            tryCompare(theme.item, "manualUser", true);
            tryCompare(item("username"), "activeFocus", true);
            compare(proxy.loginCalls, 0);
            verify(!item("loginButton").enabled);
            item("username").text = "manual";
            keyClick(Qt.Key_Return); tryCompare(item("password"), "activeFocus", true);
            item("password").text = "synthetic-only";
            openUserMenu();
            keyClick(Qt.Key_Up); keyClick(Qt.Key_Return);
            tryCompare(theme.item, "manualUser", false);
            compare(theme.item.loginUser, "fixture");
            compare(item("password").text.length, 0);
            tryCompare(item("password"), "activeFocus", true);
        }
        function test_multiple_users_and_escape() {
            reset(["alpha", "fixture", "omega"], "fixture", ["Test session"]);
            item("password").text = "synthetic-only";
            openUserMenu();
            compare(item("userPopup").currentIndex, 1);
            keyClick(Qt.Key_Down); keyClick(Qt.Key_Return);
            tryCompare(theme.item, "selectedUser", "omega");
            compare(item("password").text.length, 0);
            compare(proxy.loginCalls, 0);
            openUserMenu(); keyClick(Qt.Key_Escape);
            tryCompare(item("userSelection"), "activeFocus", true);
            compare(theme.item.selectedUser, "omega");
        }
        function test_empty_users_manual_and_no_empty_submit() {
            reset([], "", ["Test session"]);
            verify(theme.item.manualUser);
            tryCompare(item("username"), "activeFocus", true);
            verify(!item("manualUserMenu").visible && !item("userSelection").visible);
            item("username").text = "   ";
            theme.item.login(); compare(proxy.loginCalls, 0);
            item("username").text = "manual";
            keyClick(Qt.Key_Return); tryCompare(item("password"), "activeFocus", true);
            item("password").text = "synthetic-only";
            keyClick(Qt.Key_Return);
            compare(proxy.loginCalls, 1); compare(proxy.submittedUser, "manual");
        }
        function test_unlisted_remembered_user() {
            reset(["fixture"], "unlisted", ["Test session"]);
            verify(theme.item.manualUser);
            compare(item("username").text, "unlisted");
            tryCompare(item("password"), "activeFocus", true);
        }
        function test_sessions_no_enter_leak() {
            reset(["fixture"], "fixture", ["One", "Two"]);
            focusControl("sessionSelection"); keyClick(Qt.Key_Return);
            tryCompare(item("sessionPopup"), "opened", true);
            keyClick(Qt.Key_Down); keyClick(Qt.Key_Return);
            compare(theme.item.selectedSession, 1);
            compare(proxy.loginCalls, 0);
            tryCompare(item("sessionSelection"), "activeFocus", true);
            keyClick(Qt.Key_Return); keyClick(Qt.Key_Escape);
            compare(proxy.loginCalls, 0);
            focusControl("password"); item("password").text = "synthetic-only"; keyClick(Qt.Key_Return);
            compare(proxy.submittedSession, 1);
        }
        function test_no_session_blocks_login() {
            reset(["fixture"], "fixture", []);
            verify(!item("loginButton").enabled && !item("sessionSelection").enabled);
            verify(item("loginError").visible);
            theme.item.login(); compare(proxy.loginCalls, 0);
        }
        function test_error_clearing_focus_and_stable_layout() {
            let before = item("password").mapToItem(stage, 0, 0).y;
            item("password").text = "synthetic-only";
            keyClick(Qt.Key_Return);
            compare(proxy.loginCalls, 1); compare(proxy.credentialLength, 14);
            compare(item("password").text.length, 0); verify(theme.item.busy);
            proxy.loginFailed();
            tryCompare(item("password"), "activeFocus", true);
            verify(item("loginError").visible && theme.item.errorBorder);
            compare(item("password").mapToItem(stage, 0, 0).y, before);
            wait(650);
            verify(!theme.item.errorBorder && item("password").activeFocus);
        }
        function test_busy_rejects_duplicates_and_switching() {
            item("password").text = "synthetic-only"; keyClick(Qt.Key_Return);
            theme.item.login(); keyClick(Qt.Key_Return);
            compare(proxy.loginCalls, 1);
            for (let name of ["password", "userSelection", "loginButton", "sessionSelection", "shutdownButton", "rebootButton"])
                verify(!item(name).enabled, "Busy disables " + name);
        }
        function test_success_keeps_credential_empty() {
            item("password").text = "synthetic-only"; keyClick(Qt.Key_Return);
            proxy.loginSucceeded();
            compare(item("password").text.length, 0);
        }
        function test_power_calls_only_fake_backend() {
            proxy.canPowerOff = true; proxy.canReboot = true;
            focusControl("shutdownButton"); keyClick(Qt.Key_Return);
            compare(proxy.powerCalls, 1); compare(proxy.rebootCalls, 0);
            focusControl("rebootButton"); keyClick(Qt.Key_Return);
            compare(proxy.powerCalls, 1); compare(proxy.rebootCalls, 1);
            proxy.canPowerOff = false; proxy.canReboot = false;
            mouseClick(item("shutdownButton")); mouseClick(item("rebootButton"));
            compare(proxy.powerCalls, 1); compare(proxy.rebootCalls, 1);
        }
        function test_geometry_and_native_captures() {
            for (let name of ["clock", "loginGroup", "footerLeft", "footerRight"]) inside(item(name));
            verify(item("loginGroup").y + item("loginGroup").height < item("footerLeft").y);
            verify(item("footerLeft").x + item("footerLeft").width < item("footerRight").x);
            capture("single-user");
            item("password").text = "synthetic-only"; keyClick(Qt.Key_Return); proxy.loginFailed();
            capture("error");
            reset(["alpha", "a-very-long-synthetic-username-that-must-fit-without-overlap", "omega"], "alpha", ["One", "Two"]);
            openUserMenu();
            verify(item("userPopup").x >= 0 && item("userPopup").y + item("userPopup").height <= stage.height);
            capture("multi-user-menu");
            keyClick(Qt.Key_Down); keyClick(Qt.Key_Return);
            inside(item("userSelection"));
            capture("long-username");
        }
    }
}
