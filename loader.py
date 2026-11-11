import csv
import os


def load_pokemon(path=None):
    """Read the CSV and return a list of Pokemon records (dicts).

    Each record has exactly six fields:
      name (str), gen (int), type1 (str), type2 (str, "None" if missing),
      height (float, metres), weight (float, kg)
    """
    if path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "data", "pokemon.csv")
    records = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            records.append({
                "name": row["name"],
                "gen": int(row["gen"]),
                "type1": row["type1"],
                "type2": row["type2"],
                "height": float(row["height"]),
                "weight": float(row["weight"]),
            })
    return records
