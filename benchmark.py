"""Benchmark: run every solver on every possible answer; print a table, save CSV + chart."""
import time, os
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

from minimax_solver import MinimaxSolver, _key
from entropy_solver import EntropySolver

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "results"
)


TEAM_OVERRIDES = {}


def run_all(repeats=5, seed=0, save=True, show=True):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    rng = np.random.default_rng(seed)
    Mm = MinimaxSolver()
    En = EntropySolver(pokemon=Mm.pokemon)   # same clue matrix cache
    n = Mm.n

    def random_solver(a):                    # ignores clues, never repeats
        order = rng.permutation(n)
        return int(np.where(order == a)[0][0]) + 1

    def filter_solver(a):                    # random guess among still-consistent candidates
        cand, k = np.arange(n), 0
        while True:
            g = int(rng.choice(cand)); k += 1
            if g == a:
                return k
            cand = Mm.filter(cand, g, Mm.M[g, a])

    solvers = {
        "Random":  (TEAM_OVERRIDES.get("Random", random_solver), repeats),
        "Filter":  (TEAM_OVERRIDES.get("Filter", filter_solver), repeats),
        "Entropy": (lambda a: En.play(a)[0], 1),     # deterministic -> one pass
        "Minimax": (lambda a: Mm.play(a)[0], 1),
    }

    rows, all_results = [], {}
    for name, (fn, reps) in solvers.items():
        t = time.time()
        res = [fn(a) for _ in range(reps) for a in range(n)]
        elapsed = time.time() - t
        res = np.array(res)
        all_results[name] = res
        rows.append({
            "Solver": name,
            "Avg guesses": round(res.mean(), 2),
            "Median": float(np.median(res)),
            "Worst case": int(res.max()),
            "Std dev": round(res.std(), 2),
            "Solved in <=6 (%)": round((res <= 6).mean() * 100, 1),
            "ms per game": round(elapsed / len(res) * 1000, 2),
        })
    df = pd.DataFrame(rows)

    # hardest answers for the deterministic solvers (useful for the report)
    hardest = {}
    for name, solver in (("Entropy", En), ("Minimax", Mm)):
        r = all_results[name]
        top = np.argsort(-r)[:5]
        hardest[name] = [(_key(Mm.pokemon[i]), int(r[i])) for i in top]

    if show:
        print(df.to_string(index=False))
        for k, v in hardest.items():
            print(f"Hardest for {k}:", v)

    if save:
        df.to_csv(f'{RESULTS_DIR}/results_table.csv', index=False)
        _chart(df, all_results, f'{RESULTS_DIR}/benchmark_chart.png', show)
        print("Saved:", f'{RESULTS_DIR}/results_table.csv', "and", f'{RESULTS_DIR}/benchmark_chart.png')
    return df


def _chart(df, all_results, path, show):
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
    colors = {"Random": "#999999", "Filter": "#4c9be8", "Entropy": "#2ca02c", "Minimax": "#e8774c"}

    bars = ax[0].bar(df["Solver"], df["Avg guesses"], color=[colors[s] for s in df["Solver"]])
    ax[0].set_yscale("log")
    ax[0].set_ylabel("Average guesses (log scale)")
    ax[0].set_title("Average guesses per solver")
    for b, v in zip(bars, df["Avg guesses"]):
        ax[0].text(b.get_x() + b.get_width()/2, v, str(v), ha="center", va="bottom")

    cap = 10
    names = ["Filter", "Entropy", "Minimax"]
    w = 0.27
    xs = np.arange(1, cap + 1)
    for i, name in enumerate(names):
        r = np.minimum(all_results[name], cap)
        pct = np.bincount(r, minlength=cap + 1)[1:] / len(r) * 100
        ax[1].bar(xs + (i - 1) * w, pct, w, label=name, color=colors[name])
    ax[1].set_xticks(xs)
    ax[1].set_xticklabels([str(i) for i in range(1, cap)] + [f"{cap}+"])
    ax[1].set_xlabel("Guesses needed")
    ax[1].set_ylabel("% of answers")
    ax[1].set_title("Distribution of guesses (Random omitted)")
    ax[1].legend()

    plt.tight_layout()
    plt.savefig(path, dpi=200)
    if show:
        plt.show()
    plt.close(fig)
