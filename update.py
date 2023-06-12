import os
import shutil
from typing import Any
import urllib.request
import sqlite3
import json

from poketype import Type, Pokemon

squirdle_data_src = "https://raw.githubusercontent.com/Fireblend/squirdle/main/data/pokedex.json"

# Fetch squirdle pokedex from repo
def fetch_squirdle_data():
    with urllib.request.urlopen(squirdle_data_src) as f:
        data = json.load(f)
        return data

# Scrape data from csv and cast into struct
def scrape_pokemon_data(raw_data):
    index: int = 1
    pokemon: list[Pokemon] = []
    for name, details in raw_data.items():
        generation: int = details[0]
        type1: Type = Type[details[1].upper()] if details[1] != "" else Type.NONE
        type2: Type = Type[details[2].upper()] if details[2] != "" else Type.NONE
        height: float = float(details[3])
        weight: float = float(details[4])

        # Type 1 shouldn't reaaaally need the none type check, but for the sake of my sanity... 🤷
        pokemon.append(Pokemon(index, name, generation, type1, type2, height, weight))

        index += 1
    return pokemon

# Build query script to drop and create Pokemon table, populate with given Pokemon list
def build_query_script(pokemon):
    queryscript: str = """
        DROP TABLE IF EXISTS Pokemon;

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
            INSERT INTO Pokemon
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

    return queryscript

# Create new db with placeholder Pokemon table and views
def create_db():
    try:
        print("Creating new database...")
        
        con = sqlite3.connect("PokeDB.db")
        cur = con.cursor()

        queryscript = """
            CREATE TABLE Pokemon (
                PokeID INTEGER PRIMARY KEY NOT NULL,
                Name STRING NOT NULL UNIQUE,
                Generation INTEGER NOT NULL,
                Type1 INTEGER REFERENCES Type (TypeID) NOT NULL,
                Type2 INTEGER REFERENCES Type (TypeID) NOT NULL DEFAULT (0),
                Height DOUBLE, Weight DOUBLE
            );

            CREATE TABLE Type (
                TypeID INTEGER NOT NULL PRIMARY KEY,
                TypeName INTEGER NOT NULL UNIQUE
            );
        """

        for type in Type:
            query = """
                INSERT INTO Type (TypeID, TypeName)
                VALUES ({}, "{}");
            """
            queryscript += query.format(type.value, type.name.capitalize())

        queryscript += """
            CREATE VIEW MedianValues AS SELECT
                AVG(gen.Generation) AS "Median Gen",
                AVG(hgt.Height) AS "Median Height",
                AVG(wgt.Weight) AS "Median Weight"
            FROM
            (
                SELECT Generation
                FROM Pokemon
                ORDER BY Generation
                LIMIT 2 - (SELECT COUNT(*) FROM Pokemon) % 2
                OFFSET (SELECT (COUNT(*)-1)/2 FROM Pokemon)
            ) gen,
            (
                SELECT Height
                FROM Pokemon
                WHERE Height IS NOT NULL
                ORDER BY Height
                LIMIT 2 - (SELECT COUNT(Height) FROM Pokemon) % 2
                OFFSET (SELECT (COUNT(Height)-1)/2 FROM Pokemon)
            ) hgt,
            (
                SELECT Weight
                FROM Pokemon
                WHERE Weight IS NOT NULL
                ORDER BY Weight
                LIMIT 2 - (SELECT COUNT(Weight) FROM Pokemon) % 2
                OFFSET (SELECT (COUNT(Weight)-1)/2 FROM Pokemon)
            ) wgt;

            CREATE VIEW TypeAnalysis AS SELECT
                TypeName,
                '1' AS Type,
                COUNT(p.Type1) AS Qty
            FROM Pokemon p
            INNER JOIN Type t ON p.Type1 = t.TypeID
            GROUP BY p.Type1
            UNION
            SELECT
                TypeName,
                '2',
                COUNT(p.Type2) AS Type
            FROM Pokemon p
            INNER JOIN Type t ON p.Type2 = t.TypeID
            GROUP BY p.Type2
            ORDER BY 2, 3 DESC;

            CREATE VIEW StrongFirstPicks AS SELECT p.* FROM Pokemon p
            JOIN MedianValues v
                ON p.Generation BETWEEN v."Median Gen" - 1 AND v."Median Gen" + 1
                AND p.Weight BETWEEN v."Median Weight" - 6 AND v."Median Weight" + 6
                AND p.Height BETWEEN v."Median Height" - 0.3 AND v."Median Height" + 0.3
                AND p.Type1 IN (
                    SELECT TypeID FROM Type t
                        INNER JOIN TypeAnalysis ta
                            ON t.TypeName = ta.TypeName
                            AND ta.Type = '1'
                            ORDER BY ta.Type, Qty DESC
                        LIMIT 5
                )
                AND p.Type2 IN (
                    SELECT TypeID FROM Type t
                        INNER JOIN TypeAnalysis ta
                            ON t.TypeName = ta.TypeName
                            AND ta.Type = '2'
                            ORDER BY ta.Type, Qty DESC
                        LIMIT 3
                );
        """

        cur.executescript(queryscript)
        con.commit()
        con.close()

    except:
        con.close()
        os.remove("PokeDB.db")
        print("Something went wrong creating database")

# Update db, call create if it doesn't exist
def update_db():
    if not os.path.isfile("PokeDB.db"):
        print("No database found")
        create_db()

    print("Attempting to update Pokemon database...")
    
    try:
        # Get raw data
        raw_data = fetch_squirdle_data()

        # Generate Pokemon list
        pokemon = scrape_pokemon_data(raw_data)

        # Build queries to run
        query = build_query_script(pokemon)

        # Create backup of existing db
        shutil.copy("PokeDB.db", "PokeDB_old.db")

        con = sqlite3.connect("PokeDB.db")
        cur = con.cursor()
        cur.executescript(query)

        con.commit()

        os.remove("PokeDB_old.db")
        print("Database successfully updated")
    except:
        # If something went wrong, revert to backup
        con.close()

        if os.path.isfile("PokeDB_old.db"):
            os.remove("PokeDB.db")
            shutil.copy("PokeDB_old.db", "PokeDB.db")
            os.remove("PokeDB_old.db")
        
        print("Something went wrong updating database, nothing has changed")
    
    con.close()
