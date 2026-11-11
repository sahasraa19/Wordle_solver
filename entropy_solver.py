"""Entropy solver: filter candidates, then guess the Pokémon that splits them most evenly."""
import os, pickle, hashlib, math, tempfile
import numpy as np

# ---- ADJUST THESE TWO IMPORTS IF YOUR TEAMMATES NAMED THINGS DIFFERENTLY ----
from engine import feedback
from loader import load_pokemon
# -----------------------------------------------------------------------------

CACHE_DIR = os.path.join(tempfile.gettempdir(), "pokemon_wordle_cache")


def _key(p):
    """Unique identifier of a Pokémon record (dict, pandas row, or object)."""
    if isinstance(p, dict):
        return p.get('name', p.get('Name', str(p)))
    for attr in ('name', 'Name'):
        if hasattr(p, attr):
            return getattr(p, attr)
    return str(p)


class EntropySolver:
    name = "Entropy"

    def __init__(self, pokemon=None, guess_pool="all", use_cache=True):
        """
        guess_pool = "all"        -> may guess any not-yet-guessed Pokémon (best splits)
        guess_pool = "candidates" -> may only guess Pokémon still possible
        """
        pokemon = load_pokemon() if pokemon is None else pokemon
        if hasattr(pokemon, 'to_dict'):              # DataFrame -> list of dicts
            pokemon = pokemon.to_dict('records')
        self.pokemon = list(pokemon)
        self.n = len(self.pokemon)
        self.guess_pool = guess_pool
        self.index = {_key(p): i for i, p in enumerate(self.pokemon)}
        self._first = None                           # first guess computed once
        self._build_matrix(use_cache)

    # ---------- precomputed clue matrix: M[g, a] = clue-pattern id of guess g vs answer a ----------
    def _build_matrix(self, use_cache):
        sig = hashlib.md5('|'.join(str(_key(p)) for p in self.pokemon).encode()).hexdigest()[:10]
        path = f'{CACHE_DIR}/clue_matrix_{self.n}_{sig}.pkl'
        if use_cache and os.path.exists(path):
            with open(path, 'rb') as f:
                self.M, self.patterns = pickle.load(f)
            return
        codes, M = {}, np.zeros((self.n, self.n), dtype=np.int32)
        for i, g in enumerate(self.pokemon):
            for j, a in enumerate(self.pokemon):
                fb = tuple(feedback(g, a))
                M[i, j] = codes.setdefault(fb, len(codes))
        self.M, self.patterns = M, codes
        if use_cache:
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump((M, codes), f)
    except OSError:
        pass

    # ---------- helpers ----------
    def _idx(self, p):
        if isinstance(p, (int, np.integer)):
            return int(p)
        return self.index[p if isinstance(p, str) else _key(p)]

    def filter(self, cand, guess, pattern):
        """Keep only candidates that would have produced this exact feedback."""
        return cand[self.M[guess, cand] == pattern]

    def entropy(self, g, cand):
        counts = np.bincount(self.M[g, cand])
        counts = counts[counts > 0]
        p = counts / counts.sum()
        return float(-(p * np.log2(p)).sum())

    # ---------- the strategy ----------
    def choose(self, cand, guessed):
        """cand: np.array of candidate indices. guessed: set of indices already guessed."""
        if len(cand) == 1:
            return int(cand[0])
        if len(cand) == len(self.pokemon) and self._first is not None:
            return self._first                       # cached first guess
        cand_set = set(cand.tolist())
        pool = range(self.n) if (self.guess_pool == "all" and len(cand) > 2) else cand.tolist()
        best, best_score = None, -1.0
        for g in pool:
            if g in guessed:                         # never repeat a guess
                continue
            score = self.entropy(g, cand) + (1e-6 if g in cand_set else 0.0)  # tie -> prefer a possible answer
            if score > best_score:
                best, best_score = g, score
        if len(cand) == self.n:
            self._first = best
        return best

    # ---------- play a full game ----------
    def play(self, answer, max_guesses=50):
        """Returns (number_of_guesses, list_of_guessed_names)."""
        a = self._idx(answer)
        cand, guessed, history = np.arange(self.n), set(), []
        while len(history) < max_guesses:
            g = self.choose(cand, guessed)
            guessed.add(g)
            history.append(g)
            if g == a:
                return len(history), [_key(self.pokemon[i]) for i in history]
            cand = self.filter(cand, g, self.M[g, a])
        return max_guesses, [_key(self.pokemon[i]) for i in history]

    # ---------- interface for Member 5's app (works with Pokémon objects/names) ----------
    def next_guess(self, candidates, guessed=()):
        cand = np.array([self._idx(c) for c in candidates])
        gs = {self._idx(g) for g in guessed}
        return self.pokemon[self.choose(cand, gs)]
