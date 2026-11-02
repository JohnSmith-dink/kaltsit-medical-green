# Measuring video wallpaper cost

This page provides a repeatable procedure and an empty results table, without power conclusions. Software playback checks do not establish hardware decoding, long-term power use or multi-display behavior.

## Controlled conditions

Record machine, kernel, GPUs/drivers, Plasma/Qt versions, display count, resolution, scale, refresh rate, brightness, power profile, battery charge range, and video hash/resolution/frame rate/codec. Close unrelated tasks and allow temperature to stabilize.
For each state, settle for two minutes, then sample at the same interval for at least five minutes. Repeat three rounds and vary their order. Record averages, ranges and anomalies; do not compare samples with different brightness or background workloads.

The operator selects three states: a static image wallpaper, video playback, and right-click manual pause of that same video wallpaper. Keep window visibility, mouse activity and other workloads comparable.
For playback measurements on battery, temporarily set `BatteryPolicy=ignore` (keep playing), then restore the original value. Otherwise the default automatic pause invalidates the playback label. Manual pause preserves the video frame; it is not equivalent to unloading the player.

## Sampling

- Whole system: prefer the same external power meter, or read the actual discharging battery's `/sys/class/power_supply/BAT*/power_now` (normally µW; divide by 1000000 for W). If only `current_now` and `voltage_now` exist, use µA × µV / 10^12 for W after checking driver units and discharge status. Charging current or individual device power is not whole-system input power. Powertop's system estimate is another option; document its source and do not sum device estimates into a precise system reading. Do not change conditions with `--auto-tune`.
- CPU: identify the wallpaper's `plasmashell` PID and use `pidstat -p <PID> 1 300` (sysstat) or an equivalent tool. Also record total CPU utilization and whether 100% means one core or the whole machine. Plasma's PID includes other components as well as in-process video playback.
- GPU: select tools for the actual hardware, such as `intel_gpu_top` on Intel. Record render and video decode engine utilization separately. For AMD/NVIDIA, use the corresponding driver tools and record support and sampling frequency. Leave unavailable values blank. GPU utilization is not GPU power, and process utilization is not system power.

On a hybrid NVIDIA laptop, identify the discrete GPU PCI address using `lspci -D`, then read passive status first (replace the example address):

```sh
cat /sys/bus/pci/devices/0000:01:00.0/power/runtime_status
cat /sys/bus/pci/devices/0000:01:00.0/power/runtime_active_time
cat /sys/bus/pci/devices/0000:01:00.0/power/runtime_suspended_time
```

Record `active` / `suspended` and counter changes at fixed sample points in all three states. Keep external displays and other GPU applications consistent. Runtime PM state is not a precise power reading.
Then run `nvidia-smi --query-gpu=pci.bus_id,pstate,utilization.gpu,power.draw --format=csv` in a **separate round**, comparing state before and after. Diagnostic queries may disturb device sleep; do not attribute a post-query wake directly to the wallpaper. Leave unsupported fields blank. Skip this section without NVIDIA hardware; do not misidentify the actual machine.

## Results (operator fills in)

| State | System mean W / range | Plasma CPU % | Total CPU % | GPU render % | GPU decode % | Discrete GPU runtime state | Temperature / notes |
|---|---|---|---|---|---|---|---|
| Static wallpaper | | | | | | | |
| Video playback | | | | | | | |
| Manual pause | | | | | | | |

Sources: [Linux runtime PM](https://docs.kernel.org/power/runtime_pm.html), [power supply units](https://docs.kernel.org/power/power_supply_class.html), [NVIDIA SMI](https://docs.nvidia.com/deploy/nvidia-smi/index.html).
