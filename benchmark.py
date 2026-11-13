
"""Benchmark all four Pokémon Wordle strategies under actual game rules."""

import os
import time
import random

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from engine import MAX_GUESSES, FAIL_SCORE, play_game
from loader import load_pokemon
from basic_solvers import random_solver, filter_solver, filter_candidates
from entropy_solver import EntropySolver
from minimax_solver import MinimaxSolver


ROOT = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(ROOT, "results")


def run_all(repeats=5, seed=0, save=True, show=True):

    os.makedirs(RESULTS_DIR, exist_ok=True)

    random.seed(seed)
    np.random.seed(seed)

    pokemon = load_pokemon()
    n = len(pokemon)

    # Initialize advanced solvers once.
    entropy = EntropySolver(pokemon=pokemon)
    minimax = MinimaxSolver(pokemon=pokemon)

    # All solvers follow the same interface:
    # solver(pokemon, history) -> Pokemon record

    def entropy_solver(pokemon, history):
        candidates = filter_candidates(pokemon, history)
        guessed = [guess for guess, clue in history]
        return entropy.next_guess(candidates, guessed)

    def minimax_solver(pokemon, history):
        candidates = filter_candidates(pokemon, history)
        guessed = [guess for guess, clue in history]
        return minimax.next_guess(candidates, guessed)

    solvers = {
        "Random": (random_solver, repeats),
        "Filter": (filter_solver, repeats),
        "Entropy": (entropy_solver, 1),
        "Minimax": (minimax_solver, 1),
    }

    rows = []
    all_results = {}

    print(f"\nPokémon count: {n}")
    print(f"Maximum guesses: {MAX_GUESSES}")
    print(f"Lost-game score: {FAIL_SCORE}")
    print("\nRunning benchmarks...\n")

    for name, (solver, run_count) in solvers.items():

        scores = []
        start_time = time.perf_counter()

        for repetition in range(run_count):

            for answer in pokemon:

                score, game = play_game(
                    solver,
                    pokemon,
                    answer
                )

                scores.append(score)

        elapsed = time.perf_counter() - start_time

        scores = np.asarray(scores)
        all_results[name] = scores

        wins = np.sum(scores < FAIL_SCORE)

        rows.append({
            "Solver": name,
            "Runs": len(scores),
            "Avg guesses": round(float(scores.mean()), 2),
            "Median": float(np.median(scores)),
            "Worst case": int(scores.max()),
            "Std dev": round(float(scores.std()), 2),
            "Win rate": round(wins / len(scores) * 100, 2),
            "Solved in <=6 (%)": round(
                np.sum(scores <= 6) / len(scores) * 100, 2
            ),
            "ms per game": round(
                elapsed / len(scores) * 1000, 2
            ),
        })

        print(
            f"{name}: {wins}/{len(scores)} wins | "
            f"Average: {scores.mean():.2f} | "
            f"Worst: {scores.max()}"
        )

    df = pd.DataFrame(rows)

    print("\nFINAL BENCHMARK RESULTS")
    print(df.to_string(index=False))

    if save:

        csv_path = os.path.join(
            RESULTS_DIR,
            "results_table.csv"
        )

        chart_path = os.path.join(
            RESULTS_DIR,
            "benchmark_chart.png"
        )

        df.to_csv(csv_path, index=False)
        create_chart(df, chart_path, show)

        print("\nFiles saved:")
        print(csv_path)
        print(chart_path)

    return df


def create_chart(df, path, show=True):

    fig, ax = plt.subplots(figsize=(9, 5))

    bars = ax.bar(
        df["Solver"],
        df["Avg guesses"],
        width=0.6
    )

    ax.set_title(
        "Pokémon Wordle - Strategy Benchmark",
        fontsize=15,
        fontweight="bold"
    )

    ax.set_ylabel("Average guesses (loss = 9)")
    ax.set_xlabel("Strategy")
    ax.set_ylim(0, max(df["Avg guesses"]) + 1)

    ax.grid(
        axis="y",
        linestyle="--",
        alpha=0.3
    )

    ax.set_axisbelow(True)

    for bar, value in zip(bars, df["Avg guesses"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.08,
            f"{value:.2f}",
            ha="center",
            fontsize=10
        )

    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")

    if show:
        plt.show()

    plt.close(fig)


if __name__ == "__main__":
    run_all(repeats=5, seed=0)
