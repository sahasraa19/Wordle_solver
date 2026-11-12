
import os
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
    page_title="Pokémon Professor's Research Lab",
    page_icon="💗",
    layout="wide"
)


# ==================================================
# MODERN KAWAII PREMIUM DESIGN
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
    max-width: 1200px;
    padding-top: 2rem;
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
    padding: 11px 13px;
    transition: all .2s ease;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: #fff;
    border-color: #f2c8dc;
    transform: translateX(3px);
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(135deg, #f9c8dc, #f0dff5);
    border: 1px solid #edb6d0;
    box-shadow: 0 5px 15px #d98bae25;
    color: #753e60 !important;
}

/* SIDEBAR BRAND */

.lab-brand {
    text-align: center;
    padding: 14px 5px 22px;
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
    margin: 16px 0 3px;
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
    padding: 32px;
    border-radius: 26px;
    background: linear-gradient(120deg, #fff0f6, #f0ebff 75%, #fff9fc);
    border: 1px solid #f1dfeb;
    box-shadow: 0 12px 30px #9b73951a;
    margin-bottom: 24px;
}

.lab-hero:after {
    content: "✦";
    position: absolute;
    right: 42px;
    top: 12px;
    font-size: 85px;
    color: #e9b9d2;
    opacity: .55;
    text-shadow: 0 8px 20px #d99cbd55;
}

.lab-hero .eyebrow {
    color: #c16c96;
    font-weight: 900;
    letter-spacing: 2px;
    font-size: .78rem;
}

.lab-hero h1 {
    font-size: 2.35rem;
    margin: 8px 0;
}

.lab-hero p {
    color: #786d83;
    max-width: 720px;
}

/* PANELS */

.panel {
    background: linear-gradient(145deg, #fff, #fff8fc);
    border: 1px solid #f0e2eb;
    border-radius: 22px;
    padding: 23px;
    box-shadow: 0 5px 0 #f3e4ed, 0 12px 25px #8c64851c;
    transition: transform .2s ease, box-shadow .2s ease;
}

.panel:hover {
    transform: translateY(-3px);
    box-shadow: 0 7px 0 #f1dce8, 0 17px 30px #8c648526;
}

.art-panel {
    background: radial-gradient(circle at 50% 42%, #fff 0%, #fff0f6 65%, #eee8ff 100%);
    border: 1px solid #f0dfeb;
    border-radius: 25px;
    padding: 16px;
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
    border-radius: 20px;
    padding: 19px;
    box-shadow: 0 5px 0 #f2e4ec, 0 10px 20px #9b739515;
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.metric small {
    color: #897b91;
    font-weight: 800;
}

.metric b {
    color: #cf719b;
    font-size: 1.8rem;
    font-weight: 900;
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
    padding: .7rem 1.2rem;
    font-weight: 900;
    box-shadow: 0 5px 0 #c96e96, 0 9px 18px #d98bae30;
    transition: all .2s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 7px 0 #c96e96, 0 13px 22px #d98bae40;
}

/* STREAMLIT ELEMENTS */

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid var(--border);
    padding: 18px;
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

.stDownloadButton > button {
    background: #eee8ff;
    color: #51416f !important;
    border: 1px solid #dcd0fa;
    border-radius: 12px;
    font-weight: 800;
}

.battle-result {
    background: linear-gradient(120deg, #fff0f6, #f0ebff);
    border: 1px solid #efd9e8;
    border-radius: 22px;
    padding: 24px;
    box-shadow: 0 7px 20px #9b73951a;
}

.footer-text {
    text-align: center;
    color: #a18ca3;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1px;
    padding: 28px 0 8px;
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
# REUSABLE UI COMPONENTS
# ==================================================

def hero(kicker, title, subtitle):
    st.markdown(
        f"""
        <div class="lab-hero">
            <div class="eyebrow">{kicker}</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def metric(label, value, sub=""):
    st.markdown(
        f"""
        <div class="metric">
            <small>{label}</small>
            <b>{value}</b>
            <span style="color:#8a90a3;font-size:.82rem">{sub}</span>
        </div>
        """,
        unsafe_allow_html=True
    )


def clue_chip(label, value):
    colors = {
        "green": ("#d9f7e8", "#126b43"),
        "amber": ("#fff0c7", "#8a5b00"),
        "grey": ("#e9ebf1", "#606779"),
        "up": ("#dcecff", "#245b9b"),
        "down": ("#ffe1df", "#a43e39")
    }

    symbols = {
        "green": "✓",
        "amber": "◆",
        "grey": "×",
        "up": "↑",
        "down": "↓"
    }

    bg, fg = colors.get(value, ("#eee", "#333"))
    symbol = symbols.get(value, "•")

    st.markdown(
        f"""
        <span class="pill"
        style="background:{bg};color:{fg};">
        {label}: {symbol} {value.title()}
        </span>
        """,
        unsafe_allow_html=True
    )


def pokemon_art(name, caption=None, width=220):
    """Load Pokémon HOME-style artwork from the PokéAPI sprite repository."""

    artwork_ids = {
        "Pikachu": 25,
        "Eevee": 133,
        "Gengar": 94
    }

    pokemon_id = artwork_ids.get(name)

    if pokemon_id is None:
        return

    image_url = (
        "https://raw.githubusercontent.com/"
        "PokeAPI/sprites/master/sprites/pokemon/other/home/"
        f"{pokemon_id}.png"
    )

    try:
        st.image(
            image_url,
            caption=caption,
            width=width
        )
    except Exception:
        st.caption(f"Artwork could not be loaded for {name}.")


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
            "Dataset Explorer"
        ],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("TEAM PROJECT · 386 SPECIES · 4 STRATEGIES")


# ==================================================
# WELCOME HUB
# ==================================================

if page == "Welcome Hub":

    hero(
        "✦ WELCOME, RESEARCHER ✦",
        "The Pokémon Wordle Lab",
        "A playful research environment for testing how intelligent "
        "agents identify a hidden Pokémon using structured clues."
    )

    art_col, intro_col = st.columns([0.85, 2])

    with art_col:
        with st.container(border=True):
            pokemon_art("Pikachu", "Your laboratory companion", 210)

    with intro_col:
        st.markdown("""
        <div class="panel">
            <h3>✨ Welcome to the laboratory!</h3>
            <p>
            Discover how intelligent agents identify a hidden Pokémon
            using generation, type, height and weight clues.
            Explore human gameplay, AI strategies and measured
            benchmark performance in one interactive application.
            </p>
            <span class="pill" style="background:#ffe3ef;color:#a34e77">
            Intelligent guessing</span>
            <span class="pill" style="background:#eee8ff;color:#68538f">
            Strategy research</span>
            <span class="pill" style="background:#e4f5ed;color:#39775b">
            386 Pokémon</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### ✨ The laboratory at a glance")

    cols = st.columns(4)

    stats = [
        ("Pokémon indexed", len(POKEMON), "Complete dataset"),
        ("Generations", len(set(p["gen"] for p in POKEMON)),
         "Across the Pokédex"),
        ("Clue dimensions", 5, "Gen · Types · Height · Weight"),
        ("Guess limit", MAX_GUESSES, "Per human challenge")
    ]

    for col, item in zip(cols, stats):
        with col:
            metric(*item)

    st.write("")

    left, right = st.columns(2)

    with left:
        st.markdown("""
        <div class="panel">
            <h3>🧪 Your research mission</h3>
            <p>
            Discover how different guessing strategies narrow a
            search space. Start with a human challenge, watch an AI
            agent reason through clues, then compare performance
            using benchmark evidence.
            </p>
            <span class="pill" style="background:#ffe3ef;color:#a34e77">Baseline</span>
            <span class="pill" style="background:#eee8ff;color:#68538f">Filtering</span>
            <span class="pill" style="background:#e4f5ed;color:#39775b">Entropy</span>
            <span class="pill" style="background:#fff0c7;color:#8a5b00">Minimax</span>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("""
        <div class="panel">
            <h3>🧭 Explore the laboratory</h3>
            <p><b>🎮 Pokédex Challenge</b><br>
            Solve a mystery species using clues.</p>
            <p><b>🤖 AI Battle Arena</b><br>
            Watch intelligent agents make guesses.</p>
            <p><b>📊 Professor's Analytics</b><br>
            Compare measured solver performance.</p>
            <p><b>📚 Dataset Explorer</b><br>
            Investigate the actual Pokémon dataset.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 💡 How does the mystery work?")

    st.markdown("""
    <div class="panel">
        <p>
        Every guess is compared with the hidden Pokémon across five
        dimensions: generation, primary type, secondary type, height
        and weight. Feedback helps narrow the possible answers.
        </p>
        <span class="pill" style="background:#ffe3ef;color:#a34e77">5 clue dimensions</span>
        <span class="pill" style="background:#eee8ff;color:#68538f">±10% numeric tolerance</span>
        <span class="pill" style="background:#e4f5ed;color:#39775b">8 maximum guesses</span>
    </div>
    """, unsafe_allow_html=True)

    st.info(
        "Research note: the clue engine uses five attributes. "
        "Numeric clues use a ±10% band; type clues distinguish "
        "exact-slot, swapped-slot, and absent types."
    )


# ==================================================
# POKEDEX CHALLENGE
# ==================================================

elif page == "Pokédex Challenge":

    hero(
        "FIELD TEST 01 · HUMAN VS MYSTERY",
        "Pokédex Mystery Challenge",
        "One secret Pokémon. Eight guesses. Use the clues "
        "to identify the hidden species."
    )

    art_col, intro_col = st.columns([0.75, 2])

    with art_col:
        with st.container(border=True):
            pokemon_art("Eevee", "Your mystery companion", 180)

    with intro_col:
        st.markdown("""
        <div class="panel">
            <h3>🔍 Identify the mystery Pokémon</h3>
            <p>
            Choose a species from the Pokédex to submit a guess.
            The secret remains hidden until you solve it or run
            out of attempts. Study every clue carefully!
            </p>
            <span class="pill" style="background:#ffe3ef;color:#a34e77">Think strategically</span>
            <span class="pill" style="background:#eee8ff;color:#68538f">Read every clue</span>
        </div>
        """, unsafe_allow_html=True)

    if "human_game" not in st.session_state:
        st.session_state.human_game = Game(POKEMON)

    game = st.session_state.human_game

    left, right = st.columns([1.2, 1])

    with left:

        guess_name = st.selectbox("Choose your Pokémon guess", NAMES)

        if st.button(
            "🔴 Submit guess",
            use_container_width=True,
            disabled=game.status != "playing"
        ):
            game.guess(BY_NAME[guess_name])
            st.rerun()

        if st.button("✨ Start a new mystery", use_container_width=True):
            st.session_state.human_game = Game(POKEMON)
            st.rerun()

    with right:

        st.markdown("### 📍 Challenge progress")

        remaining = MAX_GUESSES - len(game.history)

        st.metric("Attempts remaining", remaining)
        st.metric("Clues discovered", len(game.history))
        st.progress(len(game.history) / MAX_GUESSES)

        if game.status == "won":
            st.success(f"🎉 You found {game.secret['name']}!")

        elif game.status == "lost":
            st.error(
                f"The mystery was {game.secret['name']}. "
                "Try another round!"
            )

        else:
            st.info("The mystery Pokémon is waiting to be discovered!")

    if game.history:

        st.markdown("### 🧩 Your clue trail")

        for idx, (guess, clue) in enumerate(game.history, 1):

            with st.container(border=True):

                st.markdown(
                    f"**{idx}. {guess['name']}** · "
                    f"Gen {guess['gen']} · "
                    f"{guess['type1']}/{guess['type2']}"
                )

                cols = st.columns(5)

                labels = [
                    "Generation",
                    "Type 1",
                    "Type 2",
                    "Height",
                    "Weight"
                ]

                for col, label, value in zip(cols, labels, clue):
                    with col:
                        clue_chip(label, value)


# ==================================================
# AI BATTLE ARENA
# ==================================================

elif page == "AI Battle Arena":

    hero(
        "FIELD TEST 02 · INTELLIGENT AGENTS",
        "AI Battle Arena",
        "Watch intelligent strategies investigate the same "
        "hidden Pokémon and see how evidence changes the candidate pool."
    )

    art_col, intro_col = st.columns([0.75, 2])

    with art_col:
        with st.container(border=True):
            pokemon_art("Gengar", "The AI battle challenger", 185)

    with intro_col:
        st.markdown("""
        <div class="panel">
            <h3>🤖 Intelligent agents are ready!</h3>
            <p>
            Select a secret Pokémon and let an AI strategy attempt
            to identify it. Observe its guesses and track how the
            candidate search space shrinks after each clue.
            </p>
            <span class="pill" style="background:#ffe3ef;color:#a34e77">Random</span>
            <span class="pill" style="background:#eee8ff;color:#68538f">Filter</span>
            <span class="pill" style="background:#e4f5ed;color:#39775b">Entropy</span>
            <span class="pill" style="background:#fff0c7;color:#8a5b00">Minimax</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### ⚙️ Configure your experiment")

    left, right = st.columns(2)

    with left:
        secret = st.selectbox(
            "Choose a secret Pokémon",
            NAMES,
            index=NAMES.index("Pikachu") if "Pikachu" in NAMES else 0
        )

    with right:
        strategy = st.selectbox(
            "Choose an AI strategy",
            [
                "Random baseline",
                "Filter-based",
                "Entropy",
                "Minimax"
            ]
        )

    st.caption(
        "Select the same secret Pokémon when comparing different "
        "strategies for a fair demonstration."
    )

    if st.button("⚡ Run AI battle", use_container_width=True):

        if strategy == "Entropy":
            solver = EntropySolver(POKEMON)

        elif strategy == "Minimax":
            solver = MinimaxSolver(POKEMON)

        else:
            solver = None

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

            remaining = len(
                filter_candidates(POKEMON, game.history)
            )

            rows.append({
                "Turn": len(rows) + 1,
                "AI guess": guess["name"],
                "Generation": guess["gen"],
                "Types": guess["type1"] + "/" + guess["type2"],
                "Candidates remaining": remaining,
                "Outcome": game.status.title()
            })

        st.session_state.last_battle = {
            "secret": secret,
            "strategy": strategy,
            "rows": rows,
            "status": game.status
        }

    if "last_battle" in st.session_state:

        battle = st.session_state.last_battle

        guesses_used = len(battle["rows"])

        st.markdown("### 🏆 Battle report")

        if battle["status"] == "won":

            st.markdown(
                f"""
                <div class="battle-result">
                    <h3>🎉 Mystery solved!</h3>
                    <p>
                    {battle['strategy']} identified
                    <b>{battle['secret']}</b> in
                    <b>{guesses_used} guesses</b>.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                f"""
                <div class="battle-result">
                    <h3>⏳ Guess limit reached</h3>
                    <p>
                    The secret Pokémon was
                    <b>{battle['secret']}</b>.
                    The strategy used {guesses_used} guesses.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

        c1, c2, c3 = st.columns(3)

        with c1:
            metric("AI strategy", battle["strategy"], "Selected solver")

        with c2:
            metric("Guesses used", guesses_used, "During this battle")

        with c3:
            metric("Initial candidates", len(POKEMON), "Search space")

        st.markdown("### 📋 Step-by-step AI decisions")

        st.dataframe(
            pd.DataFrame(battle["rows"]),
            use_container_width=True,
            hide_index=True
        )

        counts = [len(POKEMON)] + [
            row["Candidates remaining"] for row in battle["rows"]
        ]

        fig, ax = plt.subplots(figsize=(9, 3.2))

        ax.plot(
            range(len(counts)),
            counts,
            marker="o",
            linewidth=2.8,
            markersize=7
        )

        ax.fill_between(
            range(len(counts)),
            counts,
            alpha=0.12
        )

        ax.set_xticks(range(len(counts)))
        ax.set_xlabel("After guess")
        ax.set_ylabel("Possible answers")
        ax.set_title("How the candidate search space shrinks")
        ax.grid(alpha=0.2)

        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        st.caption(
            "Candidate counts are computed using the team's exact "
            "feedback rules against the Pokémon dataset."
        )

    else:

        st.markdown("""
        <div class="panel">
            <h3>🤖 Ready for the AI experiment?</h3>
            <p>
            Choose a hidden Pokémon and a strategy, then run the battle.
            The application will display every guess and show how the
            candidate search space changes.
            </p>
        </div>
        """, unsafe_allow_html=True)


# ==================================================
# PROFESSOR'S ANALYTICS
# ==================================================

elif page == "Professor’s Analytics":

    hero(
        "FIELD TEST 03 · PERFORMANCE EVALUATION",
        "Professor's Analytics Lab",
        "A benchmark-focused view of the four implemented strategies. "
        "Interpret the numbers, not just the winner."
    )

    path = os.path.join(RESULTS, "results_table.csv")

    if os.path.exists(path):

        df = pd.read_csv(path)

        best = df.loc[df["Avg guesses"].idxmin()]

        c1, c2, c3 = st.columns(3)

        with c1:
            metric(
                "Lowest average",
                f"{best['Avg guesses']:.2f}",
                str(best["Solver"]) + " strategy"
            )

        with c2:
            metric(
                "Best worst case",
                int(df["Worst case"].min()),
                "Guesses"
            )

        with c3:
            metric(
                "Strategies compared",
                len(df),
                "Same dataset"
            )

        st.markdown("### 🏅 Benchmark scoreboard")

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### 📊 Average guesses by strategy")

        fig, ax = plt.subplots(figsize=(9, 3.8))

        bars = ax.bar(
            df["Solver"],
            df["Avg guesses"]
        )

        ax.set_ylabel("Average guesses")
        ax.set_title("Strategy performance comparison")
        ax.grid(axis="y", alpha=0.2)

        for bar, value in zip(bars, df["Avg guesses"]):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.04,
                str(value),
                ha="center",
                fontweight="bold"
            )

        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        st.markdown("""
        <div class="panel">
            <h3>🧠 Understanding the strategies</h3>

            <p><b>🎲 Random baseline:</b>
            Ignores clue information and samples an unguessed Pokémon.</p>

            <p><b>🔎 Filter-based:</b>
            Removes every Pokémon inconsistent with all observed clues,
            then chooses among survivors.</p>

            <p><b>📐 Entropy:</b>
            Chooses the guess expected to split remaining candidates
            into the most informative feedback groups.</p>

            <p><b>🎯 Minimax:</b>
            Minimizes the size of the largest possible remaining
            candidate group, with tie-breakers.</p>
        </div>
        """, unsafe_allow_html=True)

        st.caption(
            "Values shown are from the project's saved benchmark CSV. "
            "Re-run benchmark.py to regenerate measurements."
        )

        st.download_button(
            "⬇ Download benchmark CSV",
            df.to_csv(index=False).encode(),
            file_name="pokemon_wordle_benchmark.csv",
            mime="text/csv"
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
        "Pokédex Data Observatory",
        "Explore the real dataset used by every solver in this project."
    )

    df = pd.DataFrame(POKEMON)

    c1, c2, c3 = st.columns(3)

    with c1:
        metric("Species", len(df), "Loaded from pokemon.csv")

    with c2:
        metric("Primary types", df.type1.nunique(), "Unique categories")

    with c3:
        metric("Generations", df.gen.nunique(), "Generation values")

    st.markdown("### 🔬 Explore dataset distributions")

    left, right = st.columns(2)

    with left:
        st.markdown("**Primary type distribution**")
        st.bar_chart(df.type1.value_counts().sort_values())

    with right:
        st.markdown("**Species by generation**")
        st.bar_chart(df.gen.value_counts().sort_index())

    st.markdown("### 🔎 Search the Pokédex")

    search = st.text_input(
        "Search by Pokémon species name",
        placeholder="For example, Pikachu..."
    )

    view = (
        df[df.name.str.contains(search, case=False, na=False)]
        if search else df
    )

    st.caption(f"Showing {len(view)} of {len(df)} Pokémon")

    st.dataframe(
        view.sort_values("name"),
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇ Export dataset CSV",
        df.to_csv(index=False).encode(),
        file_name="pokemon_dataset.csv",
        mime="text/csv"
    )


# ==================================================
# FOOTER
# ==================================================

st.markdown(
    """
    <div class="footer-text">
        💗 POKÉMON WORDLE · GROUP RESEARCH PROJECT
        <br>
        BUILT FOR INTELLIGENT EXPERIMENTATION ✦
    </div>
    """,
    unsafe_allow_html=True
)
