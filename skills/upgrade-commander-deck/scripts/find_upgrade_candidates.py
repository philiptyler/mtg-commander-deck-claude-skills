"""Source and deterministically rank upgrade candidates for a specific gap
in an already-reviewed deck (a category to reinforce, a curve slot to
fill, a combo to complete).

This does NOT pick the final card for you - it produces a ranked shortlist
grounded in checkable facts (legality, color identity, dedup against the
existing list, budget, whether it completes a combo you're one card from,
whether it lands in an undersupplied curve slot). The final pick and the
qualitative "why this one" reasoning is still a judgment call - see
SKILL.md.

Usage:
    python3 find_upgrade_candidates.py --deck-dir ../review-commander-deck/decks/my-deck --category removal
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import scryfall_search_client

# Oracle-text query fragments per category, echoing analyze_deck.py's own
# regex categories so "find me more removal" searches for the same shape
# of effect analyze_deck.py would have counted as removal.
CATEGORY_QUERIES = {
    "ramp": '(o:"search your library for a basic land" or o:"search your library for a land card" '
            'or o:"add {c}{c}" or o:"add one mana of any color" or o:"add two mana" '
            'or o:"you may play an additional land")',
    "removal": '(o:"destroy target creature" or o:"exile target creature" or o:"destroy target permanent" '
               'or o:"exile target permanent" or o:"deals damage to target creature" or o:"deals damage to any target")',
    "board_wipe": '(o:"destroy all creatures" or o:"each creature gets -" or o:"deals damage to each creature")',
    "card_draw": '(o:"draw a card" or o:"draw two cards" or o:"draw three cards" or o:"draw cards")',
    "tutors": '(o:"search your library for a card" or o:"search your library for a creature card" '
              'or o:"search your library for an artifact card")',
    "protection": '(o:hexproof or o:indestructible or o:"protection from")',
    "any": "",
}


def load(path: Path):
    return json.loads(path.read_text()) if path.exists() else None


def commander_color_identity(context: dict) -> list:
    colors = set()
    for card in context["cards"]:
        if card.get("is_commander"):
            colors |= set(card.get("color_identity") or [])
    return sorted(colors)


def build_query(category: str, color_identity: list, cmc_min, cmc_max, budget) -> str:
    parts = [
        f"id<={''.join(color_identity) or 'c'}",
        "f:commander",
        "-is:funny",
        "-t:land",
    ]
    frag = CATEGORY_QUERIES.get(category, "")
    if frag:
        parts.append(frag)
    if cmc_min is not None:
        parts.append(f"cmc>={cmc_min}")
    if cmc_max is not None:
        parts.append(f"cmc<={cmc_max}")
    if budget is not None:
        parts.append(f"usd<={budget}")
    return " ".join(parts)


def undersupplied_curve_buckets(analysis: dict) -> set:
    curve = analysis["mana_curve"]
    values = [v for k, v in curve.items() if k != "unknown"]
    if not values:
        return set()
    avg = sum(values) / len(values)
    return {bucket for bucket, count in curve.items() if bucket != "unknown" and count < avg}


def curve_bucket(cmc) -> str:
    if cmc is None:
        return "unknown"
    cmc = int(cmc)
    return str(cmc) if cmc < 7 else "7+"


def combo_completions(combos: dict, candidate_name: str) -> list:
    if not combos:
        return []
    return [
        {"id": c["id"], "url": c["url"], "cards": c["cards"], "produces": c["produces"]}
        for c in combos.get("almost_included", [])
        if c["missing_cards"] == [candidate_name]
    ]


# A "destroy/exile target X you control" match is a blink/protection effect
# that superficially matches removal-shaped query text, not actual removal -
# same false positive analyze_deck.py already had to filter out. Drop a
# candidate for the removal/board_wipe categories if every destroy/exile
# clause in its text targets the caster's own stuff.
_OWN_PERMANENT_RE = re.compile(r"(destroy|exile) (?:up to \w+ )?target [\w\s]+ you control")
_ANY_DESTROY_EXILE_RE = re.compile(r"(destroy|exile) (?:up to \w+ )?target")


# A card whose only "efficiency" is a conditional cost reduction (e.g.
# "costs {3} less to cast if it targets a tapped creature") isn't reliably
# that cheap - the board state has to cooperate. Scryfall's own `cmc` field
# is always the nominal, undiscounted cost, so that part is already honest;
# what's missing is a flag so a candidate like this doesn't get silently
# read as "efficient" when the discount won't always be live. Found via
# real feedback: this is exactly what was wrong with recommending Ride's
# End, whose only real distinguishing feature over its many near-duplicates
# ("destroy/exile target creature, costs 3 less if targeting something
# tapped") was that it hit Vehicles too - a narrow bonus for this deck.
_CONDITIONAL_COST_RE = re.compile(r"costs? \{\d+\}.{0,20}less to cast if")


def has_conditional_discount(oracle_text: str) -> bool:
    return bool(_CONDITIONAL_COST_RE.search((oracle_text or "").lower()))


# Maps this script's --category values to weak_card_signals.json's
# category_saturation keys (find-weakest-cards), so sourcing can check
# whether the category actually has room to grow before recommending a net
# add to it. "protection" and "any" have no saturation tracking - skipped.
CATEGORY_TO_SATURATION_KEY = {
    "ramp": "ramp",
    "removal": "targeted_removal",
    "board_wipe": "board_wipe",
    "card_draw": "card_draw",
    "tutors": "tutors",
}


def saturation_status(deck_dir: Path, category: str):
    """Returns the category's current saturation status dict from
    weak_card_signals.json, or None if not tracked/not available. Checking
    this before sourcing is the fix for a real mistake: recommending a net
    new removal spell for the dinos deck when weak_card_signals.json
    already showed targeted_removal at 11/[10,14] - "within", not "under"
    - meaning what the deck actually needed there (if anything) was a
    straight quality swap of an existing weak member, not one more card on
    top of an already-sufficient count."""
    key = CATEGORY_TO_SATURATION_KEY.get(category)
    if key is None:
        return None
    signals = load(deck_dir / "weak_card_signals.json")
    if signals is None:
        return None
    for row in signals.get("category_saturation", []):
        if row["category"] == key:
            return row
    return None


def is_removal_false_positive(category: str, oracle_text: str) -> bool:
    if category not in ("removal", "board_wipe") or not oracle_text:
        return False
    text = oracle_text.lower()
    for sentence in re.split(r"(?<=[.;])\s+", text):
        if _ANY_DESTROY_EXILE_RE.search(sentence) and not _OWN_PERMANENT_RE.search(sentence):
            return False  # at least one clause targets something not "you control"
    return bool(_ANY_DESTROY_EXILE_RE.search(text))  # matched, but only ever "you control"


# Split/transform/modal-DFC cards leave oracle_text (and mana_cost) null at
# the top level of a raw Scryfall response - the real per-face text lives in
# card_faces. review-commander-deck's build_context.py already backfills
# this for cards fetched through the collection endpoint; raw /cards/search
# results (what this script uses) need the same treatment, or a split card
# like "Struggle // Survive" shows up with no text at all - found while
# sourcing candidates for the dinos deck, where it silently defeated the
# false-positive filter below (nothing to match against) and would have
# been unreadable at the "read the candidate's actual oracle_text before
# recommending it" step this skill's own SKILL.md requires.
def normalize_card(card: dict) -> dict:
    faces = card.get("card_faces") or []
    if not card.get("oracle_text") and faces:
        card = dict(card)
        card["oracle_text"] = "\n".join(f.get("oracle_text", "") for f in faces if f.get("oracle_text"))
    if not card.get("mana_cost") and faces:
        card = dict(card)
        card["mana_cost"] = " // ".join(f.get("mana_cost", "") for f in faces if f.get("mana_cost"))
    return card


def score_and_filter(raw_cards, existing_names, gap_buckets, combos, category) -> list:
    scored = []
    for card in raw_cards:
        card = normalize_card(card)
        if card.get("name") in existing_names:
            continue
        if is_removal_false_positive(category, card.get("oracle_text")):
            continue
        completions = combo_completions(combos, card["name"])
        fills_gap = curve_bucket(card.get("cmc")) in gap_buckets
        scored.append({
            "name": card["name"],
            "mana_cost": card.get("mana_cost"),
            "cmc": card.get("cmc"),
            "type_line": card.get("type_line"),
            "oracle_text": card.get("oracle_text"),
            "color_identity": card.get("color_identity"),
            "usd": (card.get("prices") or {}).get("usd"),
            "edhrec_rank": card.get("edhrec_rank"),
            "game_changer": card.get("game_changer", False),
            "is_instant": "Instant" in (card.get("type_line") or ""),
            "completes_combo": bool(completions),
            "combo_details": completions,
            "fills_curve_gap": fills_gap,
            "conditional_discount": has_conditional_discount(card.get("oracle_text")),
        })

    # Deterministic sort: combo completion first (strongest, checkable
    # signal), then curve-gap fit, then instant speed (flexibility), then
    # edhrec_rank as a tiebreaker only - never the primary driver, per this
    # deck's stated EDHREC policy. A conditional-discount card is sorted as
    # if it costs its full nominal CMC (no bonus for the maybe-discount),
    # which naturally drops it behind a same-CMC card with no such caveat.
    scored.sort(key=lambda c: (
        not c["completes_combo"],
        not c["fills_curve_gap"],
        not c["is_instant"],
        c["edhrec_rank"] if c["edhrec_rank"] is not None else 10**9,
    ))
    return scored


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--deck-dir", required=True, type=Path)
    ap.add_argument("--category", required=True, choices=list(CATEGORY_QUERIES))
    ap.add_argument("--count", type=int, default=10)
    ap.add_argument("--budget", type=float, default=None, help="max USD price per card")
    ap.add_argument("--cmc-min", type=int, default=None)
    ap.add_argument("--cmc-max", type=int, default=None)
    args = ap.parse_args()

    context = json.loads((args.deck_dir / "context.json").read_text())
    analysis = json.loads((args.deck_dir / "analysis.json").read_text())
    combos = load(args.deck_dir / "combos.json")

    color_identity = commander_color_identity(context)
    existing_names = {c["name"] for c in context["cards"]}
    gap_buckets = undersupplied_curve_buckets(analysis)
    saturation = saturation_status(args.deck_dir, args.category)

    query = build_query(args.category, color_identity, args.cmc_min, args.cmc_max, args.budget)
    raw_cards = scryfall_search_client.search(query, max_results=50)
    ranked = score_and_filter(raw_cards, existing_names, gap_buckets, combos, args.category)[: args.count]

    result = {
        "category": args.category,
        "category_saturation": saturation,
        "query": query,
        "commander_color_identity": color_identity,
        "undersupplied_curve_buckets": sorted(gap_buckets),
        "candidates": ranked,
    }

    # Filename must reflect every filter that changes the result set, not
    # just category - two runs of the same category with different CMC/
    # budget bounds (a completely normal thing to do, e.g. sourcing a cheap
    # vs. an expensive removal slot in the same session) would otherwise
    # silently overwrite each other. Found by doing exactly that.
    suffix_bits = [args.category]
    if args.cmc_min is not None or args.cmc_max is not None:
        suffix_bits.append(f"cmc{args.cmc_min if args.cmc_min is not None else ''}-{args.cmc_max if args.cmc_max is not None else ''}")
    if args.budget is not None:
        suffix_bits.append(f"budget{args.budget:g}")
    out_path = args.deck_dir / f"upgrade_candidates_{'_'.join(suffix_bits)}.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Wrote {out_path} ({len(ranked)} candidates)")
    if any(c["completes_combo"] for c in ranked):
        print("Note: at least one candidate completes a combo already one card deep in this deck.")
    if saturation and saturation["status"] != "under":
        print(
            f"WARNING: {args.category} is already '{saturation['status']}' "
            f"({saturation['count']} vs. target {saturation['target_range']}) - "
            f"a net add here should be a clear quality upgrade over an existing "
            f"member of this category, not just 'good in isolation.' Consider "
            f"pairing this candidate with cutting the category's weakest current "
            f"member instead of an unrelated cut."
        )
    if any(c["conditional_discount"] for c in ranked):
        print("Note: some candidates have a conditional cost discount - see conditional_discount per candidate; don't treat their nominal cmc as reliably cheap.")


if __name__ == "__main__":
    main()
