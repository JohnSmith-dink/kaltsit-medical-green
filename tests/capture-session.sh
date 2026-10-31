#!/usr/bin/env bash
# Real KDE renders from the private validation session, never concept mockups.
set -euo pipefail
: "${KALTSIT_TEST_ROOT:?}"
test "$HOME" = "$KALTSIT_TEST_ROOT/home"
mkdir -p "$KALTSIT_TEST_ROOT/screenshots" "$HOME/Medical Green"/{Documents,Downloads,Pictures,Music,Videos}
for category in Documents Downloads Pictures Music Videos; do
  printf '[Desktop Entry]\nIcon=folder-%s\n' "${category,,}" >"$HOME/Medical Green/$category/.directory"
done
capture() {
  spectacle --background --nonotify --fullscreen --output "$KALTSIT_TEST_ROOT/screenshots/$1.png" >"$KALTSIT_TEST_ROOT/capture-$1.log" 2>&1
}
sleep 5
qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.activateLauncherMenu
sleep 2
capture launcher
qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.activateLauncherMenu
sleep 2
capture desktop
busctl --user call org.freedesktop.Notifications /org/freedesktop/Notifications org.freedesktop.Notifications Notify \
  'susssasa{sv}i' 'Medical Green' 0 'dialog-information' '凯尔希 · 医疗白绿' '正文、边框与青绿强调色 / Notification preview' 0 0 5000
sleep 1
capture notification
sleep 5
dolphin --new-window --select "$HOME/Medical Green/Documents" >"$KALTSIT_TEST_ROOT/dolphin.log" 2>&1 &
dolphin_pid=$!
sleep 3
capture dolphin
kill "$dolphin_pid" 2>/dev/null || true
wait "$dolphin_pid" 2>/dev/null || true
cat >"$KALTSIT_TEST_ROOT/terminal-preview.sh" <<'SH'
printf '\n  Kaltsit Medical Green  |  v1.1\n\n'
printf '  Plasma 6 / Wayland     warm white + medical green\n\n'
for code in 30 31 32 33 34 35 36 37 90 91 92 93 94 95 96 97; do
  printf '  \033[%smANSI %-3s  The quick brown fox  0123456789\033[0m\n' "$code" "$code"
done
printf '\n  Fonts, key bindings and shell settings remain yours.\n'
sleep 30
SH
konsole --separate --profile KaltsitMedicalGreen --hide-menubar -e bash "$KALTSIT_TEST_ROOT/terminal-preview.sh" >"$KALTSIT_TEST_ROOT/konsole.log" 2>&1 &
konsole_pid=$!
sleep 3
capture terminal
kill "$konsole_pid" 2>/dev/null || true
wait "$konsole_pid" 2>/dev/null || true
# Testing mode renders the actual native greeter without locking or auth changes.
if [[ -n "${KALTSIT_GREETER:-}" ]]; then
  "$KALTSIT_GREETER" --testing --immediateLock >"$KALTSIT_TEST_ROOT/lockscreen.log" 2>&1 &
  greeter_pid=$!
  sleep 4
  capture lockscreen
  kill "$greeter_pid" 2>/dev/null || true
  wait "$greeter_pid" 2>/dev/null || true
fi
