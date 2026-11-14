"""Depth analysis, run after the freeze and the Gujarat scoring. Selects nothing.

    python scripts/depth_analysis.py

Reads data/features/features.csv, data/results/ and data/gujarat_results/ (score maps included)
and the sealed list. Writes data/analysis/*.csv and data/analysis/depth_analysis.md:
  split_ablation.csv         every model's F1 under random pixel, held-out site and held-out region,
                             and the frozen model's pixel-level numbers on Gujarat
  feature_ablation.csv       the frozen model retrained on feature sets A0 to A5, held-out region
  precision_prevalence.csv   precision implied by the measured hit and false-alarm rates
  threshold_sensitivity.csv  Gujarat sites found and land flagged at other thresholds (post hoc)
  failure_audit_*.csv        held-out false alarms by look-alike class, by region and by state;
                             Gujarat flagged share by city
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support

from geoutil import REPO, ZONAL_COUNCILS
from run_models import FEATURES, fit, headline_folds, make_models

SETS = {
    "A0 all twelve": FEATURES,
    "A1 NDVI, NDBI, LST": ["NDVI", "NDBI", "LST"],
    "A2 A1 + BSI": ["NDVI", "NDBI", "BSI", "LST"],
    "A3 original ten (no BSI, B2)": [f for f in FEATURES if f not in ("BSI", "B2")],
    "A4 no thermal": [f for f in FEATURES if f not in ("LST", "LST_anom")],
    "A5 no terrain": [f for f in FEATURES if f not in ("elev", "slope")],
}
PREVALENCES = [0.5, 0.1, 0.01, 0.001, 0.0001]
THRESHOLDS = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


def precision_at(tpr, fpr, prev):
    hit, false = tpr * prev, fpr * (1 - prev)
    return hit / (hit + false) if hit + false else float("nan")


def md_table(df, fmt=None):
    fmt = fmt or {}
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            cells.append("" if isinstance(v, float) and np.isnan(v) else
                         fmt[c].format(v) if c in fmt else f"{v:.3f}" if isinstance(v, float) else str(v))
        out.append("| " + " | ".join(cells) + " |")
    return out


def gujarat_pixels(res, sites_path, thresholds):
    """Per threshold: pixel counts in and outside the sealed outlines, and per-site flagged share."""
    import rasterio
    from rasterio.features import geometry_mask
    from rasterio.warp import transform_geom

    sites = [f for f in json.load(open(sites_path, encoding="utf-8"))["features"]
             if f["geometry"]["type"] != "Point"]
    recall = pd.read_csv(res / "site_recall.csv")
    box_of = dict(zip(recall["test_id"], recall["box"]))
    tot = {t: {"in_flag": 0, "out_flag": 0} for t in thresholds}
    n_in = n_out = 0
    share = {t: {} for t in thresholds}
    done = []
    for tif in sorted((res / "scores").glob("gujarat_*.tif")):
        city = tif.stem.replace("gujarat_", "")
        with rasterio.open(tif) as src:
            s, tr, crs = src.read(1), src.transform, src.crs
        h, w = s.shape
        xs, ys = tr.c + tr.a * (np.arange(w) + 0.5), tr.f + tr.e * (np.arange(h) + 0.5)
        fresh = np.ones((h, w), bool)
        for l, b, r, t in done:
            fresh[np.ix_((ys > b) & (ys < t), (xs > l) & (xs < r))] = False
        done.append((tr.c, tr.f + tr.e * h, tr.c + tr.a * w, tr.f))
        valid = s != 255
        in_site = np.zeros((h, w), bool)
        masks = {}
        for f in sites:
            m = geometry_mask([transform_geom("EPSG:4326", crs, f["geometry"])], (h, w), tr, invert=True)
            if m.any():
                in_site |= m
                if box_of.get(f["properties"]["test_id"]) == city:
                    masks[f["properties"]["test_id"]] = m & valid
        n_in += int((fresh & valid & in_site).sum())
        n_out += int((fresh & valid & ~in_site).sum())
        for t in thresholds:
            flag = valid & (s >= round(t * 100))
            tot[t]["in_flag"] += int((flag & fresh & in_site).sum())
            tot[t]["out_flag"] += int((flag & fresh & ~in_site).sum())
            for tid, m in masks.items():
                share[t][tid] = float((flag & m).sum() / max(m.sum(), 1))
    return n_in, n_out, tot, share


def main():
    out = REPO / "data" / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    res, gres = REPO / "data" / "results", REPO / "data" / "gujarat_results"
    model_meta = json.loads((res / "model.json").read_text(encoding="utf-8"))
    name, thr = model_meta["model"], model_meta["threshold"]
    df = pd.read_csv(REPO / "data" / "features" / "features.csv").dropna(subset=FEATURES).reset_index(drop=True)
    y = df["label"].to_numpy(int)
    unit, folds, _ = headline_folds(df, 10, 5)
    head = f"held_out_{unit}"
    md = ["# Depth analysis", "",
          f"Frozen model: `{name}`, threshold {thr}. Everything here is post hoc and selects nothing.", ""]

    # 1. Held-out rates of the frozen model, pooled over the rounds.
    oof = pd.read_csv(res / "oof_predictions.csv")
    flag = oof[name] >= thr
    tpr_val = float(flag[oof["label"] == 1].mean())
    fpr_rand = float(flag[oof["kind"] == "random"].mean())
    fpr_all = float(flag[oof["label"] == 0].mean())

    # 2. Gujarat pixels at several thresholds (the frozen one included).
    n_in, n_out, tot, share = gujarat_pixels(gres, REPO / "labels" / "gujarat_test_sites.geojson", THRESHOLDS)
    # The maps store scores rounded to 0.01, so counts from them run about 2% high. At the frozen
    # threshold the exact counts from the scoring run are used instead.
    summ = json.loads((gres / "summary.json").read_text(encoding="utf-8"))
    exact_in = int(pd.read_csv(gres / "site_recall.csv")["pixels_flagged"].fillna(0).sum())
    g = {"in_flag": exact_in, "out_flag": summ["pixels_flagged"] - exact_in}
    tpr_g, fpr_g = g["in_flag"] / n_in, g["out_flag"] / n_out
    pos_share = float(y.mean())

    # Split ablation.
    s = pd.read_csv(res / "summary.csv")
    wide = s.pivot(index="model", columns="split", values="f1_mean").reindex(list(make_models()))
    wide = wide[["random_pixel", "held_out_site", head]].reset_index()
    wide["drop_pixel_to_" + unit] = wide["random_pixel"] - wide[head]
    wide.round(4).to_csv(out / "split_ablation.csv", index=False)
    sel = s[(s["model"] == name)].set_index("split")
    p_bal = precision_at(tpr_g, fpr_g, pos_share)
    rungs = pd.DataFrame([
        {"design": "random pixel", "precision": sel.loc["random_pixel", "precision_mean"],
         "recall": sel.loc["random_pixel", "recall_mean"], "f1": sel.loc["random_pixel", "f1_mean"]},
        {"design": "held-out site", "precision": sel.loc["held_out_site", "precision_mean"],
         "recall": sel.loc["held_out_site", "recall_mean"], "f1": sel.loc["held_out_site", "f1_mean"]},
        {"design": f"held-out {unit}", "precision": sel.loc[head, "precision_mean"],
         "recall": sel.loc[head, "recall_mean"], "f1": sel.loc[head, "f1_mean"]},
        {"design": "Gujarat pixels, at the validation class mix", "precision": p_bal, "recall": tpr_g,
         "f1": 2 * p_bal * tpr_g / (p_bal + tpr_g)},
        {"design": "Gujarat pixels, as they are", "precision": g["in_flag"] / (g["in_flag"] + g["out_flag"]),
         "recall": tpr_g, "f1": float("nan")},
    ])
    rungs.loc[4, "f1"] = 2 * rungs.loc[4, "precision"] * tpr_g / (rungs.loc[4, "precision"] + tpr_g)
    rungs.round(4).to_csv(out / "split_ablation_frozen_model.csv", index=False)
    md += ["## 1. Split ablation", "", "Mean F1 of every model under the three validation designs:", ""]
    md += md_table(wide) + [""]
    md += [f"The frozen model across all four designs. Gujarat is scored at pixel level: {n_in:,} scored pixels lie "
           f"inside the 17 sealed outlines and {n_out:,} outside. Recall is the share of outline pixels flagged "
           f"({tpr_g:.3f}); the false-alarm rate is the share of all other pixels flagged ({fpr_g:.4f}), which "
           f"counts any unlisted dump as a false alarm. \"At the validation class mix\" applies those two rates "
           f"to the {pos_share:.1%} landfill share of the validation points, so the row is comparable with the "
           f"three above; \"as they are\" uses the real mix, where outline pixels are "
           f"{n_in / (n_in + n_out):.4%} of the land. One difference remains: Gujarat counts every pixel of an "
           f"outline, edge pixels included, while validation points sit at least 15 m inside their outlines, "
           f"so part of the fall in recall is the edge.", ""]
    md += md_table(rungs, {"precision": "{:.4f}", "f1": "{:.4f}"}) + [""]
    md += [f"Site level, by the frozen rule: {summ['sites_found']} of {summ['sites_counted']} sites found "
           f"({summ['site_recall']:.1%}).", ""]

    # Feature ablation.
    rows = []
    for label, feats in SETS.items():
        X = df[feats].to_numpy(float)
        ps, rs, fs = [], [], []
        for test in folds.values():
            m = fit(name, make_models()[name], X[~test], y[~test])
            pred = m.predict_proba(X[test])[:, 1] >= thr
            p, r, f1, _ = precision_recall_fscore_support(y[test], pred, average="binary", zero_division=0)
            ps.append(p), rs.append(r), fs.append(f1)
        rows.append({"feature set": label, "features": len(feats), "precision": np.mean(ps), "recall": np.mean(rs),
                     "f1": np.mean(fs), "f1_sd": np.std(fs, ddof=1), "f1_min_fold": np.min(fs)})
    fa = pd.DataFrame(rows)
    fa["f1_change_vs_A0"] = fa["f1"] - fa.loc[0, "f1"]
    fa.round(4).to_csv(out / "feature_ablation.csv", index=False)
    md += ["## 2. Feature ablation", "",
           f"`{name}` retrained with the same settings on each feature set, {head.replace('_', ' ')} folds:", ""]
    md += md_table(fa, {"f1_change_vs_A0": "{:+.3f}"}) + [""]

    # Precision against prevalence.
    rows = []
    for prev in PREVALENCES:
        n = 1_000_000
        rows.append({"landfill share": f"1 in {round(1 / prev):,}",
                     "true alarms per million px (validation rates)": round(tpr_val * prev * n),
                     "false alarms per million px (validation rates)": round(fpr_rand * (1 - prev) * n),
                     "precision (validation rates)": precision_at(tpr_val, fpr_rand, prev),
                     "precision (Gujarat rates)": precision_at(tpr_g, fpr_g, prev)})
    pp = pd.DataFrame(rows)
    pp.to_csv(out / "precision_prevalence.csv", index=False)
    md += ["## 3. Precision against prevalence", "",
           f"Validation rates: {tpr_val:.3f} of landfill points flagged, {fpr_rand:.4f} of random background points "
           f"(pooled over the held-out rounds; {fpr_all:.3f} of all non-landfill points, look-alikes included). "
           f"Gujarat rates: {tpr_g:.3f} and {fpr_g:.4f}.", ""]
    md += md_table(pp, {"precision (validation rates)": "{:.2%}", "precision (Gujarat rates)": "{:.2%}"}) + [""]
    md += [f"Measured in Gujarat: {g['in_flag']:,} flagged pixels inside the sealed outlines out of "
           f"{g['in_flag'] + g['out_flag']:,} flagged in all, a pixel precision of "
           f"{g['in_flag'] / (g['in_flag'] + g['out_flag']):.2%} against the sealed list. This is a lower bound: "
           f"flagged land outside the list may include dumps that are not on it.", ""]

    # Threshold sensitivity.
    rows = []
    for t in THRESHOLDS:
        sh = share[t]
        rows.append({"threshold": t, "sites found (half the outline)": sum(v >= 0.5 for v in sh.values()),
                     "sites": len(sh), "median share of outline flagged": float(np.median(list(sh.values()))),
                     "outline pixels flagged": tot[t]["in_flag"] / n_in,
                     "other land flagged": tot[t]["out_flag"] / n_out,
                     "km2 flagged": (tot[t]["in_flag"] + tot[t]["out_flag"]) / 1e4})
    ts = pd.DataFrame(rows)
    ts.round(4).to_csv(out / "threshold_sensitivity.csv", index=False)
    md += ["## 4. Threshold sensitivity on Gujarat", "",
           f"Post hoc. The frozen threshold is {thr}; the other rows change no reported result. The rows are "
           f"counted from score maps rounded to 0.01, so each flags about 2% more land than an exact count; the "
           f"exact figures at {thr} are in sections 1 and 3.", ""]
    md += md_table(ts, {"threshold": "{:.1f}", "sites found (half the outline)": "{:.0f}", "sites": "{:.0f}", "other land flagged": "{:.4f}", "km2 flagged": "{:.0f}"}) + [""]

    # Failure audit.
    neg = oof[oof["label"] == 0].assign(flagged=flag[oof["label"] == 0])
    by_class = neg.groupby("class")["flagged"].agg(points="size", flagged="sum", rate="mean").reset_index()
    neg["region"] = neg["state_iso"].map(ZONAL_COUNCILS)
    by_region = (neg.groupby(["region", "kind"])["flagged"].mean().unstack().reset_index()
                 .rename(columns={"lookalike": "look-alike points flagged", "random": "random points flagged"}))
    pos = oof[oof["label"] == 1].assign(flagged=flag[oof["label"] == 1])
    pos["region"] = pos["state_iso"].map(ZONAL_COUNCILS)
    by_region = by_region.merge(pos.groupby("region")["flagged"].mean().rename("landfill points flagged").reset_index())
    by_state = (neg[neg["kind"] == "random"].groupby("state_iso")["flagged"].agg(points="size", rate="mean")
                .reset_index().sort_values("rate", ascending=False))
    site_miss = (pos.groupby(["group_id", "state_iso"])["flagged"].agg(points="size", share_flagged="mean")
                 .reset_index().sort_values("share_flagged"))
    areas = pd.read_csv(gres / "areas.csv")[["city", "pixels_scored", "share_flagged"]].sort_values(
        "share_flagged", ascending=False)
    by_class.round(4).to_csv(out / "failure_audit_by_class.csv", index=False)
    by_region.round(4).to_csv(out / "failure_audit_by_region.csv", index=False)
    by_state.round(4).to_csv(out / "failure_audit_random_by_state.csv", index=False)
    site_miss.round(4).to_csv(out / "failure_audit_landfill_places.csv", index=False)
    areas.to_csv(out / "failure_audit_gujarat_by_city.csv", index=False)
    n_missed = int((site_miss["share_flagged"] < 0.5).sum())
    md += ["## 5. Failure audit", "", "Held-out false alarms of the frozen model, by class:", ""]
    md += md_table(by_class, {"rate": "{:.1%}"}) + ["", "By held-out region:", ""]
    md += md_table(by_region) + ["", "Random background points flagged, the five highest states:", ""]
    md += md_table(by_state.head(5), {"rate": "{:.1%}"}) + [""]
    md += [f"Training places judged by the Gujarat rule while held out: {n_missed} of {len(site_miss)} have fewer "
           f"than half their points flagged. The lowest:", ""]
    md += md_table(site_miss.head(8), {"share_flagged": "{:.2f}"}) + ["", "Gujarat land flagged, by city box:", ""]
    md += md_table(areas, {"share_flagged": "{:.2%}"}) + [""]
    sr = pd.read_csv(gres / "site_recall.csv")
    sr = sr[sr["status"].isin(["found", "missed"])][["test_id", "city", "area_ha", "share_flagged", "max_score", "status"]]
    md += ["Sealed Gujarat sites, lowest flagged share first:", ""]
    md += md_table(sr.sort_values("share_flagged"), {"share_flagged": "{:.2f}", "area_ha": "{:.1f}"}) + [""]
    # 6. Blind check of the top alarms, and the post hoc comparison of every model on Gujarat
    # (written by posthoc_gujarat.py on the machine that holds the feature GeoTIFFs).
    blind_path, ph_path = gres / "blind_check.csv", out / "posthoc_gujarat_alarm_scores.csv"
    if blind_path.exists():
        blind = pd.read_csv(blind_path)
        n, dumps = len(blind), int((blind["verdict"] == "dumpsite").sum())
        upper = 1 - 0.05 ** (1 / n) if dumps == 0 else float("nan")
        seen = blind["seen"].value_counts().rename_axis("what the pin was").reset_index(name="pins")
        seen.to_csv(out / "blind_check_summary.csv", index=False)
        md += ["## 6. Blind check of the top alarms", "",
               f"{n} of the top 100 alarms were checked by eye in shuffled order with scores hidden. "
               f"{dumps} are dumpsites: precision at the top of the ranking is {dumps / n:.0%}"
               + (f", and with none in {n} the 95% upper bound is {upper:.1%}." if dumps == 0 else "."), ""]
        md += md_table(seen) + [""]
    if ph_path.exists() and blind_path.exists():
        ph = pd.read_csv(out / "posthoc_gujarat_models.csv")
        sc = pd.read_csv(ph_path).drop(columns=["seen"]).merge(blind[["blind_id", "seen"]], how="left")
        models = [c for c in sc.columns if c not in ("blind_id", "seen")]
        groups = {"all 100 alarm centres": sc, f"the {n} checked (none a dump)": sc[sc["seen"].notna()],
                  "checked blue roofs": sc[sc["seen"] == "blue_roof"],
                  "checked water and salt pans": sc[sc["seen"].isin(["water", "salt_pan"])]}
        rows = []
        for m in models:
            r = ph[ph["model"] == m].iloc[0]
            p_bal = precision_at(r["outline_pixels_flagged"], r["land_flagged"], pos_share)
            f1_g = 2 * p_bal * r["outline_pixels_flagged"] / (p_bal + r["outline_pixels_flagged"]) if p_bal > 0 else 0.0
            row = {"model": m, "sites found": f"{int(r['sites_found'])}/{int(r['sites'])}",
                   "outline pixels flagged": r["outline_pixels_flagged"], "land flagged": r["land_flagged"],
                   "F1 at the validation class mix": f1_g}
            for label, grp in groups.items():
                row[f"{label} ({len(grp)}) flagged"] = float((grp[m] >= thr).mean())
            rows.append(row)
        cmp_ = pd.DataFrame(rows)
        cmp_.round(4).to_csv(out / "posthoc_gujarat_comparison.csv", index=False)
        pct = {c: "{:.0%}" for c in cmp_.columns if c.endswith("flagged") and "(" in c}
        md += ["## 7. Every model on Gujarat, post hoc", "",
               "Each model and feature set was fitted on all training points with the frozen settings and applied "
               "to every outline pixel, a random sample of about 2 million land pixels, and the centres of the "
               "frozen model's top 100 alarms. This explains the frozen result and selects nothing. The alarm "
               "centres are the frozen model's own top alarms: a low share for another model shows it does not "
               "share that failure, not that its own top alarms would be dumps, because those were not checked.", ""]
        md += md_table(cmp_, {"land flagged": "{:.4f}", **pct}) + [""]
        full = wide.merge(cmp_[["model", "F1 at the validation class mix"]].rename(
            columns={"F1 at the validation class mix": "gujarat_pixels_at_validation_mix"}), how="left")
        full.round(4).to_csv(out / "split_ablation.csv", index=False)
        md += ["Split ablation with the Gujarat rung for every model (mean F1; Gujarat as in section 1):", ""]
        md += md_table(full.drop(columns=[c for c in full.columns if c.startswith("drop_")])) + [""]
    (out / "depth_analysis.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
