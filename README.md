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
    decks/               # one folder per deck you've reviewed (context.json,
                          #   analysis.json, report.md, weak_card_signals.json)
  find-weakest-cards/
    SKILL.md          # depends on review-commander-deck's decks/<slug>/ output
    scripts/           # find_weak_cards.py - computes signals, doesn't rank
    references/         # category_targets.md - bracket-scaled saturation targets
```

## Roadmap

Ideas for later, not yet built:

- `optimize-commander-deck` — suggest concrete swaps toward a target bracket
- `suggest-commander` — recommend commanders for a given strategy/budget

## License

MIT — see [LICENSE](LICENSE).
