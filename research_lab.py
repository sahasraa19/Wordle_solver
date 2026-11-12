


import os
import html
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from loader import load_pokemon
from engine import Game, MAX_GUESSES
from basic_solvers import random_solver, filter_solver, filter_candidates
from entropy_solver import EntropySolver
from minimax_solver import MinimaxSolver


# ==================================================
# CONFIGURATION
# ==================================================

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "pokemon.csv")
RESULTS = os.path.join(ROOT, "results")

POKEMON = load_pokemon(DATA)
BY_NAME = {p["name"]: p for p in POKEMON}
NAMES = sorted(BY_NAME)

st.set_page_config(
    page_title="Pokémon Wordle · Professor Oak's Lab",
    page_icon="💗",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================================================
# POKÉMON HOME-STYLE ARTWORK
# ==================================================

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


# ==================================================
# PREMIUM KAWAII DESIGN
# ==================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&display=swap');

:root {
    --ink: #30283f;
    --muted: #81758e;
    --pink: #e99aba;
    --pink-deep: #cc7099;
    --pink-soft: #fff0f6;
    --lavender: #eee8ff;
    --border: #f0dfeb;
}

html, body, [class*="css"] {
    font-family: 'Nunito', sans-serif !important;
    color: var(--ink);
}

.stApp {
    background:
        radial-gradient(ellipse at 3% 5%, #ffeaf3 0%, transparent 32%),
        radial-gradient(ellipse at 96% 8%, #eee9ff 0%, transparent 30%),
        #fffdfb;
}

.block-container {
    max-width: 1260px;
    padding-top: 1.6rem;
    padding-bottom: 3rem;
}

h1, h2, h3, h4 {
    color: var(--ink) !important;
    font-weight: 900 !important;
}

p, li, label {
    color: var(--ink);
}

/* SIDEBAR */

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #fff0f6 0%, #f1ebff 100%);
    border-right: 1px solid #f1dce8;
}

[data-testid="stSidebar"] * {
    color: #59445f;
    font-weight: 700;
}

[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    gap: 9px;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    background: rgba(255,255,255,0.5);
    border: 1px solid transparent;
    border-radius: 15px;
    padding: 10px 13px;
    transition: all .2s ease;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: white;
    border-color: #f2c8dc;
    transform: translateX(3px);
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(135deg, #f9c8dc, #f0dff5);
    border: 1px solid #edb6d0;
    box-shadow: 0 5px 15px #d98bae25;
    color: #753e60 !important;
}

/* BRAND */

.lab-brand {
    text-align: center;
    padding: 12px 5px 20px;
}

.lab-brand-ball {
    width: 66px;
    height: 66px;
    margin: auto;
    border-radius: 50%;
    background: linear-gradient(145deg, #fff, #f5c8dc);
    box-shadow: 0 6px 0 #e8b4ce, 0 12px 22px #d99cbd55;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 35px;
}

.lab-brand h3 {
    margin: 15px 0 3px;
    color: #70425e !important;
}

.lab-brand p {
    color: #92788d;
    font-size: 12px;
}

/* HERO */

.lab-hero {
    position: relative;
    overflow: hidden;
    padding: 28px 30px;
    border-radius: 26px;
    background: linear-gradient(120deg, #fff0f6, #f0ebff 75%, #fff9fc);
    border: 1px solid #f1dfeb;
    box-shadow: 0 12px 30px #9b73951a;
    margin-bottom: 20px;
}

.lab-hero:after {
    content: "✦";
    position: absolute;
    right: 35px;
    top: 4px;
    font-size: 82px;
    color: #e9b9d2;
    opacity: .5;
}

.lab-hero .eyebrow {
    color: #c16c96;
    font-weight: 900;
    letter-spacing: 2px;
    font-size: .76rem;
}

.lab-hero h1 {
    font-size: 2.15rem;
    margin: 7px 0;
}

.lab-hero p {
    color: #786d83;
    max-width: 760px;
    margin-bottom: 0;
}

/* CARDS */

.panel {
    background: linear-gradient(145deg, #fff, #fff8fc);
    border: 1px solid #f0e2eb;
    border-radius: 22px;
    padding: 21px;
    box-shadow: 0 5px 0 #f3e4ed, 0 12px 25px #8c64851c;
}

.panel h3 {
    margin-top: 0;
}

.art-panel {
    background: radial-gradient(circle at 50% 42%, #fff 0%, #fff0f6 65%, #eee8ff 100%);
    border: 1px solid #f0dfeb;
    border-radius: 25px;
    padding: 10px 14px;
    box-shadow: 0 6px 0 #f1e1eb, 0 15px 28px #8c64851c;
    text-align: center;
}

.art-panel img {
    filter: drop-shadow(0 12px 10px #8c648530);
}

/* METRICS */

.metric {
    background: linear-gradient(145deg, #fff, #fff5fa);
    border: 1px solid #f1e1eb;
    border-radius: 19px;
    padding: 16px;
    box-shadow: 0 5px 0 #f2e4ec, 0 10px 20px #9b739515;
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-height: 104px;
}

.metric small {
    color: #897b91;
    font-weight: 800;
}

.metric b {
    color: #cf719b;
    font-size: 1.65rem;
    font-weight: 900;
    overflow-wrap: anywhere;
}

.metric span {
    color: #8a90a3;
    font-size: .8rem;
}

/* PILLS */

.pill {
    display: inline-block;
    border-radius: 999px;
    padding: 5px 11px;
    margin: 3px;
    font-size: .78rem;
    font-weight: 900;
}

/* BUTTONS */

.stButton > button {
    background: linear-gradient(135deg, #e99aba, #d97ca5);
    color: white !important;
    border: 1px solid #df8caf;
    border-radius: 15px;
    padding: .66rem 1rem;
    font-weight: 900;
    box-shadow: 0 4px 0 #c96e96, 0 8px 17px #d98bae30;
    transition: all .18s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 0 #c96e96, 0 12px 20px #d98bae40;
}

.stButton > button:disabled {
    opacity: .45;
}

.stDownloadButton > button {
    background: #eee8ff;
    color: #51416f !important;
    border: 1px solid #dcd0fa;
    border-radius: 12px;
    font-weight: 800;
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid var(--border);
    padding: 15px;
    border-radius: 18px;
    box-shadow: 0 5px 18px #3330440a;
}

div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #cf719b !important;
    font-weight: 900 !important;
}

div[data-testid="stSelectbox"] > div > div,
div[data-testid="stTextInput"] input {
    background: white;
    border-radius: 12px;
    border-color: #edd9e5;
    color: var(--ink);
}

div[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
}

.stAlert, [data-testid="stExpander"] {
    border-radius: 15px;
}

[data-testid="stExpander"] {
    background: white;
    border: 1px solid var(--border);
}

.battle-result {
    background: linear-gradient(120deg, #fff0f6, #f0ebff);
    border: 1px solid #efd9e8;
    border-radius: 22px;
    padding: 22px;
    box-shadow: 0 7px 20px #9b73951a;
}

.game-tile {
    background: white;
    border: 1px solid #f0dce9;
    border-radius: 15px;
    padding: 12px;
    text-align: center;
    box-shadow: 0 4px 0 #f4e5ed;
}

.game-tile b {
    display: block;
    color: #6d4967;
    font-size: 1.02rem;
}

.turn-card {
    background: linear-gradient(120deg, #fff, #fff6fb);
    border: 1px solid #f0dfeb;
    border-radius: 17px;
    padding: 13px 16px;
    margin: 8px 0;
}

.footer-text {
    text-align: center;
    color: #a18ca3;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1px;
    padding: 26px 0 8px;
}

hr {
    border-color: #f0e1eb;
}

footer, #MainMenu {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


# ==================================================
# REUSABLE COMPONENTS
# ==================================================

def hero(kicker, title, subtitle):
    st.markdown(
        f'<div class="lab-hero"><div class="eyebrow">{kicker}</div>'
        f'<h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def metric(label, value, sub=""):
    st.markdown(
        f'<div class="metric"><small>{html.escape(str(label))}</small>'
        f'<b>{html.escape(str(value))}</b><span>{html.escape(str(sub))}</span></div>',
        unsafe_allow_html=True,
    )


def clue_chip(label, value):
    colors = {
        "green": ("#d9f7e8", "#126b43", "✓"),
        "amber": ("#fff0c7", "#8a5b00", "◆"),
        "grey": ("#e9ebf1", "#606779", "×"),
        "up": ("#dcecff", "#245b9b", "↑"),
        "down": ("#ffe1df", "#a43e39", "↓"),
    }

    bg, fg, symbol = colors.get(
        str(value).lower(),
        ("#eee", "#333", "•")
    )

    st.markdown(
        f'<span class="pill" style="background:{bg};color:{fg}">'
        f'{html.escape(str(label))}: {symbol} '
        f'{html.escape(str(value).title())}</span>',
        unsafe_allow_html=True,
    )


def pokemon_art(name, caption=None, width=190):
    """Show genuine Pokémon HOME-style artwork for mapped Pokédex entries."""
    pokemon_id = ART_IDS.get(name)

    if pokemon_id:
        st.image(
            ART_URL.format(pokemon_id=pokemon_id),
            caption=caption,
            width=width,
        )
    else:
        st.markdown(
            f'<div style="padding:25px 5px;text-align:center;color:#9b7893">'
            f'<div style="font-size:42px">✦</div>'
            f'<b>{html.escape(name)}</b>'
            f'<div style="font-size:12px">Pokédex entry</div></div>',
            unsafe_allow_html=True,
        )


def art_card(name, caption=None, width=175):
    with st.container(border=True):
        pokemon_art(name, caption, width)


def safe_types(pokemon):
    return (
        f"{pokemon.get('type1', '—')} / "
        f"{pokemon.get('type2') or '—'}"
    )


def render_clue_history(history):
    labels = ["Generation", "Type 1", "Type 2", "Height", "Weight"]

    for idx, (guess, clue) in enumerate(history, 1):
        with st.container(border=True):
            st.markdown(
                f"**Guess {idx}: {guess['name']}** · "
                f"Gen {guess['gen']} · {safe_types(guess)}"
            )

            cols = st.columns(5)

            for col, label, value in zip(cols, labels, clue):
                with col:
                    clue_chip(label, value)


def init_session():
    defaults = {
        "human_game": None,
        "human_games_played": 0,
        "human_games_won": 0,
        "human_total_guesses": 0,
        "human_best": None,
        "last_battle": None,
        "battle_step": 0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session()


# ==================================================
# SIDEBAR NAVIGATION
# ==================================================

with st.sidebar:
    st.markdown("""
    <div class="lab-brand">
        <div class="lab-brand-ball">🔴</div>
        <h3>Professor Oak's Lab</h3>
        <p>Pokédex Intelligence · Strategy Testing</p>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "LAB NAVIGATION",
        [
            "Welcome Hub",
            "Pokédex Challenge",
            "AI Battle Arena",
            "Professor’s Analytics",
            "Dataset Explorer",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption(f"TEAM PROJECT · {len(POKEMON)} SPECIES · 4 STRATEGIES")
    st.caption("Choose a lab station to explore.")


# ==================================================
# WELCOME HUB
# ==================================================

if page == "Welcome Hub":

    hero(
        "✦ WELCOME, RESEARCHER ✦",
        "A little world of Pokémon & strategy",
        "Enter the laboratory, solve a mystery, watch intelligent agents "
        "think, and explore the data behind every decision.",
    )

    roster = ["Eevee", "Pikachu", "Vulpix", "Piplup", "Sylveon"]
    cols = st.columns(len(roster))

    for col, name in zip(cols, roster):
        with col:
            art_card(name, name, 125)

    st.markdown("### ✨ Your laboratory dashboard")

    stats = [
        ("Pokémon indexed", len(POKEMON), "Species in the real dataset"),
        ("Generations", len(set(p["gen"] for p in POKEMON)), "Across the Pokédex"),
        ("Clue dimensions", 5, "Generation · Types · Height · Weight"),
        ("Guess limit", MAX_GUESSES, "Attempts per mystery"),
    ]

    cols = st.columns(4)

    for col, item in zip(cols, stats):
        with col:
            metric(*item)

    st.markdown("### 🧭 Choose your adventure")

    cards = [
        ("🎮", "Pokédex Challenge", "You vs. a hidden Pokémon",
         "Use clues and solve it in limited guesses."),
        ("🤖", "AI Battle Arena", "Watch the strategies think",
         "Compare guesses and candidate reduction."),
        ("📊", "Professor's Analytics", "Explore measured performance",
         "Review benchmark results and charts."),
        ("📚", "Dataset Explorer", "Browse the real Pokédex",
         "Search and inspect the dataset records."),
    ]

    cols = st.columns(2)

    for col, (emoji, title, tagline, desc) in zip(cols, cards):
        with col:
            st.markdown(
                f'<div class="panel"><div style="font-size:28px">{emoji}</div>'
                f'<h3>{title}</h3><b style="color:#c16c96">{tagline}</b>'
                f'<p>{desc}</p></div>',
                unsafe_allow_html=True,
            )

    st.markdown("### 💗 Your play history")

    played = st.session_state.human_games_played
    won = st.session_state.human_games_won
    win_rate = won / played * 100 if played else 0

    cols = st.columns(3)

    with cols[0]:
        metric("Games completed", played, "This browser session")

    with cols[1]:
        metric("Mysteries solved", won, "This browser session")

    with cols[2]:
        metric("Win rate", f"{win_rate:.1f}%", "Session-only statistic")

    st.info(
        "How the mystery works: feedback compares generation, primary type, "
        "secondary type, height and weight. Numeric clues use the engine's "
        "±10% tolerance. Each game allows up to 8 guesses."
    )


# ==================================================
# POKÉDEX CHALLENGE
# ==================================================

elif page == "Pokédex Challenge":

    hero(
        "FIELD TEST 01 · HUMAN VS MYSTERY",
        "Who's that Pokémon?",
        "Choose a species, read the clues, and solve the mystery before "
        "your attempts run out.",
    )

    left, right = st.columns([1.55, 1])

    with left:
        st.markdown("""
        <div class="panel">
            <h3>🌸 Welcome to the mystery meadow</h3>
            <p>Every guess reveals five pieces of feedback. Green means a match;
            directional clues help you understand numeric attributes.</p>
            <span class="pill" style="background:#ffe3ef;color:#a34e77">5 clue dimensions</span>
            <span class="pill" style="background:#eee8ff;color:#68538f">8 guesses max</span>
            <span class="pill" style="background:#e4f5ed;color:#39775b">386 species</span>
        </div>
        """, unsafe_allow_html=True)

    with right:
        art_card("Sylveon", "Your gameplay companion", 150)

    if st.session_state.human_game is None:
        st.session_state.human_game = Game(POKEMON)

    game = st.session_state.human_game

    if game.status != "playing":

        st.markdown("### ✨ Mystery complete")

        if game.status == "won":
            st.balloons()
            st.success(f"You found **{game.secret['name']}**!")
            pokemon_art(game.secret["name"], "Mystery Pokémon revealed", 190)
        else:
            st.error(
                f"The mystery was **{game.secret['name']}**. "
                "Better luck next time!"
            )
            pokemon_art(game.secret["name"], "The hidden Pokémon", 170)

        if st.button("🌷 Start another mystery", use_container_width=True):
            st.session_state.human_game = Game(POKEMON)
            st.rerun()

    else:

        remaining = MAX_GUESSES - len(game.history)

        st.markdown("### 🎯 Your challenge")

        cols = st.columns(3)

        with cols[0]:
            metric("Attempts left", remaining, f"of {MAX_GUESSES}")

        with cols[1]:
            metric("Guesses made", len(game.history), "Study the clues")

        with cols[2]:
            metric(
                "Possible species",
                len(filter_candidates(POKEMON, game.history)),
                "Consistent with clues",
            )

        st.progress(min(len(game.history) / MAX_GUESSES, 1.0))
        st.caption(f"Attempt {len(game.history) + 1} of {MAX_GUESSES}")

        guess_name = st.selectbox(
            "Choose your Pokémon",
            NAMES,
            key="human_guess_select",
            help="Search the list or type a species name.",
        )

        selected = BY_NAME[guess_name]

        info1, info2, info3 = st.columns(3)

        with info1:
            metric("Generation", selected["gen"], "Selected Pokémon")

        with info2:
            metric("Primary type", selected["type1"], "Selected Pokémon")

        with info3:
            metric(
                "Secondary type",
                selected.get("type2") or "None",
                "Selected Pokémon",
            )

        already_guessed = guess_name in [
            g["name"] for g, _ in game.history
        ]

        if st.button(
            "💗 Submit my guess",
            use_container_width=True,
            disabled=already_guessed,
        ):
            game.guess(selected)

            if game.status in ("won", "lost"):
                st.session_state.human_games_played += 1

                if game.status == "won":
                    st.session_state.human_games_won += 1

                st.session_state.human_total_guesses += len(game.history)

            st.rerun()

        if game.history:
            st.markdown("### 🧩 Clue trail")
            render_clue_history(game.history)
        else:
            st.markdown(
                '<div class="panel"><h3>🌟 Your first clue is waiting</h3>'
                '<p>Make your first guess to begin narrowing down the mystery.</p></div>',
                unsafe_allow_html=True,
            )


# ==================================================
# AI BATTLE ARENA
# ==================================================

elif page == "AI Battle Arena":

    hero(
        "FIELD TEST 02 · INTELLIGENT AGENTS",
        "AI Battle Arena",
        "Pick a hidden species and let an intelligent strategy investigate it. "
        "Reveal the AI's decisions one turn at a time.",
    )

    roster = ["Gengar", "Piplup", "Mimikyu", "Sprigatito"]
    cols = st.columns(4)

    for col, name in zip(cols, roster):
        with col:
            art_card(name, name, 112)

    st.markdown("### ⚙️ Set up the battle")

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
            "AI strategy",
            ["Random baseline", "Filter-based", "Entropy", "Minimax"],
            key="battle_strategy",
        )

    st.caption(
        "For a fair comparison, keep the secret Pokémon the same "
        "when switching strategies."
    )

    if st.button("⚡ Prepare AI battle", use_container_width=True):

        solver = (
            EntropySolver(POKEMON) if strategy == "Entropy"
            else MinimaxSolver(POKEMON) if strategy == "Minimax"
            else None
        )

        game = Game(POKEMON, secret=BY_NAME[secret])
        guessed = []
        rows = []

        while game.status == "playing":

            if strategy == "Random baseline":
                guess = random_solver(POKEMON, game.history)

            elif strategy == "Filter-based":
                guess = filter_solver(POKEMON, game.history)

            else:
                candidates = filter_candidates(POKEMON, game.history)
                guess = solver.next_guess(candidates, guessed)

            game.guess(guess)
            guessed.append(guess)

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
            "status": game.status,
        }

        st.session_state.battle_step = 0
        st.rerun()

    battle = st.session_state.last_battle

    if battle:

        rows = battle["rows"]
        step = min(st.session_state.battle_step, len(rows))

        st.markdown("### 🧠 Watch the AI reason")

        top = st.columns(3)

        with top[0]:
            metric("Strategy", battle["strategy"], "Selected agent")

        with top[1]:
            metric("Turn revealed", f"{step}/{len(rows)}", "Step-by-step playback")

        with top[2]:
            metric(
                "Candidates left",
                len(POKEMON) if step == 0
                else rows[step - 1]["Candidates remaining"],
                "After revealed turns",
            )

        if step == 0:

            st.markdown(
                '<div class="panel"><h3>🔎 The AI has '
                f'{len(POKEMON)} possible answers</h3>'
                '<p>Reveal the first decision to see how the agent begins its search.</p></div>',
                unsafe_allow_html=True,
            )

        else:

            current = rows[step - 1]

            st.markdown(
                f'<div class="turn-card">'
                f'<span class="pill" style="background:#ffe3ef;color:#a34e77">'
                f'TURN {current["Turn"]}</span>'
                f'<h3 style="margin:8px 0 2px">{html.escape(current["AI guess"])}</h3>'
                f'<p style="margin:0;color:#81758e">Generation {current["Generation"]} · '
                f'{html.escape(current["Types"])}</p>'
                f'<b style="color:#c16c96">{current["Candidates remaining"]} candidates remain</b>'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.progress(step / len(rows))

            st.dataframe(
                pd.DataFrame(rows[:step]),
                use_container_width=True,
                hide_index=True,
            )

        prev_col, next_col, reset_col = st.columns(3)

        with prev_col:
            if st.button(
                "← Previous turn",
                disabled=step == 0,
                use_container_width=True,
            ):
                st.session_state.battle_step = max(0, step - 1)
                st.rerun()

        with next_col:
            if st.button(
                "Reveal next turn →",
                disabled=step >= len(rows),
                use_container_width=True,
            ):
                st.session_state.battle_step = min(len(rows), step + 1)
                st.rerun()

        with reset_col:
            if st.button("↺ Restart playback", use_container_width=True):
                st.session_state.battle_step = 0
                st.rerun()

        if step == len(rows):

            st.balloons()

            if battle["status"] == "won":
                st.markdown(
                    f'<div class="battle-result"><h3>🎉 Mystery solved!</h3>'
                    f'<p>{html.escape(battle["strategy"])} identified '
                    f'<b>{html.escape(battle["secret"])}</b> in '
                    f'<b>{len(rows)} guesses</b>.</p></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.warning(
                    f"Guess limit reached. The hidden Pokémon was {battle['secret']}."
                )

            pokemon_art(battle["secret"], "The mystery revealed", 170)

        with st.expander("View the complete battle log"):
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )

        counts = [len(POKEMON)] + [
            row["Candidates remaining"] for row in rows
        ]

        fig, ax = plt.subplots(figsize=(9, 3.2))

        ax.plot(
            range(len(counts)),
            counts,
            marker="o",
            linewidth=2.8,
            markersize=7,
        )

        ax.fill_between(range(len(counts)), counts, alpha=0.12)
        ax.set_xticks(range(len(counts)))
        ax.set_xlabel("After guess")
        ax.set_ylabel("Possible answers")
        ax.set_title("Candidate search space")
        ax.grid(alpha=0.2)

        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        st.caption(
            "Candidate counts use the project's actual clue rules and dataset."
        )

    else:

        st.markdown(
            '<div class="panel"><h3>✨ Your AI challenger is ready</h3>'
            '<p>Choose a secret and strategy, prepare the battle, '
            'then reveal each AI decision.</p></div>',
            unsafe_allow_html=True,
        )


# ==================================================
# PROFESSOR'S ANALYTICS
# ==================================================

elif page == "Professor’s Analytics":

    hero(
        "FIELD TEST 03 · PERFORMANCE EVALUATION",
        "Professor's Analytics Lab",
        "A visual scoreboard for the four implemented strategies. "
        "Explore measured results and understand the trade-offs.",
    )

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
                )

            with c2:
                metric(
                    "Best worst case",
                    int(df["Worst case"].min()),
                    "Guesses",
                )

            with c3:
                metric("Strategies", len(df), "In saved benchmark")

            with c4:
                runs = int(df["Runs"].sum()) if "Runs" in df.columns else "—"
                metric("Total runs", runs, "As recorded in CSV")

            st.markdown("### 🏅 Benchmark scoreboard")

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("### 📊 Compare strategy performance")

            fig, ax = plt.subplots(figsize=(9, 3.8))

            bars = ax.bar(df["Solver"], df["Avg guesses"])

            ax.set_ylabel("Average guesses")
            ax.set_title("Average guesses by strategy")
            ax.grid(axis="y", alpha=0.2)

            for bar, value in zip(bars, df["Avg guesses"]):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.04,
                    f"{value:.2f}",
                    ha="center",
                    fontweight="bold",
                )

            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

            if "Win rate" in df.columns:

                st.markdown("### 🌷 Win rate")

                win_fig, win_ax = plt.subplots(figsize=(9, 3.0))

                win_ax.bar(df["Solver"], df["Win rate"])
                win_ax.set_ylabel("Win rate (%)")
                win_ax.set_ylim(0, 105)
                win_ax.grid(axis="y", alpha=0.2)

                win_fig.tight_layout()
                st.pyplot(win_fig)
                plt.close(win_fig)

            with st.expander("How the four strategies work"):

                st.markdown("""
                - **Random baseline:** chooses an unguessed Pokémon without using clue information.
                - **Filter-based:** removes candidates inconsistent with observed feedback.
                - **Entropy:** selects a guess expected to divide candidates into informative feedback groups.
                - **Minimax:** minimizes the largest possible remaining candidate group.
                """)

            st.download_button(
                "⬇ Download benchmark CSV",
                df.to_csv(index=False).encode(),
                file_name="pokemon_wordle_benchmark.csv",
                mime="text/csv",
            )

            st.caption(
                "These values are read from the project's saved results_table.csv."
            )

    else:

        st.warning(
            "Benchmark CSV is missing. Run benchmark.py to generate it."
        )


# ==================================================
# DATASET EXPLORER
# ==================================================

else:

    hero(
        "FIELD TEST 04 · DATA INVESTIGATION",
        "The Pokédex collection",
        "Browse the actual dataset used by every solver. Search by name "
        "and filter species by generation and primary type.",
    )

    df = pd.DataFrame(POKEMON)

    c1, c2, c3 = st.columns(3)

    with c1:
        metric("Species", len(df), "Loaded from pokemon.csv")

    with c2:
        metric("Primary types", df.type1.nunique(), "Unique categories")

    with c3:
        metric("Generations", df.gen.nunique(), "Generation values")

    st.markdown("### 🔎 Find a Pokémon")

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

    st.dataframe(
        view.sort_values("name"),
        use_container_width=True,
        hide_index=True,
    )

    if not view.empty:

        st.markdown("### 💗 Featured Pokédex entry")

        chosen = st.selectbox(
            "Choose a record to preview",
            view["name"].tolist(),
            key="dex_preview",
        )

        record = BY_NAME[chosen]

        art_col, detail_col = st.columns([1, 2])

        with art_col:
            art_card(chosen, chosen, 190)

        with detail_col:
            st.markdown(
                f'<div class="panel"><h3>{html.escape(chosen)}</h3>'
                f'<p><b>Generation:</b> {html.escape(str(record["gen"]))}</p>'
                f'<p><b>Type 1:</b> {html.escape(str(record["type1"]))}</p>'
                f'<p><b>Type 2:</b> {html.escape(str(record.get("type2") or "None"))}</p>'
                f'<p><b>Height:</b> {html.escape(str(record.get("height", "—")))}</p>'
                f'<p><b>Weight:</b> {html.escape(str(record.get("weight", "—")))}</p></div>',
                unsafe_allow_html=True,
            )

    st.download_button(
        "⬇ Export filtered dataset",
        view.to_csv(index=False).encode(),
        file_name="pokemon_dataset_filtered.csv",
        mime="text/csv",
    )


# ==================================================
# FOOTER
# ==================================================

st.markdown("""
<div class="footer-text">
    💗 POKÉMON WORDLE · GROUP RESEARCH PROJECT<br>
    BUILT FOR INTELLIGENT EXPERIMENTATION ✦
</div>
""", unsafe_allow_html=True)
