# Video/Audio Looper

This project plays pairs of video (`.mp4`) and audio (`.wav`) files in
loops. Files live in an `HD/` directory which is ignored by git.  Each
video basename must have a matching audio file so `kick.mp4` goes with
`kick.wav`.

The scripts use OpenCV and Pygame.  `player_remote.py` is started via
the `remote_server.py` helper and can be controlled from another device
on the network.

## Raspberry Pi Lite setup

1. Install system packages:
   ```bash
   sudo apt-get install python3-opencv python3-pygame python3-venv
   ```
2. Place this repository (and your `HD/` folder) somewhere under
   `/home/pi/` and make `load_venv.sh` executable:
   ```bash
   chmod +x load_venv.sh
   ```

3. If you are not running a desktop session, use the framebuffer.  Either
   export these variables yourself or rely on `load_venv.sh` which sets them
   when missing.  Also set `XDG_RUNTIME_DIR` if you see SDL errors:
   ```bash
   export SDL_VIDEODRIVER=fbcon
   export SDL_FBDEV=/dev/fb0
   export XDG_RUNTIME_DIR=/tmp
   ```
4. Run the helper with sudo so it can access `/dev/fb0`, create a
   virtual environment, install Python dependencies and start the
   server:
   ```bash
   sudo ./load_venv.sh

   ```

Use a browser pointed at `http://<pi-ip>:5003` to control playback.
