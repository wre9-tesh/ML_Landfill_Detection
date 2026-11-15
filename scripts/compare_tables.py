"""Compare two feature tables point by point, to check a refetch against the committed table.

    python scripts/compare_tables.py data/features/features.csv rep/features/features.csv

Rows are matched by point_id. For every numeric column the two files share, prints how many
points have a value in both, how many differ by more than --tol, and the largest difference.
Earth Engine archives are sometimes reprocessed, so small differences in a few points are
possible; a column that differs in most points means a setting is not the same.
"""
import argparse
import sys

import numpy as np
import pandas as pd


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reference")
    ap.add_argument("yours")
    ap.add_argument("--key", default="point_id")
    ap.add_argument("--tol", type=float, default=1e-6)
    args = ap.parse_args()
    a, b = pd.read_csv(args.reference).set_index(args.key), pd.read_csv(args.yours).set_index(args.key)
    both = a.index.intersection(b.index)
    print(f"reference {len(a)} rows, yours {len(b)} rows, {len(both)} in both")
    a, b = a.loc[both], b.loc[both]
    skip = {"lon", "lat", "label", "fetched"}
    cols = [c for c in a.columns if c in b.columns and c not in skip and pd.api.types.is_numeric_dtype(a[c])]
    worst = 0.0
    print(f"{'column':10} {'in both':>8} {'differ':>8} {'largest difference':>20} {'empty in one only':>18}")
    for c in cols:
        x, y = a[c].to_numpy(float), b[c].to_numpy(float)
        ok = np.isfinite(x) & np.isfinite(y)
        d = np.abs(x[ok] - y[ok])
        one = int((np.isfinite(x) != np.isfinite(y)).sum())
        worst = max(worst, float(d.max()) if len(d) else 0.0)
        print(f"{c:10} {int(ok.sum()):8d} {int((d > args.tol).sum()):8d} {float(d.max()) if len(d) else 0:20.6g} {one:18d}")
    print("identical within tolerance" if worst <= args.tol else f"largest difference anywhere: {worst:.6g}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
