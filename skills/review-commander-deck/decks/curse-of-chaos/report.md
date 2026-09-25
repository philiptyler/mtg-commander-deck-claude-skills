# Curse of Chaos (Shiko and Narset, Unified) — Review

**Bracket estimate: 2 (Core), consistent with 1 (Exhibition).** Matches your
stated target. No Game Changers, no mass land denial. The 1 vs. 2 split is
player intent WotC's own criteria says only you can judge — see **Caveats**
below, but a deck built to genuinely out-value the table (not just show off
a Curse gimmick) reads as squarely Bracket 2.

## What the deck is actually doing

**The commander's real trigger is broader than "copy Curses."** `Shiko and
Narset, Unified`'s Flurry ability is *"whenever you cast your second spell
each turn, copy that spell if it targets a permanent or player, and you may
choose new targets for the copy. If you don't copy a spell this way, draw a
card."* That's not Curse-specific — it triggers off any second spell, and
it has a **floor as well as a ceiling**: a targeted spell (a Curse, a
removal spell) gets copied at a new target; anything else that doesn't
target a permanent or player (a cantrip like `Opt` or `Ponder`, which
targets nothing) instead just draws you a card for free. That's why the
deck runs as many cantrips as it does — every one of them is a genuine
"cast my second spell, get a free card" engine piece, not filler. Casting a
cheap cantrip as your second spell of the turn nets you *two* cards that
turn (the cantrip's own effect, plus Flurry's fallback draw).

**The Curses are where that copy mode gets its real payoff.** All 12 are
real `Enchantment — Aura Curse` permanents (confirmed by type line, not
guessed from the name — `Curse of the Swine` looks like a Curse but is
actually a sorcery, a real distinction the deck's own card tags already got
right). Casting one as your second spell lets you choose a *new* target for
the copy — meaning you can spread two different opponents with the same
Curse in one cast, or stack two copies of a nasty one (`Curse of
Bloodletting`'s damage-doubling, `Overwhelming Splendor`'s full lockdown) on
a single problem player. `Curse of Surveillance` is a direct payoff for
stacking multiple Curses on one target: *"any number of target players...
draw cards equal to the number of Curses attached to that player"* — the
more Curses pile onto one opponent, the bigger that draw gets for everyone
*except* the cursed player. `Curse of Opulence` (Gold token whenever the
cursed player is attacked, and each attacker gets one too) is a classic
"redirect the table's violence elsewhere" political tool, very on-plan for
a deck that wants to sit back and accrue value while others fight.

**The second engine layer is magecraft/spell-value, independent of Flurry.**
`Veyran, Voice of Duality` and `Storm-Kiln Artist` both have the actual
`Magecraft` keyword (cast *or copy* an instant/sorcery); `Archmage Emeritus`
and `Fiery Inscription` have the same trigger without the keyword. `Veyran`
specifically doubles other triggered abilities off that same event, which
stacks with Flurry rather than replacing it — casting a second-spell Curse
that's also an instant/sorcery (none currently are — see **A real gap**
below) or even just casting your second *instant/sorcery* of the turn
independently triggers Storm-Kiln Artist/Veyran regardless of what Flurry
does with it. `Monastery Mentor`, `Third Path Iconoclast`, and `Manaform
Hellkite` are a related but distinct trigger — *any* noncreature spell, not
just instant/sorcery — which is exactly the line your own card tags already
drew (`Instant-Sorcery Value` vs. `Non-Creature Spell Value`); worth
knowing they're two different triggers density-wise, not the same engine
counted twice.

### A tooling note before the numbers

Three real categories didn't exist in this project's tooling before this
review — `curse`, `magecraft`/`noncreature_spell_value`, and `copy_effects`
— so `Veyran`, `Storm-Kiln Artist`, `Monastery Mentor`, and 7 of the 12
Curses were showing up as "roleless" to the automated signal, the same
shape of gap as the previous deck's tap-synergy cards. All three got added
to `analyze_deck.py` this session (`curse` is a direct type-line check —
Scryfall already marks Curses structurally, so it's not even a regex guess)
and re-verified against this deck and the two others already in this repo
with no regressions. Separately, three real regex misses in the existing
`targeted_removal` pattern got found and fixed here too: it didn't handle
**X-cost damage** (`Electrodominance`/`Expansion // Explosion`'s "deals X
damage" was invisible next to a literal-digit-only pattern), **plural
multi-target exile** (`Curse of the Swine`'s "Exile X target creatures"),
or **plural multi-target bounce** (`Baral's Expertise`'s "Return up to
three target artifacts and/or creatures to their owners' hands"). Fixing
those moved `targeted_removal` from 6 cards (misleadingly "under" Bracket
2's 8–10 target) to the true count of 10 ("within") — a real, not cosmetic,
correction to a number this report leans on below.

## Combos found

**Nothing is currently assembled** — `find-deck-combos` checked the full
database and found zero combos where every card is already in the deck.
25 near-misses turned up (full list in `combos.json`), which is a lot, but
expected for a heavy spellslinger shell: Commander Spellbook catalogs a
large family of "one more copy/mana-doubler card turns your spellslinger
payoffs infinite" combos, and this deck already runs several of the pieces
those combos build on (`Storm-Kiln Artist`, `Mana Geyser`, `Archmage
Emeritus`, `Expansion // Explosion`). None of them affect anything in this
review since none are actually in the deck, but two are worth knowing about
because they're thematically dead-on for what this deck already does:

- **`Curse of Bloodletting` + `Heartless Hidetsugu`** — near-infinite damage
  to a player, using a Curse you already run. Real prerequisite: the
  cursed player needs an *even* life total (a real, sometimes-false
  condition, not free).
- **`Curse of Exhaustion` + `Knowledge Pool`** — locks an opponent to one
  spell per turn while exiling what they'd have cast. You already run the
  Curse; `Knowledge Pool` is the missing piece.

Neither changes today's bracket estimate or anything else in this review —
flagged for if/when this deck goes through `upgrade-commander-deck`.

## The numbers

100 cards: 38 lands, 12 creatures, 16 instants, 9 sorceries, 7 artifacts,
20 enchantments (12 of them Curses). Curve: average CMC 3.29, 61.3% of
nonland cards at CMC ≤3 — comfortably inside the cited community band
(2.5–3.5 average, ≥50% at CMC≤3). No cost-reduction detected on any card,
so nominal and typical curve are identical here.

Color pips: **U 60, W 23, R 48** — white is a distant third. This deck runs
three colors on a Bracket-2 budget of fixing, and white is clearly the
thinnest — worth a dedicated look from `upgrade-commander-lands` if white
sources (not just pip *demand*, which this only estimates from cost
symbols) turn out to be light too; that skill computes the actual
probability rather than eyeballing pip counts the way this section does.

Against Bracket 2's target ranges (`find-weakest-cards/references/category_targets.md`):

| Category | Count | Bracket 2 target | Status |
|---|---|---|---|
| Lands | 38 | 36–38 | within |
| Ramp | 12 | 8–10 | **over** |
| Card draw | 25 | 8–10 | **way over** |
| Targeted removal | 10 | 8–10 | within |
| Board wipes | 0 | 1–3 | **under** |
| Nonland tutors | 0 | 0–3 | within |

**Card draw at 25 is nearly triple the Bracket-2 reference band** — but
read that against what you actually said this deck is trying to do: win by
out-valuing the table, not by combat or a fast combo kill. A control/value
shell wanting far more raw card advantage than a typical Bracket-2 aggro or
midrange deck is the expected shape of that plan, not automatically bloat.
Still worth a genuine second look at whether all 25 are pulling real
weight, or whether some are redundant cantrips now that Flurry itself
already turns every non-targeting second spell into a free card — that's
exactly the kind of question `upgrade-commander-deck` is built to answer
with real signal instead of a gut call.

**Ramp at 12 (over)** is defensible for the same reason curve-toppers
exist here at all (`Overwhelming Splendor` at 8, `Curse of Unbinding` at 7,
`Magma Opus` at 8) and for supporting a real 3-color manabase, but is worth
knowing as the more replaceable of the two "over" categories if this deck
wants a leaner build.

**Zero board wipes is the one gap that doesn't have a good explanation
in the deck's own stated plan.** A deck that wants to sit back, accrue
Curses and card advantage, and win on a long game has no answer to an
opponent's board getting wide and fast in the meantime — its 10 removal
spells are all one-for-one answers, nothing sweeps. This is the single
clearest actual weakness in the deck relative to what you said it's trying
to do, more than the raw card-draw count.

## Caveats on the bracket estimate

- Two-card infinite combo potential can't be detected from card text alone
  — reviewed by hand above via `find-deck-combos`; nothing assembled today,
  though this deck's own pieces (`Storm-Kiln Artist`, `Mana Geyser`) are
  common combo-adjacent cards worth re-checking after any future add.
- Bracket 1 vs. 2 hinges on player/table intent, not just card choices —
  this script can't infer that, only you can. A deck built to genuinely
  win via value accrual, with real (if currently gap-having) removal and a
  coherent engine, reads as Bracket 2 rather than Exhibition, but that's a
  read on intent, not a computed fact.
