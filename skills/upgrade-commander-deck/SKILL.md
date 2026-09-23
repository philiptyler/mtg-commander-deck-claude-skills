---
name: upgrade-commander-deck
description: Proposes N nonland card swaps for an already-reviewed Commander deck, sourcing candidates via Scryfall (never EDHREC directly) and ranking them deterministically before asking you to confirm. Use when the user asks to upgrade, improve, or find better nonland cards for a deck already run through review-commander-deck - not for lands specifically (that's upgrade-commander-lands) and not for applying a swap the user already decided on (that's update-commander-deck).
---

# Upgrade Commander Deck

Proposes cuts and replacements for an already-reviewed deck. The design
goal is **determinism over vibes**: candidate sourcing and ranking are
scripted and reproducible; only the final pick among close candidates and
the written reasoning are yours to judge. This is a *proposal* skill —
nothing gets applied until the user confirms, unlike `update-commander-deck`
which applies changes the user already decided on.

## Requires review-commander-deck to have already run on this deck

Reads `context.json`/`analysis.json` from
`../review-commander-deck/decks/<slug>/`. Also uses `find-weakest-cards`
(for cut candidates) and `find-deck-combos` (for combo-completion bonus and
the "don't cut a combo piece" check) if installed — run them first if their
output files don't exist yet. Applying a confirmed proposal delegates to
`update-commander-deck`'s snapshot/diff scripts rather than reimplementing
that step.

## On EDHREC — read this before sourcing anything

`find-weakest-cards` already established that EDHREC's Terms of Service
bar automated queries against their site — that rule is unchanged here.
Candidate sourcing instead uses **Scryfall's own `edhrec_rank` field**:
Scryfall computes and publishes a global "how often is this card played
across all of EDH" rank per card, and its `/cards/search` API can filter
and sort by it directly. That's what `find_upgrade_candidates.py` uses —
zero requests to edhrec.com.

This is a deliberately different signal from what the old, informal
version of this workflow used (a commander-specific "seen in X% of decks
with this commander" inclusion rate), and that's on purpose: a
commander-specific rate gets inflated by a card simply being in that
commander's preconstructed deck, or by a card being cheap/accessible
regardless of fit. A *global* popularity rank can't be skewed that way,
because it isn't tied to any one commander. Even so, treat it as a
**tiebreaker, not a primary ranking factor** — `find_upgrade_candidates.py`
sorts on combo-completion and curve-gap fit first, `edhrec_rank` only
breaks ties within those. Never present a candidate's rank as "this is
good because it's popular" — present the deterministic reasons (fills a
gap, completes a combo, fits the curve, fits the budget) and mention
popularity only as supporting color, if at all.

If genuine commander-specific EDHREC synergy data would help, that's still
only available by asking the user to check it themselves in their browser
and paste it in — same rule as `find-weakest-cards`. Offer this once, at
the end, as an optional way to sharpen a close call; don't block on it or
ask repeatedly.

## Workflow

1. **Parse the request:** how many swaps (N — ask if not given), an
   optional focus category (`ramp`, `removal`, `board_wipe`, `card_draw`,
   `tutors`, `protection`, or general), and an optional budget (max USD per
   card). If the user names specific cards to cut, treat those as fixed —
   don't second-guess them.

2. **Identify N cut candidates**, reusing `find-weakest-cards` rather than
   re-deriving weakness from scratch:
   ```
   python3 ../find-weakest-cards/scripts/find_weak_cards.py --deck-dir ../review-commander-deck/decks/<slug>
   ```
   Read `weak_card_signals.json` plus `combos.json`'s `included` list —
   **never propose cutting a card that's part of an included combo**,
   exactly the rule `find-weakest-cards` already enforces. If a focus was
   given, weight cut selection toward cards *not* serving that focus (the
   freed-up slots should go toward it).

3. **Before any category search, check for combo completions directly —
   don't rely on a category query happening to surface one by luck:**
   ```
   python3 scripts/find_combo_completions.py --deck-dir ../review-commander-deck/decks/<slug> --count 10 [--budget <usd>]
   ```
   This reads `combos.json`'s `almost_included` list for every combo
   exactly one card away, groups by the missing card, and ranks by how
   many *separately cataloged* combos that one card completes — a card
   completing 2+ combos independently is a real signal, not a coincidence.
   Writes `combo_completion_candidates.json`. This exists because it
   exists: sourcing "protection" candidates for the dinos deck happened to
   surface `Sword of Feast and Famine` completing an infinite-combat-phases
   combo with `Aggravated Assault`, already in that deck — found by luck,
   not by design, which is exactly the kind of gap this project's CLAUDE.md
   says to close rather than just note. A top result here is a strong
   candidate for one of the N swaps almost regardless of category, **but
   weigh its CMC against the deck's own curve concerns** — a combo
   completion that costs more than what it's replacing can work against a
   cut made specifically to fix a crowded curve bucket. When that tension
   exists, surface it to the user explicitly rather than picking silently.

4. **For each remaining cut, source candidates for its gap:**
   ```
   python3 scripts/find_upgrade_candidates.py --deck-dir ../review-commander-deck/decks/<slug> \
       --category <ramp|removal|board_wipe|card_draw|tutors|protection|any> \
       --count 10 [--budget <usd>] [--cmc-min N] [--cmc-max N]
   ```
   Output filename includes the CMC/budget bounds used
   (`upgrade_candidates_<category>_cmcX-Y.json` etc.) specifically so that
   sourcing the same category twice with different bounds — a normal thing
   to do — doesn't silently overwrite the first result.

   Read the resulting file. A candidate with `completes_combo: true` is a
   strong pick almost by default — read its `combo_details` and say
   plainly what it unlocks. Otherwise prefer, in order: fills an
   undersupplied curve bucket (`fills_curve_gap`), matches whatever
   specific weakness prompted this cut (read the candidate's own
   `oracle_text`, don't just trust the category match — the query is a
   substring search and can over- or under-match, same caveat as
   `analyze_deck.py`), then use `edhrec_rank`/`is_instant` only to break
   remaining ties.

5. **Sanity-check each pick** against `analysis.json` before finalizing:
   does it actually solve the problem the cut's absence creates (don't
   remove the deck's only board wipe without replacing that function)?
   Does it avoid pushing an already-crowded curve bucket further over?
   Is it within budget if one was given (the script already filters this,
   but double-check on candidates sourced without `--budget`)? Is a
   `game_changer: true` candidate going to push the deck past its
   current Bracket 3 cap of 3 — worth flagging explicitly if so.

6. **Present the proposal and wait for confirmation** — this is the one
   step this skill does differently from `update-commander-deck`. Show
   each swap (cut → add) with the reasoning from steps 2-5. Don't apply
   anything yet.

7. **On confirmation, apply via `update-commander-deck`:**
   ```
   python3 ../update-commander-deck/scripts/snapshot_before.py --deck-dir ../review-commander-deck/decks/<slug>
   ```
   Edit `decklist.txt` directly for all N swaps, then re-run
   `review-commander-deck`'s `fetch_cards.py` → `build_context.py` →
   `analyze_deck.py`, then `find-deck-combos`/`find-weakest-cards` if
   installed, then:
   ```
   python3 ../update-commander-deck/scripts/diff_after.py --deck-dir ../review-commander-deck/decks/<slug>
   ```
   Report the diff the same way `update-commander-deck` does (combo
   changes first, then bracket, then counts). Update `report.md`.

8. **Offer the manual EDHREC option once, at the end** — not before: "if
   you want me to factor in EDHREC's commander-specific synergy data for
   any of these, check `edhrec.com/commanders/<slug>` yourself and paste
   what you see."

## Known limitations

- `find_upgrade_candidates.py`'s category queries are Scryfall oracle-text
  substring searches, the same imprecise tool `analyze_deck.py` uses —
  they will over-match (a card with "destroy target permanent if it's
  blue" matches a general removal query despite being narrow) and
  under-match (unusual phrasing). Read the candidate's actual text before
  recommending it, every time.
- Nothing here is a true measure of a card's power level — "deterministic"
  describes the *sourcing and filtering* (legality, dedup, budget, curve
  fit, combo completion), not a claim that the script knows which card is
  objectively better. That final call is still a judgment call.
- Scoped to nonland cards only. For mana base changes, use
  `upgrade-commander-lands`.
