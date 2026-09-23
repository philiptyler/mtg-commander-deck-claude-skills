# Commander Bracket System — reference rubric

Source: [WotC's "Introducing Commander Brackets" beta announcement](https://magic.wizards.com/en/news/announcements/introducing-commander-brackets-beta).
This is a **beta system WotC has already revised once** and may revise again —
treat this file as the thing to update when they do, rather than hardcoding
thresholds in the analysis scripts.

`scripts/analyze_deck.py` only checks the mechanically-detectable parts
(Game Changers count, mass land denial, extra-turn density) via regex over
Scryfall oracle text. Two-card combo potential and "casual vs. optimized
intent" are explicitly **not** computed — they need a human (or Claude,
reading the actual decklist) to judge, and the script's output says so.

## Bracket 1: Exhibition
- **Game Changers:** none allowed
- **Two-card combos:** no intentional two-card infinite combos
- **Mass land denial:** none
- **Extra turns:** none
- **Tutors:** sparse
- **Intent:** themed/casual decks where winning is secondary to the deck's gimmick

## Bracket 2: Core
- **Game Changers:** none allowed
- **Two-card combos:** no intentional two-card infinite combos
- **Mass land denial:** none
- **Extra turns:** low quantities only, not chained/looped
- **Tutors:** sparse
- **Intent:** average modern preconstructed-deck power level

## Bracket 3: Upgraded
- **Game Changers:** up to 3
- **Two-card combos:** no intentional *early-game* two-card infinite combos
- **Mass land denial:** none
- **Extra turns:** low quantities only, not chained/looped
- **Intent:** stronger than precon, carefully optimized within those limits

## Bracket 4: Optimized
- **Game Changers:** unrestricted
- **Restrictions:** none beyond the banned list
- **Intent:** highest power for most casual playgroups, no tournament-metagame focus

## Bracket 5: cEDH
- **Game Changers:** unrestricted
- **Restrictions:** none beyond the banned list
- **Intent:** competitive mindset, built with the tournament metagame in mind

## Notes for the analysis script

- `game_changer` is a boolean Scryfall exposes directly on card objects — no
  need to hand-maintain the list ourselves; just verify it's still present
  next time Scryfall's schema is checked.
- Mass land denial detection is a small regex list (`destroy all lands`,
  `each player sacrifices a land`, etc.) — likely incomplete, extend it as
  false negatives show up on real decks.
- A suggested bracket of "4 or higher" doesn't distinguish 4 from 5 — that
  split is pure intent (built for a casual table vs. built for a tournament
  metagame), which only the deck's owner can actually answer.
