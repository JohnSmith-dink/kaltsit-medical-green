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
  timeout 30s spectacle --new-instance --background --nonotify --fullscreen --output "$KALTSIT_TEST_ROOT/screenshots/$1.png" >"$KALTSIT_TEST_ROOT/capture-$1.log" 2>&1
  # A successful process exit is insufficient: DBus screenshot permission or
  # asynchronous capture failures can otherwise leave an empty gallery.
  python3 - "$KALTSIT_TEST_ROOT/screenshots/$1.png" <<'PY'
import sys
import time
from pathlib import Path
from PIL import Image
path = Path(sys.argv[1])
for _ in range(40):
    if path.is_file():
        break
    time.sleep(0.1)
if not path.is_file():
    raise SystemExit(f"Screenshot was not written: {path}; inspect the capture log and XDG_DATA_DIRS")
with Image.open(path) as image:
    image.verify()
    if image.width < 1 or image.height < 1:
        raise SystemExit(f"Screenshot has no pixels: {path}")
PY
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
  if [[ -n "${KALTSIT_GREETER_WAKEUP:-}" ]]; then
    LD_PRELOAD="$KALTSIT_GREETER_WAKEUP" "$KALTSIT_GREETER" --testing --immediateLock >"$KALTSIT_TEST_ROOT/lockscreen.log" 2>&1 &
  else
    "$KALTSIT_GREETER" --testing --immediateLock >"$KALTSIT_TEST_ROOT/lockscreen.log" 2>&1 &
  fi
  greeter_pid=$!
  sleep 4
  capture lockscreen
  if [[ -n "${KALTSIT_GREETER_WAKEUP:-}" ]]; then
    test "$WAYLAND_DISPLAY" = kaltsit-test
    touch "$KALTSIT_TEST_ROOT/show-unlock"
    for attempt in $(seq 1 50); do
      test -f "$KALTSIT_TEST_ROOT/unlock-shown" && break
      sleep 0.1
    done
    test -f "$KALTSIT_TEST_ROOT/unlock-shown"
    sleep 2
    capture lockscreen-unlock
  fi
  kill "$greeter_pid" 2>/dev/null || true
  wait "$greeter_pid" 2>/dev/null || true
fi
