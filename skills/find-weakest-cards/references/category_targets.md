# Category target ranges, by Commander Bracket

Used by `scripts/find_weak_cards.py` to flag category oversaturation (e.g.
"15 ramp spells is probably too many"). These are **not** official WotC
numbers — the [Commander Bracket System](../../review-commander-deck/references/bracket_rubric.md)
only specifies Game Changers/mass land denial/extra turns/combos, nothing
about ramp or removal counts.

The Bracket 3 row is sourced directly from the widely-cited "Command Zone
Template" (Jimmy Wong / Josh Lee Kwai, *The Command Zone* podcast): 36-38
lands, 10-12 ramp, 8-10 card draw, 8-10 removal, ~3 board wipes. That matches
what we independently found in the first deck this skill was tested against
(`review-commander-deck`'s dinos review: 36 lands, 12 ramp, 10 draw, 12
targeted removal, 2 wipes), which is reassuring but is one data point.

Brackets 1, 2, 4, and 5 are **my own extrapolation** from that anchor, not a
separately-sourced figure — adjust freely if they don't match what you see
across more decks. Bracket 1 targets are intentionally loose: Exhibition
decks are built around a theme/gimmick first, so "not enough removal" is
often the point, not a flaw.

| Category | Bracket 1 | Bracket 2 | Bracket 3 | Bracket 4 | Bracket 5 |
|---|---|---|---|---|---|
| Lands | 36-40 | 36-38 | 35-38 | 33-36 | 30-34 |
| Ramp | 6-12 | 8-10 | 10-12 | 10-13 | 13-16 |
| Card draw | 6-12 | 8-10 | 10-12 | 10-14 | 8-12 |
| Targeted removal | 4-12 | 8-10 | 10-14 | 12-16 | 10-15 |
| Board wipes | 0-3 | 1-3 | 2-3 | 2-4 | 1-3 |
| Nonland tutors | 0-3 | 0-3 | 3-6 | 5-9 | 8-14 |

Notes:

- "Nonland tutors" deliberately excludes fetchlands (`land_tutor` in
  `analyze_deck.py`'s categories). Fetchlands are a mana-base/consistency
  tool almost every 2+ color deck runs regardless of power level; they
  aren't the same "silver bullet density" signal a card like Vampiric
  Tutor is, so mixing them into one count would flag a completely normal
  manabase as "too many tutors."
- Bracket 5 (cEDH) card draw looks low relative to Bracket 4 on purpose —
  those decks lean on tutors and combo pieces for card advantage more than
  raw draw spells, so a low draw count there isn't a real signal the way it
  would be at Bracket 3.
- These are ranges, not hard cutoffs. `find_weak_cards.py` reports "over"/
  "under"/"within" per category; treat "over" as "look here first for
  cuts," not "this category is definitely bloated."
