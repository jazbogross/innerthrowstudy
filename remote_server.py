#!/usr/bin/env python3
# LAN-remote controller *and* launcher for the video-looper demo.
# pip install flask

import os, sys, subprocess
from flask import Flask, jsonify, redirect

app = Flask(__name__, static_folder=None)
_command = None            # “next”, “quit”, None  – read-once by the player

# ──────────────────────── minimal HTML UI ───────────────────────────
HTML = """
<!doctype html>
<title>Video Looper Remote</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{font-family:sans-serif;margin:0;text-align:center}
button{width:90vw;height:35vh;margin:5vh 0;font-size:8vw;
       border:0;border-radius:1rem;color:#fff}
.next{background:#4CAF50}
.quit{background:#F44336}
</style>
<h1>Video Looper Remote</h1>
<a href="/next"><button class="next">NEXT / START</button></a>
<a href="/quit"><button class="quit">QUIT</button></a>
"""
# ────────────────────────────────────────────────────────────────────

@app.get("/")           # phone home-page
def index():
    return HTML

@app.get("/next")       # big green button
def next_cmd():
    global _command
    _command = "next"
    return redirect("/")

@app.get("/quit")       # big red button
def quit_cmd():
    global _command
    _command = "quit"
    return redirect("/")

@app.get("/command")    # polled by player_remote.py
def get_command():
    global _command
    cmd, _command = _command, None     # one-shot read
    return jsonify({"command": cmd})

# ─────────────────────── launch the player once ─────────────────────
def launch_player():
    """Start player_remote.py in a subprocess (same Python)."""
    here = os.path.abspath(os.path.dirname(__file__))
    player = os.path.join(here, "player_remote.py")
    # Pass the server URL via env var in case you ever change port/host
    env = os.environ.copy()
    env["LOOPER_SERVER"] = "http://127.0.0.1:5003/command"
    return subprocess.Popen([sys.executable, player], env=env)

# --------------------------------------------------------------------
if __name__ == "__main__":
    player_proc = launch_player()
    try:
        # 0.0.0.0 so that phones on the same Wi-Fi can reach it
        app.run(host="0.0.0.0", port=5003, debug=False)
    finally:
        # tidy shutdown on Ctrl-C or Quit button
        player_proc.terminate()
