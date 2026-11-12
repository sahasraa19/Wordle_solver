
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
    page_title="POKEMON · Wordle Research Lab",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# POKEMON HOME ARTWORK
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


def pokemon_url(name):
    pokemon_id = ART_IDS.get(name)
    if pokemon_id:
        return ART_URL.format(pokemon_id=pokemon_id)
    return None


# ============================================================
# PREMIUM POKEMON INTERFACE
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&family=Fredoka:wght@400;500;600;700&display=swap');

:root {
    --pink: #F5A9C7;
    --pink-dark: #D96E9B;
    --pink-light: #FFF0F6;
    --lavender: #E9DFFF;
    --lavender-dark: #BDA9E8;
    --cream: #FFFAF5;
    --plum: #49344E;
    --muted: #927F98;
    --line: #F0DCE8;
}

html, body, [class*="css"] {
    font-family: 'Nunito', sans-serif !important;
    color: var(--plum);
}

.stApp {
    background:
        radial-gradient(ellipse at 5% 5%, #FFE7F1 0%, transparent 34%),
        radial-gradient(ellipse at 95% 15%, #EEE7FF 0%, transparent 32%),
        #FFFAF7;
}

.block-container {
    max-width: 1320px;
    padding-top: 1.3rem;
    padding-bottom: 3rem;
}

h1, h2, h3, h4 {
    color: var(--plum) !important;
    font-weight: 900 !important;
}

h1, h2 {
    font-family: 'Fredoka', 'Nunito', sans-serif !important;
}

p, label, li {
    color: var(--plum);
}

header[data-testid="stHeader"] {
    background: transparent;
}

/* HIDE DEFAULT STREAMLIT ELEMENTS */

#MainMenu, footer {
    visibility: hidden;
}

[data-testid="stSidebar"] {
    display: none;
}

/* TOP BRAND */

.brand-wrap {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 14px;
    padding: 4px 0 12px;
}

.brand-icon {
    width: 47px;
    height: 47px;
    border-radius: 50%;
    background: linear-gradient(145deg, #FFF, #F5BDD5);
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 27px;
    box-shadow: 0 4px 0 #E8A8C5, 0 8px 18px #D58BAF40;
}

.brand-name {
    font-family: 'Fredoka', sans-serif;
    font-size: 2.15rem;
    font-weight: 700;
    letter-spacing: 4px;
    color: #65415F;
    line-height: 1.1;
}

.brand-subtitle {
    text-align: center;
    color: #A1819B;
    font-size: 10px;
    letter-spacing: 3px;
    font-weight: 900;
    margin-top: 2px;
}

/* TOP NAVIGATION */

div[data-testid="stRadio"] > div {
    display: flex;
    flex-direction: row !important;
    justify-content: center;
    align-items: center;
    gap: 7px;
    flex-wrap: wrap;
}

div[data-testid="stRadio"] label {
    background: rgba(255,255,255,.72);
    border: 1px solid #F0DDE8;
    border-radius: 999px;
    padding: 8px 17px;
    transition: all .2s ease;
    box-shadow: 0 3px 9px #9D74900C;
}

div[data-testid="stRadio"] label:hover {
    background: #FFF0F6;
    border-color: #E8A8C5;
    transform: translateY(-2px);
}

div[data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(135deg, #F6B8D1, #E8CFF5);
    border: 1px solid #E7A8C7;
    box-shadow: 0 4px 0 #DBA4C0, 0 7px 15px #D98BAE30;
}

div[data-testid="stRadio"] label p {
    color: #63465F !important;
    font-weight: 900 !important;
    font-size: .85rem;
}

div[data-testid="stRadio"] input {
    display: none;
}

/* BRAND DIVIDER */

.nav-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #EBCBD9, #DCCDF3, transparent);
    margin: 12px 0 27px;
}

/* HERO */

.lab-hero {
    position: relative;
    overflow: hidden;
    padding: 32px 35px;
    border-radius: 28px;
    background: linear-gradient(115deg, #FFF0F6, #F1EBFF 68%, #FFF8FC);
    border: 1px solid #F0DDE9;
    box-shadow: 0 7px 0 #F2E1EB, 0 14px 30px #8E648519;
    margin-bottom: 24px;
}

.lab-hero:after {
    content: "✦";
    position: absolute;
    right: 42px;
    top: 0;
    color: #DDB3D1;
    font-size: 100px;
    opacity: .5;
}

.lab-hero .eyebrow {
    font-size: .72rem;
    letter-spacing: 3px;
    font-weight: 900;
    color: #C06C98;
}

.lab-hero h1 {
    font-size: 2.5rem;
    margin: 8px 0 5px;
}

.lab-hero p {
    color: #84758E;
    max-width: 780px;
    font-size: 1rem;
    margin-bottom: 0;
    line-height: 1.6;
}

/* PANELS */

.panel {
    background: linear-gradient(145deg, #FFFFFF, #FFF8FC);
    border: 1px solid #F0E0EA;
    border-radius: 23px;
    padding: 21px;
    box-shadow: 0 5px 0 #F4E6EE, 0 12px 24px #86618413;
    height: 100%;
}

.panel h3 {
    margin-top: 0;
}

.art-panel {
    background: radial-gradient(circle at 50% 40%, #FFFFFF 0%, #FFF0F6 68%, #EEE8FF 100%);
    border: 1px solid #F0DFEB;
    border-radius: 25px;
    padding: 12px;
    box-shadow: 0 5px 0 #F0E0EA, 0 12px 24px #8C64851B;
    text-align: center;
}

/* METRICS */

.metric {
    background: linear-gradient(145deg, #FFFFFF, #FFF4F9);
    border: 1px solid #F1E0EA;
    border-radius: 20px;
    padding: 17px;
    box-shadow: 0 4px 0 #F2E4EC, 0 9px 18px #9B739515;
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-height: 108px;
}

.metric small {
    color: #95849B;
    font-weight: 900;
}

.metric b {
    color: #CD719B;
    font-size: 1.65rem;
    font-weight: 900;
    overflow-wrap: anywhere;
}

.metric span {
    color: #93869D;
    font-size: .8rem;
}

/* TAGS */

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
    background: linear-gradient(135deg, #F3A9C7, #DB82AC);
    color: white !important;
    border: 1px solid #E4A0BD;
    border-radius: 15px;
    padding: .65rem 1rem;
    font-weight: 900;
    box-shadow: 0 4px 0 #C96F98, 0 8px 16px #D98BAE30;
    transition: all .2s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 0 #C96F98, 0 11px 19px #D98BAE40;
}

.stButton > button:disabled {
    opacity: .45;
}

.stDownloadButton > button {
    background: linear-gradient(135deg, #EDE5FF, #F5EFFF);
    color: #604C7E !important;
    border: 1px solid #DCD0F4;
    border-radius: 13px;
    font-weight: 900;
}

/* INPUTS */

div[data-testid="stSelectbox"] > div > div,
div[data-testid="stTextInput"] input {
    background: white;
    border-radius: 13px;
    border-color: #EBD8E5;
    color: var(--plum);
}

div[data-testid="stSelectbox"] > div > div:focus-within,
div[data-testid="stTextInput"] input:focus {
    border-color: #D88DB1;
    box-shadow: 0 0 0 2px #F8DCE8;
}

/* DATAFRAMES */

div[data-testid="stDataFrame"] {
    border: 1px solid #F0DFEB;
    border-radius: 16px;
    overflow: hidden;
}

/* STREAMLIT METRICS */

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #F0DFEB;
    padding: 15px;
    border-radius: 18px;
    box-shadow: 0 5px 16px #3330440A;
}

div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #CF719B !important;
    font-weight: 900 !important;
}

/* EXPANDERS */

[data-testid="stExpander"] {
    background: #FFFFFF;
    border: 1px solid #F0DFEB;
    border-radius: 16px;
}

/* GAME COMPONENTS */

.turn-card {
    background: linear-gradient(120deg, #FFFFFF, #FFF4F9);
    border: 1px solid #F0DFEB;
    border-radius: 19px;
    padding: 16px;
    margin: 9px 0;
    box-shadow: 0 4px 12px #8C648510;
}

.battle-result {
    background: linear-gradient(120deg, #FFF0F6, #F0EBFF);
    border: 1px solid #EED9E8;
    border-radius: 23px;
    padding: 23px;
    box-shadow: 0 8px 20px #9B73951A;
}

.footer-text {
    text-align: center;
    color: #A18CA3;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 2px;
    padding: 30px 0 10px;
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #F3A9C7, #BBA6E9);
}

.stAlert {
    border-radius: 16px;
}

hr {
    border-color: #F0E1EB;
}

@media (max-width: 700px) {
    .brand-name {
        font-size: 1.7rem;
    }

    .lab-hero {
        padding: 23px;
    }

    .lab-hero h1 {
        font-size: 1.9rem;
    }

    div[data-testid="stRadio"] label {
        padding: 6px 10px;
    }
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# REUSABLE COMPONENTS
# ============================================================

def hero(kicker, title, subtitle):
    st.markdown(
        f'<div class="lab-hero">'
        f'<div class="eyebrow">{html.escape(kicker)}</div>'
        f'<h1>{html.escape(title)}</h1>'
        f'<p>{html.escape(subtitle)}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )


def metric(label, value, sub=""):
    st.markdown(
        f'<div class="metric">'
        f'<small>{html.escape(str(label))}</small>'
        f'<b>{html.escape(str(value))}</b>'
        f'<span>{html.escape(str(sub))}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def clue_chip(label, value):
    colors = {
        "green": ("#D9F7E8", "#126B43", "✓"),
        "amber": ("#FFF0C7", "#8A5B00", "◆"),
        "grey": ("#E9EBF1", "#606779", "×"),
        "up": ("#DCEBFF", "#245B9B", "↑"),
        "down": ("#FFE1DF", "#A43E39", "↓"),
    }

    bg, fg, symbol = colors.get(
        str(value).lower(),
        ("#EEEEEE", "#333333", "•")
    )

    st.markdown(
        f'<span class="pill" style="background:{bg};color:{fg}">'
        f'{html.escape(str(label))}: {symbol} '
        f'{html.escape(str(value).title())}</span>',
        unsafe_allow_html=True,
    )


def pokemon_art(name, caption=None, width=190):
    url = pokemon_url(name)

    if url:
        st.image(url, caption=caption, width=width)
    else:
        st.markdown(
            f'<div style="padding:25px;text-align:center;color:#9B7893">'
            f'<div style="font-size:38px">✦</div>'
            f'<b>{html.escape(name)}</b></div>',
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


# ============================================================
# TOP BRANDING AND NAVIGATION
# ============================================================

st.markdown("""
<div class="brand-wrap">
    <div class="brand-icon">⚡</div>
    <div>
        <div class="brand-name">POKEMON</div>
        <div class="brand-subtitle">WORDLE RESEARCH LAB</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(
    '<div style="text-align:center;color:#A78BA5;'
    'font-size:11px;letter-spacing:2px;font-weight:900">'
    '✦ PROFESSOR OAK’S INTELLIGENCE LABORATORY ✦'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

pages = [
    "🏠  Home",
    "🎮  Pokédex",
    "🤖  AI Battle",
    "📊  Analytics",
    "📚  Dataset",
]

selected_page = st.radio(
    "Navigation",
    pages,
    horizontal=True,
    label_visibility="collapsed",
)

st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)

page_map = {
    "🏠  Home": "Welcome Hub",
    "🎮  Pokédex": "Pokédex Challenge",
    "🤖  AI Battle": "AI Battle Arena",
    "📊  Analytics": "Professor’s Analytics",
    "📚  Dataset": "Dataset Explorer",
}

page = page_map[selected_page]


# ============================================================
# WELCOME HUB
# ============================================================

if page == "Welcome Hub":

    hero(
        "✦ WELCOME, TRAINER ✦",
        "Welcome to the Pokémon World!",
        "A world of mystery, intelligent guessing and Pokémon discovery. "
        "Explore the Pokédex, challenge yourself and watch AI strategies compete.",
    )

    roster = ["Eevee", "Pikachu", "Vulpix", "Piplup", "Sylveon"]

    cols = st.columns(len(roster))

    for col, name in zip(cols, roster):
        with col:
            art_card(name, name, 125)

    st.markdown("## ✨ Research Lab Overview")

    stats = [
        ("Pokémon indexed", len(POKEMON), "Species in the dataset"),
        ("Generations", len(set(p["gen"] for p in POKEMON)), "Across the Pokédex"),
        ("Clue dimensions", 5, "Attributes used by the game"),
        ("Guess limit", MAX_GUESSES, "Attempts per mystery"),
    ]

    cols = st.columns(4)

    for col, item in zip(cols, stats):
        with col:
            metric(*item)

    st.markdown("## 🌸 Explore the Laboratory")

    cards = [
        ("🎮", "Pokédex Challenge", "Human vs Mystery",
         "Solve a hidden Pokémon using five clue dimensions."),
        ("🤖", "AI Battle Arena", "Intelligent Guessing",
         "Watch four strategies investigate the same mystery."),
        ("📊", "Professor's Analytics", "Performance Insights",
         "Compare measured results from benchmark experiments."),
        ("📚", "Dataset Explorer", "Pokédex Collection",
         "Search, filter and inspect the real dataset."),
    ]

    cols = st.columns(2)

    for col, (emoji, title, tagline, desc) in zip(cols, cards):
        with col:
            st.markdown(
                f'<div class="panel">'
                f'<div style="font-size:29px">{emoji}</div>'
                f'<h3>{html.escape(title)}</h3>'
                f'<b style="color:#C16C96">{html.escape(tagline)}</b>'
                f'<p>{html.escape(desc)}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("## 💗 Trainer Statistics")

    played = st.session_state.human_games_played
    won = st.session_state.human_games_won
    win_rate = won / played * 100 if played else 0

    cols = st.columns(3)

    with cols[0]:
        metric("Games completed", played, "Current session")

    with cols[1]:
        metric("Mysteries solved", won, "Current session")

    with cols[2]:
        metric("Win rate", f"{win_rate:.1f}%", "Current session")

    st.info(
        "How to play: feedback compares generation, primary type, "
        "secondary type, height and weight. Numeric clues use the engine's "
        "±10% tolerance. Each game allows up to 8 guesses."
    )


# ============================================================
# POKÉDEX CHALLENGE
# ============================================================

elif page == "Pokédex Challenge":

    hero(
        "FIELD TEST 01 · HUMAN VS MYSTERY",
        "Who's That Pokémon?",
        "Think carefully, follow the clues and identify the hidden Pokémon "
        "before your attempts run out.",
    )

    left, right = st.columns([1.55, 1])

    with left:
        st.markdown("""
        <div class="panel">
            <h3>🌸 Welcome to the Mystery Meadow</h3>
            <p>Every guess reveals five pieces of feedback. Green means a match;
            directional clues help you understand numeric attributes.</p>
            <span class="pill" style="background:#FFE3EF;color:#A34E77">5 clue dimensions</span>
            <span class="pill" style="background:#EEE8FF;color:#68538F">8 guesses max</span>
            <span class="pill" style="background:#E4F5ED;color:#39775B">386 species</span>
        </div>
        """, unsafe_allow_html=True)

    with right:
        art_card("Sylveon", "Your gameplay companion", 150)

    if st.session_state.human_game is None:
        st.session_state.human_game = Game(POKEMON)

    game = st.session_state.human_game

    if game.status != "playing":

        st.markdown("### ✨ Mystery Complete")

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

        if st.button("🌷 Start Another Mystery", use_container_width=True):
            st.session_state.human_game = Game(POKEMON)
            st.rerun()

    else:

        remaining = MAX_GUESSES - len(game.history)

        st.markdown("### 🎯 Your Challenge")

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
            "💗 Submit My Guess",
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
            st.markdown("### 🧩 Clue Trail")
            render_clue_history(game.history)
        else:
            st.markdown(
                '<div class="panel">'
                '<h3>🌟 Your First Clue Is Waiting</h3>'
                '<p>Make your first guess to begin narrowing down the mystery.</p>'
                '</div>',
                unsafe_allow_html=True,
            )


# ============================================================
# AI BATTLE ARENA
# ============================================================

elif page == "AI Battle Arena":

    hero(
        "FIELD TEST 02 · INTELLIGENT AGENTS",
        "AI Battle Arena",
        "Choose a hidden species and watch an intelligent strategy "
        "investigate it, one decision at a time.",
    )

    roster = ["Gengar", "Piplup", "Mimikyu", "Sprigatito"]
    cols = st.columns(4)

    for col, name in zip(cols, roster):
        with col:
            art_card(name, name, 112)

    st.markdown("## ⚙️ Set Up the Battle")

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

    if st.button("⚡ Prepare AI Battle", use_container_width=True):

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

        st.markdown("## 🧠 Watch the AI Reason")

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
                '<div class="panel">'
                f'<h3>🔎 The AI has {len(POKEMON)} possible answers</h3>'
                '<p>Reveal the first decision to see how the agent begins its search.</p>'
                '</div>',
                unsafe_allow_html=True,
            )

        else:

            current = rows[step - 1]

            st.markdown(
                f'<div class="turn-card">'
                f'<span class="pill" style="background:#FFE3EF;color:#A34E77">'
                f'TURN {current["Turn"]}</span>'
                f'<h3 style="margin:8px 0 2px">{html.escape(current["AI guess"])}</h3>'
                f'<p style="margin:0;color:#81758E">Generation {current["Generation"]} · '
                f'{html.escape(current["Types"])}</p>'
                f'<b style="color:#C16C96">{current["Candidates remaining"]} candidates remain</b>'
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
                "← Previous Turn",
                disabled=step == 0,
                use_container_width=True,
            ):
                st.session_state.battle_step = max(0, step - 1)
                st.rerun()

        with next_col:
            if st.button(
                "Reveal Next Turn →",
                disabled=step >= len(rows),
                use_container_width=True,
            ):
                st.session_state.battle_step = min(len(rows), step + 1)
                st.rerun()

        with reset_col:
            if st.button("↺ Restart Playback", use_container_width=True):
                st.session_state.battle_step = 0
                st.rerun()

        if step == len(rows):

            st.balloons()

            if battle["status"] == "won":
                st.markdown(
                    f'<div class="battle-result">'
                    f'<h3>🎉 Mystery Solved!</h3>'
                    f'<p>{html.escape(battle["strategy"])} identified '
                    f'<b>{html.escape(battle["secret"])}</b> in '
                    f'<b>{len(rows)} guesses</b>.</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.warning(
                    f"Guess limit reached. The hidden Pokémon was {battle['secret']}."
                )

            pokemon_art(battle["secret"], "The mystery revealed", 170)

        with st.expander("View the Complete Battle Log"):
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
        ax.set_title("Candidate Search Space")
        ax.grid(alpha=0.2)

        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        st.caption(
            "Candidate counts use the project's actual clue rules and dataset."
        )

    else:

        st.markdown(
            '<div class="panel">'
            '<h3>✨ Your AI Challenger Is Ready</h3>'
            '<p>Choose a secret and strategy, prepare the battle, '
            'then reveal each AI decision.</p>'
            '</div>',
            unsafe_allow_html=True,
        )


# ============================================================
# PROFESSOR'S ANALYTICS
# ============================================================

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

            st.markdown("## 🏅 Benchmark Scoreboard")

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("## 📊 Compare Strategy Performance")

            fig, ax = plt.subplots(figsize=(9, 3.8))

            bars = ax.bar(df["Solver"], df["Avg guesses"])

            ax.set_ylabel("Average guesses")
            ax.set_title("Average Guesses by Strategy")
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

                st.markdown("## 🌷 Win Rate")

                win_fig, win_ax = plt.subplots(figsize=(9, 3.0))

                win_ax.bar(df["Solver"], df["Win rate"])
                win_ax.set_ylabel("Win rate (%)")
                win_ax.set_ylim(0, 105)
                win_ax.grid(axis="y", alpha=0.2)

                win_fig.tight_layout()
                st.pyplot(win_fig)
                plt.close(win_fig)

            with st.expander("How the Four Strategies Work"):

                st.markdown("""
                - **Random baseline:** chooses an unguessed Pokémon without using clue information.
                - **Filter-based:** removes candidates inconsistent with observed feedback.
                - **Entropy:** selects a guess expected to divide candidates into informative feedback groups.
                - **Minimax:** minimizes the largest possible remaining candidate group.
                """)

            st.download_button(
                "⬇ Download Benchmark CSV",
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


# ============================================================
# DATASET EXPLORER
# ============================================================

else:

    hero(
        "FIELD TEST 04 · DATA INVESTIGATION",
        "The Pokédex Collection",
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

    st.markdown("## 🔎 Find a Pokémon")

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

        st.markdown("## 💗 Featured Pokédex Entry")

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
                f'<div class="panel">'
                f'<h3>{html.escape(chosen)}</h3>'
                f'<p><b>Generation:</b> {html.escape(str(record["gen"]))}</p>'
                f'<p><b>Type 1:</b> {html.escape(str(record["type1"]))}</p>'
                f'<p><b>Type 2:</b> {html.escape(str(record.get("type2") or "None"))}</p>'
                f'<p><b>Height:</b> {html.escape(str(record.get("height", "—")))}</p>'
                f'<p><b>Weight:</b> {html.escape(str(record.get("weight", "—")))}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.download_button(
        "⬇ Export Filtered Dataset",
        view.to_csv(index=False).encode(),
        file_name="pokemon_dataset_filtered.csv",
        mime="text/csv",
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("""
<div class="nav-divider"></div>
<div class="footer-text">
    ⚡ POKEMON WORDLE · RESEARCH LAB<br>
    <span style="font-size:9px;letter-spacing:3px">
        THINK · GUESS · DISCOVER · REPEAT
    </span>
    <br><br>
    MADE WITH ♡ FOR POKÉMON RESEARCH
</div>
""", unsafe_allow_html=True)
