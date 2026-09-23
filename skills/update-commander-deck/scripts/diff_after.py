"""Compare a deck's post-change analysis.json/combos.json against the
snapshot taken by snapshot_before.py, plus a couple of sanity checks that
matter specifically after editing a decklist (card count, color identity).

Run this AFTER re-running review-commander-deck's fetch_cards.py ->
build_context.py -> analyze_deck.py (and find-deck-combos's
find_combos.py, if installed) on the updated decklist.txt.

Usage:
    python3 diff_after.py --deck-dir ../review-commander-deck/decks/my-deck
"""

import argparse
import json
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text()) if path.exists() else None


def counts_delta(before: dict, after: dict) -> dict:
    keys = set(after) | set(before)
    return {k: after.get(k, 0) - before.get(k, 0) for k in keys if after.get(k, 0) != before.get(k, 0)}


def category_changes(before: dict, after: dict) -> dict:
    changes = {}
    for key in set(after) | set(before):
        b, a = set(before.get(key, [])), set(after.get(key, []))
        added, removed = sorted(a - b), sorted(b - a)
        if added or removed:
            changes[key] = {"added": added, "removed": removed}
    return changes


def curve_delta(before: dict, after: dict):
    """Bucket-level and summary-stat curve movement, both nominal and
    typical (effective-CMC-adjusted - see
    review-commander-deck/references/effective_cmc.md). Added after direct
    feedback that swap proposals were eyeballing "cheaper CMC = better"
    with no actual computed curve-impact tooling behind that claim.
    Tolerant of a `before` snapshot predating curve_summary/
    typical_mana_curve (older analyze_deck.py output) via .get()."""
    def bucket_delta(before_curve, after_curve):
        keys = set(before_curve) | set(after_curve)
        return {k: after_curve.get(k, 0) - before_curve.get(k, 0) for k in keys
                if after_curve.get(k, 0) != before_curve.get(k, 0)}

    before_summary = before.get("curve_summary") or {}
    after_summary = after.get("curve_summary") or {}

    def stat_delta(key):
        b, a = before_summary.get(key), after_summary.get(key)
        if b is None or a is None:
            return None
        return round(a - b, 2)

    return {
        "mana_curve_bucket_delta": bucket_delta(before.get("mana_curve", {}), after.get("mana_curve", {})),
        "typical_mana_curve_bucket_delta": bucket_delta(before.get("typical_mana_curve", {}), after.get("typical_mana_curve", {})),
        "average_cmc_delta": stat_delta("average_cmc"),
        "typical_average_cmc_delta": stat_delta("typical_average_cmc"),
        "pct_cmc_le_3_delta": stat_delta("pct_cmc_le_3"),
        "typical_pct_cmc_le_3_delta": stat_delta("typical_pct_cmc_le_3"),
        "average_cmc_after": after_summary.get("average_cmc"),
        "typical_average_cmc_after": after_summary.get("typical_average_cmc"),
        "baseline_reference": after_summary.get("baseline_reference"),
    }


def combo_changes(before_combos, after_combos):
    if before_combos is None or after_combos is None:
        return None, None

    def keyset(combos):
        return {tuple(sorted(c["cards"])) for c in combos.get("included", [])}

    before_keys, after_keys = keyset(before_combos), keyset(after_combos)
    gained = [list(c) for c in (after_keys - before_keys)]
    lost = [list(c) for c in (before_keys - after_keys)]
    return gained, lost


def color_identity_violations(context: dict) -> dict:
    commanders = [c for c in context["cards"] if c.get("is_commander")]
    if not commanders:
        return {"commander_color_identity": None, "violations": None}

    commander_identity = set()
    for c in commanders:
        commander_identity |= set(c.get("color_identity") or [])

    violations = []
    for card in context["cards"]:
        if card.get("is_commander") or card.get("not_found"):
            continue
        card_identity = set(card.get("color_identity") or [])
        if not card_identity.issubset(commander_identity):
            violations.append({"name": card["name"], "color_identity": sorted(card_identity)})

    return {"commander_color_identity": sorted(commander_identity), "violations": violations}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--deck-dir", required=True, type=Path)
    args = ap.parse_args()

    tmp_dir = args.deck_dir / ".update-tmp"
    before_analysis = load(tmp_dir / "analysis.json")
    before_combos = load(tmp_dir / "combos.json")
    after_analysis = json.loads((args.deck_dir / "analysis.json").read_text())
    after_combos = load(args.deck_dir / "combos.json")
    context = json.loads((args.deck_dir / "context.json").read_text())

    combos_gained, combos_lost = combo_changes(before_combos, after_combos)

    diff = {
        "has_baseline": before_analysis is not None,
        "counts_delta": counts_delta(before_analysis["counts"], after_analysis["counts"]) if before_analysis else None,
        "category_changes": category_changes(before_analysis["categories"], after_analysis["categories"]) if before_analysis else None,
        "curve_delta": curve_delta(before_analysis, after_analysis) if before_analysis else None,
        "bracket_before": before_analysis["bracket_estimate"]["suggested"] if before_analysis else None,
        "bracket_after": after_analysis["bracket_estimate"]["suggested"],
        "combos_gained": combos_gained,
        "combos_lost": combos_lost,
        "card_count": context["card_count"],
        "card_count_warning": None if context["card_count"] == 100 else f"Deck has {context['card_count']} cards, not 100.",
        **color_identity_violations(context),
    }

    out_path = args.deck_dir / "last_update_diff.json"
    out_path.write_text(json.dumps(diff, indent=2))

    # Deliberately NOT deleting tmp_dir here. It used to be auto-cleaned on
    # every run, which meant re-running this script after any mid-update
    # fix (e.g. an analyze_deck.py regex bug found and fixed partway
    # through applying a swap) lost the baseline with no clean way to
    # re-diff - the only recovery was pulling analysis.json/combos.json
    # back out of git by hand. snapshot_before.py already overwrites this
    # directory fresh each time it's explicitly run for a new update cycle,
    # which is the right place for "clean slate" to happen - not here,
    # automatically, as a side effect of computing a diff.

    print(f"Wrote {out_path}")
    if diff["combos_lost"]:
        print(f"WARNING: this change broke {len(diff['combos_lost'])} combo(s): {diff['combos_lost']}")
    if diff["card_count_warning"]:
        print(f"WARNING: {diff['card_count_warning']}")
    if diff.get("violations"):
        print(f"WARNING: {len(diff['violations'])} card(s) outside the commander's color identity")
    cd = diff.get("curve_delta")
    if cd and cd["typical_average_cmc_delta"] is not None:
        print(
            f"Typical average CMC: {cd['typical_average_cmc_after']} "
            f"({cd['typical_average_cmc_delta']:+}), nominal delta {cd['average_cmc_delta']:+}"
        )


if __name__ == "__main__":
    main()
