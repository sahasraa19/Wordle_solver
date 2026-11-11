"""basic_solvers.py  (owner: Member 2)

Solver interface used by the whole team:
    solver(pokemon, history) -> one Pokemon record
  pokemon : list of all Pokemon records (dicts)
  history : list of (guess_record, clue) pairs so far
A solver must never repeat a guess.
"""
import random

from engine import feedback


def _unguessed(pokemon, history):
    """All Pokemon that have not been guessed yet."""
    guessed = {g["name"] for g, _ in history}
    return [p for p in pokemon if p["name"] not in guessed]


def random_solver(pokemon, history):
    """Baseline: ignores every clue and picks any Pokemon not guessed yet."""
    return random.choice(_unguessed(pokemon, history))


def filter_candidates(pokemon, history):
    """Candidates = Pokemon that are still possible answers.

    A Pokemon stays a candidate only if
      1. it has not been guessed yet, and
      2. for EVERY (guess, clue) in history, pretending it is the secret would
         have produced exactly that clue:  feedback(guess, candidate) == clue
    The real secret always survives, so the list is never empty.
    """
    candidates = []
    for p in _unguessed(pokemon, history):
        if all(feedback(g, p) == clue for g, clue in history):
            candidates.append(p)
    return candidates


def filter_solver(pokemon, history):
    """CSP-style solver: shrink the candidate list, then guess one of them."""
    candidates = filter_candidates(pokemon, history)
    if not candidates:                      # should never happen, but stay safe
        candidates = _unguessed(pokemon, history)
    return random.choice(candidates)
