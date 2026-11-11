"""engine.py  (owner: Member 1)

ALL clue rules live ONLY in this file.

A Pokemon record is a dict: name, gen, type1, type2, height, weight.
A clue is a tuple of 5 values: (generation, type1, type2, height, weight)
  generation / height / weight -> "green", "up" or "down"
        green = same generation / within 10% band
        up    = the answer is higher than the guess
        down  = the answer is lower than the guess
  type1 / type2 -> "green", "amber" or "grey"
History is a list of (guess_record, clue) pairs.
Solver interface (everyone uses this):  solver(pokemon, history) -> a Pokemon record
"""
import random

MAX_GUESSES = 8      # guesses allowed per game
FAIL_SCORE = 9       # a lost game counts as 9 guesses in the benchmark
BAND = 0.10          # 10% band for height and weight


def _number_clue(guess_value, answer_value):
    """green if the answer is within BAND of the guess, else up/down."""
    if abs(answer_value - guess_value) <= BAND * guess_value + 1e-9:
        return "green"
    return "up" if answer_value > guess_value else "down"


def feedback(guess, answer):
    """Compare a guessed Pokemon with the secret one and return the clue tuple."""
    # Generation
    if guess["gen"] == answer["gen"]:
        gen = "green"
    else:
        gen = "up" if answer["gen"] > guess["gen"] else "down"

    # Type 1: green = same slot, amber = type is in the answer's other slot
    if guess["type1"] == answer["type1"]:
        t1 = "green"
    elif guess["type1"] == answer["type2"]:
        t1 = "amber"
    else:
        t1 = "grey"

    # Type 2: None counts as a normal value for green; never amber for None
    if guess["type2"] == answer["type2"]:
        t2 = "green"
    elif guess["type2"] != "None" and guess["type2"] == answer["type1"]:
        t2 = "amber"
    else:
        t2 = "grey"

    height = _number_clue(guess["height"], answer["height"])
    weight = _number_clue(guess["weight"], answer["weight"])
    return (gen, t1, t2, height, weight)


class Game:
    """One game: a secret Pokemon, a history of guesses, win/lose after 8 guesses."""

    def __init__(self, pokemon, secret=None, max_guesses=MAX_GUESSES, seed=None):
        self.pokemon = pokemon
        self.secret = secret if secret is not None else random.Random(seed).choice(pokemon)
        self.max_guesses = max_guesses
        self.history = []          # list of (guess_record, clue)
        self.status = "playing"    # "playing", "won" or "lost"

    def guess(self, guess_record):
        """Make one guess, return the clue. Winning = guessing the secret by name
        (not 'all green', because the 10% band lets different Pokemon look alike)."""
        if self.status != "playing":
            raise ValueError("Game is already over")
        clue = feedback(guess_record, self.secret)
        self.history.append((guess_record, clue))
        if guess_record["name"] == self.secret["name"]:
            self.status = "won"
        elif len(self.history) >= self.max_guesses:
            self.status = "lost"
        return clue

    def guesses_used(self):
        return len(self.history)


def play_game(solver, pokemon, secret):
    """Let a solver play a full game against a given secret Pokemon.
    Returns (score, game). score = guesses used, or FAIL_SCORE (9) if lost."""
    game = Game(pokemon, secret=secret)
    while game.status == "playing":
        game.guess(solver(pokemon, game.history))
    score = game.guesses_used() if game.status == "won" else FAIL_SCORE
    return score, game
