"""Summarize one compatible library-by-ASV count table and plot community distances."""
import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial.distance import pdist, squareform


def read_counts(path):
    data = defaultdict(Counter)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = csv.DictReader(handle, delimiter="\t")
        fields = {"library_id", "asv_id", "count"}
        if not fields <= set(rows.fieldnames or ()):
            raise ValueError("Expected TSV columns library_id, asv_id and count.")
        for line, row in enumerate(rows, 2):
            lib, asv = row["library_id"], row["asv_id"]
            try:
                count = int(row["count"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Line {line}: invalid integer count.") from exc
            if not lib or not asv or count < 0 or asv in data[lib]:
                raise ValueError(f"Line {line}: missing ID, negative count or duplicate library/ASV pair.")
            data[lib][asv] = count
    if len(data) < 2 or any(sum(counts.values()) == 0 for counts in data.values()):
        raise ValueError("Select at least two positive-depth libraries from the same assay.")
    return data


def fit(path, out):
    data = read_counts(path)
    ids = sorted(data)
    features = sorted(set().union(*(set(counts) for counts in data.values())))
    if len(ids) > 1000 or len(ids) * len(features) > 10_000_000:
        raise ValueError("Subset libraries first. This exploratory recipe uses dense matrices.")
    matrix = np.array([[data[lib][asv] for asv in features] for lib in ids])
    totals = matrix.sum(axis=1)
    rel = matrix / totals[:, None]
    distances = squareform(pdist(rel, metric="braycurtis"))
    out.mkdir(parents=True, exist_ok=True)
    with (out / "alpha.tsv").open("w", newline="") as handle:
        rows = csv.writer(handle, delimiter="\t", lineterminator="\n")
        rows.writerow(["library_id", "reads", "observed_asvs", "shannon_ln"])
        for name, total, frequencies in zip(ids, totals, rel):
            p = frequencies[frequencies > 0]
            rows.writerow([name, total, len(p), f"{-np.dot(p,np.log(p)):.7f}"])
    with (out / "bray_curtis.tsv").open("w", newline="") as handle:
        rows = csv.writer(handle, delimiter="\t", lineterminator="\n")
        rows.writerow(["library_a", "library_b", "bray_curtis_relative_abundance"])
        for i, a in enumerate(ids):
            for j in range(i):
                rows.writerow([ids[j], a, f"{distances[i, j]:.7f}"])
    if len(ids) <= 30:
        side = max(4.3, len(ids) * 0.33)
        fig, ax = plt.subplots(figsize=(side+1.3, side), layout="constrained")
        layer = ax.imshow(distances, vmin=0, vmax=1, cmap="YlGnBu")
        ax.set_xticks(range(len(ids)), labels=ids, rotation=45, ha="right")
        ax.set_yticks(range(len(ids)), labels=ids)
        ax.tick_params(length=0, labelsize=9)
        for spine in ax.spines.values():
            spine.set_visible(False)
        if len(ids) <= 8:
            for i in range(len(ids)):
                for j in range(len(ids)):
                    x = distances[i,j]
                    ax.text(j, i, f"{x:.2f}", ha="center", va="center", color="white" if x > 0.6 else "#112b32")
        fig.colorbar(layer, ax=ax, shrink=0.75, label="Bray–Curtis dissimilarity")
        fig.savefig(out / "bray_curtis.png", dpi=170)
        plt.close(fig)
    print(f"{len(ids)} libraries, {len(features)} feature IDs, {int(totals.sum())} reads.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, default=Path(__file__).resolve().parents[1]/"data"/"atacama_counts.tsv")
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    fit(a.input, a.out)
