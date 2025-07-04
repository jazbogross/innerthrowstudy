import os
import threading
import cv2
import pygame

HD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HD")


def play_audio_loop(name: str) -> pygame.mixer.Sound:
    """Load a wav file from HD and play it looping."""
    audio_path = os.path.join(HD_DIR, f"{name}.wav")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(audio_path)

    pygame.mixer.init()
    sound = pygame.mixer.Sound(audio_path)
    sound.play(loops=-1)
    return sound


def play_video(name: str, stop_event: threading.Event) -> None:
    """Continuously play a video file from HD until stop_event is set."""
    video_path = os.path.join(HD_DIR, f"{name}.mov")
    if not os.path.exists(video_path):
        raise FileNotFoundError(video_path)

    while not stop_event.is_set():
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Failed to open {video_path}")
            break
        while cap.isOpened() and not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow("Video", frame)
            if cv2.waitKey(30) & 0xFF == ord("q"):
                stop_event.set()
                break
        cap.release()
    cv2.destroyAllWindows()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Loop audio and video clips from the HD folder.")
    parser.add_argument(
        "clip",
        help="Base name (without extension) of the clip to start playing",
    )
    args = parser.parse_args()

    play_audio_loop(args.clip)

    stop_event = threading.Event()
    video_thread = threading.Thread(target=play_video, args=(args.clip, stop_event))
    video_thread.start()

    try:
        while True:
            new_video = input("Enter new video name or 'q' to quit: ").strip()
            if new_video.lower() == "q":
                break
            if not new_video:
                continue
            stop_event.set()
            video_thread.join()
            stop_event.clear()
            video_thread = threading.Thread(target=play_video, args=(new_video, stop_event))
            video_thread.start()
    finally:
        stop_event.set()
        video_thread.join()
        pygame.mixer.quit()


if __name__ == "__main__":
    main()
