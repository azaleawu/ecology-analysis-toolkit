#!/usr/bin/env python3
"""Predict an ecological response on held-out sites with a CPU XGBoost model.

python recipes/boosted_trees.py [--out output_dir] [--input field.csv]
Input columns: site_id, moisture_pct, temperature_c, carbon_pct, respiration.
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
import xgboost as xgb

FEATURES = ["moisture_pct", "temperature_c", "carbon_pct"]
TARGET = "respiration"
SEED = 41


def simulate():
    rng = np.random.default_rng(SEED)
    rows = []
    for site in range(40):
        site_moisture = rng.uniform(10, 40)
        site_temperature = rng.uniform(3, 18)
        site_carbon = rng.uniform(1, 6)
        random_effect = rng.normal(0, 0.3)
        for _ in range(5):
            moisture = site_moisture + rng.normal(0, 2)
            temp = site_temperature + rng.normal(0, 1)
            carbon = max(0.1, site_carbon + rng.normal(0, 0.4))
            respiration = (6 - 0.015 * (moisture - 27) ** 2 + 0.2 * temp
                           + 0.5 * np.log1p(carbon) + random_effect + rng.normal(0, 0.4))
            rows.append(dict(site_id=f"site_{site:02}", moisture_pct=moisture,
                             temperature_c=temp, carbon_pct=carbon, respiration=respiration))
    return rows


def save_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("outputs/boosted_trees"))
    parser.add_argument("--input", type=Path, help="use a CSV in place of the synthetic demo")
    args = parser.parse_args()
    if args.input:
        with args.input.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            missing = {"site_id", *FEATURES, TARGET}.difference(reader.fieldnames or [])
            if missing:
                parser.error("missing columns: " + ", ".join(sorted(missing)))
            rows = list(reader)
    else:
        rows = simulate()

    sites = np.array([str(row["site_id"] or "").strip() for row in rows])
    if not len(sites) or np.any(sites == ""):
        parser.error("each observation requires a nonempty site_id")
    unique_sites = np.unique(sites)
    if len(unique_sites) < 3:
        parser.error("use at least three distinct sites to fit and assess a site split")
    predictors = np.array([[float(row[feature]) for feature in FEATURES] for row in rows])
    response = np.array([float(row[TARGET]) for row in rows])
    if not np.isfinite(predictors).all() or not np.isfinite(response).all():
        parser.error("this example expects finite predictors and responses")

    rng = np.random.default_rng(SEED)
    held_out = rng.choice(unique_sites, size=int(np.ceil(0.2 * len(unique_sites))), replace=False)
    test = np.isin(sites, held_out)
    train = ~test
    train_data = xgb.DMatrix(predictors[train], label=response[train], feature_names=FEATURES)
    test_data = xgb.DMatrix(predictors[test], feature_names=FEATURES)
    params = {"objective": "reg:squarederror", "tree_method": "hist", "max_depth": 3,
              "eta": 0.06, "seed": SEED, "nthread": 1}
    model = xgb.train(params, train_data, num_boost_round=90)
    predictions = model.predict(test_data)
    train_mean = float(response[train].mean())
    rmse = float(np.sqrt(np.mean((predictions - response[test]) ** 2)))
    baseline = float(np.sqrt(np.mean((train_mean - response[test]) ** 2)))
    # Global split-level RMSE weights each observation equally.
    summary = {"input": str(args.input) if args.input else "synthetic", "seed": SEED,
               "n_training_sites": int(len(unique_sites) - len(held_out)),
               "n_test_sites": len(held_out), "n_train": int(train.sum()), "n_test": int(test.sum()),
               "rmse": rmse, "training_mean_baseline_rmse": baseline, "xgboost_version": xgb.__version__}

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "metrics.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    save_csv(args.out / "site_split.csv", ["site_id", "split"],
             ({"site_id": site, "split": "test" if site in held_out else "train"} for site in unique_sites))
    save_csv(args.out / "held_out_predictions.csv", ["site_id", "observed", "predicted"],
             (dict(site_id=s, observed=y, predicted=float(p)) for s, y, p in zip(sites[test], response[test], predictions)))
    model.save_model(args.out / "model.json")
    print(f"RMSE {rmse:.3f}; training-mean baseline {baseline:.3f}; {len(held_out)} held-out sites.")


if __name__ == "__main__":
    main()
