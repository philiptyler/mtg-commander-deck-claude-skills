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

## Installing

Works with Claude Code (CLI) or the Claude.ai / desktop apps. Personal-scope
install is the low-friction option since it makes the skill available in
every project, not just this repo checkout.

### Claude Code (CLI)

Clone the repo, then symlink the skill folder into Claude Code's personal
skills directory (create it if it doesn't exist yet):

```
git clone git@github.com:philiptyler/mtg-commander-deck-claude-skills.git
mkdir -p ~/.claude/skills
ln -s "$(pwd)/mtg-commander-deck-claude-skills/skills/review-commander-deck" ~/.claude/skills/review-commander-deck
```

Start (or restart) a Claude Code session and it'll show up in the available
skills. To scope it to a single project instead of every project, symlink
into `<project>/.claude/skills/review-commander-deck` rather than the
`~/.claude` path above.

### Claude.ai / desktop app

Zip the skill folder and upload it as a Skill capability:

```
cd mtg-commander-deck-claude-skills/skills
zip -r review-commander-deck.zip review-commander-deck
```

Then in the app: **Settings → Capabilities → Skills → Upload skill**, and
pick `review-commander-deck.zip`.

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
    decks/               # one folder per deck you've reviewed
```

## Roadmap

Only `review-commander-deck` exists today. Ideas for later, not yet built:

- `optimize-commander-deck` — suggest concrete swaps toward a target bracket
- `suggest-commander` — recommend commanders for a given strategy/budget

## License

MIT — see [LICENSE](LICENSE).
