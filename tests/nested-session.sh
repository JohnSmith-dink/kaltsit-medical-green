#!/usr/bin/env bash
# Run ONLY inside a private dbus-run-session with a temporary HOME/runtime.
set -euo pipefail
: "${KALTSIT_TEST_ROOT:?}" "${KALTSIT_SHARE:?}" "${KALTSIT_CONTROLLER:?}"
test "$HOME" = "$KALTSIT_TEST_ROOT/home"
test "$XDG_RUNTIME_DIR" = "$KALTSIT_TEST_ROOT/runtime"
mkdir -p "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$XDG_CACHE_HOME" "$XDG_STATE_HOME"
cleanup() {
  kill "${plasma_pid:-}" "${kwin_pid:-}" 2>/dev/null || true
  wait "${plasma_pid:-}" "${kwin_pid:-}" 2>/dev/null || true
}
trap cleanup EXIT
export WAYLAND_DISPLAY=kaltsit-test
dbus-update-activation-environment WAYLAND_DISPLAY XDG_RUNTIME_DIR QT_QPA_PLATFORM
kwin_wayland --virtual --width 3120 --height 2080 --scale 1 \
  --socket kaltsit-test --no-lockscreen --no-global-shortcuts --no-kactivities \
  >"$KALTSIT_TEST_ROOT/kwin.log" 2>&1 &
kwin_pid=$!
for attempt in $(seq 1 60); do
  test -S "$XDG_RUNTIME_DIR/kaltsit-test" && break
  kill -0 "$kwin_pid"
  sleep 0.5
done
plasmashell --no-respawn >"$KALTSIT_TEST_ROOT/plasma.log" 2>&1 &
plasma_pid=$!
for attempt in $(seq 1 60); do
  count=$(qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript \
      'print(desktops().length)' 2>/dev/null || true)
  if [[ "$count" =~ ^[1-9][0-9]*$ ]]; then
    break
  fi
  kill -0 "$plasma_pid"
  sleep 0.5
done
kscreen-doctor output.Virtual-0.scale.1.75 >"$KALTSIT_TEST_ROOT/scale-change.log"
kscreen-doctor --json >"$KALTSIT_TEST_ROOT/outputs-before.json"
layout_script='var a=[]; var all=desktops().concat(panels()); for(var i=0;i<all.length;++i){var d=all[i]; a.push({id:d.id,type:d.type,widgets:d.widgetIds});} print(JSON.stringify(a));'
qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$layout_script" >"$KALTSIT_TEST_ROOT/layout-before.json"
kwriteconfig6 --file kcminputrc --group Mouse --key cursorSize 36
kwriteconfig6 --file kdeglobals --group General --key font 'Noto Sans,10,-1,5,50,0,0,0,0,0'
kwriteconfig6 --file kdeglobals --group General --key fixed 'Monospace,11,-1,5,50,0,0,0,0,0'
kwriteconfig6 --file kdeglobals --group General --key AccentColor '180,40,60'
# A fixed accent is deterministic. With wallpaper accents enabled Plasma may
# recompute AccentColor asynchronously after restore; the policy is restored,
# but that derived value is intentionally not frozen by the theme controller.
kwriteconfig6 --file kdeglobals --group General --key accentColorFromWallpaper false
python3 "$KALTSIT_CONTROLLER" --data-dir "$KALTSIT_SHARE" status >"$KALTSIT_TEST_ROOT/status-before.json"
python3 "$KALTSIT_CONTROLLER" --data-dir "$KALTSIT_SHARE" apply >"$KALTSIT_TEST_ROOT/apply.json"
python3 "$KALTSIT_CONTROLLER" --data-dir "$KALTSIT_SHARE" apply >"$KALTSIT_TEST_ROOT/apply-again.json"
python3 "$KALTSIT_CONTROLLER" --data-dir "$KALTSIT_SHARE" status >"$KALTSIT_TEST_ROOT/status-applied.json"
test "$(kreadconfig6 --file plasmarc --group Theme --key name)" = KaltsitMedicalGreen
test "$(kreadconfig6 --file kdeglobals --group General --key ColorScheme)" = KaltsitMedicalGreen
test "$(kreadconfig6 --file kdeglobals --group Icons --key Theme)" = KaltsitMedicalGreen
test "$(kreadconfig6 --file kdeglobals --group 'Colors:Selection' --key BackgroundNormal)" = '46,107,87'
test "$(kreadconfig6 --file kdeglobals --group 'Colors:View' --key ForegroundLink)" = '40,93,131'
test "$(kreadconfig6 --file kdeglobals --group General --key accentColorFromWallpaper)" = false
if [[ "${KALTSIT_CAPTURE:-0}" = 1 ]]; then
  bash "$(dirname "$0")/capture-session.sh"
fi
python3 "$KALTSIT_CONTROLLER" --data-dir "$KALTSIT_SHARE" restore >"$KALTSIT_TEST_ROOT/restore.json"
python3 "$KALTSIT_CONTROLLER" --data-dir "$KALTSIT_SHARE" status >"$KALTSIT_TEST_ROOT/status-restored.json"
qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$layout_script" >"$KALTSIT_TEST_ROOT/layout-after.json"
kscreen-doctor --json >"$KALTSIT_TEST_ROOT/outputs-after.json"
test "$(kreadconfig6 --file kcminputrc --group Mouse --key cursorSize)" = 36
test "$(kreadconfig6 --file kdeglobals --group General --key font)" = 'Noto Sans,10,-1,5,50,0,0,0,0,0'
test "$(kreadconfig6 --file kdeglobals --group General --key fixed)" = 'Monospace,11,-1,5,50,0,0,0,0,0'
test "$(kreadconfig6 --file kdeglobals --group General --key AccentColor)" = '180,40,60'
test "$(kreadconfig6 --file kdeglobals --group General --key accentColorFromWallpaper)" = false
python3 "$(dirname "$0")/session-transactions.py"
python3 "$(dirname "$0")/session-components.py"
python3 - <<'PY'
import json, os
from pathlib import Path
root=Path(os.environ['KALTSIT_TEST_ROOT'])
records={p.stem:json.loads(p.read_text()) for p in root.glob('*.json')}
assert records['apply']['result']=='applied', records
assert records['apply-again']['result']=='already-applied', records
assert records['restore']['result']=='restored', records
assert records['status-applied']['current_color_scheme']=='KaltsitMedicalGreen', records['status-applied']
assert records['status-applied']['current_icons']=='KaltsitMedicalGreen', records['status-applied']
assert records['status-before']['current_color_scheme']==records['status-restored']['current_color_scheme'], records
assert records['status-restored']['restore_available'] is False, records
assert records['layout-before']==records['layout-after'], records
assert records['outputs-before']['outputs'][0]['scale']==1.75, records['outputs-before']
assert records['outputs-after']['outputs'][0]['scale']==1.75, records['outputs-after']
print(json.dumps(records,indent=2,ensure_ascii=False))
PY
