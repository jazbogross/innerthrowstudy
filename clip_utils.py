"""High‑level audio helper layer for the video‑looper demo.

Audio behaviours are triggered by **suffix flags** appended to a WAV’s *basename*
(put them right before the ``.wav`` extension).  Any order/combination works; an
optional trailing digit ``0‑9`` scales the base volume (0→0.1 … 9→0.9, blank→1.0).

    _v   variable          – may randomly *replace* another _v clip when started
    _d   duck              – drops all other clips to 50 % for ``DUCK_TIME`` seconds
    _s   solo              – mutes every other clip and keeps new ones muted **only while this clip’s video is on‑screen**
    _p   pan               – very‑slow random stereo drift (gentle L↔R wander)
    _o   once‑N            – loops 1‑10× (random N) then stops
    _t   one‑shot          – play exactly once (no looping)
    _h   high‑pass fade    – perceptual HP sweep → silence over ``HP_FADE_MIN``–``HP_FADE_MAX`` s
    _<d> volume digit      – scale clip to *d/10* (e.g. ``_p9`` = 0.9)

``_h`` is implemented by a progressive fade‑out: when layered with other
material, the shrinking spectrum *sounds* like a high‑pass filter.
"""

from __future__ import annotations

import os
import random
import re
import time
from typing import Optional, Set, Tuple, Dict

import pygame

# ---------------------------------------------------------------------------
# 0.  Tunable timing / level constants (edit here)
# ---------------------------------------------------------------------------
DUCK_TIME: float      = 10.0    # seconds other clips stay ducked
HP_FADE_MIN: float    = 30.0    # min duration of high‑pass fade‑out
HP_FADE_MAX: float    = 120.0   # max duration of high‑pass fade‑out
PLAY_FADE_MS: int     = 200    # fade‑in when a clip starts (ms)
STOP_FADE_MS: int     = 300    # fade‑out when a clip is stopped (ms)
PAN_JITTER: float     = 1.2    # ± range of random pan drift per frame

master_gain: float    = 1.0    # global gain slider (0‑1)

# ---------------------------------------------------------------------------
# 1.  Filename‑parsing utilities
# ---------------------------------------------------------------------------
SUFFIX_RE = re.compile(r"_(?P<flags>[vdhoprst]*)(?P<vol>\d?)$", re.IGNORECASE)


def _safe_volume(raw: str) -> float:
    if not raw:
        return 1.0
    d = max(1, min(int(raw), 10))
    return d / 10.0


def parse_suffix(name: str) -> Tuple[str, Set[str], float]:
    m = SUFFIX_RE.search(name)
    if not m:
        return name, set(), 1.0
    base = name[: m.start()]
    flags = set(m.group("flags").lower())
    vol = _safe_volume(m.group("vol"))
    return base, flags, vol

# ---------------------------------------------------------------------------
# 2.  Find matching WAV for a video‑basename
# ---------------------------------------------------------------------------

def resolve_audio_name(base: str, hd_dir: str) -> Optional[str]:
    base_lc = base.lower()
    wavs = [f for f in os.listdir(hd_dir) if f.lower().endswith(".wav")]

    # exact match first
    for f in wavs:
        if os.path.splitext(f)[0].lower() == base_lc:
            return os.path.splitext(f)[0]

    pref = f"{base_lc}_"
    cands = [os.path.splitext(f)[0] for f in wavs if os.path.splitext(f)[0].lower().startswith(pref)]
    return random.choice(cands) if cands else None

# ---------------------------------------------------------------------------
# 3.  Runtime clip structure
# ---------------------------------------------------------------------------
class Clip:
    def __init__(self, wav_name: str, base: str, flags: Set[str], vol: float):
        self.wav_name = wav_name
        self.base = base
        self.flags = flags
        self.base_vol = vol
        self.active: Optional[Tuple[pygame.mixer.Sound, pygame.mixer.Channel]] = None

        # ducking / panning / filter state
        self.duck_end: float = 0.0
        self.pan_phase: float = 0.0

        # finite looping
        self.max_loops: Optional[int] = random.randint(1, 10) if "o" in flags else None

        # high‑pass fade
        if "h" in flags:
            self.fade_start = time.time()
            self.fade_dur = random.uniform(HP_FADE_MIN, HP_FADE_MAX)
        else:
            self.fade_start = 0.0
            self.fade_dur = 0.0

    @property
    def chan(self) -> Optional[pygame.mixer.Channel]:
        return None if self.active is None else self.active[1]

# key: plain video‑basename
active_clips: Dict[str, Clip] = {}
solo_owner: Optional[str] = None   # base name of current solo clip (if any)

# ---------------------------------------------------------------------------
# 4.  Low‑level helpers
# ---------------------------------------------------------------------------

def _restore_all_volumes():
    for c in active_clips.values():
        if c.chan:
            c.chan.set_volume(c.base_vol * master_gain)

def _stop_clip_by_base(base: str):
    global solo_owner
    clip = active_clips.pop(base, None)
    if not clip or not clip.chan:
        return
    clip.chan.fadeout(STOP_FADE_MS)

    # if this was the solo owner, un‑mute others
    if base == solo_owner:
        solo_owner = None
        _restore_all_volumes()

def _add_audio(wav_name: str, gain: float, hd_dir: str, loops: int) -> Tuple[pygame.mixer.Sound, Optional[pygame.mixer.Channel]]:
    snd = pygame.mixer.Sound(os.path.join(hd_dir, f"{wav_name}.wav"))
    chan = snd.play(loops=loops, fade_ms=PLAY_FADE_MS)
    if chan:
        chan.set_volume(gain)
    return snd, chan

# ---------------------------------------------------------------------------
# 5.  Public API
# ---------------------------------------------------------------------------

def start_clip(video_base: str, hd_dir: str) -> Optional[Clip]:
    global solo_owner

    # If a previous solo is active and a different video is starting, release it
    if solo_owner and solo_owner != video_base and solo_owner in active_clips:
        _stop_clip_by_base(solo_owner)

    wav_name = resolve_audio_name(video_base, hd_dir)
    if wav_name is None:
        print(f"[audio] missing wav for {video_base}")
        return None

    base, flags, vol = parse_suffix(wav_name)

    if base in active_clips:
        _stop_clip_by_base(base)

    clip = Clip(wav_name, base, flags, vol)

    # loop semantics
    if "t" in flags:
        loops = 0
    elif "o" in flags:
        loops = (clip.max_loops or 1) - 1
    else:
        loops = -1

    snd, chan = _add_audio(wav_name, vol * master_gain, hd_dir, loops)
    clip.active = (snd, chan)
    active_clips[base] = clip

    # variable replacement (_v)
    if "v" in flags:
        vs = [c for c in active_clips.values() if c is not clip and "v" in c.flags]
        if vs and random.random() < 0.6:
            _stop_clip_by_base(random.choice(vs).base)

    # ducking (_d)
    if "d" in flags:
        now = time.time()
        for c in active_clips.values():
            if c is clip or not c.chan:
                continue
            c.chan.set_volume(c.base_vol * 0.5 * master_gain)
            c.duck_end = now + DUCK_TIME

    # SOLO (_s)
    if "s" in flags:
        solo_owner = base
        for c in active_clips.values():
            if c is clip or not c.chan:
                continue
            c.chan.set_volume(0.0)
    else:
        if solo_owner and solo_owner in active_clips and clip.chan:
            clip.chan.set_volume(0.0)

    return clip

# ---------------------------------------------------------------------------
# 6.  Per‑frame update
# ---------------------------------------------------------------------------

def update_clips(dt: float):
    now = time.time()
    for base, clip in list(active_clips.items()):
        chan = clip.chan
        if not chan:
            continue

        # auto‑remove finished finite loops
        if not chan.get_busy() and ("t" in clip.flags or "o" in clip.flags):
            _stop_clip_by_base(base)
            continue

        # duck recovery
        duck_mul = 1.0
        if clip.duck_end:
            if now >= clip.duck_end:
                clip.duck_end = 0.0
            else:
                x = 1.0 - (clip.duck_end - now) / DUCK_TIME
                duck_mul = 0.5 + 0.5 * x

        # high‑pass fade
        filt_mul = 1.0
        if clip.fade_dur:
            t = (now - clip.fade_start) / clip.fade_dur
            if t >= 1.0:
                _stop_clip_by_base(base)
                continue
            filt_mul = 1.0 - t  # linear fade perceived as HP sweep

        # Stereo panning
        if "p" in clip.flags:
            clip.pan_phase += random.uniform(-PAN_JITTER, PAN_JITTER) * dt
            clip.pan_phase = max(-1.0, min(1.0, clip.pan_phase))
        
            left  = (1.0 - clip.pan_phase) * 0.5               # 0…1
            right = (1.0 + clip.pan_phase) * 0.5
        
            chan.set_volume(
                left  * clip.base_vol * duck_mul * filt_mul * master_gain,
                right * clip.base_vol * duck_mul * filt_mul * master_gain,
            )
        else:
            chan.set_volume(clip.base_vol * duck_mul * filt_mul * master_gain)

# ---------------------------------------------------------------------------
# 7.  Convenience helpers
# ---------------------------------------------------------------------------

def stop_all(fade_ms: int = STOP_FADE_MS):
    """Fade‑out and clear every active clip."""
    for b in list(active_clips.keys()):
        _stop_clip_by_base(b)
    # make sure global solo flag is cleared
    global solo_owner
    solo_owner = None

