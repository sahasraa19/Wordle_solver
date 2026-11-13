# ============================================================
# POKÉMON WORDLE · RESEARCH LAB  —  3D KAWAII PREMIUM EDITION
# ------------------------------------------------------------
# Drop-in replacement for research_lab.py.
# Every game rule, solver call, dataset load and benchmark
# calculation is the project's own code; only the presentation
# layer (theme, layout, components, animations) is new.
# ============================================================

import os
import html
import itertools
import math

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

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
    page_icon="🎀",
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
# POKÉMON HOME ARTWORK
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

ART_URL = (
    "https://raw.githubusercontent.com/PokeAPI/sprites/master/"
    "sprites/pokemon/other/home/{pokemon_id}.png"
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


def pokemon_url(name):
    pid = pokemon_id(name)
    if pid:
        return ART_URL.format(pokemon_id=pid)
    return None


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


_uid = itertools.count()

SHAPES = {
    "heart": (
        "M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3"
        "c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42"
        " 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
    ),
    "star": (
        "M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2"
        " 9.24l5.46 4.73L5.82 21z"
    ),
    "sparkle": (
        "M12 0c.7 6.6 3.9 10.3 12 12-8.1 1.7-11.3 5.4-12 12-.7-6.6-3.9-10.3"
        "-12-12 8.1-1.7 11.3-5.4 12-12z"
    ),
    "cloud": (
        "M6.5 19a4.5 4.5 0 0 1-.7-8.95A6.5 6.5 0 0 1 18.3 9.4 4.8 4.8 0 0 1"
        " 17.5 19h-11z"
    ),
}


def shape(kind, color, size=22):
    return (
        f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" '
        f'aria-hidden="true"><path d="{SHAPES[kind]}" fill="{color}"/></svg>'
    )


def pokeball(size=48, cls=""):
    """A pastel 3D Poké Ball drawn in SVG (unique gradient ids per call)."""
    n = next(_uid)
    return H(f"""
    <svg class="pball {cls}" width="{size}" height="{size}"
         viewBox="0 0 100 100" aria-hidden="true">
    <defs>
    <radialGradient id="pt{n}" cx="34%" cy="26%" r="85%">
    <stop offset="0" stop-color="#FFE6F2"/>
    <stop offset=".45" stop-color="#FF9CC8"/>
    <stop offset="1" stop-color="#D4528C"/></radialGradient>
    <radialGradient id="pb{n}" cx="34%" cy="30%" r="90%">
    <stop offset="0" stop-color="#FFFFFF"/>
    <stop offset=".55" stop-color="#F7EFFB"/>
    <stop offset="1" stop-color="#C9B8DE"/></radialGradient>
    <radialGradient id="ps{n}" cx="35%" cy="30%" r="75%">
    <stop offset=".6" stop-color="#6B3C86" stop-opacity="0"/>
    <stop offset="1" stop-color="#6B3C86" stop-opacity=".32"/></radialGradient>
    <clipPath id="pc{n}"><circle cx="50" cy="50" r="45"/></clipPath>
    </defs>
    <g clip-path="url(#pc{n})">
    <rect x="0" y="0" width="100" height="50" fill="url(#pt{n})"/>
    <rect x="0" y="50" width="100" height="50" fill="url(#pb{n})"/>
    <rect x="0" y="44" width="100" height="12" fill="#4A3355"/>
    <circle cx="50" cy="50" r="45" fill="url(#ps{n})"/>
    <ellipse cx="33" cy="24" rx="17" ry="8" fill="#fff" opacity=".6"
             transform="rotate(-30 33 24)"/>
    </g>
    <circle cx="50" cy="50" r="45" fill="none" stroke="#4A3355"
            stroke-width="4"/>
    <circle cx="50" cy="50" r="15" fill="#4A3355"/>
    <circle cx="50" cy="50" r="10" fill="#fff"/>
    <circle cx="50" cy="50" r="5" fill="#E3D6FA"/>
    </svg>
    """)


def art_img(name, size=96, cls=""):
    """Official Pokémon HOME artwork (falls back to a Poké Ball)."""
    url = pokemon_url(name)
    if not url:
        return pokeball(int(size * 0.7), cls)
    return (
        f'<img class="art {cls}" src="{url}" alt="{esc(name)}" '
        f'width="{size}" height="{size}" loading="lazy" decoding="async">'
    )


# ============================================================
# TYPE COLOURS (pastel chips with dark, readable ink)
# ============================================================

TYPE_COLORS = {
    "Normal": ("#EBE6DD", "#5A5448"), "Fire": ("#FFD6C6", "#9A3412"),
    "Water": ("#CFE5FF", "#1E4E8C"), "Electric": ("#FFF1B8", "#755500"),
    "Grass": ("#D0F0D2", "#246034"), "Ice": ("#D7F4F7", "#1B6670"),
    "Fighting": ("#F8D3CC", "#8A2D22"), "Poison": ("#E8D0F7", "#6B2B8C"),
    "Ground": ("#EEDDBD", "#6B4A12"), "Flying": ("#E0E6FF", "#3F4C99"),
    "Psychic": ("#FFD3E8", "#9B2C6B"), "Bug": ("#E6F2BE", "#4F6B0E"),
    "Rock": ("#E4DBC3", "#5E5230"), "Ghost": ("#DCD3F0", "#4B3A7A"),
    "Dragon": ("#D6D3FF", "#3B35A0"), "Dark": ("#D9D3DD", "#3F3947"),
    "Steel": ("#DBE3EB", "#44546A"), "Fairy": ("#FFD9F0", "#9C3A78"),
}


def type_chip(type_name):
    if not type_name or str(type_name) == "None":
        return '<span class="chip chip-none">—</span>'
    bg, ink = TYPE_COLORS.get(str(type_name), ("#EEE8F4", "#4F4560"))
    return (
        f'<span class="chip" style="background:{bg};color:{ink}">'
        f'{esc(type_name)}</span>'
    )


def type_chips(pokemon):
    return type_chip(pokemon.get("type1")) + type_chip(pokemon.get("type2"))


# ============================================================
# 3D KAWAII THEME
# ============================================================

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&family=Nunito:wght@400;600;700;800;900&display=swap');

:root {
  --pink: #FFB8D6;
  --pink-2: #FF93C1;
  --pink-3: #E0609A;
  --rose: #B23B78;
  --lav: #DCCBFF;
  --lav-2: #B79EF0;
  --lilac: #EFE6FF;
  --cream: #FFF8F3;
  --peach: #FFDAC5;
  --blue: #CFE6FF;
  --blue-2: #9CC8F5;
  --plum: #3F2A4A;
  --plum-2: #5B4468;
  --muted: #6B5778;
  --line: rgba(176, 120, 190, .28);
  --glass: rgba(255, 255, 255, .66);
  --lift: 0 14px 34px rgba(150, 95, 170, .18);
}

html, body, .stApp, [class*="css"] {
  font-family: 'Nunito', system-ui, sans-serif;
  color: var(--plum);
}

.stApp {
  background:
    radial-gradient(circle at 8% 4%, #FFE1EE 0, transparent 34%),
    radial-gradient(circle at 94% 10%, #E9E0FF 0, transparent 36%),
    radial-gradient(circle at 80% 92%, #D8EBFF 0, transparent 34%),
    radial-gradient(circle at 6% 88%, #FFE6D6 0, transparent 30%),
    linear-gradient(180deg, #FFF8F3, #FFF3F8);
  background-attachment: fixed;
}

.block-container {
  max-width: 1240px;
  padding: 1.1rem 1.4rem 3rem;
  position: relative;
  z-index: 1;
}

#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }

p, li, label, span, div { color: inherit; }
.stMarkdown p { color: var(--plum); }

/* ---------- floating background decorations ---------- */
.fx {
  position: fixed; inset: 0; z-index: -1; pointer-events: none;
  overflow: hidden;
}
.fx span {
  position: absolute; display: block; opacity: .55;
  animation: floaty var(--d, 9s) ease-in-out var(--dl, 0s) infinite;
}
.fx span.tw { animation-name: twinkle; }

[data-testid="stElementContainer"]:has(> .stMarkdown .fx),
.element-container:has(> .stMarkdown .fx) {
  position: absolute; height: 0; margin: 0; padding: 0;
}

@keyframes floaty {
  0%, 100% { transform: translateY(0) rotate(var(--r, 0deg)); }
  50% { transform: translateY(-16px) rotate(calc(var(--r, 0deg) + 5deg)); }
}
@keyframes twinkle {
  0%, 100% { opacity: .2; transform: scale(.75); }
  50% { opacity: .85; transform: scale(1.15); }
}
@keyframes rise {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: none; }
}
@keyframes grow { from { width: 0; } to { width: var(--w); } }
@keyframes wobble {
  0%, 100% { transform: rotate(-5deg); } 50% { transform: rotate(5deg); }
}
@keyframes shimmer {
  from { background-position: -200% 0; } to { background-position: 200% 0; }
}
@keyframes pop {
  0% { transform: scale(.6); opacity: 0; }
  70% { transform: scale(1.08); opacity: 1; }
  100% { transform: scale(1); }
}

/* ---------- brand ---------- */
.brand {
  display: flex; justify-content: center; align-items: center;
  gap: 16px; padding: 2px 0 6px; animation: rise .6s ease both;
}
.brand .pball { animation: floaty 5s ease-in-out infinite;
  filter: drop-shadow(0 8px 8px rgba(120, 60, 140, .3)); }
.brand-name {
  font-family: 'Fredoka', sans-serif; font-weight: 700;
  font-size: 2.35rem; line-height: 1; letter-spacing: .02em;
  color: var(--rose);
  text-shadow: 0 2px 0 #fff, 0 4px 0 #F7C6DE, 0 6px 0 #EDAFCF,
               0 14px 16px rgba(140, 70, 120, .28);
}
.brand-tiles { display: flex; gap: 5px; margin-top: 9px; }
.brand-tiles b {
  width: 27px; height: 27px; border-radius: 9px; display: grid;
  place-items: center; font-family: 'Fredoka', sans-serif;
  font-size: .95rem; color: var(--plum);
  box-shadow: 0 3px 0 var(--sh), inset 0 2px 0 rgba(255, 255, 255, .7);
  background: var(--bg);
}
.brand-sub {
  font-size: .68rem; font-weight: 900; letter-spacing: .34em;
  color: var(--muted); margin-top: 7px;
}
.sub-line {
  text-align: center; color: var(--muted); font-size: .74rem;
  font-weight: 900; letter-spacing: .22em; margin-bottom: .6rem;
}

/* ---------- navigation pills ---------- */
.st-key-nav [data-testid="stRadio"] > div[role="radiogroup"],
.st-key-nav div[role="radiogroup"] {
  display: flex; flex-direction: row; flex-wrap: wrap;
  justify-content: center; gap: 10px;
}
.st-key-nav label {
  background: var(--glass); backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, .95); border-radius: 999px;
  padding: 9px 20px; margin: 0; cursor: pointer;
  box-shadow: 0 4px 0 rgba(231, 195, 220, .7),
              0 10px 18px rgba(150, 95, 170, .14);
  transition: transform .22s cubic-bezier(.3, 1.5, .5, 1),
              box-shadow .22s, background .22s;
}
.st-key-nav label:hover {
  transform: translateY(-3px) scale(1.03);
  box-shadow: 0 7px 0 rgba(231, 195, 220, .7),
              0 16px 22px rgba(150, 95, 170, .2);
}
.st-key-nav, .st-key-nav [data-testid="stRadio"] { width: 100% !important; }
.st-key-nav [data-testid="stRadioOption"] > div > div:first-child {
  display: none;
}
.st-key-nav label p {
  font-family: 'Fredoka', sans-serif; font-weight: 600;
  font-size: .98rem; color: var(--plum-2); margin: 0;
}
.st-key-nav label:has(input:checked) {
  background: linear-gradient(160deg, #FF9BC8, #E0609A);
  border-color: #fff;
  box-shadow: 0 5px 0 #B23B78, 0 14px 22px rgba(178, 59, 120, .35),
              inset 0 2px 0 rgba(255, 255, 255, .55);
  transform: translateY(-2px);
  animation: pop .35s cubic-bezier(.3, 1.5, .5, 1);
}
.st-key-nav label:has(input:checked) p { color: #fff; text-shadow:
  0 1px 0 rgba(120, 30, 80, .5); }

.divider {
  height: 4px; border-radius: 99px; margin: 16px 0 26px; opacity: .8;
  background: repeating-linear-gradient(90deg, #F8BBD9 0 14px,
              transparent 14px 24px, #CDBBF5 24px 38px, transparent 38px 48px);
}

/* ---------- hero ---------- */
.hero3d {
  position: relative; overflow: hidden; display: grid;
  grid-template-columns: 1.3fr .9fr; gap: 14px; align-items: center;
  padding: 36px 40px; border-radius: 38px; margin-bottom: 26px;
  background: linear-gradient(120deg, rgba(255, 224, 240, .95),
              rgba(237, 227, 255, .95) 58%, rgba(207, 230, 255, .85));
  border: 2px solid rgba(255, 255, 255, .95);
  box-shadow: 0 10px 0 rgba(237, 199, 226, .6),
              0 30px 54px rgba(160, 100, 175, .22),
              inset 0 3px 0 rgba(255, 255, 255, .95);
  animation: rise .6s ease both;
}
.hero3d.home { padding: 44px 44px; min-height: 380px; }
.eyebrow {
  display: inline-block; font-size: .72rem; font-weight: 900;
  letter-spacing: .2em; color: var(--rose); padding: 6px 14px;
  border-radius: 99px; background: rgba(255, 255, 255, .8);
  box-shadow: 0 3px 0 rgba(231, 195, 220, .8);
}
.ht {
  font-family: 'Fredoka', sans-serif; font-weight: 700;
  font-size: clamp(2rem, 4.4vw, 3.4rem); line-height: 1.06;
  color: var(--plum); margin: 14px 0 10px;
}
.ht em {
  font-style: normal; color: var(--rose);
  text-shadow: 0 3px 0 #fff, 0 6px 12px rgba(178, 59, 120, .22);
}
.hero3d p.lead {
  color: var(--plum-2); font-size: 1.06rem; line-height: 1.65;
  max-width: 560px; margin: 0 0 14px; font-weight: 600;
}
.hero-art {
  position: relative; display: grid; place-items: center; min-height: 230px;
}
.hero-art::before {
  content: ""; position: absolute; width: min(68%, 270px); aspect-ratio: 1;
  border-radius: 50%; z-index: 0;
  background: radial-gradient(circle at 35% 30%, #fff 0, #FFE3F1 45%,
              #E6D8FF 100%);
  box-shadow: inset 0 -12px 24px rgba(184, 140, 220, .3),
              0 22px 40px rgba(160, 100, 175, .22);
}
.hero-art img.art {
  position: relative; z-index: 1; width: min(250px, 72%); height: auto;
  filter: drop-shadow(0 16px 14px rgba(110, 50, 130, .3));
  animation: floaty 6s ease-in-out infinite;
}
.hero-art .deco, .hero3d > .deco { position: absolute; z-index: 2; }
.deco { animation: twinkle 3.6s ease-in-out infinite; }
.deco.fl { animation: floaty 7s ease-in-out infinite; }

/* home stage */
.stage { position: relative; min-height: 340px; display: grid;
  place-items: center; }
.stage::before {
  content: ""; position: absolute; width: 78%; aspect-ratio: 1;
  border-radius: 50%;
  background: radial-gradient(circle at 34% 28%, #fff 0, #FFE0F0 42%,
              #E4D5FF 100%);
  box-shadow: inset 0 -16px 30px rgba(184, 140, 220, .32),
              0 26px 46px rgba(160, 100, 175, .25);
}
.stage .main { position: relative; z-index: 2;
  width: min(300px, 74%); height: auto;
  filter: drop-shadow(0 20px 16px rgba(110, 50, 130, .32));
  animation: floaty 6.5s ease-in-out infinite; }
.orb {
  position: absolute; z-index: 3; width: 84px; height: 84px;
  border-radius: 50%; display: grid; place-items: center;
  background: radial-gradient(circle at 32% 26%, #fff, #FFEAF4 60%,
              #EBDDFF);
  border: 3px solid #fff;
  box-shadow: 0 8px 0 rgba(231, 195, 220, .7),
              0 16px 22px rgba(150, 95, 170, .25);
  animation: floaty var(--d, 7s) ease-in-out var(--dl, 0s) infinite;
}
.orb img { width: 70px; height: 70px; object-fit: contain; }

/* ---------- glass cards ---------- */
.k-card {
  position: relative; height: 100%; padding: 22px 24px;
  background: var(--glass); backdrop-filter: blur(14px) saturate(1.2);
  border: 2px solid rgba(255, 255, 255, .95); border-radius: 30px;
  box-shadow: 0 7px 0 rgba(236, 200, 226, .55), var(--lift),
              inset 0 2px 0 rgba(255, 255, 255, .95),
              inset 0 -5px 0 rgba(226, 196, 238, .28);
  transition: transform .28s cubic-bezier(.3, 1.4, .5, 1), box-shadow .28s;
  animation: rise .55s ease both;
}
.k-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 0 rgba(236, 200, 226, .55),
              0 24px 40px rgba(150, 95, 170, .24),
              inset 0 2px 0 rgba(255, 255, 255, .95),
              inset 0 -5px 0 rgba(226, 196, 238, .28);
}
.k-card h3 {
  font-family: 'Fredoka', sans-serif; font-size: 1.35rem; font-weight: 600;
  color: var(--plum); margin: 0 0 4px; padding: 0;
}
.k-card p { margin: 6px 0 0; color: var(--plum-2); line-height: 1.6;
  font-weight: 600; }
.k-card .tagline { color: var(--rose); font-weight: 900; font-size: .88rem; }
.k-card.sel {
  background: linear-gradient(160deg, rgba(255, 226, 241, .95),
              rgba(236, 226, 255, .95));
  box-shadow: 0 7px 0 #E8A6C8, 0 18px 34px rgba(224, 96, 154, .28),
              inset 0 2px 0 #fff;
  border-color: #fff;
}

.nav-card .emoji {
  width: 66px; height: 66px; border-radius: 22px; display: grid;
  place-items: center; font-size: 2rem; margin-bottom: 10px;
  background: linear-gradient(160deg, #fff, var(--tint, #FFE3F0));
  box-shadow: 0 5px 0 rgba(231, 195, 220, .7), inset 0 2px 0 #fff;
}
.nav-card .corner { position: absolute; right: 12px; top: 10px;
  width: 86px; height: 86px; object-fit: contain; opacity: .95;
  filter: drop-shadow(0 8px 8px rgba(110, 50, 130, .22));
  animation: floaty 7s ease-in-out infinite; }

/* section titles */
.sec-title {
  display: flex; align-items: center; gap: 12px; margin: 34px 0 16px;
  font-family: 'Fredoka', sans-serif; font-weight: 700;
  font-size: 1.85rem; color: var(--plum);
}
.sec-title .orn { display: inline-flex; animation: twinkle 3.4s infinite; }
.sec-title::after {
  content: ""; flex: 1; height: 5px; border-radius: 99px; opacity: .75;
  background: repeating-linear-gradient(90deg, #F8BBD9 0 12px,
              transparent 12px 20px, #CDBBF5 20px 32px, transparent 32px 40px);
}
.sec-sub { margin: -8px 0 14px; color: var(--muted); font-weight: 700; }

/* ---------- metrics ---------- */
.metric3d {
  position: relative; display: flex; align-items: center; gap: 14px;
  padding: 18px 20px; min-height: 104px; border-radius: 26px;
  background: var(--glass); backdrop-filter: blur(12px);
  border: 2px solid rgba(255, 255, 255, .95);
  box-shadow: 0 6px 0 var(--edge, rgba(236, 200, 226, .6)),
              0 14px 26px rgba(150, 95, 170, .15),
              inset 0 2px 0 #fff;
  transition: transform .26s cubic-bezier(.3, 1.4, .5, 1);
  animation: rise .55s ease both;
}
.metric3d:hover { transform: translateY(-4px); }
.metric3d .ic {
  flex: none; width: 54px; height: 54px; border-radius: 18px;
  display: grid; place-items: center; font-size: 1.6rem;
  background: linear-gradient(160deg, #fff, var(--tint, #FFE3F0));
  box-shadow: 0 4px 0 var(--edge, rgba(231, 195, 220, .8)),
              inset 0 2px 0 #fff;
}
.metric3d small { display: block; font-weight: 900; font-size: .74rem;
  letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.metric3d b { display: block; font-family: 'Fredoka', sans-serif;
  font-size: 1.85rem; line-height: 1.15; color: var(--rose);
  overflow-wrap: anywhere; }
.metric3d span.sub { display: block; font-size: .8rem; color: var(--muted);
  font-weight: 700; }
.tone-pink { --tint: #FFD9EA; --edge: #F3BCD6; }
.tone-lav { --tint: #E4D8FF; --edge: #D2C0F3; }
.tone-peach { --tint: #FFE2D0; --edge: #F5CDB6; }
.tone-blue { --tint: #D6EAFF; --edge: #B9D6F3; }
.tone-mint { --tint: #D4F5E4; --edge: #B1E3CB; }

/* ---------- pills & chips ---------- */
.pill {
  display: inline-block; margin: 3px 4px 3px 0; padding: 6px 14px;
  border-radius: 99px; font-size: .8rem; font-weight: 900;
  box-shadow: 0 3px 0 rgba(0, 0, 0, .07), inset 0 2px 0 rgba(255, 255, 255, .7);
}
.pill.pink { background: #FFD9EA; color: #8A2B5C; }
.pill.lav { background: #E6DBFF; color: #55388C; }
.pill.mint { background: #D5F4E4; color: #1F6B49; }
.pill.peach { background: #FFE3D2; color: #8A4A1E; }
.pill.blue { background: #D6EAFF; color: #214F86; }
.chip {
  display: inline-block; margin: 2px 4px 2px 0; padding: 3px 11px;
  border-radius: 99px; font-size: .74rem; font-weight: 900;
  box-shadow: inset 0 2px 0 rgba(255, 255, 255, .6);
}
.chip-none { background: #F1ECF5; color: #6B5778; }

/* ---------- progress ---------- */
.kbar {
  position: relative; height: 18px; border-radius: 99px; overflow: hidden;
  background: rgba(220, 203, 255, .4);
  box-shadow: inset 0 3px 5px rgba(120, 70, 140, .14);
}
.kbar i {
  display: block; height: 100%; width: var(--w); border-radius: 99px;
  background: linear-gradient(90deg, #FF93C1, #D6A8FF);
  box-shadow: inset 0 3px 0 rgba(255, 255, 255, .5);
  animation: grow 1.1s cubic-bezier(.2, .8, .2, 1);
  position: relative; overflow: hidden;
}
.kbar i::after {
  content: ""; position: absolute; inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, .65),
              transparent);
  background-size: 200% 100%; animation: shimmer 2.4s linear infinite;
}
.kbar-label { display: flex; justify-content: space-between;
  font-weight: 800; color: var(--plum-2); font-size: .82rem; margin: 6px 2px 4px; }

.balls { display: flex; gap: 8px; flex-wrap: wrap; margin: 4px 0 2px; }
.balls .pball { transition: transform .25s; }
.balls .pball:hover { transform: rotate(18deg) scale(1.12); }
.balls .used { filter: grayscale(1) opacity(.35); }

/* ---------- clue tiles ---------- */
.guess-row {
  display: grid; grid-template-columns: minmax(190px, 260px) 1fr; gap: 18px;
  align-items: center; padding: 14px 18px; margin: 12px 0;
  border-radius: 28px; background: var(--glass);
  border: 2px solid rgba(255, 255, 255, .95);
  box-shadow: 0 6px 0 rgba(236, 200, 226, .55),
              0 12px 22px rgba(150, 95, 170, .14), inset 0 2px 0 #fff;
  animation: pop .45s cubic-bezier(.3, 1.4, .5, 1) both;
}
.guess-who { display: flex; align-items: center; gap: 12px; }
.guess-who img.art { width: 66px; height: 66px; object-fit: contain;
  filter: drop-shadow(0 6px 6px rgba(110, 50, 130, .22)); }
.guess-who .nm { font-family: 'Fredoka', sans-serif; font-weight: 600;
  font-size: 1.15rem; color: var(--plum); line-height: 1.15; }
.guess-who .mt { font-size: .76rem; font-weight: 800; color: var(--muted); }
.tiles { display: flex; gap: 10px; flex-wrap: wrap; }
.tile {
  flex: 1 1 88px; min-width: 88px; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 0; padding: 9px 6px 8px;
  border-radius: 18px; border: 2px solid var(--tb);
  background: linear-gradient(180deg, var(--tt), var(--tbg)); color: var(--ti);
  box-shadow: 0 5px 0 var(--tb), 0 10px 14px rgba(120, 70, 140, .12),
              inset 0 2px 0 rgba(255, 255, 255, .7);
  transition: transform .2s cubic-bezier(.3, 1.5, .5, 1);
}
.tile:hover { transform: translateY(-4px) rotate(-1.5deg); }
.tile small { font-weight: 900; font-size: .62rem; letter-spacing: .14em;
  text-transform: uppercase; }
.tile b { font-family: 'Fredoka', sans-serif; font-size: 1.55rem;
  line-height: 1.1; }
.tile span { font-weight: 800; font-size: .72rem; }
.t-green { --tt: #DDF7E9; --tbg: #BCEBD2; --tb: #6FC79A; --ti: #0E4D31; }
.t-amber { --tt: #FFF0C9; --tbg: #FFE19A; --tb: #E5B54D; --ti: #6E4300; }
.t-grey { --tt: #EFECF3; --tbg: #DDD8E6; --tb: #B9B1C7; --ti: #4A4259; }
.t-up { --tt: #DCEBFF; --tbg: #BCD8FA; --tb: #86B3EE; --ti: #1B4A87; }
.t-down { --tt: #FFE0DD; --tbg: #FFC4BF; --tb: #EE958E; --ti: #8A2A25; }

/* ---------- result / turn cards ---------- */
.result-card {
  display: flex; align-items: center; gap: 22px; flex-wrap: wrap;
  padding: 24px 28px; border-radius: 32px; margin: 12px 0 18px;
  border: 2px solid #fff; animation: pop .5s cubic-bezier(.3, 1.4, .5, 1);
  box-shadow: 0 8px 0 var(--edge), 0 22px 38px rgba(150, 95, 170, .2),
              inset 0 3px 0 #fff;
}
.result-card.win { background: linear-gradient(120deg, #DDF7E9, #E8F0FF);
  --edge: #A9DDC2; }
.result-card.lose { background: linear-gradient(120deg, #FFE6E2, #F1E7FF);
  --edge: #F0B7B1; }
.result-card.neutral { background: linear-gradient(120deg, #FFE3F1, #ECE2FF);
  --edge: #EBBBD7; }
.result-card img.art { width: 150px; height: 150px; object-fit: contain;
  filter: drop-shadow(0 14px 12px rgba(110, 50, 130, .28));
  animation: floaty 5s ease-in-out infinite; }
.result-card h3 { font-family: 'Fredoka', sans-serif; font-size: 1.7rem;
  margin: 0; color: var(--plum); }
.result-card p { margin: 4px 0 0; color: var(--plum-2); font-weight: 700;
  font-size: 1.02rem; }

.mystery {
  text-align: center; padding: 18px 14px 20px; border-radius: 30px;
  background: radial-gradient(circle at 50% 30%, #fff, #FFE6F2 60%, #E9DDFF);
  border: 2px solid #fff; height: 100%;
  box-shadow: 0 7px 0 rgba(236, 200, 226, .6), var(--lift), inset 0 2px 0 #fff;
}
.mystery .qb { position: relative; display: inline-block;
  animation: wobble 3.2s ease-in-out infinite; }
.mystery .qb .q { position: absolute; right: -8px; top: -10px; width: 38px;
  height: 38px; border-radius: 50%; display: grid; place-items: center;
  background: #fff; color: var(--rose); font-family: 'Fredoka', sans-serif;
  font-weight: 700; font-size: 1.4rem; box-shadow: 0 4px 0 #EBC2D9; }
.mystery .big { font-family: 'Fredoka', sans-serif; font-weight: 600;
  font-size: 1.25rem; color: var(--plum); margin-top: 6px; }
.mystery small { color: var(--muted); font-weight: 800; }

.selected-card {
  display: flex; align-items: center; gap: 14px; padding: 14px 18px;
  border-radius: 26px; background: var(--glass); border: 2px solid #fff;
  box-shadow: 0 6px 0 rgba(236, 200, 226, .55), inset 0 2px 0 #fff;
}
.selected-card img.art { width: 92px; height: 92px; object-fit: contain;
  filter: drop-shadow(0 8px 8px rgba(110, 50, 130, .25)); }
.selected-card .nm { font-family: 'Fredoka', sans-serif; font-weight: 600;
  font-size: 1.3rem; color: var(--plum); }
.selected-card .st { font-weight: 800; color: var(--muted); font-size: .8rem; }

/* ---------- strategy cards / battle ---------- */
.strat { text-align: center; padding: 18px 14px 16px; min-height: 318px; }
.tiles-wrap { margin: 4px 0 18px; }
.strat img.art { width: 96px; height: 96px; object-fit: contain;
  filter: drop-shadow(0 10px 8px rgba(110, 50, 130, .25));
  animation: floaty 6s ease-in-out infinite; }
.strat h3 { margin-top: 4px; }
.strat p { font-size: .86rem; }
.turn-card {
  display: grid; grid-template-columns: auto 1fr auto; gap: 18px;
  align-items: center; padding: 18px 22px; border-radius: 30px;
  background: linear-gradient(120deg, #FFF, #FFF1F8 60%, #F1EAFF);
  border: 2px solid #fff; margin: 14px 0;
  box-shadow: 0 7px 0 rgba(236, 200, 226, .6), var(--lift), inset 0 2px 0 #fff;
  animation: pop .45s cubic-bezier(.3, 1.4, .5, 1);
}
.turn-card img.art { width: 100px; height: 100px; object-fit: contain;
  filter: drop-shadow(0 10px 8px rgba(110, 50, 130, .25)); }
.turn-card .nm { font-family: 'Fredoka', sans-serif; font-weight: 600;
  font-size: 1.55rem; color: var(--plum); line-height: 1.1; }
.turn-card .remain { text-align: center; padding: 8px 18px;
  border-radius: 22px; background: #fff;
  box-shadow: 0 5px 0 #F0CFE2, inset 0 2px 0 #fff; }
.turn-card .remain b { display: block; font-family: 'Fredoka', sans-serif;
  font-size: 2.2rem; color: var(--rose); line-height: 1; }
.turn-card .remain small { font-weight: 900; color: var(--muted);
  font-size: .7rem; letter-spacing: .08em; text-transform: uppercase; }

.fun-row {
  display: grid; grid-template-columns: 54px 150px 1fr 74px; gap: 12px;
  align-items: center; margin: 10px 0;
}
.fun-row img.art { width: 50px; height: 50px; object-fit: contain; }
.fun-row .nm { font-weight: 900; color: var(--plum); line-height: 1.1;
  font-size: .92rem; }
.fun-row .nm small { display: block; color: var(--muted); font-weight: 800; }
.fun-row .val { font-family: 'Fredoka', sans-serif; font-weight: 600;
  text-align: right; color: var(--rose); font-size: 1.1rem; }

/* ---------- bar charts ---------- */
.brow { display: grid; grid-template-columns: 150px 1fr 84px; gap: 14px;
  align-items: center; margin: 12px 0; }
.brow .nm { font-weight: 900; color: var(--plum); }
.btrack { height: 26px; border-radius: 99px;
  background: rgba(220, 203, 255, .38);
  box-shadow: inset 0 3px 6px rgba(120, 70, 140, .14); overflow: hidden; }
.bfill { height: 100%; width: var(--w); border-radius: 99px;
  background: linear-gradient(90deg, var(--c1), var(--c2));
  box-shadow: inset 0 3px 0 rgba(255, 255, 255, .55);
  animation: grow 1.2s cubic-bezier(.2, .8, .2, 1); }
.brow .val { font-family: 'Fredoka', sans-serif; font-weight: 600;
  text-align: right; color: var(--plum); font-size: 1.05rem; }
.c0 { --c1: #FFA6CB; --c2: #E0609A; }
.c1 { --c1: #D9C4FF; --c2: #A884EE; }
.c2 { --c1: #FFD2B5; --c2: #F2A06F; }
.c3 { --c1: #BFDDFF; --c2: #7FB2EE; }
.c4 { --c1: #BDEFD6; --c2: #6FCB9F; }

/* leaderboard */
.lb { text-align: left; padding: 20px 22px; }
.lb .rank { position: absolute; left: 14px; top: 12px; font-size: 1.7rem; }
.lb img.art { position: absolute; right: 8px; top: 6px; width: 84px;
  height: 84px; object-fit: contain; animation: floaty 7s infinite;
  filter: drop-shadow(0 8px 8px rgba(110, 50, 130, .22)); }
.lb .who { margin-top: 30px; font-family: 'Fredoka', sans-serif;
  font-weight: 600; font-size: 1.4rem; color: var(--plum); }
.lb .main { font-family: 'Fredoka', sans-serif; font-weight: 700;
  font-size: 2.3rem; color: var(--rose); line-height: 1; }
.lb .main small { font-size: .78rem; color: var(--muted); font-weight: 800;
  letter-spacing: .06em; text-transform: uppercase; margin-left: 4px; }
.lb .kv { display: grid; grid-template-columns: 1fr auto; gap: 4px 10px;
  margin-top: 12px; font-size: .86rem; font-weight: 800; color: var(--plum-2); }
.lb .kv b { color: var(--plum); text-align: right; }

/* ---------- pokédex grid ---------- */
.dex-grid { display: grid; gap: 16px;
  grid-template-columns: repeat(auto-fill, minmax(168px, 1fr)); }
.dex-card {
  position: relative; text-align: center; padding: 14px 12px 14px;
  border-radius: 28px; background: var(--glass); border: 2px solid #fff;
  box-shadow: 0 6px 0 rgba(236, 200, 226, .55),
              0 12px 22px rgba(150, 95, 170, .14), inset 0 2px 0 #fff;
  transition: transform .26s cubic-bezier(.3, 1.4, .5, 1), box-shadow .26s;
  animation: rise .5s ease both;
}
.dex-card:hover { transform: translateY(-6px) rotate(-.6deg);
  box-shadow: 0 10px 0 rgba(236, 200, 226, .55),
              0 22px 34px rgba(150, 95, 170, .22), inset 0 2px 0 #fff; }
.dex-card .no { position: absolute; left: 12px; top: 10px;
  font-size: .68rem; font-weight: 900; color: var(--muted);
  letter-spacing: .06em; }
.dex-card .gen { position: absolute; right: 12px; top: 9px; font-size: .66rem;
  font-weight: 900; color: #55388C; background: #E6DBFF; padding: 2px 8px;
  border-radius: 99px; }
.dex-card .pic { margin: 14px auto 2px; width: 104px; height: 104px;
  display: grid; place-items: center; border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, #fff, #FFE6F2 62%, #EADFFF); }
.dex-card .pic img.art { width: 92px; height: 92px; object-fit: contain;
  filter: drop-shadow(0 6px 6px rgba(110, 50, 130, .25)); }
.dex-card .nm { font-family: 'Fredoka', sans-serif; font-weight: 600;
  font-size: 1.08rem; color: var(--plum); margin-top: 6px; }
.dex-card .ms { font-size: .74rem; font-weight: 800; color: var(--muted);
  margin-top: 4px; }

.detail-grid { display: grid; grid-template-columns: repeat(2, 1fr);
  gap: 10px; margin-top: 12px; }
.detail-grid div { padding: 10px 14px; border-radius: 18px; background: #fff;
  box-shadow: 0 4px 0 #F1D9E8, inset 0 2px 0 #fff; }
.detail-grid small { display: block; font-weight: 900; font-size: .66rem;
  color: var(--muted); letter-spacing: .1em; text-transform: uppercase; }
.detail-grid b { font-family: 'Fredoka', sans-serif; font-size: 1.2rem;
  color: var(--plum); }

.legend { display: grid; gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }
.legend .tile { flex-direction: row; justify-content: flex-start; gap: 10px;
  padding: 8px 12px; text-align: left; }
.legend .tile b { font-size: 1.4rem; }
.legend .tile span { font-size: .74rem; line-height: 1.2; }

.steps { display: grid; gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
.steps .stp { padding: 14px 16px; border-radius: 22px; background: #fff;
  box-shadow: 0 5px 0 #F1D9E8, inset 0 2px 0 #fff; }
.steps .stp .n { display: inline-grid; place-items: center; width: 34px;
  height: 34px; border-radius: 50%; font-family: 'Fredoka', sans-serif;
  font-weight: 700; color: #fff; background: linear-gradient(160deg,
  #FF9BC8, #E0609A); box-shadow: 0 3px 0 #B23B78; margin-bottom: 6px; }
.steps .stp b { display: block; font-family: 'Fredoka', sans-serif;
  font-size: 1.05rem; color: var(--plum); }
.steps .stp span { color: var(--plum-2); font-weight: 600; font-size: .9rem; }

.note {
  display: flex; gap: 14px; align-items: flex-start; padding: 16px 20px;
  border-radius: 24px; background: linear-gradient(120deg, #E6F1FF, #EFE6FF);
  border: 2px solid #fff; color: var(--plum);
  box-shadow: 0 5px 0 #CDDDF3, inset 0 2px 0 #fff; font-weight: 700;
}
.note .ic { font-size: 1.5rem; }

.empty {
  text-align: center; padding: 34px 20px; border-radius: 30px;
  background: var(--glass); border: 2px dashed #E2BBD5;
}
.empty .big { font-family: 'Fredoka', sans-serif; font-size: 1.45rem;
  font-weight: 600; color: var(--plum); margin-top: 8px; }
.empty p { color: var(--plum-2); font-weight: 600; margin: 4px 0 0; }

.footer {
  text-align: center; padding: 8px 0 6px; color: var(--muted);
  font-weight: 900; letter-spacing: .22em; font-size: .72rem;
}
.footer small { display: block; letter-spacing: .3em; margin-top: 4px;
  font-size: .64rem; }

/* ---------- Streamlit widgets ---------- */
[data-testid="stBaseButton-primary"], .stButton > button[kind="primary"] {
  background: linear-gradient(180deg, #FF8FBF, #D9548F) !important;
  color: #fff !important; border: 2px solid #fff !important;
  border-radius: 20px !important; padding: .7rem 1.2rem !important;
  font-family: 'Fredoka', sans-serif !important; font-weight: 600 !important;
  font-size: 1.02rem !important; letter-spacing: .01em;
  text-shadow: 0 1px 0 rgba(120, 30, 80, .45);
  box-shadow: 0 6px 0 #A8346F, 0 14px 20px rgba(178, 59, 120, .3),
              inset 0 2px 0 rgba(255, 255, 255, .5) !important;
  transition: transform .18s cubic-bezier(.3, 1.5, .5, 1), box-shadow .18s !important;
}
[data-testid="stBaseButton-primary"]:hover,
.stButton > button[kind="primary"]:hover {
  transform: translateY(-3px) !important;
  box-shadow: 0 9px 0 #A8346F, 0 20px 26px rgba(178, 59, 120, .34),
              inset 0 2px 0 rgba(255, 255, 255, .5) !important;
}
[data-testid="stBaseButton-primary"]:active,
.stButton > button[kind="primary"]:active {
  transform: translateY(4px) !important;
  box-shadow: 0 2px 0 #A8346F, inset 0 2px 0 rgba(255, 255, 255, .4) !important;
}
[data-testid="stBaseButton-secondary"], .stButton > button[kind="secondary"],
.stDownloadButton > button {
  background: linear-gradient(180deg, #FFFFFF, #EFE6FF) !important;
  color: var(--plum) !important; border: 2px solid #fff !important;
  border-radius: 20px !important; padding: .65rem 1.1rem !important;
  font-family: 'Fredoka', sans-serif !important; font-weight: 600 !important;
  box-shadow: 0 5px 0 #CDBBF0, 0 12px 18px rgba(150, 95, 170, .16),
              inset 0 2px 0 #fff !important;
  transition: transform .18s cubic-bezier(.3, 1.5, .5, 1), box-shadow .18s !important;
}
[data-testid="stBaseButton-secondary"]:hover,
.stButton > button[kind="secondary"]:hover, .stDownloadButton > button:hover {
  transform: translateY(-3px) !important;
  box-shadow: 0 8px 0 #CDBBF0, 0 18px 24px rgba(150, 95, 170, .22),
              inset 0 2px 0 #fff !important;
}
[data-testid="stBaseButton-secondary"]:active,
.stButton > button[kind="secondary"]:active { transform: translateY(3px) !important;
  box-shadow: 0 2px 0 #CDBBF0 !important; }
.stButton > button:disabled, .stDownloadButton > button:disabled {
  opacity: .5 !important; transform: none !important; }
.stButton button p, .stDownloadButton button p {
  font-family: 'Fredoka', sans-serif !important; font-weight: 600 !important;
  font-size: 1.04rem !important; margin: 0 !important; line-height: 1.3;
}
[data-testid="stBaseButton-primary"] p { color: #fff !important; }
[data-testid="stBaseButton-secondary"] p,
.stDownloadButton button p { color: var(--plum) !important; }

[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stTextInput"] [data-baseweb="input"] {
  background: rgba(255, 255, 255, .9) !important;
  border: 2px solid #F0CFE3 !important; border-radius: 18px !important;
  box-shadow: inset 0 3px 6px rgba(150, 90, 170, .08) !important;
  color: var(--plum) !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within,
[data-testid="stTextInput"] [data-baseweb="input"]:focus-within {
  border-color: #E0609A !important;
  box-shadow: 0 0 0 4px rgba(255, 147, 193, .3) !important;
}
[data-testid="stWidgetLabel"] p, label[data-testid="stWidgetLabel"] {
  font-weight: 900 !important; color: var(--plum-2) !important;
  font-size: .86rem !important; letter-spacing: .02em;
}
[data-baseweb="popover"] ul { border-radius: 18px; }

[data-testid="stExpander"] {
  background: var(--glass); border: 2px solid #fff !important;
  border-radius: 24px !important; overflow: hidden;
  box-shadow: 0 5px 0 rgba(236, 200, 226, .55), inset 0 2px 0 #fff;
}
[data-testid="stExpander"] summary { font-weight: 900; color: var(--plum); }

[data-testid="stDataFrame"] {
  border-radius: 22px; overflow: hidden; border: 2px solid #fff;
  box-shadow: 0 6px 0 rgba(236, 200, 226, .55), var(--lift);
}
[data-testid="stAlert"] { border-radius: 22px; }
[data-testid="stImage"] img { border-radius: 18px; }

[data-testid="stSpinner"] { color: var(--rose); font-weight: 900; }
[data-testid="stSpinner"] > div > i,
[data-testid="stSpinner"] svg { color: var(--pink-3); }

.stRadio [role="radiogroup"] label p { color: var(--plum); font-weight: 800; }
.st-key-an_view [data-testid="stRadioOption"] {
  background: rgba(255, 255, 255, .9); padding: 7px 18px; margin: 0;
  border-radius: 99px; border: 2px solid #F0D4E6; cursor: pointer;
  box-shadow: 0 3px 0 #EBCBDD; transition: transform .2s;
}
.st-key-an_view [data-testid="stRadioOption"]:hover {
  transform: translateY(-2px); }
.st-key-an_view [role="radiogroup"] { gap: 10px; flex-wrap: wrap; }
.st-key-an_view [data-testid="stRadioOption"] > div > div:first-child {
  display: none; }
.st-key-an_view [data-testid="stRadioOption"]:has(input:checked) {
  background: linear-gradient(180deg, #FFB8D6, #FF8FBF);
  border-color: #fff; box-shadow: 0 3px 0 #D9548F;
}
.st-key-an_view [data-testid="stRadioOption"] p { color: var(--plum); }

[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
  color: var(--muted) !important; font-weight: 700; opacity: 1 !important;
}
[data-testid="stAppDeployButton"], .stAppDeployButton { display: none; }

.rankn {
  display: inline-grid; place-items: center; width: 30px; height: 30px;
  border-radius: 50%; font-family: 'Fredoka', sans-serif; font-weight: 700;
  font-size: .95rem; color: #fff; background: linear-gradient(160deg,
  #B79EF0, #8C6FD8); box-shadow: 0 3px 0 #6D52B5; }

hr { border-color: rgba(220, 180, 220, .5); }

/* ---------- responsive ---------- */
@media (max-width: 860px) {
  .hero3d, .hero3d.home { grid-template-columns: 1fr; padding: 26px 22px; }
  .guess-row { grid-template-columns: 1fr; }
  .turn-card { grid-template-columns: auto 1fr; }
  .turn-card .remain { grid-column: 1 / -1; }
  .brow { grid-template-columns: 96px 1fr 64px; gap: 8px; }
  .fun-row { grid-template-columns: 44px 100px 1fr 54px; gap: 8px; }
  .brand-name { font-size: 1.8rem; }
  .stage { min-height: 280px; }
  .metric3d { margin-bottom: 12px; }
  .orb { width: 66px; height: 66px; } .orb img { width: 54px; height: 54px; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important;
    transition: none !important; }
}
</style>
"""

st.markdown(THEME_CSS, unsafe_allow_html=True)


# ---------- floating background decorations (fixed, behind content) ----------

def decor_layer():
    items = [
        ("heart", 4, 14, 24, "#FF9EC8", 9, 0, -8),
        ("star", 93, 22, 26, "#FFD76B", 11, 1.5, 12),
        ("sparkle", 14, 62, 22, "#C4A7F5", 5, 0.4, 0),
        ("cloud", 80, 8, 82, "#FFFFFF", 14, 0, 0),
        ("heart", 90, 70, 20, "#FFB6D4", 10, 2, 10),
        ("sparkle", 70, 40, 18, "#FFB1D3", 4.5, 1, 0),
        ("star", 7, 82, 22, "#BCD8FA", 12, 0.8, -10),
        ("cloud", 3, 40, 96, "#FFFFFF", 16, 2, 0),
        ("sparkle", 52, 90, 20, "#FFD76B", 5.5, 0.2, 0),
        ("heart", 46, 6, 18, "#E3D2FF", 10, 1, 6),
        ("sparkle", 33, 28, 16, "#FFC8DF", 4, 2, 0),
        ("cloud", 60, 78, 90, "#FFFFFF", 18, 1, 0),
    ]
    spans = []
    for kind, x, y, size, color, dur, delay, rot in items:
        tw = " tw" if kind == "sparkle" else ""
        op = "opacity:.85;" if kind == "cloud" else ""
        spans.append(
            f'<span class="{tw.strip()}" style="left:{x}%;top:{y}%;{op}'
            f'--d:{dur}s;--dl:{delay}s;--r:{rot}deg">'
            f'{shape(kind, color, size)}</span>'
        )
    md('<div class="fx" aria-hidden="true">' + "".join(spans) + "</div>")


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


def section_title(text, icon="shape"):
    ornament = shape("sparkle", "#E0609A", 24)
    md(
        f'<div class="sec-title"><span class="orn">{ornament}</span>'
        f'<span>{esc(text)}</span></div>'
    )


def hero(kicker, title, subtitle, art=None, chips=()):
    """Page hero banner (kicker / title / subtitle / optional artwork)."""
    pills = "".join(
        f'<span class="pill {tone}">{esc(label)}</span>'
        for label, tone in chips
    )
    art_html = ""
    if art:
        art_html = (
            '<div class="hero-art">'
            f'{art_img(art, 260)}'
            f'<span class="deco" style="left:10%;top:12%">'
            f'{shape("sparkle", "#E0609A", 26)}</span>'
            f'<span class="deco fl" style="right:8%;top:8%">'
            f'{shape("heart", "#FF8FBF", 30)}</span>'
            f'<span class="deco" style="right:14%;bottom:10%">'
            f'{shape("star", "#FFD76B", 26)}</span>'
            '</div>'
        )
    md(
        '<section class="hero3d"><div>'
        f'<span class="eyebrow">{esc(kicker)}</span>'
        f'<div class="ht" role="heading" aria-level="1">{title}</div>'
        f'<p class="lead">{esc(subtitle)}</p>{pills}</div>{art_html}</section>'
    )


def metric(label, value, sub="", icon="✨", tone="pink"):
    md(
        f'<div class="metric3d tone-{tone}"><div class="ic">{icon}</div><div>'
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
    """Large artwork with an optional caption."""
    cap = (
        f'<div style="font-family:Fredoka;font-weight:600;color:#5B4468;'
        f'margin-top:4px">{esc(caption)}</div>' if caption else ""
    )
    md(
        '<div style="text-align:center">'
        f'{art_img(name, width)}{cap}</div>'
    )


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
            f'{art_img(guess["name"], 66)}'
            '<div>'
            f'<div class="nm">{idx}. {esc(guess["name"])}</div>'
            f'<div>{type_chips(guess)}</div>'
            f'<div class="mt">Generation {esc(guess["gen"])}</div>'
            '</div></div>'
            f'{clue_tiles(clue)}</div>'
        )


def progress_bar(fraction, left_label="", right_label=""):
    pct = max(0.0, min(1.0, fraction)) * 100
    labels = ""
    if left_label or right_label:
        labels = (
            f'<div class="kbar-label"><span>{esc(left_label)}</span>'
            f'<span>{esc(right_label)}</span></div>'
        )
    md(f'{labels}<div class="kbar"><i style="--w:{pct:.1f}%"></i></div>')


def attempt_balls(used, total):
    balls = "".join(
        pokeball(34, "used" if i < used else "")
        for i in range(total)
    )
    md(f'<div class="balls" role="img" aria-label="{total - used} of '
       f'{total} attempts left">{balls}</div>')


def bar_chart(rows, unit="", decimals=2, tone_offset=0, max_value=None):
    """Animated horizontal bars. rows = [(label, value), ...]."""
    values = [v for _, v in rows]
    top = max_value or (max(values) if values else 1) or 1
    out = []
    for i, (label, value) in enumerate(rows):
        width = max(2.5, value / top * 100)
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
    ("W", "#FFD0E5", "#F0A9CB"), ("O", "#E3D6FF", "#C7B2F0"),
    ("R", "#FFE0CC", "#F2BE9C"), ("D", "#CFE6FF", "#A7CCF0"),
    ("L", "#D3F4E3", "#A9DEC3"), ("E", "#FFD0E5", "#F0A9CB"),
]
logo_tiles = "".join(
    f'<b style="--bg:{bg};--sh:{sh}">{letter}</b>'
    for letter, bg, sh in LOGO_TILES
)

md(
    '<div class="brand">'
    f'{pokeball(64)}'
    '<div><div class="brand-name">Pokémon</div>'
    f'<div class="brand-tiles">{logo_tiles}</div></div>'
    '</div>'
    '<div class="brand-sub" style="text-align:center">RESEARCH LAB</div>'
)

md(
    '<div class="sub-line">✦ PROFESSOR OAK’S INTELLIGENCE LABORATORY ✦</div>'
)

PAGE_DEFS = [
    ("🏠", "Home", "Welcome Hub"),
    ("🎮", "Pokédex Challenge", "Pokédex Challenge"),
    ("🤖", "AI Battle Arena", "AI Battle Arena"),
    ("📊", "Analytics", "Professor’s Analytics"),
    ("📚", "Dataset Explorer", "Dataset Explorer"),
]
NAV_LABELS = [f"{icon}  {label}" for icon, label, _ in PAGE_DEFS]
page_map = {
    f"{icon}  {label}": page for icon, label, page in PAGE_DEFS
}
NAV = {page: f"{icon}  {label}" for icon, label, page in PAGE_DEFS}

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

    stage = (
        '<div class="stage">'
        f'{art_img("Pikachu", 300, "main")}'
        f'<div class="orb" style="left:2%;top:6%;--d:7s">'
        f'{art_img("Eevee", 70)}</div>'
        f'<div class="orb" style="right:0;top:2%;--d:8s;--dl:1s">'
        f'{art_img("Sylveon", 70)}</div>'
        f'<div class="orb" style="left:0;bottom:6%;--d:9s;--dl:.5s">'
        f'{art_img("Vulpix", 70)}</div>'
        f'<div class="orb" style="right:2%;bottom:4%;--d:7.5s;--dl:1.5s">'
        f'{art_img("Piplup", 70)}</div>'
        f'<span class="deco fl" style="left:44%;top:-2%">'
        f'{shape("heart", "#FF8FBF", 32)}</span>'
        f'<span class="deco" style="left:20%;top:44%">'
        f'{shape("sparkle", "#FFC857", 28)}</span>'
        f'<span class="deco" style="right:16%;top:46%">'
        f'{shape("star", "#FFD76B", 26)}</span>'
        '</div>'
    )

    md(
        '<section class="hero3d home"><div>'
        '<span class="eyebrow">✦ WELCOME, TRAINER ✦</span>'
        '<div class="ht" role="heading" aria-level="1">'
        'Welcome to the <em>Pokémon</em> World!</div>'
        '<p class="lead">A world of mystery, intelligent guessing and '
        'Pokémon discovery. Explore the Pokédex, challenge yourself and '
        'watch AI strategies compete.</p>'
        f'<span class="pill pink">{len(POKEMON)} species</span>'
        f'<span class="pill lav">{n_gen} generations</span>'
        f'<span class="pill mint">{MAX_GUESSES} guesses per mystery</span>'
        f'<span class="pill peach">4 AI strategies</span>'
        f'</div>{stage}</section>'
    )

    cta1, cta2, cta3 = st.columns([1.1, 1.1, 2])
    with cta1:
        st.button(
            "🎮  Start the Challenge", type="primary", key="cta_play",
            on_click=go, args=(NAV["Pokédex Challenge"],), **STRETCH,
        )
    with cta2:
        st.button(
            "🤖  Watch an AI Battle", key="cta_battle",
            on_click=go, args=(NAV["AI Battle Arena"],), **STRETCH,
        )

    section_title("Trainer Crew")
    roster = ["Eevee", "Pikachu", "Vulpix", "Piplup", "Sylveon"]
    cols = st.columns(len(roster))
    for col, name in zip(cols, roster):
        with col:
            md(
                '<div class="k-card" style="text-align:center;'
                'padding:14px 10px">'
                f'{art_img(name, 112)}'
                f'<div style="font-family:Fredoka;font-weight:600;'
                f'color:#3F2A4A">{esc(name)}</div></div>'
            )

    section_title("Research Lab Overview")

    stats = [
        ("Pokémon indexed", len(POKEMON), "Species in the dataset", "🌸", "pink"),
        ("Generations", n_gen, "Across the Pokédex", "🌈", "lav"),
        ("Clue dimensions", len(CLUE_LABELS), "Attributes used by the game", "🧩", "peach"),
        ("Guess limit", MAX_GUESSES, "Attempts per mystery", "🎯", "blue"),
    ]
    cols = st.columns(4)
    for col, item in zip(cols, stats):
        with col:
            metric(*item)

    section_title("Explore the Laboratory")

    cards = [
        ("🎮", "Pokédex Challenge", "Human vs Mystery",
         "Solve a hidden Pokémon using five clue dimensions.",
         "Sylveon", "pink", "Pokédex Challenge"),
        ("🤖", "AI Battle Arena", "Intelligent Guessing",
         "Watch four strategies investigate the same mystery.",
         "Mimikyu", "lav", "AI Battle Arena"),
        ("📊", "Analytics", "Performance Insights",
         "Compare measured results from benchmark experiments.",
         "Mew", "peach", "Professor’s Analytics"),
        ("📚", "Dataset Explorer", "Pokédex Collection",
         "Search, filter and inspect the real dataset.",
         "Togepi", "blue", "Dataset Explorer"),
    ]
    cols = st.columns(4)
    for col, (emoji, title, tagline, desc, mascot, tone, target) in zip(cols, cards):
        with col:
            md(
                f'<div class="k-card nav-card tone-{tone}">'
                f'{art_img(mascot, 86, "corner")}'
                f'<div class="emoji">{emoji}</div>'
                f'<h3>{esc(title)}</h3>'
                f'<span class="tagline">{esc(tagline)}</span>'
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
            '<div class="k-card"><h3>How a mystery is solved</h3>'
            '<p>Every guess returns five clues. The laboratory\'s four '
            'strategies and your own detective skills all play by the '
            'same rules.</p>'
            '<div class="steps" style="margin-top:14px">'
            '<div class="stp"><div class="n">1</div><b>Make a guess</b>'
            '<span>Pick any Pokémon from the Pokédex.</span></div>'
            '<div class="stp"><div class="n">2</div><b>Read the clues</b>'
            '<span>Generation, both types, height and weight.</span></div>'
            '<div class="stp"><div class="n">3</div><b>Narrow it down</b>'
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
                f'<h3 style="margin-top:6px">{esc(glimpse[0])} leads the lab</h3>'
                f'<p>Lowest average in the saved results: '
                f'<b style="color:#B23B78">{glimpse[1]:.2f} guesses</b>. '
                'Open Analytics for the full scoreboard.</p></div>'
            )
        else:
            md(
                '<div class="k-card"><span class="tagline">BENCHMARKS</span>'
                '<h3 style="margin-top:6px">No saved results yet</h3>'
                '<p>Run benchmark.py to generate results_table.csv and '
                'unlock the Analytics lab.</p></div>'
            )

    section_title("Trainer Statistics")

    played = st.session_state.human_games_played
    won = st.session_state.human_games_won
    win_rate = won / played * 100 if played else 0

    cols = st.columns(3)

    with cols[0]:
        metric("Games completed", played, "Current session", "🎀", "pink")

    with cols[1]:
        metric("Mysteries solved", won, "Current session", "🏆", "mint")

    with cols[2]:
        metric("Win rate", f"{win_rate:.1f}%", "Current session", "💖", "lav")

    md('<div style="height:14px"></div>')
    md(
        '<div class="note"><span class="ic">💡</span><div><b>How to play:</b> '
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
        art="Sylveon",
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
                f'{art_img(secret_name, 150)}'
                '<div><h3>You found '
                f'{esc(secret_name)}! 🎉</h3>'
                f'<p>Solved in {len(game.history)} of {MAX_GUESSES} '
                'guesses. What a brilliant trainer!</p>'
                f'<div style="margin-top:8px">{type_chips(game.secret)}'
                f'<span class="pill lav">Gen {esc(game.secret["gen"])}</span>'
                '</div></div></div>'
            )
        else:
            md(
                '<div class="result-card lose">'
                f'{art_img(secret_name, 150)}'
                f'<div><h3>The mystery was {esc(secret_name)}</h3>'
                '<p>Better luck next time — every clue makes you sharper!</p>'
                f'<div style="margin-top:8px">{type_chips(game.secret)}'
                f'<span class="pill lav">Gen {esc(game.secret["gen"])}</span>'
                '</div></div></div>'
            )

        if game.history:
            section_title("Your Clue Trail")
            render_clue_history(game.history)

        if st.button("🌷  Start Another Mystery", type="primary", **STRETCH):
            st.session_state.human_game = Game(POKEMON)
            st.session_state.human_celebrated = False
            st.rerun()

    else:

        remaining = MAX_GUESSES - len(game.history)

        intro, mystery = st.columns([1.7, 1])

        with intro:
            md(
                '<div class="k-card"><h3>🌸 Welcome to the Mystery Meadow</h3>'
                '<p>Every guess reveals five pieces of feedback. Green means '
                'a match; directional clues help you understand numeric '
                'attributes. Pick a Pokémon, submit your guess and watch the '
                'possible species melt away.</p>'
                f'<span class="pill pink">5 clue dimensions</span>'
                f'<span class="pill lav">{MAX_GUESSES} guesses max</span>'
                f'<span class="pill mint">{len(POKEMON)} species</span></div>'
            )

        with mystery:
            md(
                '<div class="mystery"><div class="qb">'
                f'{pokeball(104)}<span class="q">?</span></div>'
                '<div class="big">A wild mystery appeared!</div>'
                '<small>Can you identify it?</small></div>'
            )

        section_title("Your Challenge")

        cols = st.columns(3)

        with cols[0]:
            metric("Attempts left", remaining, f"of {MAX_GUESSES}", "🎯", "pink")

        with cols[1]:
            metric("Guesses made", len(game.history), "Study the clues", "🔍", "lav")

        with cols[2]:
            metric(
                "Possible species",
                len(filter_candidates(POKEMON, game.history)),
                "Consistent with clues",
                "🌟",
                "peach",
            )

        md('<div style="height:12px"></div>')
        attempt_balls(len(game.history), MAX_GUESSES)
        progress_bar(
            min(len(game.history) / MAX_GUESSES, 1.0),
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
                "💗  Submit My Guess",
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
                f'{art_img(guess_name, 92)}<div>'
                f'<div class="nm">{esc(guess_name)}</div>'
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
                '<div class="big">Your First Clue Is Waiting</div>'
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
        art="Mimikyu",
        chips=[("4 strategies", "pink"), ("Step-by-step playback", "lav"),
               ("Real clue rules", "mint")],
    )

    STRATEGIES = [
        ("Random baseline", "Mimikyu", "No clue usage",
         "Chooses an unguessed Pokémon without using clue information."),
        ("Filter-based", "Piplup", "Consistency filter",
         "Removes candidates inconsistent with observed feedback."),
        ("Entropy", "Gengar", "Information gain",
         "Selects a guess expected to divide candidates into informative "
         "feedback groups."),
        ("Minimax", "Sprigatito", "Worst-case control",
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
                f'{art_img(mascot, 96)}<h3>{esc(name)}</h3>'
                f'<span class="tagline">{esc(tag)}</span>'
                f'<p>{esc(desc)}</p></div>'
            )
            st.button(
                "✓  Selected" if chosen_now else "Choose",
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

    if st.button("⚡  Prepare AI Battle", type="primary", **STRETCH):

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
            metric("Strategy", battle["strategy"], "Selected agent", "🧠", "pink")

        with top[1]:
            metric("Turn revealed", f"{step}/{len(rows)}",
                   "Step-by-step playback", "🎬", "lav")

        left_now = (
            len(POKEMON) if step == 0
            else rows[step - 1]["Candidates remaining"]
        )

        with top[2]:
            metric("Candidates left", left_now, "After revealed turns",
                   "🔭", "peach")

        md('<div style="height:10px"></div>')

        if step == 0:

            md(
                '<div class="k-card" style="text-align:center">'
                f'{pokeball(70)}'
                f'<h3 style="margin-top:6px">The AI has {len(POKEMON)} '
                'possible answers</h3>'
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
                remain_html = '<b>🎉</b><small>found it!</small>'
            else:
                remain_html = (
                    f'<b>{current["Candidates remaining"]}</b>'
                    '<small>candidates remain</small>'
                )

            md(
                '<div class="turn-card">'
                f'{art_img(current["AI guess"], 100)}'
                '<div>'
                f'<span class="pill pink">TURN {current["Turn"]}</span>'
                f'<div class="nm">{esc(current["AI guess"])}</div>'
                f'<div>{type_chips(guess_record) if guess_record else ""}'
                f'<span class="pill lav">Gen {esc(current["Generation"])}'
                '</span></div></div>'
                f'<div class="remain">{remain_html}</div></div>'
            )

            if clue_html:
                md(f'<div class="tiles-wrap">{clue_html}</div>')

        progress_bar(
            step / len(rows),
            f"Turn {step} of {len(rows)}",
            "Playback",
        )

        if step > 0:

            section_title("Candidate Reduction")

            funnel = [
                '<div class="k-card" style="padding:14px 22px">'
            ]
            for i, row in enumerate(rows[:step]):
                width = max(2.5, row["Candidates remaining"] / len(POKEMON) * 100)
                funnel.append(
                    '<div class="fun-row">'
                    f'{art_img(row["AI guess"], 50)}'
                    f'<div class="nm">{esc(row["AI guess"])}'
                    f'<small>Turn {row["Turn"]}</small></div>'
                    '<div class="btrack"><div class="bfill '
                    f'c{i % 5}" style="--w:{width:.1f}%"></div></div>'
                    f'<div class="val">{row["Candidates remaining"]}</div>'
                    '</div>'
                )
            funnel.append("</div>")
            md("".join(funnel))

            show_df(pd.DataFrame(rows[:step]))

        prev_col, next_col, reset_col = st.columns(3)

        with prev_col:
            if st.button(
                "←  Previous Turn",
                disabled=step == 0,
                **STRETCH,
            ):
                st.session_state.battle_step = max(0, step - 1)
                st.rerun()

        with next_col:
            if st.button(
                "Reveal Next Turn  →",
                type="primary",
                disabled=step >= len(rows),
                **STRETCH,
            ):
                st.session_state.battle_step = min(len(rows), step + 1)
                st.rerun()

        with reset_col:
            if st.button("↺  Restart Playback", **STRETCH):
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
                    f'{art_img(battle["secret"], 150)}'
                    '<div><h3>🎉 Mystery Solved!</h3>'
                    f'<p>{esc(battle["strategy"])} identified '
                    f'<b>{esc(battle["secret"])}</b> in '
                    f'<b>{len(rows)} guesses</b>.</p></div></div>'
                )
            else:
                md(
                    '<div class="result-card lose">'
                    f'{art_img(battle["secret"], 150)}'
                    '<div><h3>Guess limit reached</h3>'
                    f'<p>The hidden Pokémon was '
                    f'<b>{esc(battle["secret"])}</b>.</p></div></div>'
                )

            with st.expander("View the Complete Battle Log"):
                show_df(pd.DataFrame(rows))

            counts = [len(POKEMON)] + [
                row["Candidates remaining"] for row in rows
            ]

            fig, ax = plt.subplots(figsize=(9, 3.4))
            fig.patch.set_facecolor((1, 1, 1, 0))
            ax.set_facecolor((1, 1, 1, 0))

            ax.plot(
                range(len(counts)), counts,
                color="#E0609A", marker="o", linewidth=3.2,
                markersize=10, markerfacecolor="white",
                markeredgewidth=3, markeredgecolor="#E0609A",
            )
            ax.fill_between(range(len(counts)), counts, color="#FF93C1",
                            alpha=0.25)

            for x, y in enumerate(counts):
                ax.annotate(
                    str(y), (x, y), textcoords="offset points",
                    xytext=(0, 11), ha="center", color="#3F2A4A",
                    fontweight="bold", fontsize=10,
                )

            ax.set_xticks(range(len(counts)))
            ax.set_xlabel("After guess", color="#5B4468", fontweight="bold")
            ax.set_ylabel("Possible answers", color="#5B4468",
                          fontweight="bold")
            ax.set_title("Candidate Search Space", color="#3F2A4A",
                         fontweight="bold", fontsize=14, pad=12)
            ax.set_ylim(bottom=0, top=max(counts) * 1.15)
            ax.tick_params(colors="#5B4468")
            ax.grid(alpha=0.25, color="#B79EF0", linestyle="--")
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
            for side in ("left", "bottom"):
                ax.spines[side].set_color("#D8C4EE")

            fig.tight_layout()
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
            '<div class="big">Your AI Challenger Is Ready</div>'
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
        "random": "Mimikyu", "filter": "Piplup",
        "entropy": "Gengar", "minimax": "Sprigatito",
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
                    "🥇", "pink",
                )

            with c2:
                metric(
                    "Best worst case",
                    int(df["Worst case"].min()),
                    "Guesses",
                    "🛡️", "lav",
                )

            with c3:
                metric("Strategies", len(df), "In saved benchmark", "🤖", "peach")

            with c4:
                runs = int(df["Runs"].sum()) if "Runs" in df.columns else "—"
                metric(
                    "Total runs", runs,
                    "As recorded in CSV" if "Runs" in df.columns
                    else "Not recorded in this CSV",
                    "🔁", "blue",
                )

            section_title("Benchmark Scoreboard")

            ranked = df.sort_values("Avg guesses").reset_index(drop=True)
            medals = ["🥇", "🥈", "🥉"]
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
                with col:
                    md(
                        f'<div class="k-card lb tone-{tones[i % 4]}">'
                        '<div class="rank">'
                        + (medals[i] if i < 3
                           else f'<span class="rankn">{i + 1}</span>')
                        + '</div>'
                        f'{art_img(mascot, 84) if mascot else ""}'
                        f'<div class="who">{esc(row["Solver"])}</div>'
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
                '<div class="k-card"><h3>Average guesses by strategy</h3>'
                '<p style="margin-bottom:8px">Lower is better.</p>'
                + bar_chart(
                    list(zip(plot_df["Solver"], plot_df["Avg guesses"]))
                )
                + '</div>'
            )

            md('<div style="height:14px"></div>')

            pct_cols = [
                c for c in df.columns
                if c == "Win rate" or str(c).startswith("Solved")
            ]
            for pc in pct_cols:
                md(
                    f'<div class="k-card"><h3>{esc(pc)}</h3>'
                    '<p style="margin-bottom:8px">Higher is better.</p>'
                    + bar_chart(
                        list(zip(ranked["Solver"], ranked[pc])),
                        unit="%", decimals=1, max_value=100,
                    )
                    + '</div>'
                )
                md('<div style="height:14px"></div>')

            section_title("Benchmark Table")

            try:
                lower = [c for c in ("Avg guesses", "Worst case", "Std dev")
                         if c in df.columns]
                higher = [c for c in df.columns
                          if c == "Win rate" or str(c).startswith("Solved")]
                numeric = [c for c in df.columns
                           if pd.api.types.is_numeric_dtype(df[c])]
                styled = df.style.format(fmt_num, subset=numeric)
                if lower:
                    styled = styled.highlight_min(
                        subset=lower, color="#CFF3E1")
                if higher:
                    styled = styled.highlight_max(
                        subset=higher, color="#CFF3E1")
                show_df(styled)
            except Exception:
                show_df(df)

            st.caption("Green cells mark the best value in each column.")

            section_title("How the Four Strategies Work")

            how = [
                ("🎲", "Random baseline", "pink",
                 "Chooses an unguessed Pokémon without using clue "
                 "information."),
                ("🧹", "Filter-based", "lav",
                 "Removes candidates inconsistent with observed feedback."),
                ("📡", "Entropy", "peach",
                 "Selects a guess expected to divide candidates into "
                 "informative feedback groups."),
                ("🛡️", "Minimax", "blue",
                 "Minimizes the largest possible remaining candidate group."),
            ]
            cols = st.columns(4)
            for col, (ico, nm, tone, txt) in zip(cols, how):
                with col:
                    md(
                        f'<div class="k-card nav-card tone-{tone}">'
                        f'<div class="emoji">{ico}</div><h3>{esc(nm)}</h3>'
                        f'<p>{esc(txt)}</p></div>'
                    )

            section_title("Research Statistics")

            data_df = pd.DataFrame(POKEMON)
            gen_counts = data_df["gen"].value_counts().sort_index()
            type_counts = data_df["type1"].value_counts().head(8)

            g_col, t_col = st.columns(2)
            with g_col:
                md(
                    '<div class="k-card"><h3>Species per generation</h3>'
                    + bar_chart(
                        [(f"Generation {g}", float(c))
                         for g, c in gen_counts.items()],
                        decimals=0,
                    ) + '</div>'
                )
            with t_col:
                md(
                    '<div class="k-card"><h3>Most common primary types</h3>'
                    + bar_chart(
                        [(t, float(c)) for t, c in type_counts.items()],
                        decimals=0, tone_offset=2,
                    ) + '</div>'
                )

            md('<div style="height:14px"></div>')

            st.download_button(
                "⬇  Download Benchmark CSV",
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
            '<div class="big">The scoreboard is waiting for data</div>'
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
        metric("Species", len(df), "Loaded from pokemon.csv", "🌸", "pink")

    with c2:
        metric("Primary types", df.type1.nunique(), "Unique categories",
               "🎨", "lav")

    with c3:
        metric("Generations", df.gen.nunique(), "Generation values",
               "🌈", "peach")

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
            '<div class="big">No Pokémon found</div>'
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
                f'<span class="gen">Gen {esc(rec["gen"])}</span>'
                f'<div class="pic">{art_img(rec["name"], 92)}</div>'
                f'<div class="nm">{esc(rec["name"])}</div>'
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
            md(
                '<div class="mystery">'
                f'{art_img(chosen, 190)}'
                f'<div class="big">{esc(chosen)}</div>'
                f'<small>{"No. %03d" % pokemon_id(chosen) if pokemon_id(chosen) else ""}'
                '</small></div>'
            )

        with detail_col:
            md(
                '<div class="k-card">'
                f'<h3>{esc(chosen)}</h3>'
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

        md('<div style="height:14px"></div>')

        st.download_button(
            "⬇  Export Filtered Dataset",
            view.to_csv(index=False).encode(),
            file_name="pokemon_dataset_filtered.csv",
            mime="text/csv",
        )


# ============================================================
# FOOTER
# ============================================================

md(
    '<div class="divider" style="margin-top:34px"></div>'
    '<div class="footer">'
    f'{pokeball(30)}<br>'
    'POKÉMON WORDLE · RESEARCH LAB'
    '<small>THINK · GUESS · DISCOVER · REPEAT</small></div>'
)
