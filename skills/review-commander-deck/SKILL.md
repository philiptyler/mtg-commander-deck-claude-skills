---
name: review-commander-deck
description: Reviews a Magic: The Gathering Commander (EDH) decklist for ramp, removal, card draw, curve, and win conditions, and estimates its Commander Bracket (1-5). Use when the user pastes a Commander/EDH decklist and asks for a deck review, power-level check, bracket estimate, or feedback on what the deck does well or is missing.
---

# Review Commander Deck

Turns a pasted Commander decklist plus the player's own sense of the deck
into a data-backed review: real Scryfall card data, computed deck stats, and
a bracket estimate — checked against what the player actually said the deck
does well or poorly.

## Workflow

1. **Gather input.** If not already provided, ask the user for:
   - The decklist, pasted in plain text (`1 Sol Ring` / `1x Sol Ring` style,
     Moxfield/Archidekt export format both work).
   - Their own take: what the deck does well, what it struggles with, and
     its intended win condition(s). This is what the computed stats get
     checked against — don't skip asking for it.

2. **Pick a deck slug** (short kebab-case, e.g. `krenko-goblins`) and create
   `decks/<slug>/decklist.txt` with the pasted decklist, exactly as given.

3. **Fetch card data** — from the skill's root directory:
   ```
   python3 scripts/fetch_cards.py --deck-dir decks/<slug>
   ```
   If it reports any "NOT FOUND" cards, surface those to the user — usually
   a spelling issue or a card printed under a different name — before
   continuing, since they'll silently drop out of the analysis otherwise.

4. **Build the context file:**
   ```
   python3 scripts/build_context.py --deck-dir decks/<slug>
   ```
   This writes `decks/<slug>/context.json` — quantities merged with Scryfall
   data (mana cost, type, oracle text, color identity, `game_changer` flag).

5. **Run the analysis:**
   ```
   python3 scripts/analyze_deck.py --deck-dir decks/<slug>
   ```
   This writes `decks/<slug>/analysis.json` — counts, mana curve, categorized
   card lists (ramp, targeted removal, board wipes, counterspells, card draw,
   tutors, extra turns, mass land denial, Game Changers, cost reduction —
   this one isn't mana ramp, it's things like prowl/warp/"spells cost {N}
   less" (fixed) or "costs {X} less, where X is..." (scaling), which get a
   card onto the battlefield for less mana and so are a real functional
   role in any ETB-trigger-heavy deck even though they don't increase
   available mana; a scaling discount also means a card's real, typical
   cast cost can be nowhere near its printed CMC in a deck built to
   trigger it, which matters for not over-reading "high CMC" as "weak" —
   and resilience (e.g. "whenever one or more creatures you control die,
   create a token..." — recovery from a board wipe doesn't need dedicated
   sacrifice synergy to matter, the wipe itself provides the trigger)),
   and a bracket estimate. Cost reduction and resilience were both added
   after a real case where dismissing a card that had both as
   "roleless, high-CMC" led to recommending it as a cut when it was
   actually one of the stronger cards in the deck. Read
   `references/bracket_rubric.md` for what those categories mean and the
   bracket criteria they're checked against.

   There's also `fragile_trigger` — the *inverse* of a role, a caveat
   category: a creature with "whenever this creature is dealt damage" text
   at toughness ≤2, where the very damage that triggers it is likely to
   kill it too, limiting it to one real activation rather than the
   repeatable engine it looks like. Added after recommending `Raptor
   Hatchling` (1 toughness) as a clean combo piece without checking
   whether it could survive its own trigger — it couldn't, and Commander
   Spellbook's own prerequisite data for that exact combo said so directly
   (see `find-deck-combos`'s SKILL.md). Deliberately excluded from
   `find-weakest-cards`'s role-counting — it's a negative signal, not a
   function, and counting it would pull a fragile card *out* of weak-card
   flagging instead of into it.

   `analysis.json` also has `mana_curve` (printed CMC, as before),
   `typical_mana_curve` (effective-CMC-adjusted for cards with real cost
   reduction), `curve_summary` (average CMC and % of nonland cards at CMC
   ≤3, both nominal and typical, plus a cited community `baseline_reference`
   band — 2.5-3.5 average, ≥50% at CMC≤3 — to weigh against, not a
   pass/fail rule, see `references/effective_cmc.md` for why there isn't a
   stricter one), and `cost_reduction_details` (per-card nominal/typical/
   best-case CMC with a plain-language note for any card with detected
   *self* cost reduction — not reduction it grants to other cards, see the
   same reference file for that scope boundary).

6. **Check for combos.** Look for `../find-deck-combos/scripts/find_combos.py`
   (a sibling skill). If it exists:
   ```
   python3 ../find-deck-combos/scripts/find_combos.py --deck-dir decks/<slug>
   ```
   This writes `decks/<slug>/combos.json` and is not optional busywork — do
   this *before* writing conclusions about any card, not after. A card that
   looks narrow, conditional, or purely reactive when you read it in
   isolation is exactly what a combo piece looks like from the outside, and
   guessing from card text alone will miss it (see
   `find-deck-combos/SKILL.md` for how to read `included` vs.
   `almost_included`, and for the "the database models the loop, not every
   community-known finishing touch" nuance). If `find-deck-combos` isn't
   installed, skip this step, don't claim to have checked for combos, and
   mention in the report that installing it would add combo detection.

7. **Write the actual review**, synthesizing — don't just restate the JSON:
   - Compare the user's self-assessment against the numbers. If they said
     "I struggle against go-wide boards" and `categories.board_wipe` has one
     card in it, that's the finding — say so plainly.
   - Speak to their stated win condition(s): are there enough ways to find
     the answers to a stalled/wide board, other stated win con.
   - If `combos.json` has anything in `included`, give it its own section —
     don't bury it in the removal/ramp/draw breakdown. Cross-check every
     other conclusion in the review (especially anything you were about to
     call weak or narrow) against the cards involved in an included combo.
   - Give the bracket estimate with its reasoning and caveats from
     `analysis.json` — note explicitly that the Bracket 1-2 / 4-5 splits
     need the user's own read on intent, since the script can't see that.
     (Having a real combo doesn't by itself push a deck out of Bracket 3 —
     WotC's Bracket 3 criteria bars intentional *early-game* two-card
     combos, not combos generally — but call it out if the combo looks
     fast/early.)
   - Be concrete: name actual cards, actual counts, not vague advice.
   - Save the finished review as `decks/<slug>/report.md`.

## Known limitations (say so if relevant, don't overstate the analysis)

- Category detection (`scripts/analyze_deck.py`) is regex-over-oracle-text —
  it will miss cards with unusual phrasing, split/adventure/modal cards, and
  anything whose effect isn't stated in plain rules text (e.g. a card that's
  removal only in combination with something else).
- Combo detection depends on `find-deck-combos` being installed alongside
  this skill — without it, this skill has no way to see combos and
  shouldn't claim to. Even with it, the database catalogs specific known
  card combinations; it can still miss a combo that isn't in its data yet,
  and its `notes`/`produces` fields need to be read carefully (a "mandatory
  loop" that only "draws the game" per the database isn't a win until you
  verify by hand whether some other card in the deck redirects it
  favorably).
- Bracket estimates are a starting point per WotC's stated criteria, not a
  verdict — see `references/bracket_rubric.md`.
