#!/usr/bin/env python3
# Remote-driven video looper that polls /command on localhost
# pip install requests opencv-python pygame

import os, time, requests, cv2, pygame, sys
from clip_utils import start_clip, update_clips

HD_DIR = os.path.join(os.path.dirname(__file__), "HD")
SERVER = os.getenv("LOOPER_SERVER", "http://127.0.0.1:5000/command")
POLL   = 0.20        # seconds between polls / frames

def list_clips():
    files = os.listdir(HD_DIR)
    vids  = {os.path.splitext(f)[0] for f in files if f.lower().endswith(".mp4")}
    wavs  = {os.path.splitext(f)[0] for f in files if f.lower().endswith(".wav")}
    return sorted([b for b in vids if any(w == b or w.startswith(f"{b}_") for w in wavs)])

def fetch_cmd():
    try:
        return requests.get(SERVER, timeout=0.1).json().get("command")
    except requests.RequestException:
        return None

def wait_for_start():
    print("Remote ready – tap NEXT / START")
    while True:
        cmd = fetch_cmd()
        if cmd == "next":
            return True
        if cmd == "quit":
            return False
        time.sleep(POLL)

def video_player(path):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print("Can't open", path); return "next"
    while True:
        ok, frame = cap.read()
        if not ok:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0); continue
        cv2.imshow("Video", frame)
        k = cv2.waitKey(int(POLL*1000)) & 0xFF

        # keyboard fallback
        if k == ord('q'):
            return "quit"
        if k != 0xFF:
            return "next"

        cmd = fetch_cmd()
        if cmd:
            return cmd

        update_clips(POLL)

def main():
    clips = list_clips()
    if not clips:
        print("No media in HD/"); return

    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init(); pygame.mixer.set_num_channels(32)

    if not wait_for_start():
        return

    idx = 0
    while True:
        clip = clips[idx]
        print(f"▶ {clip}")
        start_clip(clip, HD_DIR)

        status = video_player(os.path.join(HD_DIR, f"{clip}.mp4"))
        cv2.destroyAllWindows()

        if status == "quit":
            break
        idx = (idx + 1) % len(clips)

    pygame.mixer.fadeout(1000); pygame.mixer.quit()

if __name__ == "__main__":
    main()
