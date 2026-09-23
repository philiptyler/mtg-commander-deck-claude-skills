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
```

## Roadmap

Ideas for later, not yet built:

- `optimize-commander-deck` — *suggest* swaps toward a target bracket
  (distinct from `update-commander-deck`, which applies swaps you already
  decided on)
- `suggest-commander` — recommend commanders for a given strategy/budget

## License

MIT — see [LICENSE](LICENSE).
