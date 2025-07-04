import os
import random
import re
import time
import pygame

# ---------------------------------------------------------------------------
# Filename parsing
# ---------------------------------------------------------------------------
SUFFIX_RE = re.compile(r"_(?P<flags>[vdhlopr]*)(?P<vol>\d?)$")


def parse_suffix(name):
    """Return (base, flags, volume) parsed from clip name.

    base    -- the portion before the optional suffix
    flags   -- set of flag characters (v d h l s o p r)
    volume  -- 0.0-1.0 multiplier from optional single digit
    """
    m = SUFFIX_RE.search(name)
    if not m:
        return name, set(), 1.0
    flags = set(m.group("flags"))
    vol = int(m.group("vol") or 10) / 10
    base = name[: m.start()]
    return base, flags, vol

# ---------------------------------------------------------------------------
# Runtime structures
# ---------------------------------------------------------------------------

class Clip:
    def __init__(self, name, base, flags, volume):
        self.name = name              # full clip name used for file lookup
        self.base = base
        self.flags = flags
        self.base_vol = volume
        self.active = None            # (Sound, Channel)
        self.loops = 0
        self.pan_phase = 0.0
        if "o" in flags:
            self.max_loops = random.randint(1, 100)
        else:
            self.max_loops = None
        self.duck_end = 0.0


# active clips by full clip name
active_clips = {}
master_gain = 1.0
DUCK_TIME = 5.0

def stop_clip(name):
    clip = active_clips.pop(name, None)
    if clip and clip.active:
        clip.active[1].stop()
        if "s" in clip.flags:
            # restore volumes that were muted for solo
            for other in active_clips.values():
                other.active[1].set_volume(other.base_vol * master_gain)


def add_looping_audio(name, volume, hd_dir):
    path = os.path.join(hd_dir, f"{name}.wav")
    snd = pygame.mixer.Sound(path)
    chan = snd.play(loops=-1, fade_ms=250)
    chan.set_volume(volume)
    return snd, chan


def start_clip(name, hd_dir):
    base, flags, vol = parse_suffix(name)

    if name in active_clips:
        stop_clip(name)

    clip = Clip(name, base, flags, vol)
    snd, chan = add_looping_audio(name, vol * master_gain, hd_dir)
    clip.active = (snd, chan)
    active_clips[name] = clip

    # --- per-flag behaviours --------------------------------------------
    if "v" in flags:
        others = [c for c in active_clips.values() if c is not clip and "v" in c.flags]
        if others and random.random() < 0.6:
            victim = random.choice(others)
            stop_clip(victim.name)

    if "d" in flags:
        now = time.time()
        for c in active_clips.values():
            if c is clip:
                continue
            c.active[1].set_volume(c.base_vol * 0.5 * master_gain)
            c.duck_end = now + DUCK_TIME

    if "s" in flags:
        for c in active_clips.values():
            if c is not clip:
                c.active[1].set_volume(0.0)

    return clip


def update_clips(dt):
    now = time.time()
    for clip in list(active_clips.values()):
        if clip.duck_end:
            if now >= clip.duck_end:
                clip.active[1].set_volume(clip.base_vol * master_gain)
                clip.duck_end = 0.0
            else:
                t = 1 - (clip.duck_end - now) / DUCK_TIME
                vol = clip.base_vol * (0.5 + 0.5 * t) * master_gain
                clip.active[1].set_volume(vol)

        if "p" in clip.flags:
            clip.pan_phase += random.uniform(-0.2, 0.2) * dt
            clip.pan_phase = max(-1.0, min(1.0, clip.pan_phase))
            left = (1.0 - clip.pan_phase) / 2.0
            right = (1.0 + clip.pan_phase) / 2.0
            clip.active[1].set_volume(left * clip.base_vol * master_gain,
                                     right * clip.base_vol * master_gain)



