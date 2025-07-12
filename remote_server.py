#!/usr/bin/env python3
# LAN-remote controller *and* launcher for the video-looper demo.
# pip install flask

import os, sys, subprocess
from flask import Flask, jsonify, redirect

app = Flask(__name__, static_folder=None)
_command = None            # “next”, “quit”, None  – read-once by the player

# ──────────────────────── minimal HTML UI ───────────────────────────
HTML = """
<!doctype html>
<title>Video Looper Remote</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
/* ───────────── CSS custom properties ───────────── */
:root{
  /* layout */
  --btn-height:100px;

  /* ─── tweak THESE to style the log ─── */
  --log-font-size:24px;        /* any CSS unit */
  --log-font-family:serif; /* or "sans-serif", etc. */
  --log-text-color:#fff;
  --log-bg-color:#000;
  --log-line-height:1.4;
  --log-padding:1rem;
}
/* ───────────────── reset & basics ───────────────── */
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:sans-serif}
/* ───────────────── fixed button bar ─────────────── */
.top-bar{
  position:fixed;top:0;left:0;width:100%;
  height:var(--btn-height);
  display:flex;
  color:white,
}
.top-bar a{flex:1;text-decoration:none}
.top-bar button{
  width:100%;height:100%;
  border:0;border-radius:0;
  color:#fff;font-size:clamp(1rem,40%,2rem);
}

.next,
.quit{
  background:#000;                     
  border:10px solid #fff;          
}

/* ───────────────── log area below bar ───────────── */
.wrapper{
  position:absolute;top:var(--btn-height);left:0;right:0;bottom:0;
}
#log{
  width:100%;height:100%;
  border:none;resize:none;overflow-y:auto;
  font-size:var(--log-font-size);
  font-family:var(--log-font-family);
  color:var(--log-text-color);
  background:var(--log-bg-color);
  line-height:var(--log-line-height);
  padding:var(--log-padding);
}
@media (max-width:320px){
  .top-bar button{font-size:0.9rem}
}
</style>

<div class="top-bar">
  <a href="/next"><button class="next">Perform</button></a>
  <a href="/quit"><button class="quit">Install</button></a>
</div>

<div class="wrapper">
  <p id="log">A voice comes out of nowhere and demands authority. The voice assures us that we have a body. The voice tells us what to do with the image in front of us, what to think and feel. Somewhere far away from this cinematic moment, a leaf blows my face inward while glossing over the crispness of its features. Rather than imploding seriously, the day continues. An unexpected outcome, everything considered. In here, with the image, the whole thing is incredible, like really really amazing and mind blowing. But it lacks vibration. Disappearing under the promise of fulfilment. There are waves. Some might call it a rumble, but that would not be accurate. In this setting it seems more like a hiss on a particularly laboured scale of deep. Still, sine waves enter the subconscious like ceilidh. Volumes of faces, joyous surprise and physical exertion giving gusts of pillowed wind. So much more than the perfectly smooth, endlessly repeating wiggles that they are. The room tilts or is it our heads? There is nothing here. Nothing but bones. Protected bones. A nauseating concert. The voice comes back and reassures us that what we are seeing is in fact what we think we are seeing. “This is a trailer”. I feel reassured, despite the incongruence of language. It never is a trailer. What this is, is more like what we might call the cinematic foreword although it serves the exact opposite purpose of the foreword. In preparation for the experience of cinema, it is our peripheral vision that is appealed to. We are asked to look everywhere but at the thing we have come for. This distraction is worth noticing. We accept the trailer. We even, as I do, love the trailer. We begin with the end. Or rather, we sense everything at once. The distance between us. The amplification of {/* black ballpoint pen on white paper dot */} that particular desire through concentrations of light. The image that moves, the market that pulls, the faces that want. A preamble designed for vibrating bodies. Poems before prose. The voice replaces the face again. Nothing is left of the face. Nothing is left of its intentions except for what our memory has already distorted with the introduction of the next image. Nothing is left of the violence of its wants. Nothing is left of everything it can be reduced to. Nothing is left of the dreams it has of being a different face. We are asked to let awe and wonder take hold. We are made aware of how inseparable the car industry is from cinema. We are present in a materialised dream of an early 20th century Italian futurist, but we call it liberalism, not fascism. I screenshot the cubo-futurist representation of you on my iPhone, we call it a glitch. We talk about the film. It is like a face. We perceive, from its surface, from the light that passes through it, an intention, a feeling, a story. I forgot to say, there is light inside you. No really. That is half of the perception that cinema intends to imitate. One being of course the external light that makes your movements visible, and then two, the inner throw, the origin of those movements, the light that we all perceive without measure. We look at the film. We wear it like a balm. The skin of what we fear. What we see is what has been removed from the surface in varying degrees to create space for us to insert ourselves. Despite Herzog’s propaganda I’ve always thought that Kinski was right when he told him to abandon the landscape for his face. Stop lying to yourself, you know? You have come to look at me you idiot, like everyone else. You wouldn’t be here if it wasn’t for me. There is no limit to the perversity of the director; their mountain of molehill style thinking, their inability to feel anything that is not felt by someone else through what they perceive to be their instruction. But I won’t get stuck on this. I will do as I am told by the trailer. I will follow the light that takes me somewhere else. And one day, with enough courage, we will simply cry into the sun instead of hiding our sadness between paper maché rocks and cameras, in front of mirrors in dressing rooms, beside bedside tables, beneath pillows and duvets, above all. You disagree of course but that is because you are not fixated. I can’t actually tell if it is a complete lack of fixation or a kind of hyperfixation on yourself. Next to you I feel scattered so I try to put the pieces together. Now there is a light behind you. I’m sure of it, in this moment. Don’t turn around. If you look into the camera you can be sure that the light will at least stay behind you, creating something more than a silhouette of dark articulation. Keep moving. Catch the various light sources. You will be illuminated and known. And you should be happy about this. You should be making the most of not only the sun but the street light too, at night. All that energy is there for the taking and who knows for how long. But that is just the living. The part before and after we press record. What about the struggle that mimics all that excess and abundance? Quantifying and materialising time does seem to hollow it out. It’s not a question of time becoming worth less through its removal from the divine in the monotheistic sense of a vulgar materiality, but rather of the feelings that arise from the ways that we are touched by industrialised, militarised time. The reason for this is that the body, our body, is the fullest expression of time and every attempt to model that, chisels out some part to stand in for its form. By ‘fullest expression of time’ I mean the body’s boney, smelly, throat-clearing, painful karate-like presence, just before it strobes into emerald loss. Elaine Scarry writes about the body “on the brink of evanescence, threatened by an impending disappearance”. She is not talking about death-drive. Not about our compulsion to return to a state of inorganic matter, not about natural processes, but about the balance between our senses and our ideas. There is a heaviness to her thinking. I think of it as writing with a body in the room. She wants us to take our senses more seriously. Developing a language of the senses is a project worthy of our time I think I know what I am talking about. It is a project that requires time and attention. It requires being alone and it requires being together. What it doesn’t require is organisation, connection, speed and efficiency. F told me that Mélenchon had spoken at Earth about our right to starlight. I dismissed it and said I don’t know what it means. What politics am I supposed to take from that and who will disagree? In fact, I know exactly what it means. It is terrifying to claim your right to what is truly yours if it is truly shared. Pleasure and sadness come to mind but also imagination, which for Scarry is a mimesis of perception, and if “imagining is a mimesis of perception, then successful imagining will of course come about through the accuracy or acuity of the mimesis.” Imagination is not something that happens automatically when we close our eyes because to accurately imitate perception we have to be with others and we have to trust them. Some call them genies, some call them geniuses. The workings of imagination reveal themselves like the spin of neutrons only at the moment they are observed, after which point they are again indeterminate and obscure to our imagining, until we approach them anew with undivided, individual attention. We look at the film again. We are always re-watching, re-membering let’s say, our bodies.
</p>
</div>

<script>
/* Preserve scroll position of the log textarea across page reloads */
window.addEventListener("DOMContentLoaded", () => {
  const log = document.getElementById("log");
  if (!log) return;

  /* Restore previous scroll position (if any) */
  const saved = sessionStorage.getItem("logScroll");
  if (saved !== null) log.scrollTop = parseInt(saved, 10);

  /* Save position whenever the user scrolls */
  log.addEventListener("scroll", () => {
    sessionStorage.setItem("logScroll", log.scrollTop);
  });
});
</script>
"""



# ────────────────────────────────────────────────────────────────────

@app.get("/")           # phone home-page
def index():
    return HTML

@app.get("/next")       # big green button
def next_cmd():
    global _command
    _command = "next"
    return redirect("/")

@app.get("/quit")       # big red button
def quit_cmd():
    global _command
    _command = "quit"
    return redirect("/")

@app.get("/command")    # polled by player_remote.py
def get_command():
    global _command
    cmd, _command = _command, None     # one-shot read
    return jsonify({"command": cmd})

# ─────────────────────── launch the player once ─────────────────────
def launch_player():
    """Start player_remote.py in a subprocess (same Python)."""
    here = os.path.abspath(os.path.dirname(__file__))
    player = os.path.join(here, "player_remote.py")
    # Pass the server URL via env var in case you ever change port/host
    env = os.environ.copy()
    env["LOOPER_SERVER"] = "http://127.0.0.1:5003/command"
    return subprocess.Popen([sys.executable, player], env=env)

# --------------------------------------------------------------------
if __name__ == "__main__":
    player_proc = launch_player()
    try:
        # 0.0.0.0 so that phones on the same Wi-Fi can reach it
        app.run(host="0.0.0.0", port=5003, debug=False)
    finally:
        # tidy shutdown on Ctrl-C or Quit button
        player_proc.terminate()
