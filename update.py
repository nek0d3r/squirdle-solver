import os
import shutil
from typing import Any
import urllib.request

squirdle_data_src = "https://raw.githubusercontent.com/Fireblend/squirdle/main/pokedex.csv"

shutil.copy("PokeDB.db", "PokeDB_old.db")

data: Any
with urllib.request.urlopen(squirdle_data_src) as f:
    data = f.read().decode("utf-8").splitlines()
    del data[0]

for line in data:
    line = line.split(",")
    print(line)
    query = """
        INSERT INTO
            Pokemon
        (
            PokeID,
            Name,
            Generation,
            Type1,
            Type2,
            Height,
            Weight
        )
        VALUES
        ({}, "{}", {}, {}, {}, {}, {})
    """

os.remove("PokeDB.db")
shutil.copy("PokeDB_old.db", "PokeDB.db")
os.remove("PokeDB_old.db")