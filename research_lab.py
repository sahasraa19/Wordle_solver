# ============================================================
# POKÉMON WORDLE · RESEARCH LAB  —  RETRO PIXEL EDITION
# ------------------------------------------------------------
# Same project, same logic: a Game Boy Color "title screen"
# theme (night-sky blue, amber pixel lettering, teal horizon,
# dialog boxes, HP bars and Silver/Emerald pixel sprites).
#
# Every game rule, solver call, dataset load and benchmark
# calculation is the project's own code; only the presentation
# layer is new. Run it exactly like the original:
#     streamlit run research_lab_retro.py
# ============================================================

import os
import html
import math

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from loader import load_pokemon
from engine import Game, MAX_GUESSES
from basic_solvers import random_solver, filter_solver, filter_candidates
from entropy_solver import EntropySolver
from minimax_solver import MinimaxSolver


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "pokemon.csv")
RESULTS = os.path.join(ROOT, "results")

POKEMON = load_pokemon(DATA)
BY_NAME = {p["name"]: p for p in POKEMON}
NAMES = sorted(BY_NAME)

st.set_page_config(
    page_title="Pokémon Wordle · Research Lab",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# SMALL COMPATIBILITY HELPERS (work on old and new Streamlit)
# ============================================================

def _stretch_kwargs():
    """Full-width kwargs for buttons across Streamlit versions."""
    try:
        import inspect
        params = inspect.signature(st.button).parameters
        if "width" in params:
            return {"width": "stretch"}
    except (TypeError, ValueError):
        pass
    return {"use_container_width": True}


STRETCH = _stretch_kwargs()


def show_df(data, **kwargs):
    """Full-width, index-less dataframe on any Streamlit version."""
    try:
        return st.dataframe(data, width="stretch", hide_index=True, **kwargs)
    except Exception:
        return st.dataframe(
            data, use_container_width=True, hide_index=True, **kwargs
        )


# ============================================================
# POKÉMON ARTWORK  (pixel sprites that match the theme)
# ============================================================

ART_IDS = {
    "Bulbasaur": 1, "Ivysaur": 2, "Venusaur": 3,
    "Charmander": 4, "Charmeleon": 5, "Charizard": 6,
    "Squirtle": 7, "Wartortle": 8, "Blastoise": 9,
    "Pikachu": 25, "Raichu": 26, "Jigglypuff": 39,
    "Vulpix": 37, "Psyduck": 54, "Growlithe": 58,
    "Arcanine": 59, "Gengar": 94, "Eevee": 133,
    "Vaporeon": 134, "Jolteon": 135, "Flareon": 136,
    "Snorlax": 143, "Dratini": 147, "Dragonite": 149,
    "Mewtwo": 150, "Mew": 151, "Togepi": 175,
    "Mareep": 179, "Espeon": 196, "Umbreon": 197,
    "Piplup": 393, "Pachirisu": 417, "Lucario": 448,
    "Leafeon": 470, "Glaceon": 471, "Sylveon": 700,
    "Rowlet": 722, "Mimikyu": 778, "Grookey": 810,
    "Scorbunny": 813, "Sobble": 816,
    "Sprigatito": 906, "Fuecoco": 909, "Quaxly": 912,
}

SPRITE_BASE = (
    "https://raw.githubusercontent.com/PokeAPI/sprites/master/"
    "sprites/pokemon/"
)

# The dataset is stored in National Pokédex order, so a species' row
# position is its Pokédex number. That is verified against the known
# IDs above; if the check ever fails, only the explicit IDs are used.
_POSITIONAL = {p["name"]: i + 1 for i, p in enumerate(POKEMON)}
_known = [n for n in ART_IDS if n in _POSITIONAL]
DEX_ID = (
    _POSITIONAL
    if _known and all(_POSITIONAL[n] == ART_IDS[n] for n in _known)
    else {}
)


def pokemon_id(name):
    return ART_IDS.get(name) or DEX_ID.get(name)


def sprite_info(pid):
    """(url, native pixel size): Silver sprites for Gen 1-2, Emerald for
    Gen 3, and the standard front sprite for anything newer."""
    if pid <= 251:
        return (SPRITE_BASE
                + f"versions/generation-ii/silver/transparent/{pid}.png", 56)
    if pid <= 386:
        return SPRITE_BASE + f"versions/generation-iii/emerald/{pid}.png", 64
    return SPRITE_BASE + f"{pid}.png", 96


def pokemon_url(name):
    pid = pokemon_id(name)
    return sprite_info(pid)[0] if pid else None


# ============================================================
# HTML HELPERS
# ============================================================

def H(markup):
    """Collapse indented markup to one line so Markdown never turns
    indentation or blank lines into code blocks."""
    return "".join(line.strip() for line in markup.strip().splitlines())


def esc(value):
    return html.escape(str(value))


def md(markup):
    st.markdown(H(markup), unsafe_allow_html=True)


# ---------- pixel art drawn from tiny ASCII bitmaps ----------

def _pixels(rows, palette, size, cls="", label=None):
    h = len(rows)
    w = max(len(r) for r in rows)
    rects = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            ch = row[x]
            if ch in palette:
                start = x
                while x + 1 < len(row) and row[x + 1] == ch:
                    x += 1
                rects.append(
                    f'<rect x="{start}" y="{y}" width="{x - start + 1}" '
                    f'height="1" fill="{palette[ch]}"/>'
                )
            x += 1
    aria = f'role="img" aria-label="{esc(label)}"' if label else 'aria-hidden="true"'
    return (
        f'<svg class="pxi {cls}" viewBox="0 0 {w} {h}" width="{size}" '
        f'height="{round(size * h / w)}" shape-rendering="crispEdges" '
        f'{aria}>{"".join(rects)}</svg>'
    )


BALL_ROWS = [
    ".....kkkkkk.....",
    "...kkrrrrrrkk...",
    "..krrRRrrrrrrk..",
    ".krrRrrrrrrrrrk.",
    ".krRrrrrrrrrrrk.",
    "krrrrrrrrrrrrrrk",
    "krrrrrkkkkrrrrrk",
    "kkkkkkkwwkkkkkkk",
    "kkkkkkkwwkkkkkkk",
    "kwwwwwkkkkwwwwwk",
    "kwwwwwwwwwwwwwwk",
    "kwwwwwwwwwwwwggk",
    ".kwwwwwwwwwwggk.",
    ".kwwwwwwwwwgggk.",
    "..kkgwwwwgggkk..",
    ".....kkkkkk.....",
]
BALL_PAL = {"k": "#0B1030", "r": "#E84040", "R": "#FF9A9A",
            "w": "#FFFFFF", "g": "#B8BCCC"}


def pokeball(size=48, cls=""):
    """A pixel-art Poké Ball."""
    return _pixels(BALL_ROWS, BALL_PAL, size, f"pball {cls}")


ICONS = {
    "home": ["...aa...", "..aaaa..", ".aaaaaa.", "aaaaaaaa",
             ".bbbbbb.", ".bb..bb.", ".bb..bb.", ".bbbbbb."],
    "bot": ["...bb...", ".aaaaaa.", "aabaabaa", "aaaaaaaa",
            "aabbbbaa", ".aaaaaa.", "..a..a..", ".aa..aa."],
    "chart": ["........", "......aa", "......aa", ".aa...aa",
              ".aa.aaaa", ".aa.aaaa", "aaaaaaaa", "aaaaaaaa"],
    "book": [".aaaaaa.", "abbbbbba", "abaaaaba", "abbbbbba",
             "abaaaaba", "abbbbbba", "abbbbbba", ".aaaaaa."],
    "star": ["...aa...", "...aa...", "aaaaaaaa", ".aaaaaa.",
             "..aaaa..", ".aaaaaa.", ".aa..aa.", "a......a"],
    "heart": [".aa..aa.", "aaaaaaaa", "aaaaaaaa", "aaaaaaaa",
              ".aaaaaa.", "..aaaa..", "...aa...", "........"],
    "target": ["..aaaa..", ".a....a.", "a..aa..a", "a.abba.a",
               "a.abba.a", "a..aa..a", ".a....a.", "..aaaa.."],
    "search": [".aaaa...", "a....a..", "a....a..", "a....a..",
               ".aaaa...", "....aa..", ".....aa.", "......aa"],
    "trophy": ["aaaaaaaa", "a.aaaa.a", "a.aaaa.a", ".aaaaaa.",
               "..aaaa..", "...aa...", "..aaaa..", ".aaaaaa."],
    "shield": ["aaaaaaaa", "abbbbbba", "abbbbbba", "abbbbbba",
               ".abbbba.", "..abba..", "...aa...", "........"],
    "play": [".a......", ".aaa....", ".aaaaa..", ".aaaaaaa",
             ".aaaaa..", ".aaa....", ".a......", "........"],
    "dice": ["aaaaaaa", "ab...ba", "a.....a", "a..b..a",
             "a.....a", "ab...ba", "aaaaaaa"],
    "funnel": ["aaaaaaaa", ".aaaaaa.", "..aaaa..", "...aa...",
               "...aa...", "...aa...", "........", "........"],
    "arrow": ["a.....", "aa....", "aaa...", "aaaa..",
              "aaa...", "aa....", "a....."],
    "sparkle": ["...a...", "...a...", "..aaa..", "aaaaaaa",
                "..aaa..", "...a...", "...a..."],
}


def px_icon(name, size=28, a="#F8B020", b="#0B1030", cls=""):
    return _pixels(ICONS[name], {"a": a, "b": b}, size, cls)


def art_img(name, size=96, cls=""):
    """Pixel sprite scaled by a whole number (falls back to a Poké Ball)."""
    pid = pokemon_id(name)
    if not pid:
        return pokeball(int(size * 0.7), cls)
    url, native = sprite_info(pid)
    scale = max(1, round(size / native))
    px = native * scale
    return (
        f'<img class="art {cls}" src="{url}" alt="{esc(name)}" '
        f'width="{px}" height="{px}" loading="lazy" decoding="async">'
    )


# ============================================================
# TYPE COLOURS (flat GBC-style chips with dark ink)
# ============================================================

TYPE_COLORS = {
    "Normal": "#C8C8A8", "Fire": "#F8A058", "Water": "#88B0F8",
    "Electric": "#F8E058", "Grass": "#98D878", "Ice": "#A0E8E0",
    "Fighting": "#E08070", "Poison": "#C890D8", "Ground": "#E8D090",
    "Flying": "#B8B0F8", "Psychic": "#F89CC0", "Bug": "#C0D860",
    "Rock": "#C8B870", "Ghost": "#A898C8", "Dragon": "#A888F8",
    "Dark": "#A89890", "Steel": "#C0C8D8", "Fairy": "#F8B8D8",
}


def type_chip(type_name):
    if not type_name or str(type_name) == "None":
        return '<span class="chip chip-none">—</span>'
    bg = TYPE_COLORS.get(str(type_name), "#D8DCF0")
    return f'<span class="chip" style="background:{bg}">{esc(type_name)}</span>'


def type_chips(pokemon):
    return type_chip(pokemon.get("type1")) + type_chip(pokemon.get("type2"))


# ============================================================
# RETRO THEME
# ============================================================

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Pixelify+Sans:wght@400;500;600;700&display=swap');

:root {
  --ink: #0B1030;
  --sky: #1D3597;
  --sky-2: #2C4DC4;
  --amber: #F8B020;
  --amber-d: #B86F00;
  --gold: #FFD060;
  --panel: #FFFFFF;
  --edge: #C8D0F0;
  --txt: #0B1030;
  --txt-2: #26306A;
  --mut: #4A5490;
  --red: #E84040;
  --f-head: 'Press Start 2P', 'Courier New', monospace;
  --f-body: 'Pixelify Sans', 'VT323', 'Courier New', monospace;
}

html, body, .stApp, [class*="css"] {
  font-family: var(--f-body);
  color: var(--txt);
  -webkit-font-smoothing: none;
}

/* ---------- the night-sky title-screen scene ---------- */
.stApp {
  background:
    linear-gradient(to bottom,
      #1D3597 0, #1D3597 54%,
      #2A5FA8 54%, #2A5FA8 55.5%,
      #1F6475 55.5%, #1F6475 59%,
      #174F5C 59%, #174F5C 62%,
      #0F353F 62%, #0F353F 65%,
      #07161B 65%, #07161B 67%,
      #000000 67%, #000000 100%);
  background-attachment: fixed;
  font-size: 17px;
}

.block-container {
  max-width: 1200px;
  padding: 1.2rem 1.4rem 3.5rem;
  position: relative;
  z-index: 1;
}

#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
[data-testid="stAppDeployButton"], .stAppDeployButton { display: none; }

.fx { position: fixed; inset: 0; z-index: -1; pointer-events: none;
  overflow: hidden; }
.fx .dz { position: absolute; left: 0; right: 0; height: 8px;
  background: repeating-conic-gradient(var(--a) 0 25%, var(--b) 0 50%)
              0 0 / 8px 8px; }
[data-testid="stElementContainer"]:has(> .stMarkdown .fx),
.element-container:has(> .stMarkdown .fx) {
  position: absolute; height: 0; margin: 0; padding: 0;
}

.pxs { position: absolute; width: 4px; height: 4px; background: #fff;
  box-shadow: 4px 0 #fff, -4px 0 #fff, 0 4px #fff, 0 -4px #fff;
  animation: tw 2.4s steps(2) var(--dl, 0s) infinite; }
.pxs.a { background: var(--gold);
  box-shadow: 4px 0 var(--gold), -4px 0 var(--gold),
              0 4px var(--gold), 0 -4px var(--gold); }
@keyframes tw { 0%, 100% { opacity: 1; } 50% { opacity: .2; } }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
@keyframes bob { 0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); } }
@keyframes drift { from { transform: translateX(0); }
  to { transform: translateX(46%); } }
@keyframes rise { from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: none; } }
@keyframes hpgrow { from { width: 0; } to { width: var(--w); } }
@keyframes pop { 0% { transform: scale(.85); opacity: 0; }
  100% { transform: scale(1); opacity: 1; } }

img.art, .pxi { image-rendering: pixelated; }
img.art { object-fit: fill !important; max-width: none !important; }

/* ---------- brand ---------- */
.brand { display: flex; justify-content: center; align-items: center;
  gap: 18px; padding: 4px 0 4px; animation: rise .5s steps(5) both; }
.brand .pball { animation: bob 2.4s steps(2) infinite;
  filter: drop-shadow(4px 4px 0 rgba(0, 0, 0, .5)); }
.brand-name {
  font-family: var(--f-head); font-size: 1.9rem; line-height: 1.2;
  color: var(--amber);
  text-shadow: 3px 0 0 #1840A8, -3px 0 0 #1840A8, 0 3px 0 #1840A8,
    0 -3px 0 #1840A8, 3px 3px 0 #1840A8, -3px -3px 0 #1840A8,
    3px -3px 0 #1840A8, -3px 3px 0 #1840A8, 6px 6px 0 var(--ink);
}
.brand-tiles { display: flex; gap: 6px; margin-top: 12px; }
.brand-tiles b {
  width: 26px; height: 26px; display: grid; place-items: center;
  font-family: var(--f-head); font-size: .62rem; color: var(--ink);
  background: var(--bg); box-shadow: 0 0 0 3px var(--ink),
    inset 0 -4px 0 rgba(0, 0, 0, .2), inset 0 3px 0 rgba(255, 255, 255, .45);
}
.plate {
  display: inline-block; font-family: var(--f-head); font-size: .62rem;
  letter-spacing: .12em; color: #fff; background: #6A7196;
  padding: 7px 12px; box-shadow: 0 0 0 3px #2B3157;
  text-shadow: 2px 2px 0 #2B3157;
}
.sub-line { text-align: center; color: #DCE4FF; font-family: var(--f-head);
  font-size: .5rem; letter-spacing: .12em; margin: 14px 0 12px;
  text-shadow: 2px 2px 0 var(--ink); line-height: 1.8; }

/* ---------- navigation ---------- */
.st-key-nav, .st-key-nav [data-testid="stRadio"] { width: 100% !important; }
.st-key-nav div[role="radiogroup"] {
  display: flex; flex-direction: row; flex-wrap: wrap;
  justify-content: center; gap: 14px;
}
.st-key-nav [data-testid="stRadioOption"] > div > div:first-child {
  display: none;
}
.st-key-nav label {
  position: relative; margin: 4px; padding: 12px 16px 12px 16px;
  background: #D8DCF8; cursor: pointer;
  box-shadow: 0 0 0 4px var(--ink), inset 0 -5px 0 #9AA2D0,
              inset 0 3px 0 #fff, 6px 6px 0 4px rgba(0, 0, 0, .45);
  transition: transform .1s steps(2);
}
.st-key-nav label:hover { transform: translate(-2px, -3px); background: #fff; }
.st-key-nav label p {
  font-family: var(--f-head); font-size: .6rem; letter-spacing: .02em;
  color: var(--ink); margin: 0; text-transform: uppercase; line-height: 1.5;
}
.st-key-nav label:has(input:checked) {
  background: var(--amber); padding-left: 32px;
  box-shadow: 0 0 0 4px var(--ink), inset 0 -5px 0 var(--amber-d),
              inset 0 3px 0 #FFE9A8, 6px 6px 0 4px rgba(0, 0, 0, .45);
}
.st-key-nav label:has(input:checked)::before {
  content: ""; position: absolute; left: 12px; top: 50%;
  width: 10px; height: 14px; margin-top: -7px; background: var(--ink);
  clip-path: polygon(0 0, 100% 50%, 0 100%);
  animation: blink 1s steps(2) infinite;
}

.divider { height: 4px; margin: 22px 0 30px;
  background: repeating-linear-gradient(90deg, var(--amber) 0 12px,
              transparent 12px 24px); opacity: .9; }

/* ---------- hero / title screen ---------- */
.hero {
  position: relative; overflow: hidden; display: grid;
  grid-template-columns: 1.2fr 1fr; gap: 10px; margin: 14px 10px 40px;
  padding: 34px 36px 0; min-height: 300px;
  background: linear-gradient(to bottom,
      #1D3597 0, #1D3597 56%, #2A5FA8 56%, #2A5FA8 58%,
      #1F6475 58%, #1F6475 64%, #174F5C 64%, #174F5C 68%,
      #0F353F 68%, #0F353F 71%, #000 71%, #000 100%);
  box-shadow: 0 0 0 4px var(--ink), 0 0 0 8px var(--edge),
              0 0 0 12px var(--ink), 18px 18px 0 12px rgba(0, 0, 0, .45);
  animation: rise .5s steps(6) both;
}
.hero.home { min-height: 470px; }
.hero .left { position: relative; z-index: 2; padding-bottom: 40px; }
.eyebrow { display: inline-block; font-family: var(--f-head); font-size: .56rem;
  letter-spacing: .08em; color: var(--ink); background: var(--gold);
  padding: 8px 12px; box-shadow: 0 0 0 3px var(--ink); margin-bottom: 18px; }
.ht {
  font-family: var(--f-head); font-weight: 400; line-height: 1.55;
  font-size: clamp(1.15rem, 2.4vw, 1.9rem); color: var(--amber);
  margin: 6px 0 16px;
  text-shadow: 3px 0 0 #1840A8, -3px 0 0 #1840A8, 0 3px 0 #1840A8,
    0 -3px 0 #1840A8, 3px 3px 0 #1840A8, -3px -3px 0 #1840A8,
    3px -3px 0 #1840A8, -3px 3px 0 #1840A8, 6px 6px 0 var(--ink);
}
.ht em { font-style: normal; color: #fff; }
.hero p.lead { color: #fff; font-size: 1.15rem; line-height: 1.55;
  max-width: 540px; margin: 0 0 16px; font-weight: 500;
  text-shadow: 2px 2px 0 var(--ink); }
.hero .scene { position: relative; min-height: 260px; }
.hero.home .scene { min-height: 400px; }
.hero .scene img.main { position: absolute; left: 50%; bottom: 3%;
  margin-left: -112px; animation: bob 1.6s steps(2) infinite;
  filter: drop-shadow(8px 8px 0 rgba(0, 0, 0, .5)); }
.hero .scene img.main.sm { margin-left: -84px; }
.hero .scene img.lugia { position: absolute; left: 6%; top: 12%; width: 168px;
  filter: brightness(0) opacity(.78); animation: drift 11s steps(44) infinite alternate; }
.hero .pxs { z-index: 1; }

.pill { display: inline-block; margin: 4px 10px 6px 3px; padding: 8px 10px;
  font-family: var(--f-head); font-size: .5rem; line-height: 1.3;
  color: var(--ink); box-shadow: 0 0 0 3px var(--ink); }
.pill.pink { background: #FF9890; }
.pill.lav { background: #B8A8F8; }
.pill.mint { background: #7FDB8A; }
.pill.peach { background: #FFC070; }
.pill.blue { background: #8CB8FF; }

.chip { display: inline-block; margin: 3px 6px 3px 2px; padding: 5px 8px;
  font-family: var(--f-head); font-size: .46rem; text-transform: uppercase;
  color: var(--ink); box-shadow: 0 0 0 2px var(--ink); line-height: 1.2; }
.chip-none { background: #E4E7F6; }

/* ---------- panels (GBC dialog boxes) ---------- */
.k-card {
  position: relative; height: 100%; margin: 4px 4px 8px; padding: 22px 24px;
  background: var(--panel); color: var(--txt);
  box-shadow: 0 -4px 0 0 var(--ink), 0 4px 0 0 var(--ink),
              -4px 0 0 0 var(--ink), 4px 0 0 0 var(--ink),
              inset 0 0 0 4px var(--edge);
  filter: drop-shadow(6px 6px 0 rgba(0, 0, 0, .5));
  transition: transform .12s steps(2);
  animation: rise .45s steps(5) both;
}
.k-card:hover { transform: translate(-2px, -3px); }
.k-card h3 { font-family: var(--f-head); font-weight: 400; font-size: .85rem;
  line-height: 1.6; color: var(--txt); margin: 0 0 8px; padding: 0; }
.k-card p { margin: 6px 0 0; color: var(--txt-2); line-height: 1.5;
  font-size: 1.05rem; font-weight: 500; }
.k-card .tagline { font-family: var(--f-head); font-size: .5rem; line-height: 1.6;
  color: #A04800; }
.k-card.sel { background: #FFF3CC;
  box-shadow: 0 -4px 0 0 var(--ink), 0 4px 0 0 var(--ink),
              -4px 0 0 0 var(--ink), 4px 0 0 0 var(--ink),
              inset 0 0 0 4px var(--amber); }

.sec-title { display: flex; align-items: center; gap: 14px;
  margin: 44px 0 20px; font-family: var(--f-head); font-size: 1.05rem;
  line-height: 1.5; color: #fff; text-shadow: 3px 3px 0 var(--ink); }
.sec-title .orn { display: inline-flex; animation: blink 1.2s steps(2) infinite; }
.sec-title::after { content: ""; flex: 1; height: 4px;
  background: repeating-linear-gradient(90deg, var(--amber) 0 8px,
              transparent 8px 16px); }

/* nav cards */
.nav-card .top { display: flex; justify-content: space-between;
  align-items: flex-start; margin-bottom: 10px; }
.nav-card .ibox { width: 60px; height: 60px; display: grid; place-items: center;
  background: var(--tint, #FFC070); box-shadow: 0 0 0 3px var(--ink),
    inset 0 -4px 0 rgba(0, 0, 0, .2), inset 0 3px 0 rgba(255, 255, 255, .5); }
.nav-card img.art { animation: bob 1.8s steps(2) infinite; }

/* ---------- metrics ---------- */
.mbox { position: relative; display: flex; align-items: center; gap: 16px;
  margin: 4px; padding: 18px 20px; min-height: 108px; background: var(--panel);
  box-shadow: 0 -4px 0 0 var(--ink), 0 4px 0 0 var(--ink),
              -4px 0 0 0 var(--ink), 4px 0 0 0 var(--ink),
              inset 0 0 0 4px var(--edge);
  filter: drop-shadow(6px 6px 0 rgba(0, 0, 0, .5));
  transition: transform .12s steps(2); animation: rise .45s steps(5) both; }
.mbox:hover { transform: translate(-2px, -3px); }
.mbox .ic { flex: none; width: 58px; height: 58px; display: grid;
  place-items: center; background: var(--tint, #FFC070);
  box-shadow: 0 0 0 3px var(--ink), inset 0 -4px 0 rgba(0, 0, 0, .2),
              inset 0 3px 0 rgba(255, 255, 255, .5); }
.mbox small { display: block; font-family: var(--f-head); font-size: .5rem;
  line-height: 1.5; color: var(--mut); text-transform: uppercase; }
.mbox b { display: block; font-family: var(--f-head); font-weight: 400;
  font-size: 1.1rem; line-height: 1.5; color: #A04800; margin: 4px 0 2px;
  overflow-wrap: anywhere; }
.mbox span.sub { display: block; font-size: .95rem; color: var(--txt-2);
  font-weight: 500; }
.tone-pink { --tint: #FF9890; }
.tone-lav { --tint: #B8A8F8; }
.tone-peach { --tint: #FFC070; }
.tone-blue { --tint: #8CB8FF; }
.tone-mint { --tint: #7FDB8A; }

/* ---------- HP / EXP bars ---------- */
.hp { display: flex; align-items: center; gap: 10px; margin: 4px 4px 10px; }
.hp-tag { font-family: var(--f-head); font-size: .55rem; color: #fff;
  background: var(--ink); padding: 8px 8px; line-height: 1;
  box-shadow: 0 0 0 3px var(--ink); }
.hp-track { flex: 1; height: 22px; padding: 4px; background: #fff;
  box-shadow: 0 0 0 4px var(--ink), 6px 6px 0 4px rgba(0, 0, 0, .45); }
.hp-track i { display: block; height: 100%; width: var(--w);
  background: var(--hc, #3CB043);
  box-shadow: inset 0 -4px 0 rgba(0, 0, 0, .28),
              inset 0 3px 0 rgba(255, 255, 255, .45);
  animation: hpgrow 1s steps(18); }
.hp-g { --hc: #3CB043; } .hp-y { --hc: #F8D030; } .hp-r { --hc: #E84040; }
.hp-exp { --hc: #4878F8; }
.hp-lab { display: flex; justify-content: space-between; margin: 4px 6px 8px;
  font-family: var(--f-head); font-size: .5rem; line-height: 1.6; color: #fff;
  text-shadow: 2px 2px 0 var(--ink); }

.balls { display: flex; gap: 8px; flex-wrap: wrap; margin: 6px 4px 12px; }
.balls .pball { filter: drop-shadow(3px 3px 0 rgba(0, 0, 0, .5)); }
.balls .pball.used { filter: grayscale(1) brightness(.55); opacity: .75; }

/* ---------- clue tiles ---------- */
.guess-row { display: grid; grid-template-columns: minmax(200px, 270px) 1fr;
  gap: 18px; align-items: center; margin: 14px 4px; padding: 14px 18px;
  background: var(--panel);
  box-shadow: 0 -4px 0 0 var(--ink), 0 4px 0 0 var(--ink),
              -4px 0 0 0 var(--ink), 4px 0 0 0 var(--ink),
              inset 0 0 0 4px var(--edge);
  filter: drop-shadow(6px 6px 0 rgba(0, 0, 0, .5));
  animation: pop .25s steps(3) both; }
.guess-who { display: flex; align-items: center; gap: 12px; }
.guess-who .nm { font-family: var(--f-head); font-size: .72rem; line-height: 1.6;
  color: var(--txt); }
.guess-who .mt { font-size: .95rem; font-weight: 600; color: var(--mut); }
.tiles { display: flex; gap: 12px; flex-wrap: wrap; }
.tile { flex: 1 1 90px; min-width: 90px; margin: 3px; padding: 10px 4px 9px;
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; text-align: center; background: var(--tb);
  color: var(--ink);
  box-shadow: 0 0 0 4px var(--ink), inset 0 -6px 0 rgba(0, 0, 0, .2),
              inset 0 4px 0 rgba(255, 255, 255, .5);
  transition: transform .1s steps(2); }
.tile:hover { transform: translateY(-4px); }
.tile small { font-family: var(--f-head); font-size: .46rem; line-height: 1.6;
  text-transform: uppercase; }
.tile b { font-family: var(--f-head); font-weight: 400; font-size: 1.15rem;
  line-height: 1.4; }
.tile span { font-weight: 700; font-size: .9rem; }
.t-green { --tb: #7FDB8A; } .t-amber { --tb: #F8D030; }
.t-grey { --tb: #C8CCDC; } .t-up { --tb: #8CB8FF; } .t-down { --tb: #FF9890; }

/* ---------- dialog / result ---------- */
.result-card { position: relative; display: flex; align-items: center;
  gap: 24px; flex-wrap: wrap; margin: 14px 6px 22px; padding: 22px 28px 30px;
  background: #fff; color: var(--txt);
  box-shadow: 0 -4px 0 0 var(--ink), 0 4px 0 0 var(--ink),
              -4px 0 0 0 var(--ink), 4px 0 0 0 var(--ink),
              inset 0 0 0 4px var(--tone, var(--edge));
  filter: drop-shadow(6px 6px 0 rgba(0, 0, 0, .5));
  animation: pop .3s steps(3) both; }
.result-card.win { --tone: #3CB043; }
.result-card.lose { --tone: #E84040; }
.result-card::after { content: ""; position: absolute; right: 22px; bottom: 12px;
  width: 16px; height: 11px; background: var(--ink);
  clip-path: polygon(0 0, 100% 0, 50% 100%);
  animation: blink 1s steps(2) infinite; }
.result-card h3 { font-family: var(--f-head); font-weight: 400; font-size: 1rem;
  line-height: 1.6; margin: 0; color: var(--txt); }
.result-card p { margin: 8px 0 0; color: var(--txt-2); font-size: 1.12rem;
  font-weight: 500; }
.result-card img.art { animation: bob 1.8s steps(2) infinite; }

.mystery { text-align: center; padding: 20px 14px 22px; height: 100%;
  margin: 4px; background: #fff;
  box-shadow: 0 -4px 0 0 var(--ink), 0 4px 0 0 var(--ink),
              -4px 0 0 0 var(--ink), 4px 0 0 0 var(--ink),
              inset 0 0 0 4px var(--edge);
  filter: drop-shadow(6px 6px 0 rgba(0, 0, 0, .5)); }
.mystery .qb { position: relative; display: inline-block;
  animation: bob 1.4s steps(2) infinite; }
.mystery .qb .q { position: absolute; right: -14px; top: -14px; width: 30px;
  height: 30px; display: grid; place-items: center; background: var(--gold);
  color: var(--ink); font-family: var(--f-head); font-size: .8rem;
  box-shadow: 0 0 0 3px var(--ink); }
.mystery .big { font-family: var(--f-head); font-size: .7rem; line-height: 1.7;
  color: var(--txt); margin-top: 12px; }
.mystery small { color: var(--mut); font-weight: 600; font-size: 1rem; }

.selected-card { display: flex; align-items: center; gap: 14px; margin: 4px;
  padding: 14px 18px; background: #fff;
  box-shadow: 0 -4px 0 0 var(--ink), 0 4px 0 0 var(--ink),
              -4px 0 0 0 var(--ink), 4px 0 0 0 var(--ink),
              inset 0 0 0 4px var(--edge);
  filter: drop-shadow(6px 6px 0 rgba(0, 0, 0, .5)); }
.selected-card .nm { font-family: var(--f-head); font-size: .75rem;
  line-height: 1.6; color: var(--txt); }
.selected-card .st { font-weight: 600; color: var(--mut); font-size: 1rem; }

/* ---------- strategy / battle ---------- */
.strat { text-align: center; padding: 18px 14px 16px; min-height: 330px; }
.strat img.art { animation: bob 1.8s steps(2) infinite; }
.strat h3 { margin-top: 6px; font-size: .75rem; }
.strat p { font-size: 1rem; }
.turn-card { display: grid; grid-template-columns: auto 1fr auto; gap: 18px;
  align-items: center; margin: 16px 4px; padding: 16px 22px; background: #fff;
  box-shadow: 0 -4px 0 0 var(--ink), 0 4px 0 0 var(--ink),
              -4px 0 0 0 var(--ink), 4px 0 0 0 var(--ink),
              inset 0 0 0 4px var(--edge);
  filter: drop-shadow(6px 6px 0 rgba(0, 0, 0, .5));
  animation: pop .25s steps(3) both; }
.turn-card .nm { font-family: var(--f-head); font-size: 1rem; line-height: 1.6;
  color: var(--txt); margin: 6px 0; }
.turn-card .remain { text-align: center; padding: 12px 16px; background: #FFF3CC;
  box-shadow: 0 0 0 3px var(--ink); min-width: 130px; }
.turn-card .remain b { display: block; font-family: var(--f-head); font-weight: 400;
  font-size: 1.5rem; color: #A04800; line-height: 1.4; }
.turn-card .remain small { font-family: var(--f-head); font-size: .44rem;
  line-height: 1.6; color: var(--txt-2); text-transform: uppercase; }
.tiles-wrap { margin: 6px 0 20px; }

.fun-row { display: grid; grid-template-columns: 56px 150px 1fr 70px; gap: 12px;
  align-items: center; margin: 12px 0; }
.fun-row .nm { font-family: var(--f-head); font-size: .56rem; line-height: 1.5;
  color: var(--txt); }
.fun-row .nm small { display: block; color: var(--mut); font-size: .46rem; }
.fun-row .val { font-family: var(--f-head); font-size: .8rem; text-align: right;
  color: #A04800; }

/* ---------- bar charts ---------- */
.brow { display: grid; grid-template-columns: 150px 1fr 96px; gap: 14px;
  align-items: center; margin: 14px 0; }
.brow .nm { font-family: var(--f-head); font-size: .6rem; line-height: 1.5;
  color: var(--txt); }
.btrack { height: 26px; padding: 4px; background: #fff;
  box-shadow: 0 0 0 3px var(--ink); }
.bfill { height: 100%; width: var(--w); background-color: var(--c1);
  background-image: repeating-linear-gradient(90deg, transparent 0 14px,
                    rgba(11, 16, 48, .3) 14px 16px);
  box-shadow: inset 0 -4px 0 rgba(0, 0, 0, .22),
              inset 0 3px 0 rgba(255, 255, 255, .45);
  animation: hpgrow 1s steps(18); }
.brow .val { font-family: var(--f-head); font-size: .7rem; text-align: right;
  color: var(--txt); }
.c0 { --c1: #F8A020; } .c1 { --c1: #4878F8; } .c2 { --c1: #3CB043; }
.c3 { --c1: #E84040; } .c4 { --c1: #A878F0; }

.lb { text-align: left; padding: 20px 22px; min-height: 270px; }
.lb .rank { position: absolute; left: 16px; top: 14px; }
.lb img.art { position: absolute; right: 10px; top: 8px;
  animation: bob 1.8s steps(2) infinite; }
.lb .who { margin-top: 56px; font-family: var(--f-head); font-size: .8rem;
  line-height: 1.6; color: var(--txt); }
.lb .main { font-family: var(--f-head); font-size: 1.5rem; line-height: 1.5;
  color: #A04800; }
.lb .main small { display: block; font-size: .46rem; color: var(--mut); margin: 2px 0 0;
  text-transform: uppercase; }
.lb .kv { display: grid; grid-template-columns: 1fr auto; gap: 6px 10px;
  margin-top: 12px; font-size: .98rem; font-weight: 600; color: var(--txt-2); }
.lb .kv b { color: var(--txt); text-align: right; }
.rankn { display: inline-grid; place-items: center; width: 32px; height: 32px;
  font-family: var(--f-head); font-size: .75rem; color: #fff;
  background: #6A7196; box-shadow: 0 0 0 3px var(--ink); }

/* ---------- pokédex grid ---------- */
.dex-grid { display: grid; gap: 22px; padding: 4px;
  grid-template-columns: repeat(auto-fill, minmax(176px, 1fr)); }
.dex-card { position: relative; text-align: center; padding: 14px 10px 14px;
  background: #fff;
  box-shadow: 0 -4px 0 0 var(--ink), 0 4px 0 0 var(--ink),
              -4px 0 0 0 var(--ink), 4px 0 0 0 var(--ink),
              inset 0 0 0 4px var(--edge);
  filter: drop-shadow(6px 6px 0 rgba(0, 0, 0, .5));
  transition: transform .12s steps(2); animation: rise .4s steps(5) both; }
.dex-card:hover { transform: translate(-2px, -4px); }
.dex-card .no { position: absolute; left: 12px; top: 10px;
  font-family: var(--f-head); font-size: .44rem; color: var(--mut); }
.dex-card .gen { position: absolute; right: 12px; top: 8px;
  font-family: var(--f-head); font-size: .42rem; color: var(--ink);
  background: #B8A8F8; padding: 4px 5px; box-shadow: 0 0 0 2px var(--ink); }
.dex-card .pic { margin: 22px auto 6px; width: 128px; height: 128px;
  display: grid; place-items: center; background: #D6E4FF;
  box-shadow: 0 0 0 3px var(--ink), inset 0 0 0 3px #fff; }
.dex-card .nm { font-family: var(--f-head); font-size: .6rem; line-height: 1.6;
  color: var(--txt); margin-top: 8px; }
.dex-card .ms { font-size: .95rem; font-weight: 600; color: var(--mut); }

.detail-grid { display: grid; grid-template-columns: repeat(2, 1fr);
  gap: 14px; margin-top: 14px; }
.detail-grid div { padding: 10px 14px; background: #EEF1FF;
  box-shadow: 0 0 0 3px var(--ink); }
.detail-grid small { display: block; font-family: var(--f-head); font-size: .44rem;
  color: var(--mut); text-transform: uppercase; line-height: 1.6; }
.detail-grid b { font-family: var(--f-head); font-weight: 400; font-size: .8rem;
  color: var(--txt); line-height: 1.6; }

.legend { display: grid; gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); }
.legend .tile { flex-direction: row; justify-content: flex-start; gap: 10px;
  padding: 10px 12px; text-align: left; }
.legend .tile span { font-size: .9rem; line-height: 1.2; }
.steps { display: grid; gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); }
.steps .stp { padding: 14px 16px; background: #EEF1FF;
  box-shadow: 0 0 0 3px var(--ink); }
.steps .stp .n { display: inline-grid; place-items: center; width: 30px; height: 30px;
  font-family: var(--f-head); font-size: .7rem; color: var(--ink);
  background: var(--amber); box-shadow: 0 0 0 3px var(--ink); margin-bottom: 10px; }
.steps .stp b { display: block; font-family: var(--f-head); font-weight: 400;
  font-size: .6rem; line-height: 1.7; color: var(--txt); }
.steps .stp span { color: var(--txt-2); font-weight: 500; font-size: 1rem; }

.note { display: flex; gap: 16px; align-items: flex-start; margin: 6px 4px;
  padding: 16px 20px; background: #fff; color: var(--txt);
  box-shadow: 0 -4px 0 0 var(--ink), 0 4px 0 0 var(--ink),
              -4px 0 0 0 var(--ink), 4px 0 0 0 var(--ink),
              inset 0 0 0 4px #8CB8FF;
  filter: drop-shadow(6px 6px 0 rgba(0, 0, 0, .5)); font-weight: 500;
  font-size: 1.08rem; line-height: 1.5; }
.empty { text-align: center; padding: 34px 20px; margin: 6px 4px;
  background: #fff;
  box-shadow: 0 -4px 0 0 var(--ink), 0 4px 0 0 var(--ink),
              -4px 0 0 0 var(--ink), 4px 0 0 0 var(--ink),
              inset 0 0 0 4px var(--edge);
  filter: drop-shadow(6px 6px 0 rgba(0, 0, 0, .5)); }
.empty .big { font-family: var(--f-head); font-size: .8rem; line-height: 1.7;
  color: var(--txt); margin-top: 14px; }
.empty p { color: var(--txt-2); font-weight: 500; margin: 6px 0 0; }

.footer { text-align: center; padding: 8px 0 6px; color: #fff;
  font-family: var(--f-head); font-size: .58rem; line-height: 2;
  text-shadow: 2px 2px 0 var(--ink); }
.footer small { display: block; color: var(--gold); font-size: .46rem;
  margin-top: 4px; }

/* ---------- Streamlit widgets ---------- */
[data-testid="stBaseButton-primary"], .stButton > button[kind="primary"] {
  background: var(--amber) !important; color: var(--ink) !important;
  border: 0 !important; border-radius: 0 !important;
  padding: 1rem 1rem !important; margin: 4px;
  box-shadow: 0 0 0 4px var(--ink), inset 0 -6px 0 var(--amber-d),
              inset 0 4px 0 #FFE9A8, 6px 6px 0 4px rgba(0, 0, 0, .45) !important;
  transition: transform .1s steps(2) !important;
}
[data-testid="stBaseButton-primary"]:hover,
.stButton > button[kind="primary"]:hover {
  background: var(--gold) !important; transform: translate(-2px, -3px) !important;
}
[data-testid="stBaseButton-primary"]:active,
.stButton > button[kind="primary"]:active {
  transform: translate(2px, 3px) !important;
  box-shadow: 0 0 0 4px var(--ink), inset 0 -2px 0 var(--amber-d) !important;
}
[data-testid="stBaseButton-secondary"], .stButton > button[kind="secondary"],
.stDownloadButton > button {
  background: #D8DCF8 !important; color: var(--ink) !important;
  border: 0 !important; border-radius: 0 !important;
  padding: 1rem 1rem !important; margin: 4px;
  box-shadow: 0 0 0 4px var(--ink), inset 0 -6px 0 #9AA2D0,
              inset 0 4px 0 #fff, 6px 6px 0 4px rgba(0, 0, 0, .45) !important;
  transition: transform .1s steps(2) !important;
}
[data-testid="stBaseButton-secondary"]:hover,
.stButton > button[kind="secondary"]:hover, .stDownloadButton > button:hover {
  background: #fff !important; transform: translate(-2px, -3px) !important;
}
[data-testid="stBaseButton-secondary"]:active,
.stButton > button[kind="secondary"]:active, .stDownloadButton > button:active {
  transform: translate(2px, 3px) !important;
}
.stButton > button:disabled, .stDownloadButton > button:disabled {
  opacity: .55 !important; transform: none !important; filter: grayscale(.6); }
.stButton button p, .stDownloadButton button p {
  font-family: var(--f-head) !important; font-size: .62rem !important;
  line-height: 1.6 !important; margin: 0 !important; color: var(--ink) !important;
  text-transform: uppercase;
}

[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stTextInput"] [data-baseweb="input"],
[data-testid="stTextInput"] [data-baseweb="base-input"] {
  background: #fff !important; border: 0 !important; border-radius: 0 !important;
  box-shadow: 0 0 0 4px var(--ink), inset 0 4px 0 #E4E8FA !important;
  color: var(--ink) !important; font-family: var(--f-body) !important;
  font-size: 1.1rem !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within,
[data-testid="stTextInput"] [data-baseweb="input"]:focus-within {
  box-shadow: 0 0 0 4px var(--amber), 0 0 0 8px var(--ink) !important;
}
[data-testid="stSelectbox"] div:has(> input), [data-testid="stTextInput"] div:has(> input),
[data-testid="stSelectbox"] div:has(> div > input) {
  background: #fff !important; border-radius: 0 !important; }
[data-testid="stSelectbox"] div:has(> div > input), [data-testid="stTextInput"] div:has(> div > input) {
  box-shadow: 0 0 0 4px var(--ink), inset 0 4px 0 #E4E8FA !important; }
[data-testid="stSelectbox"] [data-baseweb="select"] * { color: var(--ink) !important; }
[data-testid="stSelectbox"] input, [data-testid="stTextInput"] input {
  color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important;
}
[data-testid="stSelectbox"] svg { fill: var(--ink) !important; }
[data-testid="stWidgetLabel"] p, label[data-testid="stWidgetLabel"] {
  font-family: var(--f-head) !important; font-size: .56rem !important;
  line-height: 1.8 !important; color: #fff !important;
  text-shadow: 2px 2px 0 var(--ink); text-transform: uppercase;
}
[data-baseweb="popover"] ul, [data-baseweb="menu"] {
  border-radius: 0 !important; background: #fff !important; }
[data-baseweb="popover"] li { color: var(--ink) !important; }

[data-testid="stExpander"] { background: #fff; border: 0 !important;
  border-radius: 0 !important; margin: 6px 4px;
  box-shadow: 0 0 0 4px var(--ink), inset 0 0 0 4px var(--edge),
              6px 6px 0 4px rgba(0, 0, 0, .45); }
[data-testid="stExpander"] summary { font-family: var(--f-head);
  font-size: .6rem; color: var(--ink); text-transform: uppercase; }
[data-testid="stExpander"] summary p { color: var(--ink) !important; }
[data-testid="stExpander"] details > div { color: var(--txt); }

[data-testid="stDataFrame"] { margin: 6px 4px; border-radius: 0;
  box-shadow: 0 0 0 4px var(--ink), 6px 6px 0 4px rgba(0, 0, 0, .45); }
[data-testid="stAlert"] { border-radius: 0; box-shadow: 0 0 0 4px var(--ink); }
[data-testid="stAlert"] p { color: var(--ink) !important; font-weight: 600; }
[data-testid="stSpinner"] { color: #fff; font-family: var(--f-head);
  font-size: .6rem; text-shadow: 2px 2px 0 var(--ink); }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
  color: #DCE4FF !important; font-weight: 600; opacity: 1 !important;
  text-shadow: 2px 2px 0 var(--ink); font-size: 1rem;
}
[data-testid="stSlider"] [data-testid="stTickBarMin"],
[data-testid="stSlider"] [data-testid="stTickBarMax"],
[data-testid="stSlider"] [data-testid="stThumbValue"] {
  color: #fff !important; font-family: var(--f-head); font-size: .56rem; }

.st-key-an_view [data-testid="stRadioOption"] {
  background: #D8DCF8; padding: 10px 16px; margin: 4px 8px 4px 4px; cursor: pointer;
  box-shadow: 0 0 0 4px var(--ink), inset 0 -4px 0 #9AA2D0,
              inset 0 3px 0 #fff; }
.st-key-an_view [role="radiogroup"] { gap: 14px; flex-wrap: wrap; }
.st-key-an_view [data-testid="stRadioOption"] > div > div:first-child {
  display: none; }
.st-key-an_view [data-testid="stRadioOption"]:has(input:checked) {
  background: var(--amber);
  box-shadow: 0 0 0 4px var(--ink), inset 0 -4px 0 var(--amber-d),
              inset 0 3px 0 #FFE9A8; }
.st-key-an_view [data-testid="stRadioOption"] p {
  color: var(--ink) !important; font-family: var(--f-head);
  font-size: .55rem; line-height: 1.6; text-transform: uppercase; }

hr { border-color: rgba(248, 176, 32, .5); }

/* ---------- responsive ---------- */
@media (max-width: 860px) {
  .hero, .hero.home { grid-template-columns: 1fr; padding: 26px 20px 0;
    margin: 14px 8px 34px; }
  .hero .scene, .hero.home .scene { min-height: 260px; }
  .guess-row { grid-template-columns: 1fr; }
  .turn-card { grid-template-columns: auto 1fr; }
  .turn-card .remain { grid-column: 1 / -1; }
  .brow { grid-template-columns: 96px 1fr 70px; gap: 8px; }
  .fun-row { grid-template-columns: 44px 100px 1fr 54px; gap: 8px; }
  .brand-name { font-size: 1.25rem; }
  .sec-title { font-size: .8rem; }
  .mbox { margin-bottom: 14px; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important;
    transition: none !important; }
}
</style>
"""

st.markdown(THEME_CSS, unsafe_allow_html=True)


def decor_layer():
    """Fixed night-sky stars and dithered horizon bands behind the app."""
    stars = [
        (6, 7, "", 0), (14, 21, "a", .7), (23, 5, "", 1.2), (31, 32, "", .3),
        (40, 11, "a", 1.8), (52, 4, "", .9), (61, 27, "", 1.5),
        (70, 9, "a", .2), (78, 35, "", 1.1), (86, 6, "", .6),
        (92, 25, "a", 1.9), (48, 41, "", .4), (9, 44, "", 1.3),
        (96, 45, "", .8), (66, 45, "a", 1.0),
    ]
    bands = [
        (54, "#1D3597", "#2A5FA8"), (55.5, "#2A5FA8", "#1F6475"),
        (59, "#1F6475", "#174F5C"), (62, "#174F5C", "#0F353F"),
        (65, "#0F353F", "#07161B"), (67, "#07161B", "#000000"),
    ]
    parts = [
        f'<span class="pxs {cls}" style="left:{x}%;top:{y}%;--dl:{d}s"></span>'
        for x, y, cls, d in stars
    ]
    parts += [
        f'<div class="dz" style="top:calc({y}% - 4px);--a:{a};--b:{b}"></div>'
        for y, a, b in bands
    ]
    md('<div class="fx" aria-hidden="true">' + "".join(parts) + "</div>")


decor_layer()


# ============================================================
# REUSABLE COMPONENTS
# ============================================================

CLUE_LABELS = ["Generation", "Type 1", "Type 2", "Height", "Weight"]
CLUE_SHORT = ["Gen", "Type 1", "Type 2", "Height", "Weight"]

CLUE_STYLE = {
    "green": ("t-green", "✓", "Match"),
    "amber": ("t-amber", "◆", "Other slot"),
    "grey": ("t-grey", "✕", "No match"),
    "up": ("t-up", "↑", "Higher"),
    "down": ("t-down", "↓", "Lower"),
}


def section_title(text):
    md(
        f'<div class="sec-title"><span class="orn">{px_icon("arrow", 20)}</span>'
        f'<span>{esc(text)}</span></div>'
    )


def stars_html(spots):
    return "".join(
        f'<span class="pxs {cls}" style="left:{x}%;top:{y}%;--dl:{d}s"></span>'
        for x, y, cls, d in spots
    )


HERO_STARS = [(6, 8, "", 0), (22, 16, "a", .6), (38, 7, "", 1.1),
              (52, 20, "", .3), (66, 9, "a", 1.4), (80, 18, "", .8),
              (92, 8, "", 1.7), (14, 34, "", 1.2), (74, 38, "a", .2)]


def hero(kicker, title, subtitle, art=None, chips=()):
    """Page hero banner styled as a little title screen."""
    pills = "".join(
        f'<span class="pill {tone}">{esc(label)}</span>'
        for label, tone in chips
    )
    scene = ""
    if art:
        scene = (
            '<div class="scene">'
            f'{art_img(art, 168, "main sm")}</div>'
        )
    md(
        '<section class="hero">'
        f'{stars_html(HERO_STARS)}'
        '<div class="left">'
        f'<span class="eyebrow">{esc(kicker)}</span>'
        f'<div class="ht" role="heading" aria-level="1">{title}</div>'
        f'<p class="lead">{esc(subtitle)}</p>{pills}</div>{scene}</section>'
    )


def metric(label, value, sub="", icon="star", tone="pink"):
    md(
        f'<div class="mbox tone-{tone}"><div class="ic">'
        f'{px_icon(icon, 34)}</div><div>'
        f'<small>{esc(label)}</small><b>{esc(value)}</b>'
        f'<span class="sub">{esc(sub)}</span></div></div>'
    )


def clue_tile(label, value):
    key = str(value).lower()
    css, symbol, word = CLUE_STYLE.get(key, ("t-grey", "•", str(value)))
    return (
        f'<div class="tile {css}" title="{esc(label)}: {esc(word)}">'
        f'<small>{esc(label)}</small><b>{symbol}</b><span>{esc(word)}</span>'
        '</div>'
    )


def clue_tiles(clue):
    return '<div class="tiles">' + "".join(
        clue_tile(label, value) for label, value in zip(CLUE_SHORT, clue)
    ) + "</div>"


def pokemon_art(name, caption=None, width=190):
    """Large sprite with an optional caption."""
    cap = (
        f'<div style="font-family:var(--f-head);font-size:.6rem;'
        f'color:#fff;margin-top:8px">{esc(caption)}</div>' if caption else ""
    )
    md(f'<div style="text-align:center">{art_img(name, width)}{cap}</div>')


def safe_types(pokemon):
    return (
        f"{pokemon.get('type1', '—')} / "
        f"{pokemon.get('type2') or '—'}"
    )


def render_clue_history(history):
    for idx, (guess, clue) in enumerate(history, 1):
        md(
            '<div class="guess-row">'
            '<div class="guess-who">'
            f'{art_img(guess["name"], 112)}'
            '<div>'
            f'<div class="nm">{idx}. {esc(guess["name"]).upper()}</div>'
            f'<div>{type_chips(guess)}</div>'
            f'<div class="mt">Generation {esc(guess["gen"])}</div>'
            '</div></div>'
            f'{clue_tiles(clue)}</div>'
        )


def hp_class(fraction):
    return "hp-g" if fraction > 0.5 else ("hp-y" if fraction > 0.2 else "hp-r")


def hp_bar(fraction, tag="HP", left="", right="", kind=None):
    """Pokémon-style HP bar (green / yellow / red) or EXP bar (kind='hp-exp')."""
    fraction = max(0.0, min(1.0, fraction))
    kind = kind or hp_class(fraction)
    labels = ""
    if left or right:
        labels = (
            f'<div class="hp-lab"><span>{esc(left)}</span>'
            f'<span>{esc(right)}</span></div>'
        )
    md(
        f'{labels}<div class="hp"><span class="hp-tag">{esc(tag)}</span>'
        f'<div class="hp-track"><i class="{kind}" '
        f'style="--w:{fraction * 100:.1f}%"></i></div></div>'
    )


def attempt_balls(used, total):
    balls = "".join(
        pokeball(34, "used" if i < used else "") for i in range(total)
    )
    md(f'<div class="balls" role="img" aria-label="{total - used} of '
       f'{total} attempts left">{balls}</div>')


def bar_chart(rows, unit="", decimals=2, tone_offset=0, max_value=None):
    """Segmented retro bars. rows = [(label, value), ...]."""
    values = [v for _, v in rows]
    top = max_value or (max(values) if values else 1) or 1
    out = []
    for i, (label, value) in enumerate(rows):
        width = max(3.0, value / top * 100)
        tone = (i + tone_offset) % 5
        out.append(
            '<div class="brow">'
            f'<div class="nm">{esc(label)}</div>'
            f'<div class="btrack"><div class="bfill c{tone}" '
            f'style="--w:{width:.1f}%"></div></div>'
            f'<div class="val">{value:.{decimals}f}{esc(unit)}</div></div>'
        )
    return "".join(out)


def fmt_num(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.2f}".rstrip("0").rstrip(".")


def go(label):
    """Navigation callback used by the home-page cards."""
    st.session_state["nav"] = label


def init_session():
    defaults = {
        "human_game": None,
        "human_games_played": 0,
        "human_games_won": 0,
        "human_total_guesses": 0,
        "human_best": None,
        "last_battle": None,
        "battle_step": 0,
        "human_celebrated": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session()


@st.cache_resource(show_spinner="Warming up the AI strategist…")
def get_solver(strategy):
    """Build (and cache) the matrix-based solvers once per server."""
    if strategy == "Entropy":
        return EntropySolver(POKEMON)
    if strategy == "Minimax":
        return MinimaxSolver(POKEMON)
    return None


# ============================================================
# TOP BRANDING AND NAVIGATION
# ============================================================

LOGO_TILES = [
    ("W", "#FF9890"), ("O", "#B8A8F8"), ("R", "#FFC070"),
    ("D", "#8CB8FF"), ("L", "#7FDB8A"), ("E", "#F8D030"),
]
logo_tiles = "".join(
    f'<b style="--bg:{bg}">{letter}</b>' for letter, bg in LOGO_TILES
)

md(
    '<div class="brand">'
    f'{pokeball(72)}'
    '<div><div class="brand-name">POKÉMON</div>'
    f'<div class="brand-tiles">{logo_tiles}</div></div>'
    '</div>'
    '<div style="text-align:center;margin-top:14px">'
    '<span class="plate">RESEARCH LAB</span></div>'
    '<div class="sub-line">★ PROFESSOR OAK’S INTELLIGENCE LABORATORY ★</div>'
)

PAGE_DEFS = [
    ("Home", "Welcome Hub"),
    ("Pokédex Challenge", "Pokédex Challenge"),
    ("AI Battle Arena", "AI Battle Arena"),
    ("Analytics", "Professor’s Analytics"),
    ("Dataset Explorer", "Dataset Explorer"),
]
NAV_LABELS = [label for label, _ in PAGE_DEFS]
page_map = {label: page for label, page in PAGE_DEFS}
NAV = {page: label for label, page in PAGE_DEFS}

if st.session_state.get("nav") not in NAV_LABELS:
    st.session_state["nav"] = NAV_LABELS[0]

selected_page = st.radio(
    "Navigation",
    NAV_LABELS,
    horizontal=True,
    label_visibility="collapsed",
    key="nav",
)

md('<div class="divider"></div>')

page = page_map[selected_page]


# ============================================================
# WELCOME HUB
# ============================================================

if page == "Welcome Hub":

    n_gen = len(set(p["gen"] for p in POKEMON))

    md(
        '<section class="hero home">'
        f'{stars_html(HERO_STARS)}'
        '<div class="left">'
        '<span class="eyebrow">★ WELCOME, TRAINER ★</span>'
        '<div class="ht" role="heading" aria-level="1">'
        'Welcome to the <em>Pokémon</em> World!</div>'
        '<p class="lead">A world of mystery, intelligent guessing and '
        'Pokémon discovery. Explore the Pokédex, challenge yourself and '
        'watch AI strategies compete.</p>'
        f'<span class="pill pink">{len(POKEMON)} species</span>'
        f'<span class="pill lav">{n_gen} generations</span>'
        f'<span class="pill mint">{MAX_GUESSES} guesses per mystery</span>'
        '<span class="pill peach">4 AI strategies</span></div>'
        '<div class="scene">'
        f'{art_img("Lugia", 168, "lugia")}'
        f'{art_img("Pikachu", 224, "main")}</div></section>'
    )

    cta1, cta2, cta3 = st.columns([1.1, 1.1, 1.4])
    with cta1:
        st.button(
            "Start the Challenge", type="primary", key="cta_play",
            on_click=go, args=(NAV["Pokédex Challenge"],), **STRETCH,
        )
    with cta2:
        st.button(
            "Watch an AI Battle", key="cta_battle",
            on_click=go, args=(NAV["AI Battle Arena"],), **STRETCH,
        )

    section_title("Trainer Crew")
    roster = ["Eevee", "Pikachu", "Vulpix", "Togepi", "Espeon"]
    cols = st.columns(len(roster))
    for col, name in zip(cols, roster):
        with col:
            pid = pokemon_id(name)
            md(
                '<div class="k-card" style="text-align:center;'
                'padding:16px 10px">'
                f'{art_img(name, 112)}'
                f'<div style="font-family:var(--f-head);font-size:.6rem;'
                f'line-height:1.8;color:#0B1030;margin-top:8px">'
                f'{esc(name).upper()}</div>'
                f'<div style="font-family:var(--f-head);font-size:.44rem;'
                f'color:#4A5490">No. {pid:03d}</div></div>'
            )

    section_title("Research Lab Overview")

    stats = [
        ("Pokémon indexed", len(POKEMON), "Species in the dataset", "ball", "pink"),
        ("Generations", n_gen, "Across the Pokédex", "star", "lav"),
        ("Clue dimensions", len(CLUE_LABELS), "Attributes used by the game", "search", "peach"),
        ("Guess limit", MAX_GUESSES, "Attempts per mystery", "target", "blue"),
    ]
    cols = st.columns(4)
    for col, item in zip(cols, stats):
        with col:
            if item[3] == "ball":
                md(
                    f'<div class="mbox tone-{item[4]}"><div class="ic">'
                    f'{pokeball(36)}</div><div><small>{esc(item[0])}</small>'
                    f'<b>{esc(item[1])}</b>'
                    f'<span class="sub">{esc(item[2])}</span></div></div>'
                )
            else:
                metric(*item)

    section_title("Explore the Laboratory")

    cards = [
        ("ball", "Pokédex Challenge", "Human vs Mystery",
         "Solve a hidden Pokémon using five clue dimensions.",
         "Eevee", "pink", "Pokédex Challenge"),
        ("bot", "AI Battle Arena", "Intelligent Guessing",
         "Watch four strategies investigate the same mystery.",
         "Gengar", "lav", "AI Battle Arena"),
        ("chart", "Analytics", "Performance Insights",
         "Compare measured results from benchmark experiments.",
         "Mew", "peach", "Professor’s Analytics"),
        ("book", "Dataset Explorer", "Pokédex Collection",
         "Search, filter and inspect the real dataset.",
         "Togepi", "blue", "Dataset Explorer"),
    ]
    cols = st.columns(4)
    for col, (ico, title, tagline, desc, mascot, tone, target) in zip(cols, cards):
        with col:
            icon_html = (
                pokeball(38) if ico == "ball" else px_icon(ico, 36)
            )
            md(
                f'<div class="k-card nav-card tone-{tone}">'
                f'<div class="top"><div class="ibox">{icon_html}</div>'
                f'{art_img(mascot, 112)}</div>'
                f'<h3>{esc(title).upper()}</h3>'
                f'<span class="tagline">{esc(tagline).upper()}</span>'
                f'<p>{esc(desc)}</p></div>'
            )
            st.button(
                f"Open {title}", key=f"open_{target}",
                on_click=go, args=(NAV[target],), **STRETCH,
            )

    section_title("Inside the Research Laboratory")

    left, right = st.columns([1.5, 1])
    with left:
        md(
            '<div class="k-card"><h3>HOW A MYSTERY IS SOLVED</h3>'
            '<p>Every guess returns five clues. The laboratory\'s four '
            'strategies and your own detective skills all play by the '
            'same rules.</p>'
            '<div class="steps" style="margin-top:16px">'
            '<div class="stp"><div class="n">1</div><b>MAKE A GUESS</b>'
            '<span>Pick any Pokémon from the Pokédex.</span></div>'
            '<div class="stp"><div class="n">2</div><b>READ THE CLUES</b>'
            '<span>Generation, both types, height and weight.</span></div>'
            '<div class="stp"><div class="n">3</div><b>NARROW IT DOWN</b>'
            f'<span>Find the secret within {MAX_GUESSES} guesses.</span>'
            '</div></div></div>'
        )
    with right:
        bench_path = os.path.join(RESULTS, "results_table.csv")
        glimpse = None
        if os.path.exists(bench_path):
            try:
                bdf = pd.read_csv(bench_path)
                if {"Solver", "Avg guesses"}.issubset(bdf.columns):
                    top = bdf.loc[bdf["Avg guesses"].idxmin()]
                    glimpse = (str(top["Solver"]), float(top["Avg guesses"]))
            except Exception:
                glimpse = None
        if glimpse:
            md(
                '<div class="k-card"><span class="tagline">LATEST SAVED BENCHMARK</span>'
                f'<h3 style="margin-top:8px">{esc(glimpse[0]).upper()} LEADS THE LAB</h3>'
                f'<p>Lowest average in the saved results: '
                f'<b style="color:#A04800">{glimpse[1]:.2f} guesses</b>. '
                'Open Analytics for the full scoreboard.</p></div>'
            )
        else:
            md(
                '<div class="k-card"><span class="tagline">BENCHMARKS</span>'
                '<h3 style="margin-top:8px">NO SAVED RESULTS YET</h3>'
                '<p>Run benchmark.py to generate results_table.csv and '
                'unlock the Analytics lab.</p></div>'
            )

    section_title("Trainer Statistics")

    played = st.session_state.human_games_played
    won = st.session_state.human_games_won
    win_rate = won / played * 100 if played else 0

    cols = st.columns(3)

    with cols[0]:
        metric("Games completed", played, "Current session", "play", "pink")

    with cols[1]:
        metric("Mysteries solved", won, "Current session", "trophy", "mint")

    with cols[2]:
        metric("Win rate", f"{win_rate:.1f}%", "Current session", "heart", "lav")

    md('<div style="height:18px"></div>')
    md(
        f'<div class="note"><div>{px_icon("sparkle", 28, "#4878F8")}</div>'
        '<div><b>How to play:</b> '
        'feedback compares generation, primary type, secondary type, height '
        "and weight. Numeric clues use the engine's ±10% tolerance. Each "
        f'game allows up to {MAX_GUESSES} guesses.</div></div>'
    )


# ============================================================
# POKÉDEX CHALLENGE
# ============================================================

elif page == "Pokédex Challenge":

    hero(
        "FIELD TEST 01 · HUMAN VS MYSTERY",
        "Who's That <em>Pokémon?</em>",
        "Think carefully, follow the clues and identify the hidden Pokémon "
        "before your attempts run out.",
        art="Eevee",
        chips=[(f"{len(POKEMON)} species", "pink"),
               (f"{MAX_GUESSES} guesses max", "lav"),
               ("5 clue dimensions", "mint")],
    )

    if st.session_state.human_game is None:
        st.session_state.human_game = Game(POKEMON)
        st.session_state.human_celebrated = False

    game = st.session_state.human_game

    if game.status != "playing":

        section_title("Mystery Complete")

        secret_name = game.secret["name"]

        if game.status == "won":
            if not st.session_state.human_celebrated:
                st.balloons()
                st.session_state.human_celebrated = True
            md(
                '<div class="result-card win">'
                f'{art_img(secret_name, 168)}'
                '<div><h3>YOU FOUND '
                f'{esc(secret_name).upper()}!</h3>'
                f'<p>Solved in {len(game.history)} of {MAX_GUESSES} '
                'guesses. What a brilliant trainer!</p>'
                f'<div style="margin-top:10px">{type_chips(game.secret)}'
                f'<span class="pill lav">Gen {esc(game.secret["gen"])}</span>'
                '</div></div></div>'
            )
        else:
            md(
                '<div class="result-card lose">'
                f'{art_img(secret_name, 168)}'
                f'<div><h3>THE MYSTERY WAS {esc(secret_name).upper()}</h3>'
                '<p>Better luck next time — every clue makes you sharper!</p>'
                f'<div style="margin-top:10px">{type_chips(game.secret)}'
                f'<span class="pill lav">Gen {esc(game.secret["gen"])}</span>'
                '</div></div></div>'
            )

        if game.history:
            section_title("Your Clue Trail")
            render_clue_history(game.history)

        if st.button("Start Another Mystery", type="primary", **STRETCH):
            st.session_state.human_game = Game(POKEMON)
            st.session_state.human_celebrated = False
            st.rerun()

    else:

        remaining = MAX_GUESSES - len(game.history)

        intro, mystery = st.columns([1.7, 1])

        with intro:
            md(
                '<div class="k-card"><h3>WELCOME TO THE MYSTERY MEADOW</h3>'
                '<p>Every guess reveals five pieces of feedback. Green means '
                'a match; directional clues help you understand numeric '
                'attributes. Pick a Pokémon, submit your guess and watch the '
                'possible species melt away.</p>'
                '<div style="margin-top:12px">'
                '<span class="pill pink">5 clue dimensions</span>'
                f'<span class="pill lav">{MAX_GUESSES} guesses max</span>'
                f'<span class="pill mint">{len(POKEMON)} species</span>'
                '</div></div>'
            )

        with mystery:
            md(
                '<div class="mystery"><div class="qb">'
                f'{pokeball(104)}<span class="q">?</span></div>'
                '<div class="big">A WILD MYSTERY APPEARED!</div>'
                '<small>Can you identify it?</small></div>'
            )

        section_title("Your Challenge")

        cols = st.columns(3)

        with cols[0]:
            metric("Attempts left", remaining, f"of {MAX_GUESSES}", "target", "pink")

        with cols[1]:
            metric("Guesses made", len(game.history), "Study the clues", "search", "lav")

        with cols[2]:
            metric(
                "Possible species",
                len(filter_candidates(POKEMON, game.history)),
                "Consistent with clues",
                "star",
                "peach",
            )

        md('<div style="height:14px"></div>')
        attempt_balls(len(game.history), MAX_GUESSES)
        hp_bar(
            remaining / MAX_GUESSES, "HP",
            f"Attempt {len(game.history) + 1} of {MAX_GUESSES}",
            f"{remaining} left",
        )

        md('<div style="height:10px"></div>')

        pick, preview = st.columns([1.1, 1])

        with pick:
            guess_name = st.selectbox(
                "Choose your Pokémon",
                NAMES,
                key="human_guess_select",
                help="Search the list or type a species name.",
            )

            selected = BY_NAME[guess_name]

            already_guessed = guess_name in [
                g["name"] for g, _ in game.history
            ]

            if already_guessed:
                st.caption("You already tried this one — pick another!")

            if st.button(
                "Submit My Guess",
                type="primary",
                disabled=already_guessed,
                **STRETCH,
            ):
                game.guess(selected)

                if game.status in ("won", "lost"):
                    st.session_state.human_games_played += 1

                    if game.status == "won":
                        st.session_state.human_games_won += 1

                    st.session_state.human_total_guesses += len(game.history)

                st.rerun()

        with preview:
            md(
                '<div class="selected-card">'
                f'{art_img(guess_name, 112)}<div>'
                f'<div class="nm">{esc(guess_name).upper()}</div>'
                f'<div>{type_chips(selected)}</div>'
                f'<div class="st">Generation {esc(selected["gen"])} · '
                f'{esc(selected["height"])} m · {esc(selected["weight"])} kg'
                '</div></div></div>'
            )

        if game.history:
            section_title("Clue Trail")
            render_clue_history(game.history)
        else:
            md(
                '<div class="empty">'
                f'{pokeball(64)}'
                '<div class="big">YOUR FIRST CLUE IS WAITING</div>'
                '<p>Make your first guess to begin narrowing down the '
                'mystery.</p></div>'
            )

        with st.expander("How to read the clues"):
            legend = "".join(
                f'<div class="tile {css}"><b>{sym}</b><span>{esc(text)}</span></div>'
                for css, sym, text in [
                    ("t-green", "✓", "Match — same value (±10% for numbers)"),
                    ("t-amber", "◆", "Type is in the other slot"),
                    ("t-grey", "✕", "No match"),
                    ("t-up", "↑", "The answer is higher"),
                    ("t-down", "↓", "The answer is lower"),
                ]
            )
            md(f'<div class="legend">{legend}</div>')


# ============================================================
# AI BATTLE ARENA
# ============================================================

elif page == "AI Battle Arena":

    hero(
        "FIELD TEST 02 · INTELLIGENT AGENTS",
        "AI <em>Battle</em> Arena",
        "Choose a hidden species and watch an intelligent strategy "
        "investigate it, one decision at a time.",
        art="Mewtwo",
        chips=[("4 strategies", "pink"), ("Step-by-step playback", "lav"),
               ("Real clue rules", "mint")],
    )

    STRATEGIES = [
        ("Random baseline", "Unown", "No clue usage",
         "Chooses an unguessed Pokémon without using clue information."),
        ("Filter-based", "Smeargle", "Consistency filter",
         "Removes candidates inconsistent with observed feedback."),
        ("Entropy", "Gengar", "Information gain",
         "Selects a guess expected to divide candidates into informative "
         "feedback groups."),
        ("Minimax", "Alakazam", "Worst-case control",
         "Minimizes the largest possible remaining candidate group."),
    ]

    if "battle_strategy" not in st.session_state:
        st.session_state["battle_strategy"] = STRATEGIES[0][0]

    section_title("Choose Your Strategist")

    cols = st.columns(4)
    for col, (name, mascot, tag, desc) in zip(cols, STRATEGIES):
        chosen_now = st.session_state["battle_strategy"] == name
        with col:
            md(
                f'<div class="k-card strat{" sel" if chosen_now else ""}">'
                f'{art_img(mascot, 112)}<h3>{esc(name).upper()}</h3>'
                f'<span class="tagline">{esc(tag).upper()}</span>'
                f'<p>{esc(desc)}</p></div>'
            )
            st.button(
                "Selected" if chosen_now else "Choose",
                key=f"pick_{name}",
                type="primary" if chosen_now else "secondary",
                on_click=lambda n=name: st.session_state.update(
                    battle_strategy=n),
                **STRETCH,
            )

    section_title("Set Up the Battle")

    left, right = st.columns(2)

    with left:
        secret = st.selectbox(
            "Secret Pokémon",
            NAMES,
            index=NAMES.index("Pikachu") if "Pikachu" in NAMES else 0,
            key="battle_secret",
        )

    with right:
        strategy = st.selectbox(
            "AI Strategy",
            ["Random baseline", "Filter-based", "Entropy", "Minimax"],
            key="battle_strategy",
        )

    st.caption(
        "For a fair comparison, keep the secret Pokémon the same "
        "when switching strategies."
    )

    if st.button("Prepare AI Battle", type="primary", **STRETCH):

        with st.spinner("The AI is studying the Pokédex…"):

            solver = get_solver(strategy)

            game = Game(POKEMON, secret=BY_NAME[secret])
            guessed = []
            rows = []
            clues = []

            while game.status == "playing":

                if strategy == "Random baseline":
                    guess = random_solver(POKEMON, game.history)

                elif strategy == "Filter-based":
                    guess = filter_solver(POKEMON, game.history)

                else:
                    candidates = filter_candidates(POKEMON, game.history)
                    guess = solver.next_guess(candidates, guessed)

                clue = game.guess(guess)
                guessed.append(guess)
                clues.append(clue)

                remaining_candidates = len(
                    filter_candidates(POKEMON, game.history)
                )

                rows.append({
                    "Turn": len(rows) + 1,
                    "AI guess": guess["name"],
                    "Generation": guess["gen"],
                    "Types": safe_types(guess),
                    "Candidates remaining": remaining_candidates,
                    "Outcome": game.status.title(),
                })

        st.session_state.last_battle = {
            "secret": secret,
            "strategy": strategy,
            "rows": rows,
            "clues": clues,
            "status": game.status,
            "celebrated": False,
        }

        st.session_state.battle_step = 0
        st.rerun()

    battle = st.session_state.last_battle

    if battle:

        rows = battle["rows"]
        clues = battle.get("clues", [])
        step = min(st.session_state.battle_step, len(rows))

        section_title("Watch the AI Reason")

        top = st.columns(3)

        with top[0]:
            metric("Strategy", battle["strategy"], "Selected agent", "bot", "pink")

        with top[1]:
            metric("Turn revealed", f"{step}/{len(rows)}",
                   "Step-by-step playback", "play", "lav")

        left_now = (
            len(POKEMON) if step == 0
            else rows[step - 1]["Candidates remaining"]
        )

        with top[2]:
            metric("Candidates left", left_now, "After revealed turns",
                   "search", "peach")

        md('<div style="height:12px"></div>')

        if step == 0:

            md(
                '<div class="k-card" style="text-align:center">'
                f'{pokeball(70)}'
                f'<h3 style="margin-top:10px">THE AI HAS {len(POKEMON)} '
                'POSSIBLE ANSWERS</h3>'
                '<p>Reveal the first decision to see how the agent begins '
                'its search.</p></div>'
            )

        else:

            current = rows[step - 1]
            guess_record = BY_NAME.get(current["AI guess"], {})
            clue_html = (
                clue_tiles(clues[step - 1]) if step - 1 < len(clues) else ""
            )

            if current["Outcome"] == "Won":
                remain_html = '<b>★</b><small>found it!</small>'
            else:
                remain_html = (
                    f'<b>{current["Candidates remaining"]}</b>'
                    '<small>candidates remain</small>'
                )

            md(
                '<div class="turn-card">'
                f'{art_img(current["AI guess"], 112)}'
                '<div>'
                f'<span class="pill pink">TURN {current["Turn"]}</span>'
                f'<div class="nm">{esc(current["AI guess"]).upper()}</div>'
                f'<div>{type_chips(guess_record) if guess_record else ""}'
                f'<span class="pill lav">Gen {esc(current["Generation"])}'
                '</span></div></div>'
                f'<div class="remain">{remain_html}</div></div>'
            )

            if clue_html:
                md(f'<div class="tiles-wrap">{clue_html}</div>')

        hp_bar(
            left_now / len(POKEMON), "HP",
            "Candidates remaining", f"{left_now} / {len(POKEMON)}",
        )
        hp_bar(
            step / len(rows), "EXP",
            f"Turn {step} of {len(rows)}", "Playback", kind="hp-exp",
        )

        if step > 0:

            section_title("Candidate Reduction")

            funnel = [
                '<div class="k-card" style="padding:14px 22px">'
            ]
            for i, row in enumerate(rows[:step]):
                frac = row["Candidates remaining"] / len(POKEMON)
                width = max(3.0, frac * 100)
                funnel.append(
                    '<div class="fun-row">'
                    f'{art_img(row["AI guess"], 56)}'
                    f'<div class="nm">{esc(row["AI guess"]).upper()}'
                    f'<small>Turn {row["Turn"]}</small></div>'
                    '<div class="btrack"><div class="bfill" '
                    f'style="--w:{width:.1f}%;--c1:'
                    f'{"#3CB043" if frac > .5 else "#F8D030" if frac > .2 else "#E84040"}'
                    '"></div></div>'
                    f'<div class="val">{row["Candidates remaining"]}</div>'
                    '</div>'
                )
            funnel.append("</div>")
            md("".join(funnel))

            show_df(pd.DataFrame(rows[:step]))

        prev_col, next_col, reset_col = st.columns(3)

        with prev_col:
            if st.button(
                "Previous Turn",
                disabled=step == 0,
                **STRETCH,
            ):
                st.session_state.battle_step = max(0, step - 1)
                st.rerun()

        with next_col:
            if st.button(
                "Reveal Next Turn",
                type="primary",
                disabled=step >= len(rows),
                **STRETCH,
            ):
                st.session_state.battle_step = min(len(rows), step + 1)
                st.rerun()

        with reset_col:
            if st.button("Restart Playback", **STRETCH):
                st.session_state.battle_step = 0
                st.rerun()

        if step == len(rows):

            if not battle.get("celebrated"):
                st.balloons()
                battle["celebrated"] = True

            section_title("Battle Results")

            if battle["status"] == "won":
                md(
                    '<div class="result-card win">'
                    f'{art_img(battle["secret"], 168)}'
                    '<div><h3>MYSTERY SOLVED!</h3>'
                    f'<p>{esc(battle["strategy"])} identified '
                    f'<b>{esc(battle["secret"])}</b> in '
                    f'<b>{len(rows)} guesses</b>.</p></div></div>'
                )
            else:
                md(
                    '<div class="result-card lose">'
                    f'{art_img(battle["secret"], 168)}'
                    '<div><h3>GUESS LIMIT REACHED</h3>'
                    f'<p>The hidden Pokémon was '
                    f'<b>{esc(battle["secret"])}</b>.</p></div></div>'
                )

            with st.expander("View the Complete Battle Log"):
                show_df(pd.DataFrame(rows))

            counts = [len(POKEMON)] + [
                row["Candidates remaining"] for row in rows
            ]

            fig, ax = plt.subplots(figsize=(9, 3.6))
            fig.patch.set_facecolor("#FFFFFF")
            ax.set_facecolor("#EEF1FF")
            fig.add_artist(Rectangle(
                (0, 0), 1, 1, transform=fig.transFigure, fill=False,
                edgecolor="#0B1030", linewidth=8))

            ax.plot(
                range(len(counts)), counts,
                color="#4878F8", marker="s", linewidth=3.5,
                markersize=11, markerfacecolor="#F8B020",
                markeredgewidth=3, markeredgecolor="#0B1030",
                drawstyle="steps-post",
            )
            ax.fill_between(range(len(counts)), counts, color="#8CB8FF",
                            alpha=0.35, step="post")

            for x, y in enumerate(counts):
                ax.annotate(
                    str(y), (x, y), textcoords="offset points",
                    xytext=(0, 12), ha="center", color="#0B1030",
                    fontweight="bold", fontsize=11, family="monospace",
                )

            ax.set_xticks(range(len(counts)))
            ax.set_xlabel("AFTER GUESS", color="#26306A", fontweight="bold",
                          family="monospace")
            ax.set_ylabel("POSSIBLE ANSWERS", color="#26306A",
                          fontweight="bold", family="monospace")
            ax.set_title("CANDIDATE SEARCH SPACE", color="#0B1030",
                         fontweight="bold", fontsize=13, pad=14,
                         family="monospace")
            ax.set_ylim(bottom=0, top=max(counts) * 1.18)
            ax.tick_params(colors="#26306A")
            ax.grid(alpha=0.5, color="#C8D0F0", linestyle=":")
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
            for side in ("left", "bottom"):
                ax.spines[side].set_color("#0B1030")
                ax.spines[side].set_linewidth(2.5)

            fig.tight_layout(pad=1.6)
            st.pyplot(fig)
            plt.close(fig)

            st.caption(
                "Candidate counts use the project's actual clue rules and "
                "dataset."
            )

    else:

        md(
            '<div class="empty">'
            f'{pokeball(70)}'
            '<div class="big">YOUR AI CHALLENGER IS READY</div>'
            '<p>Choose a secret and strategy, prepare the battle, then '
            'reveal each AI decision.</p></div>'
        )


# ============================================================
# PROFESSOR'S ANALYTICS
# ============================================================

elif page == "Professor’s Analytics":

    hero(
        "FIELD TEST 03 · PERFORMANCE EVALUATION",
        "Professor's <em>Analytics</em> Lab",
        "A visual scoreboard for the four implemented strategies. "
        "Explore measured results and understand the trade-offs.",
        art="Mew",
        chips=[("Measured results", "pink"), ("Saved benchmark", "lav")],
    )

    SOLVER_ART = {
        "random": "Unown", "filter": "Smeargle",
        "entropy": "Gengar", "minimax": "Alakazam",
    }

    def solver_art(name):
        low = str(name).lower()
        for key, mascot in SOLVER_ART.items():
            if low.startswith(key):
                return mascot
        return None

    path = os.path.join(RESULTS, "results_table.csv")

    if os.path.exists(path):

        df = pd.read_csv(path)

        required = {"Solver", "Avg guesses", "Worst case"}

        if not required.issubset(df.columns):

            st.error(
                "The benchmark CSV does not contain the expected columns: "
                "Solver, Avg guesses, Worst case."
            )

        else:

            best = df.loc[df["Avg guesses"].idxmin()]

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                metric(
                    "Lowest average",
                    f"{best['Avg guesses']:.2f}",
                    str(best["Solver"]),
                    "trophy", "pink",
                )

            with c2:
                metric(
                    "Best worst case",
                    int(df["Worst case"].min()),
                    "Guesses",
                    "shield", "lav",
                )

            with c3:
                metric("Strategies", len(df), "In saved benchmark", "bot", "peach")

            with c4:
                runs = int(df["Runs"].sum()) if "Runs" in df.columns else "—"
                metric(
                    "Total runs", runs,
                    "As recorded in CSV" if "Runs" in df.columns
                    else "Not recorded in this CSV",
                    "chart", "blue",
                )

            section_title("Benchmark Scoreboard")

            ranked = df.sort_values("Avg guesses").reset_index(drop=True)
            medals = ["1ST", "2ND", "3RD"]
            tones = ["pink", "lav", "peach", "blue"]
            cols = st.columns(len(ranked))

            detail_cols = [c for c in ranked.columns
                           if c not in ("Solver", "Avg guesses")]

            for i, (col, (_, row)) in enumerate(zip(cols, ranked.iterrows())):
                mascot = solver_art(row["Solver"])
                kv = "".join(
                    f'<span>{esc(c)}</span><b>{esc(fmt_num(row[c]))}</b>'
                    for c in detail_cols
                )
                rank_html = (
                    f'<span class="pill {["peach", "lav", "pink"][i]}" '
                    f'style="margin:0">{medals[i]}</span>'
                    if i < 3 else f'<span class="rankn">{i + 1}</span>'
                )
                with col:
                    md(
                        f'<div class="k-card lb tone-{tones[i % 4]}">'
                        f'<div class="rank">{rank_html}</div>'
                        f'{art_img(mascot, 112) if mascot else ""}'
                        f'<div class="who">{esc(row["Solver"]).upper()}</div>'
                        f'<div class="main">{fmt_num(row["Avg guesses"])}'
                        '<small>avg guesses</small></div>'
                        f'<div class="kv">{kv}</div></div>'
                    )

            section_title("Compare Strategy Performance")

            plot_df = ranked
            outliers = ranked[ranked["Avg guesses"] > 10 * best["Avg guesses"]]

            if len(outliers):
                view = st.radio(
                    "Chart view",
                    ["All strategies", "Zoom in on the smarter strategies"],
                    horizontal=True,
                    key="an_view",
                )
                if view != "All strategies":
                    plot_df = ranked.drop(outliers.index)
                    names = ", ".join(str(n) for n in outliers["Solver"])
                    st.caption(
                        f"{names} hidden in this view so the differences "
                        "between the other strategies are easier to see."
                    )

            md(
                '<div class="k-card"><h3>AVERAGE GUESSES BY STRATEGY</h3>'
                '<p style="margin-bottom:8px">Lower is better.</p>'
                + bar_chart(
                    list(zip(plot_df["Solver"], plot_df["Avg guesses"]))
                )
                + '</div>'
            )

            md('<div style="height:18px"></div>')

            pct_cols = [
                c for c in df.columns
                if c == "Win rate" or str(c).startswith("Solved")
            ]
            for pc in pct_cols:
                md(
                    f'<div class="k-card"><h3>{esc(pc).upper()}</h3>'
                    '<p style="margin-bottom:8px">Higher is better.</p>'
                    + bar_chart(
                        list(zip(ranked["Solver"], ranked[pc])),
                        unit="%", decimals=2, max_value=100,
                    )
                    + '</div>'
                )
                md('<div style="height:18px"></div>')

            section_title("Benchmark Table")

            try:
                lower = [c for c in ("Avg guesses", "Worst case", "Std dev")
                         if c in df.columns]
                higher = [c for c in df.columns
                          if c == "Win rate" or str(c).startswith("Solved")]
                numeric = [c for c in df.columns
                           if pd.api.types.is_numeric_dtype(df[c])]
                mark = "background-color: #7FDB8A; color: #0B1030; font-weight: 700"
                styled = df.style.format(fmt_num, subset=numeric)
                if lower:
                    styled = styled.highlight_min(subset=lower, props=mark)
                if higher:
                    styled = styled.highlight_max(subset=higher, props=mark)
                show_df(styled)
            except Exception:
                show_df(df)

            st.caption("Green cells mark the best value in each column.")

            section_title("How the Four Strategies Work")

            how = [
                ("dice", "Random baseline", "pink",
                 "Chooses an unguessed Pokémon without using clue "
                 "information."),
                ("funnel", "Filter-based", "lav",
                 "Removes candidates inconsistent with observed feedback."),
                ("sparkle", "Entropy", "peach",
                 "Selects a guess expected to divide candidates into "
                 "informative feedback groups."),
                ("shield", "Minimax", "blue",
                 "Minimizes the largest possible remaining candidate group."),
            ]
            cols = st.columns(4)
            for col, (ico, nm, tone, txt) in zip(cols, how):
                with col:
                    md(
                        f'<div class="k-card nav-card tone-{tone}">'
                        f'<div class="top"><div class="ibox">'
                        f'{px_icon(ico, 36)}</div></div>'
                        f'<h3>{esc(nm).upper()}</h3>'
                        f'<p>{esc(txt)}</p></div>'
                    )

            section_title("Research Statistics")

            data_df = pd.DataFrame(POKEMON)
            gen_counts = data_df["gen"].value_counts().sort_index()
            type_counts = data_df["type1"].value_counts().head(8)

            g_col, t_col = st.columns(2)
            with g_col:
                md(
                    '<div class="k-card"><h3>SPECIES PER GENERATION</h3>'
                    + bar_chart(
                        [(f"Gen {g}", float(c))
                         for g, c in gen_counts.items()],
                        decimals=0,
                    ) + '</div>'
                )
            with t_col:
                md(
                    '<div class="k-card"><h3>COMMON PRIMARY TYPES</h3>'
                    + bar_chart(
                        [(t, float(c)) for t, c in type_counts.items()],
                        decimals=0, tone_offset=2,
                    ) + '</div>'
                )

            md('<div style="height:18px"></div>')

            st.download_button(
                "Download Benchmark CSV",
                df.to_csv(index=False).encode(),
                file_name="pokemon_wordle_benchmark.csv",
                mime="text/csv",
            )

            st.caption(
                "These values are read from the project's saved "
                "results_table.csv."
            )

    else:

        st.warning(
            "Benchmark CSV is missing. Run benchmark.py to generate it."
        )

        md(
            '<div class="empty">'
            f'{pokeball(70)}'
            '<div class="big">THE SCOREBOARD IS WAITING FOR DATA</div>'
            '<p>Run benchmark.py to generate results/results_table.csv, '
            'then refresh this page.</p></div>'
        )


# ============================================================
# DATASET EXPLORER
# ============================================================

else:

    hero(
        "FIELD TEST 04 · DATA INVESTIGATION",
        "The <em>Pokédex</em> Collection",
        "Browse the actual dataset used by every solver. Search by name "
        "and filter species by generation and primary type.",
        art="Togepi",
        chips=[(f"{len(POKEMON)} species", "pink"), ("Real dataset", "lav")],
    )

    df = pd.DataFrame(POKEMON)

    c1, c2, c3 = st.columns(3)

    with c1:
        metric("Species", len(df), "Loaded from pokemon.csv", "book", "pink")

    with c2:
        metric("Primary types", df.type1.nunique(), "Unique categories",
               "star", "lav")

    with c3:
        metric("Generations", df.gen.nunique(), "Generation values",
               "chart", "peach")

    section_title("Find a Pokémon")

    f1, f2, f3 = st.columns([1.5, 1, 1])

    with f1:
        search = st.text_input(
            "Search species",
            placeholder="Try Pikachu, Eevee...",
        )

    with f2:
        generations = sorted(df["gen"].dropna().unique().tolist())
        selected_gen = st.selectbox("Generation", ["All"] + generations)

    with f3:
        types = sorted(df["type1"].dropna().unique().tolist())
        selected_type = st.selectbox("Primary type", ["All"] + types)

    view = df.copy()

    if search:
        view = view[
            view["name"].str.contains(search, case=False, na=False)
        ]

    if selected_gen != "All":
        view = view[view["gen"] == selected_gen]

    if selected_type != "All":
        view = view[view["type1"] == selected_type]

    st.caption(f"Showing {len(view)} of {len(df)} species")

    ordered = view.sort_values("name")

    if ordered.empty:
        md(
            '<div class="empty">'
            f'{pokeball(70)}'
            '<div class="big">NO POKÉMON FOUND</div>'
            '<p>Try a different name or clear a filter.</p></div>'
        )
    else:
        section_title("Pokédex Gallery")

        PAGE_SIZE = 24
        total_pages = max(1, math.ceil(len(ordered) / PAGE_SIZE))
        page_no = 1
        if total_pages > 1:
            page_no = st.slider(
                "Gallery page", 1, total_pages, 1,
                key=f"dex_page_{search}_{selected_gen}_{selected_type}",
            )
        chunk = ordered.iloc[(page_no - 1) * PAGE_SIZE: page_no * PAGE_SIZE]

        cards = []
        for _, rec in chunk.iterrows():
            nid = pokemon_id(rec["name"])
            number = f"No. {nid:03d}" if nid else ""
            cards.append(
                '<div class="dex-card">'
                f'<span class="no">{number}</span>'
                f'<span class="gen">GEN {esc(rec["gen"])}</span>'
                f'<div class="pic">{art_img(rec["name"], 112)}</div>'
                f'<div class="nm">{esc(rec["name"]).upper()}</div>'
                f'<div>{type_chips(rec)}</div>'
                f'<div class="ms">{esc(rec["height"])} m · '
                f'{esc(rec["weight"])} kg</div></div>'
            )
        md('<div class="dex-grid">' + "".join(cards) + "</div>")

        section_title("Dataset Table")

        show_df(ordered)

        section_title("Featured Pokédex Entry")

        chosen = st.selectbox(
            "Choose a record to preview",
            view["name"].tolist(),
            key="dex_preview",
        )

        record = BY_NAME[chosen]

        art_col, detail_col = st.columns([1, 2])

        with art_col:
            nid = pokemon_id(chosen)
            md(
                '<div class="mystery">'
                f'{art_img(chosen, 168)}'
                f'<div class="big">{esc(chosen).upper()}</div>'
                f'<small>{"No. %03d" % nid if nid else ""}</small></div>'
            )

        with detail_col:
            md(
                '<div class="k-card">'
                f'<h3>{esc(chosen).upper()}</h3>'
                f'<div>{type_chips(record)}</div>'
                '<div class="detail-grid">'
                f'<div><small>Generation</small><b>{esc(record["gen"])}</b></div>'
                f'<div><small>Type 1</small><b>{esc(record["type1"])}</b></div>'
                f'<div><small>Type 2</small>'
                f'<b>{esc(record.get("type2") or "None")}</b></div>'
                f'<div><small>Height</small>'
                f'<b>{esc(record.get("height", "—"))} m</b></div>'
                f'<div><small>Weight</small>'
                f'<b>{esc(record.get("weight", "—"))} kg</b></div>'
                '</div></div>'
            )

        md('<div style="height:18px"></div>')

        st.download_button(
            "Export Filtered Dataset",
            view.to_csv(index=False).encode(),
            file_name="pokemon_dataset_filtered.csv",
            mime="text/csv",
        )


# ============================================================
# FOOTER
# ============================================================

md(
    '<div class="divider" style="margin-top:40px"></div>'
    '<div class="footer">'
    f'{pokeball(32)}<br>'
    'POKÉMON WORDLE · RESEARCH LAB'
    '<small>THINK · GUESS · DISCOVER · REPEAT</small></div>'
)
