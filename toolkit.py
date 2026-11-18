#!/usr/bin/env python3
"""Search the ecology tool directory or run one of its worked examples."""
import argparse
import csv
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SUBJECTS = ("microbiome", "models", "ecology")
WORKFLOWS = {
    "count-table": ("count_table.py", "Describe ASV diversity and plot Bray–Curtis distances."),
    "community": ("community.R", "Compare independent habitats using vegan."),
    "path-analysis": ("path_analysis.R", "Fit direct and indirect ecological paths using lavaan."),
    "boosted-trees": ("boosted_trees.py", "Predict respiration in held-out sites using XGBoost."),
    "spatial": ("spatial.py", "Extract a raster covariate at georeferenced sites."),
    "meta-analysis": ("meta_analysis.py", "Pool effects from independent studies."),
}
ALIASES = {
    "结构方程": "structural equation", "sem": "structural equation", "差异丰度": "differential abundance",
    "多样性": "diversity", "群落组装": "community assembly", "随机森林": "forest",
    "系统发育": "phylogen", "空间": "spatial", "网络": "network", "元分析": "meta-analysis",
    "荟萃分析": "meta-analysis", "栅格": "raster", "机器学习": "learning", "遥感": "remote sensing",
}


def search(words, subject):
    terms = [ALIASES.get(w.casefold(), w.casefold()) for w in words]
    hits = 0
    for name in ([subject] if subject else SUBJECTS):
        with (ROOT / "catalog" / (name + ".tsv")).open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream, delimiter="\t"):
                description = " ".join([name, *(v for k, v in row.items() if k != "source_url")]).casefold()
                if all(term in description for term in terms):
                    print(f"{row['tool']} | {row['task']} | {row['ecosystem']}")
                    print(f"  {row['when_to_use']}\n  {row['source_url']}")
                    hits += 1
    print(f"{hits} matching entries.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    find = sub.add_parser("find", help="Search curated tools and data resources.")
    find.add_argument("words", nargs="*", help="Case-insensitive keywords (all must match).")
    find.add_argument("--subject", choices=SUBJECTS)
    sub.add_parser("recipes", help="List the runnable workflows.")
    run = sub.add_parser("run", help="Run a workflow on example or user-supplied inputs.")
    workflows = run.add_subparsers(dest="name", required=True)
    for name, (_, description) in WORKFLOWS.items():
        command = workflows.add_parser(name, help=description, description=description)
        command.add_argument("--out", type=Path, required=True, help="New or empty output directory.")
        if name == "community":
            command.add_argument("--counts", type=Path, help="Wide TSV starting with sample_id.")
            command.add_argument("--metadata", type=Path, help="TSV with sample_id and habitat.")
        elif name == "spatial":
            command.add_argument("--sites", type=Path, help="CSV with site_id, longitude, latitude (WGS84).")
            command.add_argument("--raster", type=Path, help="Georeferenced raster with a valid band 1.")
        else:
            command.add_argument("--input", type=Path, help="Optional user dataset. See README for schema.")
    args = parser.parse_args()
    if args.action == "find":
        return search(args.words, args.subject)
    if args.action == "recipes":
        for name, (_, description) in WORKFLOWS.items():
            print(f"{name:15} {description}")
        return 0

    if args.out.exists() and (not args.out.is_dir() or any(args.out.iterdir())):
        parser.error("Choose a new or empty output directory.")
    filename = WORKFLOWS[args.name][0]
    script = str(ROOT / "recipes" / filename)
    if filename.endswith(".R"):
        rscript = shutil.which(os.environ.get("RSCRIPT", "Rscript"))
        if not rscript:
            parser.error("Install R and put Rscript on PATH, or set RSCRIPT to its executable.")
        cmd = [rscript, script, str(args.out)]
        if args.name == "community":
            if bool(args.counts) != bool(args.metadata):
                parser.error("--counts and --metadata must be supplied together.")
            if args.counts:
                cmd.extend([str(args.counts), str(args.metadata)])
        elif args.input:
            cmd.append(str(args.input))
    else:
        cmd = [sys.executable, script, "--out", str(args.out)]
        if args.name == "spatial":
            if bool(args.sites) != bool(args.raster):
                parser.error("--sites and --raster must be supplied together.")
            if args.sites:
                cmd.extend(["--sites", str(args.sites), "--raster", str(args.raster)])
        elif args.input:
            cmd.extend(["--input", str(args.input)])
    return subprocess.run(cmd, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
