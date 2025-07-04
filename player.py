import os
import cv2
import pygame
import time

from clip_utils import start_clip, update_clips, active_clips, master_gain

HD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HD")


def list_clips():
    """Return base names that have BOTH .mov and .wav."""
    bases = {os.path.splitext(f)[0] for f in os.listdir(HD_DIR)}
    return sorted([
        b for b in bases
        if os.path.exists(os.path.join(HD_DIR, f"{b}.mov"))
        and os.path.exists(os.path.join(HD_DIR, f"{b}.wav"))
    ])


def video_player(path):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print(f"Couldn't open {path}"); return "next"
    while True:
        ok, frame = cap.read()
        if not ok:                       # loop video endlessly
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        cv2.imshow("Video", frame)
        k = cv2.waitKey(24) & 0xFF
        update_clips(0.024)
        if k == ord('q'):
            return "quit"
        if k != 0xFF:                    # any other key ⇒ next clip
            return "next"


def main():
    clips = list_clips()
    if not clips:
        print("No matching .mov/.wav pairs in HD/"); return

    # --- robust mixer initialisation ---------------------------
    pygame.mixer.pre_init(44100, -16, 2, 512)   # 44.1 kHz, 16-bit, stereo
    pygame.init()
    pygame.mixer.set_num_channels(32)           # plenty of mixing room
    # -----------------------------------------------------------

    idx = 0

    while True:
        clip = clips[idx]
        print(f"\n▶ {clip}  (any key → next, q → quit)")

        # start/stack the new loop with flag handling
        start_clip(clip, HD_DIR)

        # show video (runs in the MAIN thread!)
        status = video_player(os.path.join(HD_DIR, f"{clip}.mov"))
        cv2.destroyAllWindows()

        if status == "quit":
            break
        idx = (idx + 1) % len(clips)

    pygame.mixer.fadeout(1000)    # gentle exit
    pygame.mixer.quit()


if __name__ == "__main__":
    main()
