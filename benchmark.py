
"""Benchmark all solvers under the actual 8-guess game rules."""

import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from engine import MAX_GUESSES, FAIL_SCORE, play_game
from loader import load_pokemon
from basic_solvers import random_solver, filter_solver
from entropy_solver import EntropySolver
from minimax_solver import MinimaxSolver

ROOT = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(ROOT, "results")


def run_all(repeats=5, seed=0, save=True, show=True):
    os.makedirs(RESULTS_DIR, exist_ok=True)

    pokemon = load_pokemon()
    rng = np.random.default_rng(seed)

    entropy = EntropySolver(pokemon=pokemon)
    minimax = MinimaxSolver(pokemon=pokemon)

    def random_fn(pokemon, history):
        guessed = {g["name"] for g, _ in history}
        remaining = [p for p in pokemon if p["name"] not in guessed]
        return remaining[int(rng.integers(len(remaining)))]

    solvers = {
        "Random": (random_fn, repeats),
        "Filter": (filter_solver, repeats),
        "Entropy": (
            lambda p, h: entropy.next_guess(
                [x for x in p if x["name"] not in {g["name"] for g, _ in h}]
                if not h else entropy_candidates(p, h),
                [g for g, _ in h]
            ),
            1
        ),
        "Minimax": (
            lambda p, h: minimax.next_guess(
                [x for x in p if x["name"] not in {g["name"] for g, _ in h}]
                if not h else minimax_candidates(p, h),
                [g for g, _ in h]
            ),
            1
        ),
    }

    def candidates_for(solver, p, history):
        if solver == "Entropy":
            return entropy_candidates(p, history)
        return minimax_candidates(p, history)

    rows = []
    all_results = {}

    for name, (solver, reps) in solvers.items():
        scores = []
        start = time.perf_counter()

        for _ in range(reps):
            for answer in pokemon:
                if name in ("Entropy", "Minimax"):
                    def wrapped(p, h, s=name):
                        candidates = candidates_for(s, p, h)
                        guessed = [g for g, _ in h]
                        obj = entropy if s == "Entropy" else minimax
                        return obj.next_guess(candidates, guessed)
                else:
                    wrapped = solver

                score, _ = play_game(wrapped, pokemon, answer)
                scores.append(score)

        elapsed = time.perf_counter() - start
        scores = np.asarray(scores)
        all_results[name] = scores

        rows.append({
            "Solver": name,
            "Runs": len(scores),
            "Avg guesses": round(scores.mean(), 2),
            "Median": float(np.median(scores)),
            "Worst case": int(scores.max()),
            "Win rate": round((scores < FAIL_SCORE).mean() * 100, 2),
            "Solved in <=6 (%)": round((scores <= 6).mean() * 100, 2),
            "ms per game": round(elapsed / len(scores) * 1000, 2),
        })

    df = pd.DataFrame(rows)

    if save:
        df.to_csv(os.path.join(RESULTS_DIR, "results_table.csv"), index=False)
        _chart(df, all_results, os.path.join(RESULTS_DIR, "benchmark_chart.png"), show)

    print(df.to_string(index=False))
    return df


def entropy_candidates(pokemon, history):
    from basic_solvers import filter_candidates
    return filter_candidates(pokemon, history)


def minimax_candidates(pokemon, history):
    from basic_solvers import filter_candidates
    return filter_candidates(pokemon, history)


def _chart(df, results, path, show):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(df["Solver"], df["Avg guesses"])
    ax.set_ylabel("Average guesses (loss = 9)")
    ax.set_title("Pokémon Wordle — Strategy Benchmark")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")

    if show:
        plt.show()
    plt.close(fig)


if __name__ == "__main__":
    run_all()
