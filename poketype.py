from dataclasses import dataclass
from enum import Enum

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