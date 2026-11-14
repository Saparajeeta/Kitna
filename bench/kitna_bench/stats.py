"""Statistics, all through scipy / statsmodels / numpy. See docs/analysis_plan.md."""
from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np


def wilson(successes: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson score interval for a proportion; (nan, nan) when n is 0."""
    if n == 0:
        return (math.nan, math.nan)
    from statsmodels.stats.proportion import proportion_confint

    lo, hi = proportion_confint(successes, n, alpha=alpha, method="wilson")
    return (float(lo), float(hi))


def mcnemar_exact(a: Sequence[bool], b: Sequence[bool]) -> dict[str, Any]:
    """Exact (binomial) McNemar test on paired outcomes. b01: a wrong, b right. b10: a right, b wrong."""
    if len(a) != len(b):
        raise ValueError("paired samples must have the same length")
    from statsmodels.stats.contingency_tables import mcnemar

    n11 = sum(x and y for x, y in zip(a, b, strict=True))
    n10 = sum(x and not y for x, y in zip(a, b, strict=True))
    n01 = sum((not x) and y for x, y in zip(a, b, strict=True))
    n00 = len(a) - n11 - n10 - n01
    p = float(mcnemar([[n11, n10], [n01, n00]], exact=True).pvalue) if (n10 + n01) else 1.0
    return {"n_pairs": len(a), "both_right": n11, "only_first_right": n10, "only_second_right": n01,
            "both_wrong": n00, "p_value": p}


def paired_bootstrap_diff(a: Sequence[bool], b: Sequence[bool], *, n_boot: int = 10000, seed: int = 20261112,
                          alpha: float = 0.05) -> dict[str, float]:
    """Mean(a) - mean(b) with a percentile bootstrap interval, resampling pairs."""
    if len(a) != len(b):
        raise ValueError("paired samples must have the same length")
    if not a:
        return {"diff": math.nan, "ci_low": math.nan, "ci_high": math.nan}
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(d), size=(n_boot, len(d)))
    means = d[idx].mean(axis=1)
    lo, hi = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return {"diff": float(d.mean()), "ci_low": float(lo), "ci_high": float(hi)}


def holm(p_values: Sequence[float], alpha: float = 0.05) -> list[dict[str, Any]]:
    """Holm-Bonferroni adjusted p-values, in the input order."""
    if not p_values:
        return []
    from statsmodels.stats.multitest import multipletests

    reject, adjusted, _, _ = multipletests(list(p_values), alpha=alpha, method="holm")
    return [{"p_holm": float(p), "reject": bool(r)} for p, r in zip(adjusted, reject, strict=True)]


def cohen_kappa(labels_a: Sequence[str], labels_b: Sequence[str]) -> dict[str, Any]:
    """Cohen's kappa for two annotators over nominal labels, with percent agreement.

    kappa is None when it is undefined (no items, or both annotators used one single category).
    """
    if len(labels_a) != len(labels_b):
        raise ValueError("both annotators must label the same units")
    n = len(labels_a)
    if n == 0:
        return {"n": 0, "percent_agreement": None, "kappa": None, "ci_low": None, "ci_high": None}
    agree = sum(x == y for x, y in zip(labels_a, labels_b, strict=True)) / n
    cats = sorted(set(labels_a) | set(labels_b))
    if len(cats) < 2:
        return {"n": n, "percent_agreement": agree, "kappa": None, "ci_low": None, "ci_high": None}
    from statsmodels.stats.inter_rater import cohens_kappa

    index = {c: i for i, c in enumerate(cats)}
    table = np.zeros((len(cats), len(cats)))
    for x, y in zip(labels_a, labels_b, strict=True):
        table[index[x], index[y]] += 1
    with np.errstate(invalid="ignore", divide="ignore"):    # perfect agreement makes the variance term 0/0
        res = cohens_kappa(table)
    k = float(res.kappa)
    if math.isnan(k):
        return {"n": n, "percent_agreement": agree, "kappa": None, "ci_low": None, "ci_high": None}
    return {"n": n, "percent_agreement": agree, "kappa": k, "ci_low": float(res.kappa_low),
            "ci_high": float(res.kappa_upp)}
