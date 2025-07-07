#!/usr/bin/env bash
#
# load_venv.sh  – set up venv (once) and launch remote_server.py
# put this in /home/mpi/innerthrowstudy/  and  chmod +x load_venv.sh

set -e                          # bail on first error

# ── 1. always run from the script’s own folder ─────────────────────
cd "$(dirname "$(readlink -f "$0")")"

# ── 2. bootstrap the virtual environment (once) ────────────────────
if [[ ! -d ".venv" ]]; then
    python3 -m venv .venv
fi

# make sure we’re using the venv’s interpreter + pip
source .venv/bin/activate
python -m pip install --upgrade pip   # safe to run repeatedly
python -m pip install -r requirements.txt

# Use the framebuffer if no desktop session is running
export SDL_VIDEODRIVER=${SDL_VIDEODRIVER:-fbcon}
export SDL_FBDEV=${SDL_FBDEV:-/dev/fb0}
uid=$(id -u)
runtime_default="/run/user/$uid"
if [ ! -d "$runtime_default" ]; then
    runtime_default="/tmp/xdg-$uid"
fi
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-$runtime_default}"

[ -d "$XDG_RUNTIME_DIR" ] || mkdir -p "$XDG_RUNTIME_DIR"

# ── 3. exec the real application  (so systemd sees its PID) ────────
exec python remote_server.py          # remote_server will spawn player_remote
