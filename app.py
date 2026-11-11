
import random
import streamlit as st
import pandas as pd

from loader import load_pokemon
from engine import Game, feedback
from basic_solvers import random_solver, filter_solver
from entropy_solver import EntropySolver
from minimax_solver import MinimaxSolver


st.set_page_config(
    page_title="Pokémon Wordle",
    page_icon="⚡",
    layout="wide"
)

MAX_GUESSES = 8


# ---------------- DATA LOADING ----------------

@st.cache_data
def load_data():
    return load_pokemon("data/pokemon_full.csv")


@st.cache_resource
def load_ai(pokemon):
    entropy = EntropySolver(pokemon=pokemon)
    minimax = MinimaxSolver(pokemon=pokemon)
    return entropy, minimax


st.title("⚡ Pokémon Wordle")
st.subheader("Intelligent Guessing Strategies")
st.write("Guess the hidden Pokémon or watch AI strategies solve it!")

try:
    pokemon = load_data()

    if not pokemon:
        st.error("The Pokémon dataset is empty.")
        st.stop()

    pokemon_dict = {p["name"]: p for p in pokemon}

except Exception as e:
    st.error("Unable to load the Pokémon dataset.")
    st.exception(e)
    st.stop()


# ---------------- GAME MODE ----------------

mode = st.sidebar.selectbox(
    "Choose Game Mode",
    [
        "Human Gameplay",
        "AI Demonstration",
        "Algorithm Comparison"
    ]
)


# ---------------- DISPLAY HISTORY ----------------

def show_history(history):
    rows = []

    for i, (guess, clue) in enumerate(history, 1):
        rows.append({
            "Guess": i,
            "Pokémon": guess["name"],
            "Generation": clue[0],
            "Type 1": clue[1],
            "Type 2": clue[2],
            "Height": clue[3],
            "Weight": clue[4]
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True
    )


# ---------------- BASIC AI ----------------

def run_basic(strategy, secret):
    game = Game(
        pokemon,
        secret=secret,
        max_guesses=MAX_GUESSES
    )

    solver = (
        random_solver
        if strategy == "Random"
        else filter_solver
    )

    while game.status == "playing":
        guess = solver(pokemon, game.history)
        game.guess(guess)

    return game


# ---------------- ADVANCED AI ----------------

def run_advanced(strategy, secret):
    entropy, minimax = load_ai(pokemon)

    solver = (
        entropy
        if strategy == "Entropy"
        else minimax
    )

    count, names = solver.play(
        secret,
        max_guesses=MAX_GUESSES
    )

    game = Game(
        pokemon,
        secret=secret,
        max_guesses=MAX_GUESSES
    )

    for name in names:
        if game.status != "playing":
            break

        if name not in pokemon_dict:
            continue

        game.guess(pokemon_dict[name])

    return game


def run_ai(strategy, secret):
    if strategy in ["Random", "Filter"]:
        return run_basic(strategy, secret)

    return run_advanced(strategy, secret)


# ==================================================
# HUMAN GAMEPLAY
# ==================================================

if mode == "Human Gameplay":

    st.header("🎮 Human Gameplay")

    if "human_secret" not in st.session_state:
        st.session_state.human_secret = random.choice(pokemon)["name"]
        st.session_state.human_history = []
        st.session_state.human_status = "playing"

    if st.button("🔄 New Game"):
        st.session_state.human_secret = random.choice(pokemon)["name"]
        st.session_state.human_history = []
        st.session_state.human_status = "playing"
        st.rerun()

    secret = pokemon_dict[st.session_state.human_secret]
    history = st.session_state.human_history

    st.write(
        f"**Guesses used:** {len(history)} / {MAX_GUESSES}"
    )

    if st.session_state.human_status == "playing":

        guessed = [
            guess["name"]
            for guess, clue in history
        ]

        available = [
            p["name"]
            for p in pokemon
            if p["name"] not in guessed
        ]

        selected = st.selectbox(
            "Choose a Pokémon",
            available
        )

        if st.button("Submit Guess", type="primary"):

            guess = pokemon_dict[selected]
            clue = feedback(guess, secret)

            history.append((guess, clue))

            if guess["name"] == secret["name"]:
                st.session_state.human_status = "won"

            elif len(history) >= MAX_GUESSES:
                st.session_state.human_status = "lost"

            st.rerun()

    if history:
        st.subheader("Your Guess History")
        show_history(history)

    if st.session_state.human_status == "won":
        st.success(
            f"You won! The Pokémon was {secret['name']} 🎉"
        )

    elif st.session_state.human_status == "lost":
        st.error(
            f"Game over! The Pokémon was {secret['name']}."
        )


# ==================================================
# AI DEMONSTRATION
# ==================================================

elif mode == "AI Demonstration":

    st.header("🤖 AI Demonstration")

    strategy = st.selectbox(
        "Choose AI Strategy",
        ["Random", "Filter", "Entropy", "Minimax"]
    )

    secret_name = st.selectbox(
        "Choose Secret Pokémon",
        [p["name"] for p in pokemon]
    )

    if st.button("Run AI", type="primary"):

        try:
            with st.spinner("AI is thinking..."):

                game = run_ai(
                    strategy,
                    pokemon_dict[secret_name]
                )

            st.subheader("AI Guess History")
            show_history(game.history)

            if game.status == "won":
                st.success(
                    f"{strategy} solved {secret_name} "
                    f"in {game.guesses_used()} guesses! 🎉"
                )

            else:
                st.warning(
                    f"{strategy} could not solve it "
                    f"within {MAX_GUESSES} guesses."
                )

        except Exception as e:
            st.error("An error occurred while running the AI.")
            st.exception(e)


# ==================================================
# ALGORITHM COMPARISON
# ==================================================

elif mode == "Algorithm Comparison":

    st.header("📊 Algorithm Comparison")

    st.write(
        "Compare the performance of four Pokémon guessing strategies."
    )

    sample_size = st.slider(
        "Number of Pokémon to test",
        min_value=5,
        max_value=len(pokemon),
        value=min(25, len(pokemon))
    )

    if st.button("Compare Algorithms", type="primary"):

        selected_answers = random.sample(
            pokemon,
            sample_size
        )

        strategies = [
            "Random",
            "Filter",
            "Entropy",
            "Minimax"
        ]

        results = []

        progress = st.progress(0)
        total = len(strategies) * sample_size
        completed = 0

        try:
            for strategy in strategies:

                scores = []
                wins = 0

                for secret in selected_answers:

                    game = run_ai(strategy, secret)

                    if game.status == "won":
                        wins += 1
                        scores.append(game.guesses_used())

                    else:
                        scores.append(MAX_GUESSES)

                    completed += 1
                    progress.progress(completed / total)

                results.append({
                    "Strategy": strategy,
                    "Average Guesses": round(
                        sum(scores) / len(scores), 2
                    ),
                    "Win Rate (%)": round(
                        wins / len(scores) * 100, 2
                    )
                })

            df = pd.DataFrame(results)

            st.subheader("Comparison Results")
            st.dataframe(
                df,
                use_container_width=True
            )

            st.subheader("Average Guesses")
            st.bar_chart(
                df.set_index("Strategy")["Average Guesses"]
            )

            st.subheader("Win Rate")
            st.bar_chart(
                df.set_index("Strategy")["Win Rate (%)"]
            )

        except Exception as e:
            st.error("Algorithm comparison failed.")
            st.exception(e)


# ---------------- FOOTER ----------------

st.markdown("---")

st.caption(
    "Pokémon Wordle | Intelligent Guessing Strategies | "
    "Academic Year 2026–27"
)
