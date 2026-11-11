
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

html, body, [class*="css"] {font-family:Nunito,sans-serif}
.stApp {
 background:radial-gradient(circle at 85% 3%,#fff1d6 0,transparent 27%),
 linear-gradient(135deg,#fffaf0,#f5f7ff 55%,#fff5f2)
}
.block-container {padding-top:1.6rem;max-width:1320px}
.lab-hero {
 background:linear-gradient(120deg,#242b52,#384b7b 58%,#e35b59);
 padding:28px 34px;border-radius:25px;color:white;
 box-shadow:0 14px 35px #28345a25;margin-bottom:18px
}
.lab-hero h1 {
 font-family:'Space Grotesk';font-size:2.45rem;
 margin:0;color:white;letter-spacing:-1.5px
}
.lab-hero p {color:#e8edff;margin:.35rem 0 0;font-size:1.02rem}
.eyebrow {
 font-size:.72rem;letter-spacing:2px;
 text-transform:uppercase;font-weight:900;color:#ffd56a
}
.panel {
 background:#ffffffd9;border:1px solid #e8e9f2;
 border-radius:18px;padding:18px 20px;
 box-shadow:0 7px 22px #27345a0c
}
.metric {
 background:white;border:1px solid #ececf4;
 border-radius:16px;padding:15px 17px;
 box-shadow:0 5px 15px #27345a0a
}
.metric small {
 color:#747b91;font-weight:800;
 text-transform:uppercase;letter-spacing:1px
}
.metric b {
 display:block;font-family:'Space Grotesk';
 font-size:1.75rem;color:#29365f
}
.pill {
 display:inline-block;border-radius:99px;padding:5px 11px;
 background:#fff0c9;color:#78510b;font-size:.78rem;
 font-weight:900;margin:3px
}
div[data-testid="stMetric"] {
 background:white;border:1px solid #ececf4;
 padding:14px;border-radius:15px
}
.stButton>button {
 border-radius:12px;font-weight:800;border:0;
 background:#344775;color:white;padding:.55rem 1rem
}
.stButton>button:hover {background:#e35b59;color:white}
footer {visibility:hidden}
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
