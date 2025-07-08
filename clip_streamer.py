#!/usr/bin/env python3
"""
Play local HD/*.mp4 clips with audio and, in parallel, stream them
to a Raspberry Pi either via FFmpeg+MPEG‑TS or GStreamer+RTP.

Example:
    python clip_streamer.py --pi 192.168.1.42 --method ffmpeg
"""
import os, argparse, subprocess, shlex
from typing import Optional  # Python < 3.10 compatibility

import cv2, pygame

from clip_utils import start_clip, update_clips  # external helpers

HD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HD")

# ────────────────────────────────────────────────────────────────────
#  Helper: enumerate video/audio pairs
# ────────────────────────────────────────────────────────────────────

def list_clips():
    files = os.listdir(HD_DIR)
    video_bases = {os.path.splitext(f)[0] for f in files if f.lower().endswith(".mp4")}
    wavs = [f for f in files if f.lower().endswith(".wav")]

    return sorted([
        base for base in video_bases
        if any(w == f"{base}.wav" or w.startswith(f"{base}_") for w in wavs)
    ])

# ────────────────────────────────────────────────────────────────────
#  Network streaming back‑ends
# ────────────────────────────────────────────────────────────────────

def _spawn(cmd: list[str]):
    """Utility: show the command then launch it detached."""
    print("\n[stream] →", " ".join(shlex.quote(p) for p in cmd))
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def start_stream_ffmpeg(path: str, pi_host: str, port: int = 1234):
    """Start FFmpeg (VideoToolbox) → MPEG‑TS → UDP sender."""
    cmd = [
        "ffmpeg", "-nostdin", "-stream_loop", "-1", "-re", "-i", path,
        "-c:v", "h264_videotoolbox", "-b:v", "6M", "-g", "48", "-profile:v", "high",
        "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "44100",
        "-f", "mpegts", f"udp://{pi_host}:{port}?pkt_size=1316"
    ]
    return _spawn(cmd)


def start_stream_gst(path: str, pi_host: str, v_port: int = 5000, a_port: int = 5002):
    """Start GStreamer → RTP/H.264 + RTP/AAC sender and PRINT the exact command."""
    pipeline = (
        f"filesrc location={shlex.quote(path)} ! "
        "decodebin name=d "
        "d.video ! queue ! videoconvert ! vtenc_h264 ! "
        "rtph264pay config-interval=1 pt=96 ! "
        f"udpsink host={pi_host} port={v_port} "
        "d.audio ! queue ! audioconvert ! audioresample ! avenc_aac ! "
        "rtpmp4gpay pt=97 ! "
        f"udpsink host={pi_host} port={a_port}"
    )
    cmd = ["gst-launch-1.0", "-q", *shlex.split(pipeline)]
    return _spawn(cmd)


def stop_process(proc: Optional[subprocess.Popen]):
    """Terminate a Popen if it's still running."""
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()

# ────────────────────────────────────────────────────────────────────
#  Video preview
# ────────────────────────────────────────────────────────────────────

def video_player(path: str):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print(f"Couldn't open {path}")
        return "next"

    while True:
        ok, frame = cap.read()
        if not ok:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        cv2.imshow("Video", frame)
        k = cv2.waitKey(24) & 0xFF
        update_clips(0.024)

        if k == ord('q'):
            return "quit"
        if k != 0xFF:
            return "next"

# ────────────────────────────────────────────────────────────────────
#  Main loop
# ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--pi", required=True, help="IP/hostname of the Raspberry Pi receiver")
    ap.add_argument("--method", choices=("ffmpeg", "gst"), default="ffmpeg",
                    help="Network streaming back‑end")
    ap.add_argument("--port", type=int, default=1234,
                    help="Base UDP port (ffmpeg) or video port (gst)")
    args = ap.parse_args()

    clips = list_clips()
    if not clips:
        print("No matching .mp4/.wav pairs in HD/")
        return

    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    pygame.mixer.set_num_channels(32)

    stream_proc: Optional[subprocess.Popen] = None
    idx = 0

    while True:
        clip = clips[idx]
        path = os.path.join(HD_DIR, f"{clip}.mp4")

        print(f"\n▶ {clip}  (any key → next, q → quit)")

        # Restart stream for each clip
        stop_process(stream_proc)
        if args.method == "ffmpeg":
            stream_proc = start_stream_ffmpeg(path, args.pi, port=args.port)
        else:
            stream_proc = start_stream_gst(path, args.pi, v_port=args.port, a_port=args.port + 2)

        start_clip(clip, HD_DIR)
        status = video_player(path)
        cv2.destroyAllWindows()

        if status == "quit":
            break
        idx = (idx + 1) % len(clips)

    stop_process(stream_proc)
    pygame.mixer.fadeout(1000)
    pygame.mixer.quit()


if __name__ == "__main__":
    main()
