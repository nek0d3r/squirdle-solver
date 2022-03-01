from enum import Enum
import math
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
import sqlite3

from poketype import Type, Pokemon
import update

try:
    update.update_db()
except:
    print("Error updating database, exiting")
    sys.exit()

# Possible clues
class Clue(Enum):
    WRONG = 0
    CORRECT = 1
    WRONGPOS = 2
    UP = 3
    DOWN = 4

# Transient Pokemon data (defaults from db, will be overwritten by db values)
median_gen: int = 5
median_height: float = 1.0
median_weight: float = 30.0
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

# Load all transient data into memory
def load_pokemon():
    con = sqlite3.connect("PokeDB.db")
    cur = con.cursor()

    # Get all Pokemon
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
        global pokemon
        pokemon.append(Pokemon(row[0], row[1], row[2], Type(row[3]), Type(row[4]), row[5], row[6]))
    
    # Get median values from view table
    query = """
        SELECT
            MedianValues."Median Gen",
            MedianValues."Median Height",
            MedianValues."Median Weight"
        FROM MedianValues
    """
    cur.execute(query)

    res = cur.fetchone()
    global median_gen, median_height, median_weight
    median_gen = int(res[0])
    median_height = float(res[1])
    median_weight = float(res[2])

# Helper function, returns true if Pokemon is a possible pick
def is_filtered(pkmn: Pokemon):
    if pkmn.id in guessed_pokemon: return False
    if pkmn.generation < gen_low_bound or pkmn.generation > gen_high_bound: return False
    if pkmn.type1.value in type1_filter: return False
    if pkmn.type2.value in type2_filter: return False
    if pkmn.height < height_low_bound or pkmn.height > height_high_bound: return False
    if pkmn.weight < weight_low_bound or pkmn.weight > weight_high_bound: return False
    return True

# Get next best guess
def get_pick():
    # Get filtered list of possible Pokemon
    possible = []
    global pokemon
    for pkmn in pokemon:
        if is_filtered(pkmn):
            possible.append(pkmn)
    
    # Weight defaults
    top_pick: Pokemon
    best_score = 9999999999

    for pkmn in possible:
        # Total possible Pokemon
        total = float(len(possible))

        # Pokemon with matching types
        type1 = []
        type2 = []
        for type in possible:
            if type.type1 == pkmn.type1:
                type1.append(type)
            if type.type2 == pkmn.type2:
                type2.append(type)
        
        # Total Pokemon with matching types
        type1_qty = len(type1)
        type2_qty = len(type2)
        
        # Calculate weight
        global median_gen, median_height, median_weight
        score = math.pow(median_gen - pkmn.generation, 2.0) * 500 + \
            math.pow(total - type1_qty, 2.0) / total + \
            math.pow(total - type2_qty, 2.0) / total + \
            math.pow(median_height - pkmn.height, 2.0) * 100 + \
            math.pow(median_weight - pkmn.weight, 2.0) * 10
        
        # Update top pick if weight is lower than last top pick
        if score < best_score:
            best_score = score
            top_pick = pkmn
        
        # Dump score data
        # print(("\t{}(Gen {}, Type of {}/{}, Height of {}, Weight of {}):\t\t{}").format(pkmn.name, pkmn.generation, pkmn.type1.name, pkmn.type2.name, pkmn.height, pkmn.weight, score))
    try:
        return top_pick
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

# Reads, parses, and returns last row of clues
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
