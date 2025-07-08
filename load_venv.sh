#!/usr/bin/env bash
#
# load_venv.sh  – set up venv (once) and launch remote_server.py
# put this in /home/mpi/innerthrowstudy/  and  chmod +x load_venv.sh

set -e  # bail on first error

export QT_QPA_PLATFORM_PLUGIN_PATH="$HOME/innerthrowstudy/.venv/lib/python3.11/site-packages/cv2/qt/plugins/platforms"


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

# ── 3. ensure XDG_RUNTIME_DIR is set ──────────────────────────────
# Qt and other GUI libraries expect a writable runtime directory
if [[ -z "$XDG_RUNTIME_DIR" ]] || [[ ! -d "$XDG_RUNTIME_DIR" ]]; then
    if [[ -d "/run/user/$(id -u)" ]]; then
        export XDG_RUNTIME_DIR="/run/user/$(id -u)"
    else
        export XDG_RUNTIME_DIR="$HOME/.runtime"
        mkdir -p "$XDG_RUNTIME_DIR"
        chmod 700 "$XDG_RUNTIME_DIR"
    fi
fi

# ── 4. exec the real application (so systemd sees its PID) ─────────
exec python remote_server.py  # remote_server will spawn player_remote
