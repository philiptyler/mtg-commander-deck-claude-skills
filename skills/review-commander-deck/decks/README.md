# decks/

Each subdirectory here is one reviewed deck. This folder is the shared home
for a deck's data across skills, even though each skill's *code* lives in
its own directory (`review-commander-deck`, `find-weakest-cards`,
`find-deck-combos`) — see each skill's SKILL.md for what depends on what.

- `decklist.txt` — the raw pasted decklist (input) — from `review-commander-deck`
- `context.json` — decklist quantities merged with Scryfall card data — from `review-commander-deck`
- `analysis.json` — computed stats and bracket estimate — from `review-commander-deck`
- `report.md` — the final written review — from `review-commander-deck`
- `weak_card_signals.json` — cut-candidate signals — from `find-weakest-cards`
- `combos.json` — combos already in the deck / one card away — from `find-deck-combos`

Nothing in here is hand-written; it's all produced by running each skill's
scripts against a decklist.
