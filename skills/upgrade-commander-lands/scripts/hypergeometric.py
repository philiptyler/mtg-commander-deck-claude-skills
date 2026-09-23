"""Stdlib hypergeometric probability, used to compute the actual odds of
having enough colored mana sources by a given turn - no scipy dependency,
matching the rest of this repo.

Why a computed probability instead of a lookup table: the commonly-cited
Frank Karsten "sources needed" figures are well-corroborated as flat
99-card-deck numbers (~22 sources for reliable single-pip, ~29 for
double-pip) but a reliable turn-by-turn breakdown specifically for
Commander wasn't verifiable from primary sources when this was built.
Computing the probability directly from the deck's actual numbers is more
precise than reproducing a table anyway - this was sanity-checked against
the externally-corroborated 22/29-source figures at turn 4 on the play and
lines up (20-22 sources ~ 90-93% for one pip; 29-32 sources ~ 85-90% for
two pips), which validates the model without asserting exact numbers this
project couldn't independently confirm.
"""

import math

TARGET_PROBABILITY = 0.90


def cards_seen_by_turn(turn: int, on_the_play: bool = True) -> int:
    """Opening hand (7) plus one draw per turn from turn 2 onward if on the
    play (no draw turn 1), or from turn 1 if on the draw."""
    draws = max(0, turn - 1) if on_the_play else turn
    return 7 + draws


def probability_at_least(k_min: int, population: int, successes: int, draws: int) -> float:
    """P(X >= k_min) where X ~ Hypergeometric(population, successes, draws)."""
    if k_min <= 0:
        return 1.0
    if successes <= 0:
        return 0.0
    draws = min(draws, population)
    complement = 0.0
    for x in range(0, min(k_min, successes + 1)):
        if (draws - x) > (population - successes) or (draws - x) < 0:
            continue
        complement += math.comb(successes, x) * math.comb(population - successes, draws - x) / math.comb(population, draws)
    return max(0.0, 1.0 - complement)
