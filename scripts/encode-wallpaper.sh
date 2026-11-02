#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
set -euo pipefail
usage() {
  echo 'Usage: encode-wallpaper.sh [--fps N] [--width N] [--bitrate RATE] INPUT [OUTPUT.mp4]'
  echo 'Defaults: 30 fps, width at most 1920, maxrate 6M. Output stays in the real input directory.'
}
fail() { echo "encode-wallpaper: $*" >&2; exit 2; }
fps=30
width=1920
bitrate=6M
while [[ $# -gt 0 ]]; do
  case "$1" in
    --fps|--width|--bitrate)
      [[ $# -ge 2 ]] || fail "Missing value for $1"
      case "$1" in --fps) fps=$2;; --width) width=$2;; --bitrate) bitrate=$2;; esac
      shift 2;;
    -h|--help) usage; exit 0;;
    --) shift; break;;
    -*) fail "Unknown option: $1";;
    *) break;;
  esac
done
[[ $# -ge 1 && $# -le 2 ]] || { usage >&2; exit 2; }
[[ "$fps" =~ ^[1-9][0-9]*$ ]] || fail 'fps must be a positive integer'
[[ "$width" =~ ^[1-9][0-9]*$ && ${#width} -le 5 && "$width" -ge 2 ]] || fail 'width must be an integer from 2 to 99999'
[[ "$bitrate" =~ ^[1-9][0-9]*[kKmM]?$ ]] || fail 'bitrate must be positive, optionally ending in k or M'
command -v ffmpeg >/dev/null 2>&1 || fail 'ffmpeg is missing; install ffmpeg before running this script'
command -v realpath >/dev/null 2>&1 || fail 'realpath is missing (GNU coreutils required)'
[[ -f "$1" ]] || fail 'Input must be an existing local regular file'
input=$(realpath -e -- "$1")
input_dir=${input%/*}
input_name=${input##*/}
output=${2:-"$input_dir/${input_name%.*}-wallpaper.mp4"}
[[ "$output" = /* ]] || output="$PWD/$output"
[[ ! -e "$output" && ! -L "$output" ]] || fail 'Output already exists; refusing to overwrite a file or symlink'
output_dir=$(realpath -e -- "${output%/*}") || fail 'Output directory does not exist'
[[ "$output_dir" = "$input_dir" ]] || fail 'Output must be in the real input directory'
output="$output_dir/${output##*/}"
[[ ! -e "$output" && ! -L "$output" ]] || fail 'Output already exists; refusing to overwrite a file or symlink'
# Prevent an inherited FFREPORT from writing a report outside the input directory.
unset FFREPORT
# The protocol whitelist rejects network input even if a local playlist refers to it.
exec ffmpeg -hide_banner -nostdin -loglevel warning -n -protocol_whitelist file \
  -i "$input" -map 0:v:0 -an -sn -dn -map_metadata -1 -map_chapters -1 \
  -vf "scale=w='min($width,iw)':h=ih:force_original_aspect_ratio=decrease:force_divisible_by=2" \
  -r "$fps" -fps_mode cfr -c:v libx264 -pix_fmt yuv420p \
  -maxrate "$bitrate" -bufsize "$bitrate" -movflags +faststart -f mp4 "$output"
