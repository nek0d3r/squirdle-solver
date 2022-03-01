import os
import shutil
import sys
from typing import Any
import urllib.request
import sqlite3

from poketype import Type, Pokemon

squirdle_data_src = "https://raw.githubusercontent.com/Fireblend/squirdle/main/pokedex.csv"

shutil.copy("PokeDB.db", "PokeDB_old.db")

data: Any
with urllib.request.urlopen(squirdle_data_src) as f:
    data = f.read().decode("utf-8").splitlines()
    del data[0]

index: int = 1
pokemon: list[Pokemon] = []
for line in data:
    line = line.split(",")
    # Type 1 shouldn't reaaaally need the none type check, but for the sake of my sanity... 🤷
    pokemon.append(Pokemon(\
        index,\
        line[0],\
        int(line[1]),\
        Type[line[2].upper()] if line[2] != "" else Type.NONE,\
        Type[line[3].upper()] if line[3] != "" else Type.NONE,\
        float(line[4]),\
        float(line[5])))
    index += 1

queryscript: str = """
    DROP TABLE Pokemon;

    CREATE TABLE Pokemon (
        PokeID INTEGER PRIMARY KEY NOT NULL,
        Name STRING NOT NULL UNIQUE,
        Generation INTEGER NOT NULL,
        Type1 INTEGER REFERENCES Type (TypeID) NOT NULL,
        Type2 INTEGER REFERENCES Type (TypeID) NOT NULL DEFAULT (0),
        Height DOUBLE, Weight DOUBLE
    );
"""

for pkmn in pokemon:
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
        ({}, "{}", {}, {}, {}, {}, {});
    """
    queryscript += query.format(\
        pkmn.id,\
        pkmn.name,\
        pkmn.generation,\
        pkmn.type1.value,\
        pkmn.type2.value,\
        pkmn.height,\
        pkmn.weight)

os.remove("PokeDB.db")
shutil.copy("PokeDB_old.db", "PokeDB.db")
os.remove("PokeDB_old.db")