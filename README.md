# mtg-commander-deck-claude-skills

Claude Skills for building and reviewing Magic: The Gathering Commander
(EDH) decks. Each skill is a self-contained directory under `skills/` — see
[Installing](#installing) below to use one.

## Skills

### [`review-commander-deck`](skills/review-commander-deck/SKILL.md)

Takes a pasted Commander decklist plus your own read on what the deck does
well or poorly, pulls real card data from the [Scryfall API](https://scryfall.com/docs/api),
and produces a data-backed review: mana curve, ramp/removal/draw counts,
tutors, and a [Commander Bracket](https://magic.wizards.com/en/news/announcements/introducing-commander-brackets-beta)
(1-5) estimate — checked against what you actually said the deck is trying
to do.

No third-party Python dependencies — the Scryfall client uses the standard
library only, so there's no install step to use the skill.

If `find-deck-combos` is installed alongside it, this skill runs it as part
of the review and includes a dedicated combos section — checking for combos
during the review itself, not only when someone later asks about a specific
card, is what caught the miss described under `find-deck-combos` below.

### [`find-weakest-cards`](skills/find-weakest-cards/SKILL.md)

Finds the weakest N cards in a deck already reviewed by
`review-commander-deck` — the whole deck, just the lands, or a specific
category ("weakest 2 removal spells", "weakest 3 lands"). Combines category
oversaturation (compared against bracket-scaled targets), cards with no
detected functional role, high-CMC single-purpose cards, and land quality
checks (enters tapped with no upside, off-color) into signals — then reads
each candidate's actual card text before concluding anything, since the
signals are heuristics that can miss real upside phrased unusually.

**Depends on `review-commander-deck`'s output** (`context.json` and
`analysis.json` for the deck in question) rather than re-implementing
decklist parsing/Scryfall fetching — install both together.

No EDHREC integration: their public JSON endpoint exists, but their Terms
of Service explicitly prohibit automated queries against it, so this skill
doesn't hit it. If EDHREC context matters for a specific card, check it
yourself in your browser and paste the number in.

### [`find-deck-combos`](skills/find-deck-combos/SKILL.md)

Checks a deck already reviewed by `review-commander-deck` against
[Commander Spellbook](https://commanderspellbook.com)'s combo database —
what combos are already fully in the deck, and what combos are one or two
cards away. Unlike EDHREC, Commander Spellbook's API is open source and
built for exactly this kind of programmatic use, so this one does hit a
live API.

This isn't just a nice-to-have: `find-weakest-cards` called `Wrathful
Raptors` one of a test deck's weakest removal spells before this skill
existed — it's actually the finishing piece of an infinite-damage combo
with two other cards already in that same deck, and this skill also
surfaced a second, completely independent combo in it that nobody had
noticed. `find-weakest-cards` now checks this skill's output before
recommending any cut.

**Depends on `review-commander-deck`'s output**, same as `find-weakest-cards`
— and `review-commander-deck` in turn calls into this skill when it's
present (see above). Install all three together.

### [`update-commander-deck`](skills/update-commander-deck/SKILL.md)

For a deck that's already been reviewed: apply a card swap/add/cut, refresh
every downstream artifact, and — the actual point of this skill — report
what the change actually did. Snapshots the current analysis/combos before
editing `decklist.txt`, re-runs the pipeline (the Scryfall cache means only
genuinely new cards get fetched), then diffs before vs. after: category
count shifts, a bracket estimate change and why, and — the finding that
would otherwise be easy to miss — whether the swap broke a combo. Tested by
deliberately swapping out a combo piece from the example deck in this repo:
it correctly flagged the break and, separately, correctly left the *other*,
unrelated combo in that deck untouched.

**Depends on `review-commander-deck`'s output**, and re-runs
`find-deck-combos`/`find-weakest-cards` if either was already in use for
the deck being changed.

### [`upgrade-commander-deck`](skills/upgrade-commander-deck/SKILL.md)

Proposes N nonland card swaps — this is the "suggest changes" skill the
roadmap above used to describe as not-yet-built. Sources candidates via
Scryfall's own `edhrec_rank` field (a global popularity rank Scryfall
computes and publishes itself), never by querying edhrec.com directly, and
ranks them deterministically: whether a candidate completes a combo
`find-deck-combos` already found the deck one card away from, whether it
fills an undersupplied curve slot, then popularity only as a tiebreaker —
never the primary factor, specifically because a commander-specific EDHREC
inclusion rate can be skewed by precon inclusion or a card just being cheap
and accessible. This is a *proposal* skill: nothing gets applied until you
confirm, then it delegates the actual apply-and-diff step to
`update-commander-deck` rather than reimplementing it.

**Depends on `review-commander-deck`'s output**, uses `find-weakest-cards`
for cut candidates and `find-deck-combos` for the combo-completion bonus
(and to enforce the same "never cut a combo piece" rule), and hands
confirmed swaps to `update-commander-deck` to apply.

### [`upgrade-commander-lands`](skills/upgrade-commander-lands/SKILL.md)

Same idea, scoped to the mana base only. The old, informal version of this
workflow cited a specific turn-by-turn Frank Karsten source-count table;
when building this skill, those exact numbers weren't verifiable against
primary sources, so instead of repeating a table that couldn't be checked,
`mana_base_analysis.py` computes the actual hypergeometric probability
directly from the deck's real current source counts (stdlib `math.comb`,
no scipy) — sanity-checked against the externally-corroborated "~22
sources for single-pip, ~29 for double-pip" figures and it lines up. Caught
a real, easy-to-miss shortfall in the example deck in this repo on first
run: `Grand Abolisher` costs `{W}{W}`, and the deck's actual white source
count gives only a 65% chance of having it online by turn 2.

**Depends on `review-commander-deck`'s output**, same delegation to
`update-commander-deck` for applying confirmed swaps.

## Installing

Works with Claude Code (CLI) or the Claude.ai / desktop apps. Personal-scope
install is the low-friction option since it makes skills available in every
project, not just this repo checkout.

### Claude Code (CLI)

Clone the repo, then symlink each skill folder into Claude Code's personal
skills directory (create it if it doesn't exist yet):

```
git clone git@github.com:philiptyler/mtg-commander-deck-claude-skills.git
mkdir -p ~/.claude/skills
ln -s "$(pwd)/mtg-commander-deck-claude-skills/skills/review-commander-deck" ~/.claude/skills/review-commander-deck
ln -s "$(pwd)/mtg-commander-deck-claude-skills/skills/find-weakest-cards" ~/.claude/skills/find-weakest-cards
ln -s "$(pwd)/mtg-commander-deck-claude-skills/skills/find-deck-combos" ~/.claude/skills/find-deck-combos
ln -s "$(pwd)/mtg-commander-deck-claude-skills/skills/update-commander-deck" ~/.claude/skills/update-commander-deck
ln -s "$(pwd)/mtg-commander-deck-claude-skills/skills/upgrade-commander-deck" ~/.claude/skills/upgrade-commander-deck
ln -s "$(pwd)/mtg-commander-deck-claude-skills/skills/upgrade-commander-lands" ~/.claude/skills/upgrade-commander-lands
```

Start (or restart) a Claude Code session and they'll show up in the
available skills. To scope them to a single project instead of every
project, symlink into `<project>/.claude/skills/<name>` rather than the
`~/.claude` path above.

### Claude.ai / desktop app

Zip each skill folder and upload it as a Skill capability:

```
cd mtg-commander-deck-claude-skills/skills
zip -r review-commander-deck.zip review-commander-deck
zip -r find-weakest-cards.zip find-weakest-cards
zip -r find-deck-combos.zip find-deck-combos
zip -r update-commander-deck.zip update-commander-deck
zip -r upgrade-commander-deck.zip upgrade-commander-deck
zip -r upgrade-commander-lands.zip upgrade-commander-lands
```

Then in the app: **Settings → Capabilities → Skills → Upload skill**, and
pick the zip.

## Trying it out

Once installed, start a new conversation, paste a decklist, and say what you
think of it — no special command needed, Claude picks up the skill from its
description. For example:

> Review this Commander deck. It's fast goblin aggro, wins by going wide and
> burning out the table with Impact Tremors-style effects, but it feels like
> it folds to a single board wipe. Bracket 3 target.
>
> 1 Krenko, Mob Boss \*CMDR\*
> 1 Sol Ring
> ...(rest of the 100-card list)

Claude will ask for anything missing (usually the full decklist), fetch card
data from Scryfall, build the deck's context file, run the analysis, and
write `decks/<slug>/report.md` with the review.

A ready-made example list to try it on is at
[`skills/review-commander-deck/examples/sample_decklist.txt`](skills/review-commander-deck/examples/sample_decklist.txt).

## Repo layout

```
skills/
  review-commander-deck/
    SKILL.md          # what Claude reads to run the skill
    scripts/           # parse decklist -> fetch Scryfall -> build context -> analyze
    references/         # editable rubrics (e.g. bracket criteria)
    cache/scryfall/      # cached Scryfall responses, reused across decks
    decks/               # one folder per deck you've reviewed - shared by all
                          #   three skills (context.json, analysis.json,
                          #   report.md, weak_card_signals.json, combos.json)
  find-weakest-cards/
    SKILL.md          # depends on review-commander-deck's decks/<slug>/ output
    scripts/           # find_weak_cards.py - computes signals, doesn't rank
    references/         # category_targets.md - bracket-scaled saturation targets
  find-deck-combos/
    SKILL.md          # depends on review-commander-deck's decks/<slug>/ output
    scripts/           # spellbook_client.py + find_combos.py
  update-commander-deck/
    SKILL.md          # applies changes, doesn't suggest them - re-runs the
                          #   other skills' scripts, adds the diff step
    scripts/           # snapshot_before.py + diff_after.py
  upgrade-commander-deck/
    SKILL.md          # proposes nonland swaps, delegates apply to
                          #   update-commander-deck once confirmed
    scripts/           # scryfall_search_client.py (edhrec_rank-sorted
                          #   Scryfall search) + find_upgrade_candidates.py
  upgrade-commander-lands/
    SKILL.md          # proposes land swaps, same delegation pattern
    scripts/           # hypergeometric.py (stdlib probability model) +
                          #   mana_base_analysis.py + find_land_candidates.py
```

## Roadmap

Ideas for later, not yet built:

- `suggest-commander` — recommend commanders for a given strategy/budget

## License

MIT — see [LICENSE](LICENSE).
