from dataclasses import dataclass
from enum import Enum
from selenium import webdriver
from selenium.webdriver.common.by import By
import sqlite3

# Pokemon types
class Type(Enum):
    NONE = 0
    NORMAL = 1
    ELECTRIC = 2
    PSYCHIC = 3
    POISON = 4
    GHOST = 5
    FIRE = 6
    WATER = 7
    GROUND = 8
    FIGHTING = 9
    GRASS = 10
    FLYING = 11
    BUG = 12
    DRAGON = 13
    FAIRY = 14
    STEEL = 15
    DARK = 16
    ICE = 17
    ROCK = 18

# Possible clues
class Clue(Enum):
    WRONG = 0
    CORRECT = 1
    WRONGPOS = 2
    UP = 3
    DOWN = 4

# Pokemon struct
@dataclass
class Pokemon:
    id: int
    name: str
    generation: int
    type1: Type
    type2: Type
    height: float
    weight: float

# All Pokemon
pokemon: list[Pokemon] = []

# Query filters
gen_low_bound: int = 1
gen_high_bound: int = 8
type1_filter: list[Type] = []
type2_filter: list[Type] = []
height_low_bound: float = 0
height_high_bound: float = 10000000
weight_low_bound: float = 0
weight_high_bound: float = 10000000
guessed_pokemon: list[int] = []

def load_pokemon():
    con = sqlite3.connect("PokeDB.db")
    cur = con.cursor()

    query = """
        SELECT
            PokeID,
            Name,
            Generation,
            Type1,
            Type2,
            Height,
            Weight
        FROM Pokemon
    """

    cur.execute(query)
    
    for row in cur.fetchall():
        pokemon.append(Pokemon(row[0], row[1], row[2], Type(row[3]), Type(row[4]), row[5], row[6]))

def is_filtered(pkmn: Pokemon):
    if pkmn.id in guessed_pokemon: return False
    if pkmn.generation < gen_low_bound or pkmn.generation > gen_high_bound: return False
    if pkmn.type1 in type1_filter: return False
    if pkmn.type2 in type2_filter: return False
    if pkmn.height < height_low_bound or pkmn.height > height_high_bound: return False
    if pkmn.weight < weight_low_bound or pkmn.weight > weight_high_bound: return False
    return True

# Get next best guess
def get_pick():
    possible = (pkmn for pkmn in pokemon if is_filtered(pkmn))
    
    con = sqlite3.connect("PokeDB.db")
    cur = con.cursor()

    query = """
        WITH p AS (
            SELECT
                p.PokeID,
                p.Name,
                p.Generation,
                p.Type1,
                p.Type2,
                p.Height,
                p.Weight
            FROM
                Pokemon p
            -- Now for the filters
            WHERE p.Generation BETWEEN {} AND {}
                AND p.Type1 NOT IN ({})
                AND p.Type2 NOT IN ({})
                AND (p.Height BETWEEN {} AND {} OR p.Height IS NULL)
                AND (p.Weight BETWEEN {} AND {} OR p.Weight IS NULL)
                AND p.PokeID NOT IN ({})
        ),
        TypeListOrdered AS (
            SELECT p.Type1 AS TypeName, COUNT(p.Type1) AS Qty
            FROM p
            GROUP BY p.Type1
            UNION
            SELECT p.Type2, COUNT(p.Type2)
            FROM p
            GROUP BY p.Type2
        ),
        TypeList AS (
            SELECT
                TypeName,
                SUM(Qty) AS Qty
            FROM TypeListOrdered
            GROUP BY TypeName
            ORDER BY 2 DESC
        ),
        TotalPoke AS (
            SELECT COUNT(*) AS Total FROM p
        ),
        Medians AS (
            SELECT
                AVG(gen.Generation) AS "Median Gen",
                AVG(hgt.Height) AS "Median Height",
                AVG(wgt.Weight) AS "Median Weight"
            FROM
            (
                SELECT Generation
                FROM p
                ORDER BY Generation
                LIMIT 2 - (SELECT Total FROM TotalPoke) % 2
                OFFSET (SELECT (Total-1)/2 FROM TotalPoke)
            ) gen,
            (
                SELECT Height
                FROM p
                WHERE Height IS NOT NULL
                ORDER BY Height
                LIMIT 2 - (SELECT Total FROM TotalPoke) % 2
                OFFSET (SELECT (Total-1)/2 FROM TotalPoke)
            ) hgt,
            (
                SELECT Weight
                FROM p
                WHERE Weight IS NOT NULL
                ORDER BY Weight
                LIMIT 2 - (SELECT Total FROM TotalPoke) % 2
                OFFSET (SELECT (Total-1)/2 FROM TotalPoke)
            ) wgt
        )

        SELECT
            p.*,
            ("Median Gen"-p.Generation)*("Median Gen"-p.Generation)*500 +
                (Total - tl1.Qty)*(Total - tl1.Qty)/Total +
                (Total - tl2.Qty)*(Total - tl2.Qty)/Total +
                ("Median Height" - p.Height)*("Median Height" - p.Height)*100 +
                ("Median Weight" - p.Weight)*("Median Weight" - p.Weight)*10 AS PickDistance
        FROM p, Medians, TotalPoke
        INNER JOIN TypeList tl1
            ON tl1.TypeName = p.Type1
        INNER JOIN TypeList tl2
            ON tl2.TypeName = p.Type2

        ORDER BY 7
        LIMIT 1
    """

    cur.execute(query.format(\
        gen_low_bound,\
        gen_high_bound,\
        ", ".join(f"{type}" for type in type1_filter),\
        ", ".join(f"{type}" for type in type2_filter),\
        height_low_bound,\
        height_high_bound,\
        weight_low_bound,\
        weight_high_bound,\
        ", ".join(f"{id}" for id in guessed_pokemon)))

    # Get first listed result and return as Pokemon object
    res = cur.fetchone()
    con.close()

    try:
        pick = Pokemon(res[0], res[1], res[2], Type(res[3]), Type(res[4]), res[5], res[6])
    except:
        print('No remaining options found.')
        print('gen_low_bound = {}\ngen_high_bound = {}\ntype1_filter = {}\ntype2_filter = {}\nheight_low_bound = {}\nheight_high_bound = {}\nweight_low_bound = {}\nweight_high_bound = {}\npokemon = {}'.format(\
        gen_low_bound,\
        gen_high_bound,\
        (", ".join(f"'{type}'" for type in type1_filter)) if len(type1_filter) > 0 else "''",\
        (", ".join(f"'{type}'" for type in type2_filter)) if len(type2_filter) > 0 else "''",\
        height_low_bound,\
        height_high_bound,\
        weight_low_bound,\
        weight_high_bound,\
        ", ".join(f"{id}" for id in guessed_pokemon)))
        pick = None

    return pick

def get_clues():
    clues = []
    try:
        # Get columns from last listed row of clues
        last_guess = driver.find_elements(by=By.CSS_SELECTOR, value="div.guesses > div:last-of-type > div.column")
        for i in range(5):
            # Image path is the only way to determine clue type
            clue = last_guess[i].find_element(by=By.TAG_NAME, value="img").get_attribute("src")
            # Positive lookbehind requires fixed-length so here's a messy alternative
            text = clue.split("/")[4].split(".")[0].upper()
            # Cast into clue enumerator
            clues.append(Clue[text])
    except:
        # Default results for loop before first guess
        clues = [None, None, None, None, None]
    return clues

# Defaults for loop before first guess
load_pokemon()
pick = get_pick()
clues = get_clues()

driver = webdriver.Firefox()
driver.get("https://squirdle.fireblend.com/")

guesses = 0

# Continue while guesses allowed and Pokemon not guessed
while(guesses < 8 and not (\
    clues[0] == Clue.CORRECT and\
    clues[1] == Clue.CORRECT and\
    clues[2] == Clue.CORRECT and\
    clues[3] == Clue.CORRECT and\
    clues[4] == Clue.CORRECT)):
    # Add pick to filter
    guessed_pokemon.append(pick.id)

    # Get next best pick
    pick = get_pick()

    # Get guess textbox and input pick
    guess_input = driver.find_element(by=By.ID, value="guess")
    guess_input.send_keys(pick.name)

    # Find submit button and click, increment guesses
    submit = driver.find_element(by=By.CSS_SELECTOR, value="input[type=submit]")
    submit.click()
    guesses += 1

    # Get last set of clues
    clues = get_clues()

    # Update generation filter
    match clues[0]:
        case Clue.DOWN:
            gen_high_bound = pick.generation - 1
        case Clue.UP:
            gen_low_bound = pick.generation + 1
        case Clue.CORRECT:
            gen_low_bound = pick.generation
            gen_high_bound = pick.generation

    # Update type 1 filter
    match clues[1]:
        case Clue.WRONG:
            type1_filter.append(pick.type1.value)
            # If the type in type 1 is wrong, it is in neither slot.
            type2_filter.append(pick.type1.value)
        case Clue.WRONGPOS:
            type1_filter.append(pick.type1.value)
            type2_filter = [type.value for type in Type]
            type2_filter.remove(pick.type1.value)
        case Clue.CORRECT:
            type1_filter = [type.value for type in Type]
            type1_filter.remove(pick.type1.value)

    # Update type 2 filter
    match clues[2]:
        case Clue.WRONG:
            type2_filter.append(pick.type2.value)
            # If the type in type 2 is wrong, it is in neither slot.
            type1_filter.append(pick.type2.value)
        case Clue.WRONGPOS:
            type2_filter.append(pick.type2.value)
            type1_filter = [type.value for type in Type]
            type1_filter.remove(pick.type2.value)
        case Clue.CORRECT:
            type2_filter = [type.value for type in Type]
            type2_filter.remove(pick.type2.value)

    # Update height filter
    match clues[3]:
        case Clue.DOWN:
            height_high_bound = pick.height - 0.05
        case Clue.UP:
            height_low_bound = pick.height + 0.05
        case Clue.CORRECT:
            height_low_bound = pick.height
            height_high_bound = pick.height

    # Update weight filter
    match clues[4]:
        case Clue.DOWN:
            weight_high_bound = pick.weight - 0.05
        case Clue.UP:
            weight_low_bound = pick.weight + 0.05
        case Clue.CORRECT:
            weight_low_bound = pick.weight
            weight_high_bound = pick.weight
