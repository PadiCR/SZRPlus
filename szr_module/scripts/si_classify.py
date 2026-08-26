# -*- coding: utf-8 -*-
"""
Shared Susceptibility Index classification helpers.

The raster Classify SI tools and their vector counterparts pick the same
optimal point on the ROC curve and derive the same class edges from it. Keeping
that arithmetic in one place is what makes the two modes agree - the earlier
divergence between the raster and vector Weight-of-Evidence implementations is
exactly what happens when the same method is written twice.

Nothing here touches QGIS or GDAL, so it can be called from a worker thread.
"""

import csv

import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Class names
# ─────────────────────────────────────────────────────────────────────────────
# Susceptibility maps are conventionally read as a small ordered set of named
# levels. Two, three and five classes have standard names; anything else falls
# back to generic labels.

DESCRIPTIVE_CLASS_NAMES = {
    2: ('Low', 'High'),
    3: ('Low', 'Moderate', 'High'),
    5: ('Very Low', 'Low', 'Moderate', 'High', 'Very High'),
}


def class_names(n_classes):
    """{class value: label} for `n_classes`, named where a convention exists."""
    names = DESCRIPTIVE_CLASS_NAMES.get(n_classes)
    if names:
        return {i + 1: names[i] for i in range(n_classes)}
    return {i: f'Class {i}' for i in range(1, n_classes + 1)}


# ─────────────────────────────────────────────────────────────────────────────
# Optimal ROC threshold
# ─────────────────────────────────────────────────────────────────────────────
# Each method answers "which SI value best separates landslide from
# non-landslide?" with a different definition of "best":
#   closest_point - the ROC point nearest the perfect corner (0,1)
#   f1            - the point maximising the harmonic mean of precision/recall
#   csi           - the point maximising the Critical Success Index, which
#                   ignores true negatives and so suits rare events
#   youden        - the point furthest above the diagonal, i.e. max TPR - FPR
#
# Note that f1 and csi ALWAYS agree: F1 = 2*CSI/(1+CSI) is strictly increasing,
# so maximising one maximises the other. They are kept as separate entries
# because the literature cites them separately, but they cannot disagree.

METHOD_LABELS = {
    'closest_point': 'ClosestPoint',
    'f1': 'F1Score',
    'csi': 'ThreatScore_CSI',
    'youden': 'YoudenJ',
}


def optimal_threshold(y_true, y_scores, method):
    """The SI value that optimises `method` on the ROC curve of these scores."""
    from sklearn.metrics import roc_curve

    if method not in METHOD_LABELS:
        raise ValueError(f'unknown threshold method: {method}')

    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    y_true = np.asarray(y_true)
    P = float(np.sum(y_true == 1))
    N = float(np.sum(y_true == 0))
    tp = tpr * P
    fp = fpr * N
    fn = P - tp

    if method == 'closest_point':
        best = int(np.argmin(np.sqrt((1 - tpr) ** 2 + fpr ** 2)))
    elif method == 'f1':
        denom = 2 * tp + fp + fn
        best = int(np.argmax(np.where(denom > 0, 2 * tp / denom, 0)))
    elif method == 'csi':
        denom = tp + fp + fn
        best = int(np.argmax(np.where(denom > 0, tp / denom, 0)))
    else:   # 'youden'
        best = int(np.argmax(tpr - fpr))

    # roc_curve prepends an artificial "predict nothing positive" point whose
    # threshold is +inf. Every metric here scores 0 there so it never wins, but
    # an inf slipping through would make every class edge inf and silently drop
    # the whole map into class 1.
    chosen = float(thresholds[best])
    if not np.isfinite(chosen):
        chosen = float(np.nanmax(y_scores))
    return chosen


BREAK_MODES = ('equal', 'quantile')


def cutoff_edges(y_scores, threshold, n_classes, break_mode='equal'):
    """Class edges: `n_classes - 1` classes below `threshold`, then the top one.

    Returns `n_classes + 1` values, so edges[i]..edges[i+1] bounds class i+1.
    The top class always starts at the optimal threshold - that is the boundary
    the ROC analysis actually chose. `break_mode` only decides how the range
    below it is divided:

      'equal'    - equal-width intervals. Simple, but WoE and FR produce very
                   skewed SI, so the classes end up wildly uneven in area.
      'quantile' - equal-count intervals, so each lower class holds roughly the
                   same number of units. Better for area statistics and for
                   skewed SI, at the cost of uneven SI widths.
    """
    if break_mode not in BREAK_MODES:
        raise ValueError(f'unknown break mode: {break_mode}')

    scores = np.asarray(y_scores, dtype=float)
    si_min = float(np.nanmin(scores))
    si_max = float(np.nanmax(scores))
    if n_classes <= 1:
        return [si_min, si_max + 1]

    if break_mode == 'equal':
        lower = np.linspace(si_min, threshold, num=n_classes)
        return [float(v) for v in np.append(lower, si_max + 1)]

    # Quantiles of the units that actually fall below the threshold. With none
    # there (threshold at or below the minimum) there is nothing to divide, so
    # fall back rather than emit degenerate edges.
    below = scores[np.isfinite(scores) & (scores < threshold)]
    if below.size == 0 or n_classes == 2:
        if below.size == 0:
            return cutoff_edges(scores, threshold, n_classes, 'equal')
        return [si_min, float(threshold), si_max + 1]

    qs = np.linspace(0.0, 1.0, n_classes)[1:-1]     # n_classes - 2 interior
    interior = [float(v) for v in np.quantile(below, qs)]
    edges = [si_min] + interior + [float(threshold), si_max + 1]
    # Ties in the data can make two quantiles equal; keep the list sorted so
    # np.digitize still behaves (the affected class simply comes out empty).
    return sorted(edges)


def assign_classes(scores, edges):
    """Class value 1..n for each score, from `edges` as built above."""
    return np.digitize(np.asarray(scores, dtype=float), list(edges)[1:-1]) + 1


def classification_metrics(y_true, y_scores, threshold):
    """The confusion matrix and its usual derivatives at `threshold`.

    `threshold` is the lower bound of the top class, i.e. everything at or
    above it is what the map predicts as susceptible.
    """
    from sklearn.metrics import roc_auc_score

    y_true = np.asarray(y_true).astype(int)
    scores = np.asarray(y_scores, dtype=float)
    predicted = scores >= threshold

    tp = int(np.sum(predicted & (y_true == 1)))
    fp = int(np.sum(predicted & (y_true == 0)))
    fn = int(np.sum(~predicted & (y_true == 1)))
    tn = int(np.sum(~predicted & (y_true == 0)))

    def ratio(num, den):
        return float(num) / float(den) if den else float('nan')

    recall = ratio(tp, tp + fn)          # sensitivity / TPR
    fpr = ratio(fp, fp + tn)
    try:
        auc = float(roc_auc_score(y_true, scores))
    except ValueError:
        auc = float('nan')

    return {
        'SI Threshold': float(threshold),
        'True Positives': tp,
        'False Positives': fp,
        'False Negatives': fn,
        'True Negatives': tn,
        'Precision': ratio(tp, tp + fp),
        'Recall (Sensitivity, TPR)': recall,
        'Specificity (TNR)': ratio(tn, tn + fp),
        'False Positive Rate': fpr,
        'F1-Score': ratio(2 * tp, 2 * tp + fp + fn),
        'Threat Score (CSI)': ratio(tp, tp + fp + fn),
        "Youden's J": recall - fpr,
        'Accuracy': ratio(tp + tn, tp + fp + fn + tn),
        'AUC': auc,
    }


def write_metrics_csv(path, metrics):
    """One metric per row, so the file stays readable in any spreadsheet."""
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Metric', 'Value'])
        for key, value in metrics.items():
            writer.writerow([key, value])


def write_cutoffs_csv(path, edges):
    """Write the class table in the layout every Classify SI tool shares."""
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Class', 'Lower Bound', 'Upper Bound'])
        for i in range(len(edges) - 1):
            writer.writerow([i + 1, edges[i], edges[i + 1]])
