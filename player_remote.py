#!/usr/bin/env python3
# Remote-driven video looper that polls /command on localhost

import os

# Ensure Pygame can use the framebuffer when no desktop session is running
os.environ.setdefault("SDL_VIDEODRIVER", "fbcon")
os.environ.setdefault("SDL_FBDEV", "/dev/fb0")
os.environ.setdefault("XDG_RUNTIME_DIR", "/tmp")

import time
import requests
import pygame
import cv2

from clip_utils import start_clip, update_clips

# ── Configuration ───────────────────────────────────────────────────────
HD_DIR = os.path.join(os.path.dirname(__file__), "HD")
SERVER = os.getenv("LOOPER_SERVER", "http://127.0.0.1:5000/command")
POLL   = 0.20  # seconds between polls / audio updates

# ── Utility functions ───────────────────────────────────────────────────

def list_clips() -> list[str]:
    files = os.listdir(HD_DIR)
    vids  = {os.path.splitext(f)[0] for f in files if f.lower().endswith(".mp4")}
    wavs  = {os.path.splitext(f)[0] for f in files if f.lower().endswith(".wav")}
    return sorted(b for b in vids if any(w == b or w.startswith(f"{b}_") for w in wavs))


def fetch_cmd() -> str | None:
    try:
        return requests.get(SERVER, timeout=0.1).json().get("command")
    except requests.RequestException:
        return None


def wait_for_start() -> bool:
    print("Remote ready – tap NEXT / START")
    while True:
        cmd = fetch_cmd()
        if cmd == "next":
            return True
        if cmd == "quit":
            return False
        time.sleep(POLL)

# ── Video & command-aware playback ─────────────────────────────────────

def video_player(path: str) -> str:
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print(f"Couldn't open {path}")
        return "next"

    # use the current display resolution rather than the video size
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    screen_size = screen.get_size()

    fps = cap.get(cv2.CAP_PROP_FPS)
    delay = 1.0 / fps if fps > 0 else POLL

    while True:
        ok, frame = cap.read()
        if not ok:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        if surf.get_size() != screen_size:
            surf = pygame.transform.smoothscale(surf, screen_size)
        screen.blit(surf, (0, 0))
        pygame.display.flip()

        update_clips(delay)
        cmd = fetch_cmd()
        if cmd == "quit":
            cap.release()
            pygame.display.quit()
            return "quit"
        if cmd == "next":
            cap.release()
            pygame.display.quit()
            return "next"

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    cap.release()
                    pygame.display.quit()
                    return "quit"
                else:
                    cap.release()
                    pygame.display.quit()
                    return "next"

        time.sleep(delay)

# ── Main loop ──────────────────────────────────────────────────────────

def main():
    clips = list_clips()
    if not clips:
        print("No media in HD/")
        return

    # initialize mixer for layered audio
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    pygame.mixer.set_num_channels(32)

    # wait for first "next"
    if not wait_for_start():
        return

    idx = 0
    while True:
        clip = clips[idx]
        print(f"▶ {clip}")
        start_clip(clip, HD_DIR)

        status = video_player(os.path.join(HD_DIR, f"{clip}.mp4"))
        if status == "quit":
            break

        idx = (idx + 1) % len(clips)

    # clean exit
    pygame.mixer.fadeout(1000)
    pygame.mixer.quit()

if __name__ == "__main__":
    main()
