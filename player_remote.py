#!/usr/bin/env python3
"""
Video-looper with Random ↔ User modes, now with a single full-screen window
that stays open while clips change.

Random  : random clip every 1–60 s, audio loops stack (START ⇒ user)
User    : NEXT advances sequentially, QUIT ⇒ random

Keyboard fallback (when LOOPER_SERVER unset):
    any key → NEXT,   q → quit program

All video is forced to 24 fps so playback speed is correct.
"""
import os, time, random, cv2, pygame, requests, sys
import clip_utils                                              # ← NEW
from clip_utils import start_clip, update_clips, active_clips, master_gain

HD_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HD")
SERVER_URL = os.environ.get("LOOPER_SERVER")       # e.g. "http://…/command"

# ───────────────────── helper utilities ──────────────────────
def list_clips() -> list[str]:
    """Return every video base that has at least one matching WAV."""
    files  = os.listdir(HD_DIR)
    vids   = {os.path.splitext(f)[0] for f in files if f.lower().endswith(".mov")}
    wavs   = [f for f in files if f.lower().endswith(".wav")]
    good   = [b for b in vids if any(w == f"{b}.wav" or w.startswith(f"{b}_") for w in wavs)]
    return sorted(good)

def get_remote_command():
    """Poll the Flask server once; return 'next', 'quit' or None."""
    try:
        r = requests.get(SERVER_URL, timeout=0.5)
        return r.json().get("command")
    except Exception:
        return None

# ─────────────────── reset mixer helper (NEW) ─────────────────
def reset_mixer():
    """Completely restart pygame.mixer and clear clip_utils state."""
    pygame.mixer.quit()
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
    pygame.mixer.set_num_channels(32)

    active_clips.clear()
    clip_utils.solo_owner = None
# ──────────────────────────────────────────────────────────────


# ────────────────────── video helpers ─────────────────────────
FORCED_FPS = 24.0                       # every clip is exactly 24 fps
FRAME_DT   = 1.0 / FORCED_FPS           # 0.041 667 s

def _frame_delay(start_of_frame: float) -> None:
    """Sleep (if needed) so each frame lasts exactly FRAME_DT seconds."""
    leftover = FRAME_DT - (time.perf_counter() - start_of_frame)
    if leftover > 0:
        time.sleep(leftover)

def video_player(path: str) -> str:
    """
    Loop a clip until:
        • remote NEXT / QUIT
        • local any-key / 'q'  (when no server)
    Returns "next" or "quit".
    """
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print(f"Couldn't open {path}")
        return "next"

    while True:
        frame_start = time.perf_counter()

        ok, frame = cap.read()
        if not ok:                                  # reached end ⇒ loop
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = cap.read()
            if not ok:
                cap.release(); return "next"

        cv2.imshow("Video", frame)
        k = cv2.waitKey(1) & 0xFF                   # pump UI events

        # ─ local keyboard (when no remote) ─
        if SERVER_URL is None:
            if k == ord('q'):
                cap.release(); return "quit"
            if k != 0xFF:
                cap.release(); return "next"

        # ─ remote buttons ─
        else:
            cmd = get_remote_command()
            if cmd == "quit":
                cap.release(); return "quit"
            if cmd == "next":
                cap.release(); return "next"

        update_clips(FRAME_DT)
        _frame_delay(frame_start)                   # pace to 24 fps

def timed_video_player(path: str, duration: int) -> str:
    """
    Play `path` for up to `duration` seconds.
    Returns "start" if remote NEXT arrives, else "timeout".
    """
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print(f"Couldn't open {path}")
        return "timeout"

    t0 = time.perf_counter()
    while time.perf_counter() - t0 < duration:
        frame_start = time.perf_counter()

        ok, frame = cap.read()
        if not ok:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0); continue

        cv2.imshow("Video", frame)
        cv2.waitKey(1)
        update_clips(FRAME_DT)

        if SERVER_URL and get_remote_command() == "next":
            cap.release(); return "start"

        _frame_delay(frame_start)

    cap.release(); return "timeout"
# ──────────────────────────────────────────────────────────────


# ───────────────────────── modes ──────────────────────────────
def random_mode(clips: list[str]) -> None:
    while True:
        clip     = random.choice(clips)
        duration = random.randint(1, 60)            # seconds
        print(f"\n⏲ Random: '{clip}' for {duration}s  (START ⇒ user)")
        start_clip(clip, HD_DIR)

        res = timed_video_player(os.path.join(HD_DIR, f"{clip}.mov"), duration)
        if res == "start":
            pygame.mixer.stop(); return             # → user_mode

def user_mode(clips: list[str]) -> None:
    idx = 0
    while True:
        clip = clips[idx]
        print(f"\n▶ User: {clip}  (NEXT ⇒ advance, QUIT ⇒ random)")
        start_clip(clip, HD_DIR)

        res = video_player(os.path.join(HD_DIR, f"{clip}.mov"))
        if res == "quit":
            pygame.mixer.stop(); return             # → random_mode
        idx = (idx + 1) % len(clips)
# ──────────────────────────────────────────────────────────────


def main():
    clips = list_clips()
    if not clips:
        print("No matching .mov/.wav pairs in HD/"); return

    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init(); pygame.mixer.set_num_channels(32)

    # ── create the full-screen window once ──
    cv2.namedWindow("Video", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Video",
                          cv2.WND_PROP_FULLSCREEN,
                          cv2.WINDOW_FULLSCREEN)

    while True:
        random_mode(clips)
        reset_mixer()
        user_mode(clips)
        reset_mixer()

if __name__ == "__main__":
    try:
        main()
    finally:
        cv2.destroyAllWindows()      # tidy exit when program ends
