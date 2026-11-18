"""Extract site values from a georeferenced raster. Demo uses synthetic data in memory.

Run: python recipes/spatial.py --out results/spatial
Requires numpy and rasterio. No internet connection is needed to run the example.
"""
import argparse
import csv
from pathlib import Path

import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from rasterio.warp import transform


def extract_sites(dataset, sites):
    """Sample a single raster band at WGS84 sites and preserve all input records."""
    longitudes = [site[1] for site in sites]
    latitudes = [site[2] for site in sites]
    xs, ys = transform("EPSG:4326", dataset.crs, longitudes, latitudes)
    for (site, longitude, latitude), x, y in zip(sites, xs, ys):
        row, column = dataset.index(x, y)
        status, value = "outside_extent", ""
        if 0 <= row < dataset.height and 0 <= column < dataset.width:
            sample = next(dataset.sample([(x, y)], indexes=1, masked=True))[0]
            if np.ma.is_masked(sample):
                status = "no_data"
            else:
                status, value = "ok", float(sample)
        yield {
            "site_id": site, "longitude": longitude, "latitude": latitude,
            "raster_crs": dataset.crs.to_string(), "coverage": status,
            "raster_value": value,
        }


def demo_records():
    sites = [
        ("west", -0.01, 0.01),
        ("east", 0.01, 0.01),
        ("masked", 0.004, -0.004),
        ("distant", 1.0, 1.0),
    ]
    # North-up 4 x 3 grid in metres. The lower-right interior cell has no pH data.
    grid = np.array(
        [[5.1, 5.2, 5.3, 5.4], [5.5, 5.6, 5.7, 5.8], [5.9, 6.0, -9999, 6.2]],
        dtype="float64",
    )
    with MemoryFile() as mem:
        with mem.open(driver="GTiff", height=grid.shape[0], width=grid.shape[1],
                      count=1, dtype=grid.dtype, crs="EPSG:3857",
                      transform=from_origin(-2000, 2000, 1000, 1000),
                      nodata=-9999) as dataset:
            dataset.write(grid, 1)
            records = list(extract_sites(dataset, sites))
    if [record["coverage"] for record in records] != ["ok", "ok", "no_data", "outside_extent"]:
        raise RuntimeError("Unexpected coverage codes for the synthetic sites")
    if not np.allclose([record["raster_value"] for record in records[:2]], [5.1, 5.4]):
        raise RuntimeError("Unexpected sampled cells after coordinate transformation")
    return records


def read_sites(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        table = csv.DictReader(stream)
        if not {"site_id", "longitude", "latitude"} <= set(table.fieldnames or ()):
            raise ValueError("Sites CSV requires site_id, longitude and latitude.")
        sites = []
        used = set()
        for row in table:
            name = (row["site_id"] or "").strip()
            if not name or name in used:
                raise ValueError("Each site needs a distinct, nonempty site_id.")
            lng, lat = float(row["longitude"]), float(row["latitude"])
            if not (-180 <= lng <= 180 and -90 <= lat <= 90):
                raise ValueError(f"Invalid WGS84 coordinates for {name}.")
            used.add(name)
            sites.append((name, lng, lat))
        if not sites:
            raise ValueError("Sites CSV is empty.")
        return sites


def main(output_dir, sites_path, raster_path):
    if sites_path:
        sites = read_sites(sites_path)
        with rasterio.open(raster_path) as dataset:
            if not dataset.crs:
                raise ValueError("The raster needs a coordinate reference system.")
            records = list(extract_sites(dataset, sites))
    else:
        records = demo_records()
    output_dir.mkdir(exist_ok=True, parents=True)
    path = output_dir / "site_covariates.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {len(records)} sites to {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path,
                        default=Path("results/spatial"), help="Directory for the site table")
    parser.add_argument("--sites", type=Path, help="CSV containing site_id, longitude and latitude in WGS84.")
    parser.add_argument("--raster", type=Path, help="Georeferenced raster (band 1).")
    args = parser.parse_args()
    if bool(args.sites) != bool(args.raster):
        parser.error("--sites and --raster must be supplied together.")
    main(args.out, args.sites, args.raster)
