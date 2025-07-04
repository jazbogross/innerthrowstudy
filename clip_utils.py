import os, random, re, time, pygame

# ---------------------------------------------------------------------------
# 1.  Filename parsing utilities
# ---------------------------------------------------------------------------
SUFFIX_RE = re.compile(r"_(?P<flags>[vdhlopr]*)(?P<vol>\d?)$")

def parse_suffix(name):
    """Return (base, flags-set, volume 0-1) from a WAV basename."""
    m = SUFFIX_RE.search(name)
    if not m:                                  # no suffix at all
        return name, set(), 1.0
    flags = set(m.group("flags"))
    vol   = int(m.group("vol") or 10) / 10
    base  = name[:m.start()]
    return base, flags, vol

def resolve_audio_name(base, hd_dir):
    """
    Given a *video* base name (e.g. 'car'),
    return a matching WAV basename *with* suffix if present.
    • Prefer exact match  <base>.wav
    • Otherwise pick randomly from <base>_*.wav
    • Return None if nothing found.
    """
    exact = os.path.join(hd_dir, f"{base}.wav")
    if os.path.exists(exact):
        return base                              # no suffix

    prefix = f"{base}_"
    candidates = [
        os.path.splitext(f)[0]                   # strip '.wav'
        for f in os.listdir(hd_dir)
        if f.lower().endswith(".wav") and f.startswith(prefix)
    ]
    return random.choice(candidates) if candidates else None

# ---------------------------------------------------------------------------
# 2.  Runtime structures
# ---------------------------------------------------------------------------
class Clip:
    def __init__(self, wav_name, base, flags, volume):
        self.wav_name  = wav_name        # basename *with* suffix flags
        self.base      = base            # plain video base
        self.flags     = flags
        self.base_vol  = volume
        self.active    = None            # (Sound, Channel)
        self.loops     = 0
        self.duck_end  = 0.0
        self.pan_phase = 0.0
        self.max_loops = random.randint(1, 100) if "o" in flags else None

# key = *base*, never more than one instance per clip
active_clips = {}
master_gain   = 1.0
DUCK_TIME     = 5.0

# ---------------------------------------------------------------------------
# 3.  Helpers
# ---------------------------------------------------------------------------
def _stop_clip_by_base(base):
    clip = active_clips.pop(base, None)
    if clip and clip.active:
        clip.active[1].stop()
        if "s" in clip.flags:                    # restore after solo
            for other in active_clips.values():
                other.active[1].set_volume(other.base_vol * master_gain)

def _add_looping_audio(wav_name, volume, hd_dir):
    snd  = pygame.mixer.Sound(os.path.join(hd_dir, f"{wav_name}.wav"))
    chan = snd.play(loops=-1, fade_ms=250)
    chan.set_volume(volume)
    return snd, chan

# ---------------------------------------------------------------------------
# 4.  Public entry points
# ---------------------------------------------------------------------------
def start_clip(video_base, hd_dir):
    """
    Launch (or replace) the audio layer for a given *video* base name.
    Looks up an appropriate WAV with suffix flags and applies
    all behaviours (_v, _d, _s, _p, etc.).
    """
    wav_name = resolve_audio_name(video_base, hd_dir)
    if wav_name is None:
        print(f"No WAV found for base '{video_base}'")
        return None

    base, flags, vol = parse_suffix(wav_name)

    # uniqueness rule: one instance per base
    if base in active_clips:
        _stop_clip_by_base(base)

    clip = Clip(wav_name, base, flags, vol)
    snd, chan = _add_looping_audio(wav_name, vol * master_gain, hd_dir)
    clip.active = (snd, chan)
    active_clips[base] = clip

    # ---------------- flag-specific behaviours -------------------------
    if "v" in flags:                                   # variable replacement
        variable_others = [
            c for c in active_clips.values()
            if c is not clip and "v" in c.flags
        ]
        if variable_others and random.random() < 0.6:
            victim = random.choice(variable_others)
            _stop_clip_by_base(victim.base)

    if "d" in flags:                                   # ducking
        now = time.time()
        for c in active_clips.values():
            if c is clip:
                continue
            c.active[1].set_volume(c.base_vol * 0.5 * master_gain)
            c.duck_end = now + DUCK_TIME

    if "s" in flags:                                   # solo
        for c in active_clips.values():
            if c is not clip:
                c.active[1].set_volume(0.0)

    return clip

def update_clips(dt):
    """
    Call every frame (or at least ~30×/s). Handles:
    • fading ducked channels back up
    • generative panning (_p)
    """
    now = time.time()
    for clip in list(active_clips.values()):

        # Ducking recovery
        if clip.duck_end:
            if now >= clip.duck_end:
                clip.active[1].set_volume(clip.base_vol * master_gain)
                clip.duck_end = 0.0
            else:
                t = 1 - (clip.duck_end - now) / DUCK_TIME
                vol = clip.base_vol * (0.5 + 0.5 * t) * master_gain
                clip.active[1].set_volume(vol)

        # Generative panning
        if "p" in clip.flags:
            clip.pan_phase += random.uniform(-0.2, 0.2) * dt
            clip.pan_phase  = max(-1.0, min(1.0, clip.pan_phase))
            left  = (1.0 - clip.pan_phase) / 2.0
            right = (1.0 + clip.pan_phase) / 2.0
            clip.active[1].set_volume(left  * clip.base_vol * master_gain,
                                     right * clip.base_vol * master_gain)
