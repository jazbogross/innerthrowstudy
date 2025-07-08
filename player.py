import os
import cv2
import pygame
import time

from clip_utils import start_clip, update_clips, active_clips, master_gain

HD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HD")


def list_clips():
    """
    Return every video *base* that             ─────┐
    has at least one WAV beginning with it.  <──────┘
    Audio files may carry suffix flags (e.g. _v3, _dp…).
    """
    files = os.listdir(HD_DIR)

    # collect all .mp4 basenames first
    video_bases = {
        os.path.splitext(f)[0]
        for f in files
        if f.lower().endswith(".mp4")
    }

    # now keep only those that have ≥1 matching wav (base or base_*)
    good = []
    wav_set = [f for f in files if f.lower().endswith(".wav")]

    for base in video_bases:
        prefix  = f"{base}_"         # base followed by an underscore
        has_wav = any(
            w == f"{base}.wav" or w.startswith(prefix)
            for w in wav_set
        )
        if has_wav:
            good.append(base)

    return sorted(good)



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
        print("No matching .mp4/.wav pairs in HD/"); return

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
        status = video_player(os.path.join(HD_DIR, f"{clip}.mp4"))
        cv2.destroyAllWindows()

        if status == "quit":
            break
        idx = (idx + 1) % len(clips)

    pygame.mixer.fadeout(1000)    # gentle exit
    pygame.mixer.quit()


if __name__ == "__main__":
    main()
