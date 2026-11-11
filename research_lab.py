
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from loader import load_pokemon
from engine import Game, MAX_GUESSES
from basic_solvers import random_solver, filter_solver, filter_candidates
from entropy_solver import EntropySolver
from minimax_solver import MinimaxSolver

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "pokemon.csv")
RESULTS = os.path.join(ROOT, "results")

POKEMON = load_pokemon(DATA)
BY_NAME = {p["name"]: p for p in POKEMON}
NAMES = sorted(BY_NAME)

st.set_page_config(
    page_title="Pokémon Professor's Research Lab",
    page_icon="🔴",
    layout="wide"
)


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
    --navy: #17233f;
    --red: #e63946;
    --blue: #3155a4;
    --gold: #f4b942;
    --bg: #f3f5fa;
}

.stApp {
    background: var(--bg);
    color: var(--navy);
    font-family: 'Nunito', sans-serif;
}

.block-container {
    max-width: 1350px;
    padding-top: 2rem;
}

h1, h2, h3, h4, p, label, li,
[data-testid="stMarkdownContainer"] {
    color: var(--navy);
}

h1, h2, h3 {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
}

.lab-hero {
    background: linear-gradient(115deg, #17233f, #263f70);
    border-left: 8px solid var(--red);
    padding: 34px;
    border-radius: 18px;
    color: #ffffff;
    margin-bottom: 24px;
    box-shadow: 0 10px 28px #17233f22;
}

.lab-hero h1 {
    color: #ffffff !important;
    font-size: 2.7rem;
    margin: 8px 0;
}

.lab-hero p {
    color: #e8edf8 !important;
    font-size: 1.05rem;
}

.eyebrow {
    color: #ffd166;
    font-size: .75rem;
    font-weight: 900;
    letter-spacing: 2px;
}

.panel {
    background: #ffffff;
    border: 1px solid #dce2ed;
    border-radius: 16px;
    padding: 22px;
    color: #17233f;
    box-shadow: 0 5px 18px #17233f0b;
}

.panel h3, .panel p {
    color: #17233f !important;
}

.metric {
    background: #ffffff;
    border: 1px solid #dce2ed;
    border-top: 4px solid #e63946;
    border-radius: 14px;
    padding: 17px;
    box-shadow: 0 5px 15px #17233f0b;
}

.metric small {
    color: #58647a;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: .8px;
}

.metric b {
    display: block;
    color: #17233f;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.9rem;
    margin: 5px 0;
}

.metric span {
    color: #58647a !important;
}

.pill {
    display: inline-block;
    border-radius: 8px;
    padding: 6px 11px;
    background: #e9eefb;
    color: #1c3975;
    font-size: .8rem;
    font-weight: 900;
    margin: 3px;
}

[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #dce2ed;
    border-radius: 14px;
    padding: 16px;
}

[data-testid="stMetricLabel"] p {
    color: #58647a !important;
    font-weight: 800;
}

[data-testid="stMetricValue"] {
    color: #17233f !important;
}

[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #dce2ed;
}

[data-testid="stSidebar"] * {
    color: #17233f;
}

[data-testid="stSidebar"] [aria-checked="true"] p {
    color: #e63946 !important;
    font-weight: 900;
}

.stButton > button {
    background: #e63946;
    color: #ffffff !important;
    border: 0;
    border-radius: 10px;
    padding: .65rem 1rem;
    font-weight: 900;
}

.stButton > button:hover {
    background: #bd2634;
    color: #ffffff !important;
    border: 0;
}

.stButton > button:disabled {
    background: #d5dbe6;
    color: #58647a !important;
}

input, textarea,
[data-baseweb="select"] > div {
    background: #ffffff !important;
    color: #17233f !important;
    border-color: #cbd3e1 !important;
}

[data-testid="stDataFrame"] {
    background: #ffffff;
    border: 1px solid #dce2ed;
    border-radius: 12px;
}

[data-testid="stAlert"] {
    border-radius: 12px;
}

.stProgress > div > div > div {
    background: #e63946;
}

footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


def hero(kicker, title, subtitle):
    st.markdown(
        f'<div class="lab-hero"><div class="eyebrow">{kicker}</div>'
        f'<h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True
    )


def metric(label, value, sub=""):
    st.markdown(
        f'<div class="metric"><small>{label}</small>'
        f'<b>{value}</b><span style="color:#8a90a3;font-size:.82rem">'
        f'{sub}</span></div>',
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
        "green": "✓", "amber": "◆", "grey": "×",
        "up": "↑", "down": "↓"
    }
    bg, fg = colors.get(value, ("#eee", "#333"))
    symbol = symbols.get(value, "•")
    st.markdown(
        f'<span class="pill" style="background:{bg};color:{fg}">'
        f'{label}: {symbol} {value.title()}</span>',
        unsafe_allow_html=True
    )


with st.sidebar:
    st.markdown("## 🔴 Professor Oak’s Lab")
    st.caption("Pokédex intelligence • Strategy testing")
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


# --------------------------------------------------
# WELCOME HUB
# --------------------------------------------------

if page == "Welcome Hub":
    hero(
        "WELCOME, RESEARCHER",
        "The Pokémon Wordle Lab",
        "A playful research environment for testing how intelligent "
        "agents identify a hidden Pokémon from structured clues."
    )

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
    left, right = st.columns([1.25, 1])

    with left:
        st.markdown("""
        <div class="panel">
        <h3>🧪 Your research mission</h3>
        <p>Discover how different guessing strategies narrow a
        search space. Start with a human challenge, watch an AI
        agent reason through clues, then compare performance
        using benchmark evidence.</p>
        <span class="pill">Baseline</span>
        <span class="pill">Constraint filtering</span>
        <span class="pill">Entropy</span>
        <span class="pill">Minimax</span>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("""
        <div class="panel">
        <h3>🧭 Explore the lab</h3>
        <p><b>Pokédex Challenge</b> — solve a mystery species.</p>
        <p><b>AI Battle Arena</b> — inspect machine guesses.</p>
        <p><b>Analytics</b> — compare measured solver performance.</p>
        <p><b>Dataset Explorer</b> — inspect the actual dataset.</p>
        </div>
        """, unsafe_allow_html=True)

    st.info(
        "Research note: the clue engine uses five attributes. "
        "Numeric clues use a ±10% band; type clues distinguish "
        "exact-slot, swapped-slot, and absent types."
    )


# --------------------------------------------------
# POKEDEX CHALLENGE
# --------------------------------------------------

elif page == "Pokédex Challenge":
    hero(
        "FIELD TEST 01",
        "Pokédex Mystery Challenge",
        "One secret Pokémon. Eight guesses. Use the clues "
        "to identify the hidden species."
    )

    if "human_game" not in st.session_state:
        st.session_state.human_game = Game(POKEMON)

    game = st.session_state.human_game
    left, right = st.columns([1.2, 1])

    with left:
        st.markdown("""
        <div class="panel">
        <h3>🔍 Identify the mystery Pokémon</h3>
        <p>Choose a species from the Pokédex to submit a guess.
        The secret remains hidden until you solve it or run
        out of attempts.</p>
        </div>
        """, unsafe_allow_html=True)

        guess_name = st.selectbox("Your guess", NAMES)

        if st.button(
            "Submit guess",
            use_container_width=True,
            disabled=game.status != "playing"
        ):
            game.guess(BY_NAME[guess_name])
            st.rerun()

        if st.button("New mystery", use_container_width=True):
            st.session_state.human_game = Game(POKEMON)
            st.rerun()

    with right:
        st.metric(
            "Attempts remaining",
            MAX_GUESSES - len(game.history)
        )
        st.metric("Clues discovered", len(game.history))
        st.progress(len(game.history) / MAX_GUESSES)

        if game.status == "won":
            st.success(f"🎉 You found {game.secret['name']}!")
        elif game.status == "lost":
            st.error(
                f"The mystery was {game.secret['name']}. "
                "Try another round!"
            )

    if game.history:
        st.subheader("Your clue trail")

        for idx, (guess, clue) in enumerate(game.history, 1):
            with st.container(border=True):
                st.markdown(
                    f"**{idx}. {guess['name']}** · "
                    f"Gen {guess['gen']} · "
                    f"{guess['type1']}/{guess['type2']}"
                )

                cols = st.columns(5)
                labels = [
                    "Generation", "Type 1", "Type 2",
                    "Height", "Weight"
                ]

                for col, label, value in zip(cols, labels, clue):
                    with col:
                        clue_chip(label, value)


# --------------------------------------------------
# AI BATTLE ARENA
# --------------------------------------------------

elif page == "AI Battle Arena":
    hero(
        "FIELD TEST 02",
        "AI Battle Arena",
        "Watch intelligent strategies investigate the same "
        "hidden Pokémon and see how evidence changes the candidate pool."
    )

    secret = st.selectbox(
        "Choose a secret Pokémon for a reproducible battle",
        NAMES,
        index=NAMES.index("Pikachu") if "Pikachu" in NAMES else 0
    )

    strategy = st.selectbox(
        "Select strategy",
        ["Random baseline", "Filter-based", "Entropy", "Minimax"]
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

        st.markdown(
            f"### {'🏆 Solved' if battle['status'] == 'won' else '⏳ Attempt limit reached'}"
            f" · {battle['strategy']}"
        )

        st.success(
            f"Mystery Pokémon: **{battle['secret']}** · "
            f"Guesses used: **{len(battle['rows'])}**"
        )

        st.dataframe(
            pd.DataFrame(battle["rows"]),
            use_container_width=True,
            hide_index=True
        )

        counts = [len(POKEMON)] + [
            row["Candidates remaining"] for row in battle["rows"]
        ]

        fig, ax = plt.subplots(figsize=(9, 2.8))
        ax.plot(range(len(counts)), counts, marker="o", linewidth=2.5)
        ax.fill_between(range(len(counts)), counts, alpha=0.12)
        ax.set_xticks(range(len(counts)))
        ax.set_xlabel("After guess")
        ax.set_ylabel("Possible answers")
        ax.grid(alpha=0.2)
        st.pyplot(fig)
        plt.close(fig)

    st.caption(
        "Candidate counts are computed using the team's exact "
        "feedback rules against the Pokémon dataset."
    )


# --------------------------------------------------
# PROFESSOR'S ANALYTICS
# --------------------------------------------------

elif page == "Professor’s Analytics":
    hero(
        "FIELD TEST 03",
        "Professor’s Analytics Lab",
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
            metric("Strategies compared", len(df), "Same dataset")

        st.subheader("Benchmark scoreboard")
        st.dataframe(df, use_container_width=True, hide_index=True)

        fig, ax = plt.subplots(figsize=(9, 3.6))
        bars = ax.bar(df["Solver"], df["Avg guesses"])
        ax.set_ylabel("Average guesses")
        ax.set_title("Average guesses by strategy")
        ax.grid(axis="y", alpha=0.2)

        for bar, value in zip(bars, df["Avg guesses"]):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.04,
                str(value),
                ha="center",
                fontweight="bold"
            )

        st.pyplot(fig)
        plt.close(fig)

        st.markdown("""
        <div class="panel">
        <h3>🧠 How to read the strategies</h3>
        <p><b>Random baseline:</b> ignores clue information and
        samples an unguessed Pokémon.</p>
        <p><b>Filter-based:</b> removes every Pokémon inconsistent
        with all observed clues, then chooses among survivors.</p>
        <p><b>Entropy:</b> chooses the guess expected to split
        remaining candidates into the most informative feedback groups.</p>
        <p><b>Minimax:</b> minimizes the size of the largest possible
        remaining candidate group, with tie-breakers.</p>
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


# --------------------------------------------------
# DATASET EXPLORER
# --------------------------------------------------

else:
    hero(
        "FIELD TEST 04",
        "Pokédex Data Observatory",
        "Explore the real dataset used by every solver in this project."
    )

    df = pd.DataFrame(POKEMON)

    c1, c2, c3 = st.columns(3)

    with c1:
        metric("Species", len(df), "Loaded from pokemon.csv")

    with c2:
        metric("Unique primary types", df.type1.nunique(), "Type categories")

    with c3:
        metric("Generations", df.gen.nunique(), "Generation values")

    left, right = st.columns(2)

    with left:
        st.subheader("Primary type distribution")
        st.bar_chart(df.type1.value_counts().sort_values())

    with right:
        st.subheader("Species by generation")
        st.bar_chart(df.gen.value_counts().sort_index())

    search = st.text_input("Search the Pokédex by species name")

    view = (
        df[df.name.str.contains(search, case=False, na=False)]
        if search else df
    )

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


st.markdown(
    '<p style="text-align:center;color:#9aa0b2;font-size:.8rem;'
    'margin-top:35px">POKÉMON WORDLE · GROUP RESEARCH PROJECT · '
    'BUILT FOR EXPERIMENTATION</p>',
    unsafe_allow_html=True
)
