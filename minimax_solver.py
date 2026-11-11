"""Minimax solver: pick the guess whose WORST-case feedback leaves the fewest candidates."""
import os, pickle, hashlib, math, tempfile
import numpy as np

# ---- ADJUST THESE TWO IMPORTS IF YOUR TEAMMATES NAMED THINGS DIFFERENTLY ----
from engine import feedback
from loader import load_pokemon
# -----------------------------------------------------------------------------

CACHE_DIR = os.path.join(tempfile.gettempdir(), "pokemon_wordle_cache")


def _key(p):
    if isinstance(p, dict):
        return p.get('name', p.get('Name', str(p)))
    for attr in ('name', 'Name'):
        if hasattr(p, attr):
            return getattr(p, attr)
    return str(p)


class MinimaxSolver:
    name = "Minimax"

    def __init__(self, pokemon=None, guess_pool="all", use_cache=True):
        pokemon = load_pokemon() if pokemon is None else pokemon
        if hasattr(pokemon, 'to_dict'):
            pokemon = pokemon.to_dict('records')
        self.pokemon = list(pokemon)
        self.n = len(self.pokemon)
        self.guess_pool = guess_pool
        self.index = {_key(p): i for i, p in enumerate(self.pokemon)}
        self._first = None
        self._build_matrix(use_cache)

    # Same cache file name as Member 3's EntropySolver, so the matrix is shared and built only once.
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
                M[i, j] = codes.setdefault(tuple(feedback(g, a)), len(codes))
        self.M, self.patterns = M, codes
        if use_cache:
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump((M, codes), f)
    except OSError:
        pass

    def _idx(self, p):
        if isinstance(p, (int, np.integer)):
            return int(p)
        return self.index[p if isinstance(p, str) else _key(p)]

    def filter(self, cand, guess, pattern):
        return cand[self.M[guess, cand] == pattern]

    def worst_case(self, g, cand):
        """Size of the biggest group of candidates this guess could leave."""
        return int(np.bincount(self.M[g, cand]).max())

    def choose(self, cand, guessed):
        if len(cand) == 1:
            return int(cand[0])
        if len(cand) == self.n and self._first is not None:
            return self._first                        # first guess computed once
        cand_set = set(cand.tolist())
        pool = range(self.n) if (self.guess_pool == "all" and len(cand) > 2) else cand.tolist()
        best, best_key = None, None
        for g in pool:
            if g in guessed:                          # never repeat a guess
                continue
            counts = np.bincount(self.M[g, cand])
            worst = int(counts.max())
            expected = float((counts.astype(float) ** 2).sum() / len(cand))
            # smallest worst case; tie -> a possible answer; tie -> smaller expected remainder
            k = (worst, 0 if g in cand_set else 1, expected)
            if best_key is None or k < best_key:
                best, best_key = g, k
        if len(cand) == self.n:
            self._first = best
        return best

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

    def next_guess(self, candidates, guessed=()):
        cand = np.array([self._idx(c) for c in candidates])
        gs = {self._idx(g) for g in guessed}
        return self.pokemon[self.choose(cand, gs)]
