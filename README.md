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

3. If you are not running a desktop session, point Pygame at the
   framebuffer before launching:
   ```bash
   export SDL_VIDEODRIVER=fbcon
   export SDL_FBDEV=/dev/fb0
   ```
4. Run the helper to create a virtual environment, install Python

   dependencies and start the server:
   ```bash
   ./load_venv.sh
   ```

Use a browser pointed at `http://<pi-ip>:5003` to control playback.
