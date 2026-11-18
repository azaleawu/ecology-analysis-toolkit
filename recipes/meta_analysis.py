#!/usr/bin/env python3
"""Random-effects meta-analysis of independent studies on a common effect scale.

python recipes/meta_analysis.py --out outputs/meta_analysis [--input effects.csv]
Input CSV: study_id,effect,variance (one effect and its sampling variance per
independent study, with a common contrast direction). The synthetic example uses
log response ratios of soil respiration under warming versus control conditions.
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.stats import chi2, t
import statsmodels
from statsmodels.stats.meta_analysis import combine_effects


def demo():
    rng = np.random.default_rng(41)
    se = np.linspace(0.055, 0.15, 12)
    true_effect = rng.normal(0.16, 0.12, len(se))
    observed = true_effect + rng.normal(0, se)
    return [dict(study_id=f"study_{i + 1:02d}", effect=y, variance=s**2)
            for i, (y, s) in enumerate(zip(observed, se))]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("outputs/meta_analysis"))
    parser.add_argument("--input", type=Path, help="CSV with independent study-level effects")
    args = parser.parse_args()
    if args.input:
        with args.input.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            required = {"study_id", "effect", "variance"}
            if not required.issubset(reader.fieldnames or []):
                parser.error("required CSV columns: study_id,effect,variance")
            rows = list(reader)
    else:
        rows = demo()

    ids = [str(row["study_id"] or "").strip() for row in rows]
    if len(ids) < 2 or not all(ids) or len(set(ids)) != len(ids):
        parser.error("provide at least two distinct, nonempty study IDs with one effect each")
    try:
        effects = np.array([float(row["effect"]) for row in rows])
        variances = np.array([float(row["variance"]) for row in rows])
    except (TypeError, ValueError):
        parser.error("every effect and sampling variance must be numeric")
    if not np.isfinite(effects).all() or not np.isfinite(variances).all() or (variances <= 0).any():
        parser.error("effects must be finite and sampling variances finite and positive")

    # Centering preserves effect differences and improves numerical stability.
    center = float(effects.mean())
    centered = effects - center
    with np.errstate(divide="ignore", invalid="ignore"):  # library also computes untruncated I² at Q=0
        fit = combine_effects(centered, variances, method_re="iterated", maxiter=200)
    tau2 = float(fit.tau2)
    weights = 1.0 / (variances + tau2)
    estimate = float(fit.mean_effect_re + center)
    df = len(effects) - 1
    residual_scale = float(np.sum(weights * (effects - estimate) ** 2) / df)
    # Modified Knapp–Hartung: use a t critical value and floor the scale at 1.
    se = np.sqrt(max(1.0, residual_scale) / weights.sum())
    half_width = float(t.ppf(0.975, df) * se)
    fixed_mean = np.average(centered, weights=1.0 / variances)
    q = float(np.sum((centered - fixed_mean) ** 2 / variances))
    i2 = max(0.0, 1.0 - df / q) if q > 0 else 0.0
    summary = {
        "input": str(args.input) if args.input else "synthetic log response ratios",
        "k_independent_studies": len(effects), "pooled_mean_effect": estimate,
        "ci95_lower": estimate - half_width, "ci95_upper": estimate + half_width,
        "interval_method": "modified Knapp-Hartung, residual scale floored at 1",
        "df": df, "tau2_paule_mandel": tau2, "cochran_Q": q,
        "Q_pvalue": float(chi2.sf(q, df)), "I2_Q_based_percent": 100 * i2,
        "statsmodels_version": statsmodels.__version__,
    }

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n",
                                           encoding="utf-8")
    with (args.out / "studies.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["study_id", "effect", "variance", "random_effects_weight_fraction"])
        writer.writerows(zip(ids, effects, variances, weights / weights.sum()))
    print(f"{len(effects)} studies; pooled {estimate:.4f} "
          f"(95% CI {estimate - half_width:.4f} to {estimate + half_width:.4f}), tau² {tau2:.4f}.")


if __name__ == "__main__":
    main()
