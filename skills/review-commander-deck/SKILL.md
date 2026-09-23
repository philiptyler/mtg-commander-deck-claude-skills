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
   tutors, extra turns, mass land denial, Game Changers), and a bracket
   estimate. Read `references/bracket_rubric.md` for what those categories
   mean and the bracket criteria they're checked against.

6. **Write the actual review**, synthesizing — don't just restate the JSON:
   - Compare the user's self-assessment against the numbers. If they said
     "I struggle against go-wide boards" and `categories.board_wipe` has one
     card in it, that's the finding — say so plainly.
   - Speak to their stated win condition(s): are there enough ways to find
     the answers to a stalled/wide board, other stated win con.
   - Give the bracket estimate with its reasoning and caveats from
     `analysis.json` — note explicitly that combo potential and Bracket 1-2
     / 4-5 splits need the user's own read on intent, since the script can't
     see that.
   - Be concrete: name actual cards, actual counts, not vague advice.
   - Save the finished review as `decks/<slug>/report.md`.

## Known limitations (say so if relevant, don't overstate the analysis)

- Category detection (`scripts/analyze_deck.py`) is regex-over-oracle-text —
  it will miss cards with unusual phrasing, split/adventure/modal cards, and
  anything whose effect isn't stated in plain rules text (e.g. a card that's
  removal only in combination with something else).
- No two-card infinite combo detection — that needs actual card-interaction
  reasoning, which is a job for you (Claude) reading the decklist, not for
  the regex script.
- Bracket estimates are a starting point per WotC's stated criteria, not a
  verdict — see `references/bracket_rubric.md`.
