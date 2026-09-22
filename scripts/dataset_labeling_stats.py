from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from typing import List, Optional


def read_labels_csv(path: str) -> List[List[str]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rater_columns = [c for c in (reader.fieldnames or []) if c != "image_id"]
        if not rater_columns:
            raise ValueError("CSV must have an 'image_id' column plus one column per rater.")

        rows: List[List[str]] = []
        row_counts = set()
        for record in reader:
            labels = [record[c].strip() for c in rater_columns if record.get(c, "").strip()]
            if not labels:
                continue
            rows.append(labels)
            row_counts.add(len(labels))

        if len(row_counts) > 1:
            raise ValueError(
                "Fleiss' kappa requires the same number of raters for every image. "
                f"Found varying rater counts: {sorted(row_counts)}. "
                "Drop incomplete rows or backfill missing ratings before running this tool."
            )

        return rows


def fleiss_kappa(rows: List[List[str]]) -> float:
    if not rows:
        raise ValueError("No labeled rows provided.")

    n = len(rows[0])
    if n < 2:
        raise ValueError("Fleiss' kappa requires at least 2 raters per item.")
    if any(len(r) != n for r in rows):
        raise ValueError("All rows must have the same number of ratings.")

    categories = sorted({label for row in rows for label in row})
    num_items = len(rows)

    category_counts_per_item = []
    for row in rows:
        counts = Counter(row)
        category_counts_per_item.append([counts.get(c, 0) for c in categories])

    p_i_values = []
    for counts in category_counts_per_item:
        sum_sq = sum(c * c for c in counts)
        p_i = (sum_sq - n) / (n * (n - 1))
        p_i_values.append(p_i)
    p_bar = sum(p_i_values) / num_items

    total_assignments = num_items * n
    category_totals = [0] * len(categories)
    for counts in category_counts_per_item:
        for idx, c in enumerate(counts):
            category_totals[idx] += c
    p_j = [total / total_assignments for total in category_totals]
    p_e_bar = sum(p * p for p in p_j)

    if p_e_bar == 1.0:
        return 1.0

    return (p_bar - p_e_bar) / (1 - p_e_bar)


def interpret_kappa(kappa: float) -> str:
    if kappa < 0.0:
        return "poor (worse than chance)"
    if kappa < 0.20:
        return "slight"
    if kappa < 0.40:
        return "fair"
    if kappa < 0.60:
        return "moderate"
    if kappa < 0.80:
        return "substantial"
    return "almost perfect"


def majority_vote(labels: List[str]) -> Optional[str]:
    counts = Counter(labels)
    top = counts.most_common()
    if len(top) > 1 and top[0][1] == top[1][1]:
        return None
    return top[0][0]


def class_balance(rows: List[List[str]]) -> Counter:
    balance: Counter = Counter()
    ties = 0
    for row in rows:
        label = majority_vote(row)
        if label is None:
            ties += 1
            continue
        balance[label] += 1
    if ties:
        balance["__no_majority__"] = ties
    return balance


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute Fleiss' kappa inter-rater agreement and class balance from a "
                    "wide-format CSV of multi-rater muscle-level labels."
    )
    parser.add_argument("csv_path", help="Path to a CSV with an image_id column plus one column per rater.")
    args = parser.parse_args(argv)

    rows = read_labels_csv(args.csv_path)
    kappa = fleiss_kappa(rows)
    balance = class_balance(rows)

    print(f"Items labeled: {len(rows)}")
    print(f"Raters per item: {len(rows[0])}")
    print(f"Fleiss' kappa: {kappa:.4f} ({interpret_kappa(kappa)})")
    print()
    print("Class balance (majority vote):")
    for label, count in sorted(balance.items(), key=lambda kv: kv[0]):
        print(f"  {label}: {count}")

    if kappa < 0.20:
        print()
        print("RECOMMENDATION: kappa is 'slight' or worse. Revise the labeling rubric and "
              "re-pilot before scaling up labeling (see Documents/muscle_level_labeling_protocol.md).")
    elif kappa < 0.40:
        print()
        print("RECOMMENDATION: kappa is 'fair'. Review disagreements before scaling up.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
