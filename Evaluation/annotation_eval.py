"""
Annotation evaluation script.

Compares company annotations against ground truth, reporting precision/recall/F1
overall and per class at multiple frame-tolerance thresholds (label-only matching).

For true positive pairs, subtype confusion matrices are reported per event label,
showing how accurately the company predicted the subtype given a correct label match.

Usage (from the evaluation/ directory):
    python annotation/annotation_eval.py
"""

import json
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration — adjust paths, thresholds, and display options here
# ---------------------------------------------------------------------------

GT_PATH = "annotation/wvu_buff_gt.json"
COMPANY_PATH = "annotation/annotation_company1.json"

THRESHOLDS = [10, 20, 30]  # frame-tolerance thresholds to evaluate

# Max FN/FP entries to print per section (None = print all)
MAX_DETAIL_ROWS = None

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_annotations(path):
    try:
        with open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(
            f"Error: file not found: {path}\n"
            "Set GT_PATH and COMPANY_PATH at the top of the script to the correct paths."
        )
        raise SystemExit(1)
    annotations = data["annotations"]
    for ann in annotations:
        ann["frame"] = int(ann["frame"])
    return annotations


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def _match_key(ann, mode):
    if mode == "label+subType":
        return f"{ann['label']}|{ann['subType']}"
    return ann["label"]


def match_annotations(gt, pred, threshold, mode):
    """
    Greedily match GT annotations to predicted annotations within `threshold` frames.

    Returns
    -------
    tp_pairs : list of (gt_ann, pred_ann) matched pairs
    fn_list  : unmatched GT annotations (missed by company)
    fp_list  : unmatched pred annotations (added by company, not in GT)
    """
    gt_by_key = defaultdict(list)
    pred_by_key = defaultdict(list)

    for ann in gt:
        gt_by_key[_match_key(ann, mode)].append(ann)
    for ann in pred:
        pred_by_key[_match_key(ann, mode)].append(ann)

    tp_pairs = []
    fn_list = []
    fp_list = []

    all_keys = set(gt_by_key) | set(pred_by_key)

    for key in all_keys:
        gt_anns = gt_by_key.get(key, [])
        pred_anns = pred_by_key.get(key, [])

        if not gt_anns:
            fp_list.extend(pred_anns)
            continue

        if not pred_anns:
            fn_list.extend(gt_anns)
            continue

        # Build all candidate pairs within threshold, sorted by frame distance
        candidates = []  # (distance, gt_idx, pred_idx)
        for gi, g in enumerate(gt_anns):
            for pi, p in enumerate(pred_anns):
                dist = abs(g["frame"] - p["frame"])
                if dist <= threshold:
                    candidates.append((dist, gi, pi))

        candidates.sort(key=lambda x: x[0])

        matched_gt = set()
        matched_pred = set()

        for dist, gi, pi in candidates:
            if gi not in matched_gt and pi not in matched_pred:
                tp_pairs.append((gt_anns[gi], pred_anns[pi]))
                matched_gt.add(gi)
                matched_pred.add(pi)

        for gi, g in enumerate(gt_anns):
            if gi not in matched_gt:
                fn_list.append(g)

        for pi, p in enumerate(pred_anns):
            if pi not in matched_pred:
                fp_list.append(p)

    return tp_pairs, fn_list, fp_list


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_metrics(tp, fp, fn):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def compute_subtype_confusion(tp_pairs):
    """
    For each label, build a confusion matrix over subType predictions.

    Only includes labels where at least one TP pair has a non-"None" subType
    in either ground truth or prediction.

    Returns
    -------
    { label: { gt_subType: { pred_subType: count } } }
    """
    raw = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    has_meaningful = defaultdict(bool)

    for gt_ann, pred_ann in tp_pairs:
        label = gt_ann["label"]
        gt_sub = gt_ann["subType"]
        pred_sub = pred_ann["subType"]
        raw[label][gt_sub][pred_sub] += 1
        if gt_sub != "None" or pred_sub != "None":
            has_meaningful[label] = True

    return {label: raw[label] for label in raw if has_meaningful[label]}


def compute_per_class_metrics(tp_pairs, fn_list, fp_list):
    tp_by_label = defaultdict(int)
    fp_by_label = defaultdict(int)
    fn_by_label = defaultdict(int)

    for gt_ann, _ in tp_pairs:
        tp_by_label[gt_ann["label"]] += 1
    for ann in fp_list:
        fp_by_label[ann["label"]] += 1
    for ann in fn_list:
        fn_by_label[ann["label"]] += 1

    all_labels = set(tp_by_label) | set(fp_by_label) | set(fn_by_label)
    return {
        label: compute_metrics(tp_by_label[label], fp_by_label[label], fn_by_label[label])
        for label in sorted(all_labels)
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

_COL_LABEL = 42

def _fmt(val):
    return f"{val:.4f}"


def _print_section(title):
    print()
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)


def _print_metrics_row(label, m, indent=0):
    pad = " " * indent
    label_str = label.ljust(_COL_LABEL - indent)
    print(
        f"{pad}{label_str}"
        f"  {_fmt(m['precision']):>8}"
        f"  {_fmt(m['recall']):>8}"
        f"  {_fmt(m['f1']):>8}"
        f"  {m['tp']:>6}  {m['fp']:>6}  {m['fn']:>6}"
    )


def _print_detail_list(anns, title):
    rows = anns if MAX_DETAIL_ROWS is None else anns[:MAX_DETAIL_ROWS]
    print(f"\n  {title} ({len(anns)} total):")
    if not rows:
        print("    (none)")
        return
    for ann in sorted(rows, key=lambda a: a["frame"]):
        print(
            f"    frame={ann['frame']:>7d}"
            f"  label={ann['label']:<32s}"
            f"  subType={ann['subType']:<12s}"
            f"  gameTime={ann['gameTime']}"
        )
    if MAX_DETAIL_ROWS is not None and len(anns) > MAX_DETAIL_ROWS:
        print(f"    ... {len(anns) - MAX_DETAIL_ROWS} more rows omitted")


def print_subtype_confusion(confusion):
    """Print per-label subtype confusion matrices for TP pairs."""
    print(f"\n  SUBTYPE ACCURACY (among correctly matched events):")
    for label in sorted(confusion):
        matrix = confusion[label]
        gt_subs = sorted(matrix.keys())
        pred_subs = sorted({p for row in matrix.values() for p in row})
        col_w = max(len(s) for s in pred_subs + gt_subs + ["GT \\ Pred"])
        total = sum(matrix[g][p] for g in gt_subs for p in pred_subs)
        correct = sum(matrix[s].get(s, 0) for s in gt_subs)

        print(f"\n  {label}  —  subtype accuracy: {correct}/{total} ({correct/total:.1%})")
        header = "    " + "GT \\ Pred".ljust(col_w) + "  " + "  ".join(p.ljust(col_w) for p in pred_subs)
        print(header)
        print("    " + "-" * (len(header) - 4))
        for gt_sub in gt_subs:
            row_total = sum(matrix[gt_sub].values())
            cells = "  ".join(str(matrix[gt_sub].get(p, 0)).ljust(col_w) for p in pred_subs)
            print(f"    {gt_sub.ljust(col_w)}  {cells}  (n={row_total})")


def print_report(threshold, overall, per_class, fn_list, fp_list, confusion, show_details=False):
    _print_section(f"Threshold: ±{threshold} frames")

    print(f"\n  PER-CLASS BREAKDOWN:")
    header = f"  {'Label':<{_COL_LABEL}}  {'Prec':>8}  {'Rec':>8}  {'F1':>8}  {'TP':>6}  {'FP':>6}  {'FN':>6}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    print(f"  {'OVERALL':<{_COL_LABEL}}  {_fmt(overall['precision']):>8}  {_fmt(overall['recall']):>8}  {_fmt(overall['f1']):>8}  {overall['tp']:>6}  {overall['fp']:>6}  {overall['fn']:>6}")
    print("  " + "-" * (len(header) - 2))
    for label, m in per_class.items():
        _print_metrics_row(label, m, indent=2)

    if show_details:
        _print_detail_list(fn_list, "Missing from Company (GT not matched — False Negatives)")
        _print_detail_list(fp_list, "Extra from Company (not in GT — False Positives)")
    else:
        print(f"\n  Missing from Company (FN): {len(fn_list)}  |  Extra from Company (FP): {len(fp_list)}  (use --details to print full lists)")

    print_subtype_confusion(confusion)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate company annotations against ground truth.")
    parser.add_argument(
        "--details",
        action="store_true",
        help="Print the full list of missing (FN) and extra (FP) annotations for each threshold/mode.",
    )
    args = parser.parse_args()

    gt = load_annotations(Path(GT_PATH))
    pred = load_annotations(Path(COMPANY_PATH))

    print(f"\nGround truth annotations : {len(gt)}")
    print(f"Company annotations      : {len(pred)}")

    for threshold in THRESHOLDS:
        tp_pairs, fn_list, fp_list = match_annotations(gt, pred, threshold, "label")
        overall = compute_metrics(len(tp_pairs), len(fp_list), len(fn_list))
        per_class = compute_per_class_metrics(tp_pairs, fn_list, fp_list)
        confusion = compute_subtype_confusion(tp_pairs)
        print_report(threshold, overall, per_class, fn_list, fp_list, confusion, show_details=args.details)

    print()


if __name__ == "__main__":
    main()
