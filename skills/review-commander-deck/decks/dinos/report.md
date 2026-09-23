# Dinos (Pantlaza, Sun-Favored) — Review

**Updated:** swapped `Annie Joins Up` out for `Personify`. See **Personify's
actual impact** below for the analysis you asked for on what else it
triggers — it's more than you might have guessed. Numbers throughout this
report reflect the swap; `last_update_diff.json` has the raw before/after.

**Bracket estimate: 3 (Upgraded).** Matches your stated target. The deck carries
exactly 3 Game Changers (`Jeska's Will`, `Teferi's Protection`, `Worldly Tutor`)
— right at Bracket 3's cap of 3. That's worth knowing as a ceiling: any future
upgrade that adds a 4th Game Changer pushes this into Bracket 4 territory, not
because the deck got meaningfully stronger, just because you'd be over the
line WotC draws. No mass land denial, no extra-turn chaining detected. See the
caveats below on what this estimate can't see.

## What the deck is actually doing

**The discover engine — blink genuinely doubles it. (Correction from the
first version of this review.)** I originally said blinking Pantlaza
couldn't get around her "do this only once each turn" cap — that was wrong,
and you were right to push back on it. Per CR 400.7 ("an object that moves
from one zone to another becomes a new object with no memory of, or
relation to, its previous existence"), when `Ephemerate`, `Daydream`, or
`Teleportation Circle` exile Pantlaza and return her, she comes back as a
**new permanent** carrying a **new, independent instance** of her triggered
ability — the "already discovered once this turn" restriction belonged to
the old Pantlaza-object and doesn't carry over to the new one. So blinking
Pantlaza really does let her ability trigger, and let you discover, a second
time in the same turn (more, with repeat blinks). This is a well-documented
interaction in the Pantlaza community for exactly this reason (see the
"Blink and You Lose Your Pants" primer on Moxfield). I should have checked
the ruling instead of asserting from a general impression — thanks for
catching it.

`Curator of Sun's Creation` stacks on top of this rather than being the only
way to get a second discover: *"whenever you discover, discover again for
the same value... once each turn."* Blink resets Pantlaza's own cap;
Curator adds a further discover on top of whichever trigger fires. With
both in play, a single blinked Dinosaur ETB can chain three-plus discovers
in one turn — a stronger, more central engine than my original read gave it
credit for. `Daydream`, `Ephemerate`, and `Teleportation Circle` are direct
engine pieces here, not just incidental re-trigger value on your other ETBs
(though that's real too — see `Regisaur Alpha` below).

**Personify's actual impact.** You added it as another blink spell (correct
— `{1}{W}` instant, exile target creature you control and return it, same
family as `Daydream`/`Ephemerate`), but the part you flagged not having
analyzed is the bigger deal: it also creates a 1/1 colorless Shapeshifter
token **with changeling** ("it's every creature type"), which means that
token is genuinely a Dinosaur, not Dinosaur-flavored. In this deck
specifically, that token entering the battlefield fires almost the entire
ETB engine at once:
- `Pantlaza` sees a Dinosaur enter and can discover (toughness 1, so
  discover 1) — if her once-per-turn allowance hasn't already been used.
- `Marauding Raptor` pings it for 2 as it enters, which **kills the token
  outright** (1 toughness) — but that same ping is itself damage dealt to a
  Dinosaur you control, which is exactly what `Wrathful Raptors` redirects:
  2 damage to any target that isn't a Dinosaur. So with both of those out,
  casting Personify on anything turns into 2 damage to an opponent, on top
  of the blink.
- `Forerunner of the Empire` deals 1 damage to each creature on any
  Dinosaur ETB, so the token triggers that too (on top of eating Marauding
  Raptor's 2, if that's in play).
- `Warstorm Surge` and `Terror of the Peaks` both trigger off *any* creature
  you control entering (not just Dinosaurs), so the token pings for 1
  more from each of those, independent of its Dinosaur-ness.

None of this needs the token to survive or do anything on its own — it's
value from existing, once, for a moment, as a Dinosaur. That's a genuinely
strong reason to like this card beyond "more blink," and it's a good
illustration of why this deck's ETB density (the thing `Curator of Sun's
Creation` and the burn plan both already lean on) keeps paying off in ways
that aren't obvious from any one card's text in isolation.

**The burn plan is well-supported, not bolted on.** `Terror of the Peaks` and
`Warstorm Surge` both trigger off creatures entering, and this deck generates
an unusually high number of ETBs for its size: discover casts creatures for
free, `Ghalta and Mavren` / `Quartzwood Crasher` / `The Skullspore Nexus` /
`Regisaur Alpha` all make tokens, and the blink package re-enters things a
second time. That volume of ETBs is exactly what makes Terror/Warstorm Surge
a credible win condition here rather than a cute inclusion — the deck's own
game plan feeds it.

**`Roaming Throne`** is a strong doubler for other Dinosaurs' own triggered
abilities (e.g. a second `Regisaur Alpha` token, a second Gishath hit) if you
name Dinosaur — but it specifically doubles triggers whose source is "another
creature," which by the rules text doesn't include Pantlaza's own discover
trigger. Worth double-checking against Gatherer rulings if a specific line
depends on it, but don't expect it to be a second Pantlaza-doubler alongside
Curator.

**Combat/outvalue plan:** `Ghalta, Stampede Tyrant`, `Gishath, Sun's Avatar`,
`Zacama, Primal Calamity`, both Etali — a real top end, and `Green Sun's
Zenith`/`Worldly Tutor` can go find Pantlaza itself (or another key creature)
since both tutor specifically for creatures. `Aggravated Assault` doesn't
combo with anything else in the list — it's a genuine power piece
(untap-and-extra-combat with a board of hasty, discovered Dinosaurs is a lot
of damage) but not an infinite loop.

## Combos found (correction — the deck is not combo-free)

**This section didn't exist in the first version of this review**, which
said flatly that no combo was found. That was wrong, and it's a direct
result of only checking one card (`Aggravated Assault`) by hand instead of
checking the whole card pool against an actual combo database. Once
`find-deck-combos` existed and was run against this decklist, two real
combos turned up — one of them explains a card ( `Wrathful Raptors`) that a
later pass of `find-weakest-cards` had specifically called one of the two
weakest removal spells in the deck. That call was wrong too, for the same
underlying reason: a narrow, reactive-looking card is exactly what a combo
piece looks like from the outside.

- **`Polyraptor` + `Marauding Raptor`** — Marauding Raptor deals 2 damage to
  every creature you control as it enters (including itself and Polyraptor
  copies); Polyraptor makes a token copy of itself whenever it's dealt
  damage; each new copy entering triggers Marauding Raptor again. This loops
  forever. Commander Spellbook's own data on this exact pair notes it "will
  result in a mandatory infinite loop... cause the game to end in a draw" —
  by itself, this is bad for you, not a win.
  **`Wrathful Raptors`** is what turns it into a win: whenever a Dinosaur
  you control is dealt damage, it redirects that damage to any target that
  isn't a Dinosaur. With Wrathful Raptors out, every one of Marauding
  Raptor's pings on an entering Polyraptor copy becomes redirectable
  damage to an opponent — infinite damage, not just infinite tokens. This
  specific 3-card framing isn't its own cataloged entry in Commander
  Spellbook's database (it only lists the 2-card loop), but it's
  well-documented in the wider Commander community for exactly this
  interaction, and it matches what `Wrathful Raptors`'s actual rules text
  does once you trace it through.
- **`Polyraptor` + `Forerunner of the Empire`** — a second, independent combo
  neither version of this review had caught before running the combo
  database. Forerunner deals 1 damage to each creature whenever a Dinosaur
  you control enters; a Polyraptor copy entering triggers that damage,
  which triggers Polyraptor's own copy-on-damage ability, whose new copy
  entering triggers Forerunner again. This one doesn't need Wrathful
  Raptors — it independently produces infinite damage to *every* creature
  on the battlefield (yours and opponents'), which is effectively an
  infinite board wipe. Given the earlier finding that this deck's real
  removal is almost entirely sorcery-speed, this combo is a meaningfully
  bigger answer to a wide opposing board than the removal count alone
  suggested.

Both require `Polyraptor` plus one setup piece already in the deck and rely
on repeatedly triggering ETBs, which is exactly what the discover/blink
package is already doing — this isn't a bolted-on combo, it fits the
deck's existing engine.

## The numbers

| | |
|---|---|
| Total cards | 100 |
| Lands | 36 |
| Creatures | 37 |
| Instants / Sorceries | 7 / 7 |
| Artifacts / Enchantments | 6 / 8 |
| Color identity (pips) | G 54, R 36, W 30 |

**Mana curve** (nonland, 64 cards):

| CMC | 1 | 2 | 3 | 4 | 5 | 6 | 7+ |
|---|---|---|---|---|---|---|---|
| Count | 7 | 11 | 10 | 11 | 8 | 6 | **11** |

11 cards at CMC 7+ is a lot for a 100-card deck — about 17% of your nonland
slots. That's a deliberate top-heavy build (matches the "big Dinosaurs" plan),
and you've got 12 ramp sources plus discover to compensate, but it does mean
a hand without early ramp or discover fuel can feel clunky. Worth watching,
not necessarily worth fixing.

**Ramp (12):** `Arcane Signet`, `Atzocan Seer`, `Birds of Paradise`, `Gwenna,
Eyes of Gaea`, `Herd Heirloom`, `Hulking Raptor`, `Intrepid Paleontologist`,
`Jeska's Will`, `Regal Behemoth`, `Sol Ring`, `The Great Henge`, `Three
Visits`. Healthy count for the curve above. Note: `Hunting Velociraptor`,
`Marauding Raptor`, and `Tannuk, Steadfast Second` are tagged `[Ramp]` in
your list but are actually cost-reduction/haste effects, not mana
acceleration — they help you deploy threats cheaper or faster, but they
don't get you ahead on lands/mana the way the 12 above do. Worth knowing the
difference if you're ever counting on "ramp" to hit a specific land drop.

**Removal (13 total: 11 targeted + 2 board wipes):** `Swords to Plowshares`,
`Bronzebeak Foragers`, `Itzquinth, Firstborn of Gishath`,
`Kogla and Yidaro`, `Swooping Pteranodon`, `Terror of the Peaks`, `Tranquil
Frillback`, `Trumpeting Carnosaur`, `Warstorm Surge`, `Wrathful Raptors`,
`Zacama, Primal Calamity` / board wipes: `Austere Command`, `Wakening Sun's
Avatar`. (`Annie Joins Up` dropped off this list when it left the deck —
her static ability doubling legendary creatures' triggered abilities was
mostly dead text here anyway: doubling `Pantlaza`'s own discover trigger
does nothing, since a "do this only once each turn" restriction blocks a
second resolution from the same permanent even when a doubling effect makes
it trigger twice — "can't" beats "can." That's a different rule than the
one that makes blink work, where the restriction resets because blinking
creates a genuinely new permanent, not just a second trigger off the old
one. Your read on cutting her was right.) Still a solid count for Bracket 3.
**But look at the speed:** almost all of it is sorcery-speed or
ETB-triggered — `Swords to Plowshares` is your only card that answers
something at instant speed on someone else's turn. If an opponent tries to
close out a game on their turn (a combo, an alpha strike, a must-answer
bomb), you have one card that can do anything about it before your next
turn. That's the single biggest structural gap I'd flag from the numbers,
independent of what you already know the deck struggles with.
(`Wrathful Raptors` is on this list because it does function as removal —
but see **Combos found** above: it's really the finishing piece of an
infinite-damage combo, not just a conditional damage redirector.)

**Card draw (10):** `Garruk's Uprising`, `Guardian Project`, `Herd Heirloom`,
`Jetmir's Garden` (cycling), `Kogla and Yidaro`, `Last March of the Ents`,
`Runic Armasaur`, `Sylvan Library`, `The Great Henge`, `Vaultborn Tyrant`.
Healthy. Not counted here but worth knowing about: `Bonehoard Dracosaur`,
`Cream of the Crop`, both `Etali`s, and `Trumpeting Carnosaur`'s discover all
generate real card advantage through impulse-draw/library manipulation
rather than literal "draw a card" text — so your actual advantage engine is
stronger than the count above suggests.

**Tutors:** 5 land fetches (`Arid Mesa`, `Fabled Passage`, `Prismatic Vista`,
`Windswept Heath`, `Wooded Foothills`) plus 5 nonland (`Forerunner of the
Empire`, `Green Sun's Zenith`, `Savage Order`, `Three Visits`, `Worldly
Tutor`). `Green Sun's Zenith` and `Worldly Tutor` both fetch specifically
creatures, so either can go get Pantlaza if she's not on the battlefield —
good consistency for a commander-dependent plan.

**Protection:** `Grand Abolisher`, `Heroic Intervention`, `Rhythm of the
Wild`, `Teferi's Protection`, plus a mode of `Akroma's Will` — a real
protection suite for a deck that wants to hold a board state, which matters
given how ETB-dependent the value engine is.

**No counterspells, no extra-turn cards, no mass land denial.** Consistent
with a Bracket 3 creature-value shell — though see **Combos found** above,
this is not actually a combo-free deck, it just doesn't lean on the
control/extra-turn tools those restrictions are about.

## Caveats

- `analyze_deck.py`'s regex-based analysis still can't see combos itself —
  that's what `find-deck-combos` (checking against Commander Spellbook's
  database) is for, and it's what caught the two combos above. Its
  `almost_included` list also has ~78 near-miss combos for this deck
  (missing one or more cards); most are noise, but worth a look if you want
  to hunt for more.
- The Bracket 1/2 vs. 4/5 splits depend on table intent, not card choices —
  not relevant here since you're squarely in Bracket 3 territory either way.
  (Also worth noting: having a real infinite combo is itself relevant to
  the Bracket 3 vs. 4 line — WotC's criteria for Bracket 3 is "no
  intentional *early-game* two-card combos," not "no combos at all," so
  this alone doesn't push the deck out of Bracket 3, but it's worth keeping
  in mind if the deck's power creeps up further.)

## Next steps

`find-weakest-cards` and `find-deck-combos` both exist now. The instant-speed
removal gap and the crowded 7+ CMC top end (11 cards) are still the two
places I'd look first for trims; anything flagged as weak should be
cross-checked against `combos.json` first, per the miss above.
