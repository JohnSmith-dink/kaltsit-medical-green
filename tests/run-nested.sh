#!/usr/bin/env bash
# Usage: bash tests/run-nested.sh PACKAGE_SHARE OUTPUT_DIRECTORY [--capture]
# KDE tools and python3 must be on PATH. No daily-session config is copied.
set -euo pipefail
share=$(realpath "${1:?package share directory}")
output=$(realpath -m "${2:?fresh validation output directory}")
test ! -e "$output" || { echo 'Use a fresh output directory.' >&2; exit 1; }
export KALTSIT_TEST_WIDTH=${KALTSIT_TEST_WIDTH:-3120}
export KALTSIT_TEST_HEIGHT=${KALTSIT_TEST_HEIGHT:-2080}
export KALTSIT_TEST_SCALE=${KALTSIT_TEST_SCALE:-1.75}
[[ "$KALTSIT_TEST_WIDTH" =~ ^[1-9][0-9]*$ && "$KALTSIT_TEST_HEIGHT" =~ ^[1-9][0-9]*$ ]] || { echo 'Invalid virtual output dimensions.' >&2; exit 1; }
[[ "$KALTSIT_TEST_SCALE" =~ ^[0-9]+([.][0-9]+)?$ && "$KALTSIT_TEST_SCALE" != 0 ]] || { echo 'Invalid virtual output scale.' >&2; exit 1; }
mkdir -m 700 -p "$output/home" "$output/runtime"
export KALTSIT_TEST_ROOT="$output"
export KALTSIT_SHARE="$share"
export KALTSIT_CONTROLLER="$(realpath "$(dirname "$0")/../tools/kaltsit_theme.py")"
export KALTSIT_CAPTURE=0
[[ "${3:-}" != --capture ]] || export KALTSIT_CAPTURE=1
export HOME="$output/home"
export XDG_CONFIG_HOME="$HOME/.config" XDG_DATA_HOME="$HOME/.local/share"
export XDG_CACHE_HOME="$HOME/.cache" XDG_STATE_HOME="$HOME/.local/state"
export XDG_RUNTIME_DIR="$output/runtime"
export XDG_DATA_DIRS="$share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
export QT_QPA_PLATFORM=wayland XDG_SESSION_TYPE=wayland
export XDG_CURRENT_DESKTOP=KDE KDE_FULL_SESSION=true KDE_SESSION_VERSION=6 XDG_MENU_PREFIX=plasma-
export LIBGL_ALWAYS_SOFTWARE=1
case "${KALTSIT_QT_RENDERER:-software}" in
  software) export QT_QUICK_BACKEND=software ;;
  default) unset QT_QUICK_BACKEND ;;
  *) echo 'Use software or default for KALTSIT_QT_RENDERER.' >&2; exit 1 ;;
esac
if [[ "$KALTSIT_CAPTURE" = 1 ]]; then
  # Only this private, virtual KWin receives the test permission. Nix wrappers
  # do not always match Spectacle's desktop-file identity in a private bus.
  # The user's compositor and its screenshot permissions are untouched.
  export KWIN_SCREENSHOT_NO_PERMISSION_CHECKS=1
fi
export PYTHONDONTWRITEBYTECODE=1
unset DISPLAY DBUS_SESSION_BUS_ADDRESS SESSION_MANAGER
exec dbus-run-session -- bash "$(dirname "$0")/nested-session.sh"
