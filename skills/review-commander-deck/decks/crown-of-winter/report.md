# Crown of Winter (Hylda of the Icy Crown) — Review

**Bracket estimate: 2 (Core), consistent with 1 (Exhibition).** Matches your
stated target exactly. No Game Changers, no mass land denial, no extra-turn
chaining detected. The split between 2 and 1 is a matter of intent WotC's
own criteria says only you can judge (the deck is clearly built to win, not
just to showcase a gimmick, which points toward 2 rather than 1) — see
**Caveats on the bracket estimate** below.

## What the deck is actually doing

This is a genuinely tight build. Nearly a quarter of the 100 cards — roughly
24 of them — exist specifically to tap an opponent's creature, and that's
not incidental: it's the deck's whole engine, because of exactly what your
commander does.

**`Hylda of the Icy Crown`** reads: *"Whenever you tap an untapped creature
an opponent controls, you may pay `{1}`. When you do, choose one — create a
4/4 Elemental token, put a +1/+1 counter on each creature you control, or
scry 2 and draw a card."* Every one of those ~24 tap effects is a Hylda
trigger. The mana cost (`{1}` per activation) is the deck's real throttle —
this isn't a free engine, it's a "how much spare mana do I have this turn"
engine, which is exactly the kind of self-limiting design that keeps a
Bracket 2 deck from running away with a game.

**The tap effects aren't just Hylda fuel — several of them double back into
each other:**
- `Court Street Denizen`, `Junk Winder`, and `Kapsho Kitefins` each tap an
  opponent's creature *whenever a creature (or token) you control enters*.
- Hylda's own token mode makes a 4/4 Elemental — a creature entering.
- `Bard, King of Dale` and `Mondrak, Glory Dominus` both double any tokens
  you'd create, so a single Hylda trigger can make *two* Elementals if
  either is on the battlefield.

Chain those together and a single tap effect can cascade: tap an opponent's
creature → pay `{1}`, make a 4/4 (or two, with Bard/Mondrak out) → each
token entering re-triggers `Court Street Denizen`/`Junk Winder`/`Kapsho
Kitefins` → which taps *another* opponent creature → which triggers Hylda
again. It's gated by mana and by how many untapped creatures your opponents
actually have, so it isn't a true infinite loop, but it's a real snowball,
and it's the actual mechanical reason this deck can go from "a couple of
tokens" to "a wide board" in one good turn — not just flavor text.

**The same tap events are also feeding two other payoffs for free:**
`Verity Circle` draws a card off *any* opponent creature becoming tapped
outside combat (not just its own ability), and `Sharae of Numbing Depths`
draws once per turn under the same condition. Every one of the ~24 tap
cards is quietly also a card-draw engine as a side effect of doing its
main job.

**Then the payoff plan matches what you described:** `Cathars' Crusade`
turns every one of those token-creation events into a counter on *every*
creature you control (so the +1/+1-counters mode isn't the only way
counters pile up — pure token volume does it too, and it compounds with
Bard/Mondrak doubling the number of ETBs). `Intangible Virtue` gives token
creatures +1/+1 and vigilance. For evasion, `Archetype of Imagination`
gives your whole board flying while stripping opponents' flying entirely,
`Toby, Beastie Befriender` gives token creatures flying once you have 4+ of
them, and `Moonshaker Cavalry` is a genuine alpha-strike finisher (flying
and +X/+X to your whole board, X = creature count, on ETB) built for
exactly the wide token board this deck assembles. This is a coherent,
closable win condition, not just a value engine that never gets there.

### A tooling note, and what it means for reading the numbers below

`analyze_deck.py` has no dedicated category for "taps an opponent's
creature" — that's a deck-specific synergy, not a generic Commander-deck
health check the way ramp/removal/draw are, so it isn't (and shouldn't be)
one of the script's regex categories. The practical effect: most of the
~24 tap cards above, plus the token/counter payoffs (`Cathars' Crusade`,
`Intangible Virtue`, `Mondrak`), show up in `find-weakest-cards`' signals as
**"roleless"** — 22 cards flagged, nearly all of them cards this review just
said are core to the plan. That's not a real weak-card signal here; it's
the tool not having a name for what this deck is doing. Don't read that
list as "these are cuts" — read it as "these are the cards a generic
category-counter can't see the job of." Everything else the script *can*
check (curve, ramp/removal/draw saturation, protection, combos) is real
signal and is below.

## Combos found

**Nothing is currently assembled.** `find-deck-combos` checked the full
Commander Spellbook database against this decklist and found zero combos
where every required card is already in the deck. That's worth saying
plainly since you flagged "there are some combos in the deck that you
should study" — right now, there isn't a completed one; what's here is
several combos that are **one card away**, and two of them are built
directly from this deck's own core pieces, which is probably what you were
sensing:

- **`Hylda of the Icy Crown` + `Opposition` + a sacrifice outlet** (either
  `Ashnod's Altar` or `Phyrexian Altar` — both already catalogued as
  completing this specific combo) produces *"tap all creatures opponents
  control during each turn."* You already run Hylda and `Opposition`; this
  is one card away, and it's a genuine lock effect, not a cute value line.
  Commander Spellbook's own prerequisite for it: *"You control at least
  one additional untapped creature"* — a real but easy condition for this
  deck to meet, since untapped creatures are the whole resource Hylda and
  `Opposition` both spend.
- **`Verity Circle` + `Junk Winder` + `The Watcher in the Water`** produces
  the same kind of lock: opponents' creatures don't untap, tap all
  creatures they control. You run `Verity Circle` and `Junk Winder`
  already; `The Watcher in the Water` is the missing piece. Prerequisite:
  *"An opponent controls a creature without flying"* — worth knowing this
  one has a real condition attached, unlike the Ashnod's/Phyrexian Altar
  line above.

Neither is in the deck today, so neither affects the bracket estimate or
anything else in this review — they're flagged here because you asked, and
because they're exactly the kind of "one card away, built from cards
already doing work" finding `find-deck-combos` exists to catch. Worth
bringing up explicitly when this deck goes through `upgrade-commander-deck`.

Twelve other near-misses turned up (full list in `combos.json`'s
`almost_included`) but the rest need cards unrelated to this deck's build
(`Hullbreaker Horror`, `Tidespout Tyrant`, `Stormtide Leviathan`, `Moat`,
etc.) — noted for completeness, not flagged as real opportunities the way
the two above are.

## The numbers

100 cards: 38 lands, 24 creatures, 18 instants, 10 artifacts, 7
enchantments, 5 sorceries, 1 planeswalker. Curve: average CMC 3.13 (typical
3.10 after the deck's two detected self cost-reducers), 61.3% of nonland
cards at CMC ≤3 — comfortably inside the cited community band (2.5–3.5
average, ≥50% at CMC≤3, see `references/effective_cmc.md`). This is a
well-curved deck; nothing here is top-heavy.

Against Bracket 2's target ranges (`find-weakest-cards/references/category_targets.md`):

| Category | Count | Bracket 2 target | Status |
|---|---|---|---|
| Lands | 38 | 36–38 | within |
| Ramp | 8 | 8–10 | within (low end) |
| Card draw | 10 | 8–10 | within (high end) |
| Targeted removal | 9 | 8–10 | within |
| Board wipes | 4 | 1–3 | **over** |
| Nonland tutors | 0 | 0–3 | within |

**Board wipes (4, over target):** `Split Up`, `Sunblast Angel`, `Supreme
Verdict`, and `Cloud's Limit Break` (its "Omnislash" mode — `{3}{W}`,
destroy all *tapped* creatures — is the interesting one here, since it's
the one board wipe in the deck that's actually *synergistic* rather than
symmetric: if you've spent the turn tapping down the opponents' board with
your own tap suite while your side stays untapped, Omnislash can be a
one-sided wipe). Four is a real number to be aware of, though: this deck's
whole win condition is building a wide token board and holding it, and a
symmetric wipe kills your own Elementals along with everyone else's stuff.
`Split Up` and `Supreme Verdict` are fully symmetric with no built-in
out. Worth knowing you have real protection for exactly this tension (see
below) — but it's worth double-checking, before a game, that you're
timing your own wipes around your own board, not just casting them on
autopilot as "removal."

**Protection (6 cards, a newly-added category — see below) mitigates the
wipe tension above:** `Eerie Interlude`, `Clever Concealment`, and
`Glorious Protector` can all blink/phase your own board out of the way of
a wipe — yours or an opponent's — in response, before it resolves.
`Swiftfoot Boots` and `You See a Guard Approach` protect one creature at a
time with hexproof. `Thassa, Deep-Dwelling` is indestructible itself and
can blink one other creature at your end step (less reactive than the
instant-speed options, more of a value/ETB-retrigger tool, but it can
double as protection in a pinch). Six real answers to "opponent casts a
wrath" is solid for Bracket 2, and it directly covers the deck's own
symmetric-wipe risk too.

**No `resilience` (recursion-after-loss) cards detected** — nothing here
converts creatures dying into a token/value the way, say, `The Skullspore
Nexus` does in this repo's other example deck. Given how much protection
this deck runs, that's a minor gap rather than a real hole — the plan is
"don't lose the board" more than "recover after losing it" — but it's
worth naming as the one resilience angle this deck doesn't cover.

**Ramp (8, low end of target) and card draw (10, high end)** are both
within range but worth flagging as the two categories closest to their
edges — if this deck goes through `upgrade-commander-deck` later, ramp is
the more natural place to add a card than draw.

## Protection detail — a tooling gap closed this session

Worth being direct about this one: `analyze_deck.py` had no `protection`
category at all before this review. You'd hand-tagged 5 cards
`[Protection]` in your own decklist (`Clever Concealment`, `Eerie
Interlude`, `Glorious Protector`, `Swiftfoot Boots`, `You See a Guard
Approach`), and every one of them was invisible to the analysis — not
miscategorized, just entirely unseen. Per this repo's own working
philosophy, that got fixed in `analyze_deck.py` itself this session (now
detects granted/self hexproof, indestructible, phasing, and
temporary-exile-to-dodge-removal), re-verified against this deck (it now
finds exactly your 5 tagged cards, plus `Thassa, Deep-Dwelling` for its own
`Indestructible` keyword — a sixth genuine case you hadn't tagged), and
spot-checked against this repo's other reviewed deck (`dinos`) with no
regressions and six new legitimate protection cards found there too.

**A second, related gap found and fixed in the same pass:** the
`counterspell` category was matching the literal phrase "counter target
spell" only, which missed every counterspell that qualifies its target —
`Dovin's Veto` and `Negate` ("counter target *noncreature* spell") and
`Swan Song` ("counter target *enchantment, instant, or sorcery* spell")
were all showing up as "roleless" cards despite being exactly what they
look like. Fixed, re-verified against this deck (all 6 counterspells now
detected: `Cryptic Command`, `Dovin's Veto`, `Flare of Denial`, `Negate`,
`Swan Song`, `Urza's Rebuff`) and against `dinos` (no counterspells there,
so no regression possible, confirmed empty as before).

## Caveats on the bracket estimate

- Two-card infinite combo potential can't be detected from card text alone
  — reviewed by hand above via `find-deck-combos`; nothing assembled today.
- Bracket 1 vs. 2 hinges on player/table intent, not just card choices —
  this script can't infer that, only you can. Given the deck has a real,
  closable win condition (wide token board + evasion + an alpha-strike
  finisher), not just a "tap things" gimmick with no follow-through, this
  reads as squarely Bracket 2 rather than Exhibition, but that's a read on
  intent, not a computed fact.
