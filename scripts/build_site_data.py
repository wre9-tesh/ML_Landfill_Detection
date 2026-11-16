"""Build the website in docs/ from the result files.

    python scripts/build_site_data.py            write the data files, maps and the six pages
    python scripts/build_site_data.py --check    write nothing; exit 1 if anything in docs/ is out of date

Reads only files that are in the repository (no Earth Engine, no Gujarat feature rasters) and
writes
    docs/site/data/site.json            every number used in the text, with its source
    docs/site/data/tables.json          the data behind each chart and generated table
    docs/site/data/features_hist.json   the feature explorer
    docs/site/data/threshold.json       the threshold slider
    docs/site/data/maps.json            box frames and site outlines for the flagged-pixel maps
    docs/site/img/boxes/<city>.png      flagged pixels of each scored box at 50 m
    docs/*.html                         the pages, from site_src/*.html

Pages are written in site_src/ with placeholders: {{k:key}} a number from site.json,
{{table:ID}} a generated table, {{tv:ID}} the numbers behind a chart, {{svg:name}} a map,
{{note:slug}} a margin note, {{term:slug|text}} a glossary link, {{glossary}} the glossary.
A placeholder that cannot be filled stops the build. The plan is docs/website_plan.md.
"""
import argparse
import html
import io
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from diagnostics import GROUPS, LABEL
from geoutil import REPO, ZONAL_COUNCILS, haversine_m
from run_models import load_tables
from site_text import FEATURE_INFO, GLOSSARY, PAGES

DOCS = REPO / "docs"
SITE = DOCS / "site"
SRC = REPO / "site_src"
V3 = REPO / "data" / "results_v3"
GUJ = REPO / "data" / "gujarat_results_v3"
AN = REPO / "data" / "analysis"
CLASSES = ["landfill", "near_site", "random", "bare_soil", "quarry", "ash_pond"]
REGIONS = ["Central", "Eastern", "North-Eastern", "Northern", "Southern", "Western"]
MODELS = {"flag_nothing": "Flag nothing", "published_rule": "Published threshold rule",
          "recalibrated_rule": "Refitted threshold rule", "logistic_regression": "Logistic regression",
          "decision_tree": "Decision tree", "bagged_trees": "Bagged trees", "random_forest": "Random forest",
          "adaboost": "AdaBoost", "gradient_boosting": "Gradient boosting"}
GUJARAT_KM2 = 196024  # area of the state, Census of India
KNOWN_TO_CHECKER = {"A021": "beside one of the 17 listed sites", "A065": "the Surendranagar landfill"}
UNSEEN = {"name": "Surendranagar", "lat": 22.7418, "lon": 71.5922, "blind_id": "A065"}
SEEN_LABEL = {"bare_soil": "Bare soil or open plot", "field_or_grass": "Field, grass or scrub", "building": "Buildings",
              "industrial_plant": "Industrial plant", "other": "Other", "dump": "Dumpsite", "riverbed": "Riverbed",
              "blue_roof": "Blue roof", "unsure": "Unsure", "water": "Water", "salt_pan": "Salt pan"}

K = {}       # site.json
T = {}       # tables.json
FILES = {}   # path -> bytes, everything this build writes
MAPS = {}    # box name -> image size and site outlines


def put(key, v, s, src):
    K[key] = {"v": v, "s": s, "src": src}


def n_(x):
    return f"{int(round(x)):,}"


def pct(x, d=None):
    x *= 100
    if d is None:
        d = 1 if x < 10 else 0
    return f"{x:.{d}f}%"


def f3(x):
    return f"{x:.3f}"


def f2(x):
    return f"{x:.2f}"


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def class_of(df):
    return np.where(df["label"] == 1, "landfill", df["class"].fillna("")).astype(object)


# ---------------------------------------------------------------- numbers

def numbers():
    oof = pd.read_csv(V3 / "oof_predictions.csv")
    oof["cls"] = class_of(oof)
    oof["region"] = oof["state_iso"].map(ZONAL_COUNCILS)
    src = "data/results_v3/oof_predictions.csv"
    put("train.points", len(oof), n_(len(oof)), src)
    for c in CLASSES:
        put(f"train.{c}", int((oof.cls == c).sum()), n_((oof.cls == c).sum()), src)
    put("train.landfill_share", float((oof.cls == "landfill").mean()), pct((oof.cls == "landfill").mean(), 0), src)
    pts = pd.read_csv(REPO / "data/samples/points.csv")
    bg = pd.read_csv(REPO / "data/samples/points_v2_background.csv")
    total = len(pts) + len(bg)
    put("train.points_drawn", total, n_(total), "data/samples/points.csv + points_v2_background.csv")
    put("train.points_dropped", total - len(oof), n_(total - len(oof)), "points drawn minus points with all 26 features")
    put("train.dropped_share", (total - len(oof)) / total, pct((total - len(oof)) / total), "as above")
    put("train.background_points", len(bg), n_(len(bg)), "data/samples/points_v2_background.csv")
    sites = pts[pts.kind == "site"]
    put("train.states", sites.state_iso.nunique(), str(sites.state_iso.nunique()), "data/samples/points.csv")
    per_state = sites.groupby("state_iso").group_id.nunique()
    put("train.states_small", int((per_state <= 2).sum()), str(int((per_state <= 2).sum())), "data/samples/points.csv")
    put("train.places_mh", int(per_state["IN-MH"]), str(int(per_state["IN-MH"])), "data/samples/points.csv")

    txt = (REPO / "data/samples/samples_summary.txt").read_text(encoding="utf-8")
    src = "data/samples/samples_summary.txt"
    m = re.search(r"Screening rows: (\d+); decisions: \(blank\) (\d+), drop (\d+), keep (\d+), unsure (\d+)", txt)
    rows, blank, drop, keep, unsure = map(int, m.groups())
    put("screen.osm_candidates", rows, n_(rows), src)
    put("screen.not_screened", blank, n_(blank), src)
    put("screen.screened", rows - blank, n_(rows - blank), src)
    put("screen.dropped", drop, str(drop), src)
    put("screen.kept", keep, str(keep), src)
    put("screen.unsure", unsure, str(unsure), src)
    put("screen.kept_share", keep / (rows - blank), pct(keep / (rows - blank), 0), src)
    m = re.search(r"Site places: (\d+) \(OSM (\d+), extra (\d+)\)", txt)
    places, osm, extra = map(int, m.groups())
    put("train.places", places, str(places), src)
    put("train.places_osm", osm, str(osm), src)
    put("train.places_drawn", extra, str(extra), src)
    m = re.search(r"Look-alike places by class: ash_pond (\d+), bare_soil (\d+), quarry (\d+)", txt)
    ash, bare, quarry = map(int, m.groups())
    put("train.lookalike_places", ash + bare + quarry, str(ash + bare + quarry), src)
    drawn = len(pd.read_csv(REPO / "labels/extra_sites.csv"))
    put("train.outlines_drawn", drawn, str(drawn), "labels/extra_sites.csv")
    T["F-D1"] = [{"step": "OpenStreetMap candidates outside Gujarat", "count": rows},
                 {"step": "Screened by eye in the time available", "count": rows - blank},
                 {"step": "Kept as active dumpsites", "count": keep},
                 {"step": "Kept as look-alike examples", "count": ash + bare + quarry},
                 {"step": "Outlines drawn by hand", "count": drawn},
                 {"step": "Places used for training (OSM and hand-drawn, merged)", "count": places}]
    T["T-D3"] = [{"region": r, **{c: int(((oof.region == r) & (oof.cls == c)).sum()) for c in CLASSES}} for r in REGIONS]

    s = pd.read_csv(V3 / "summary.csv").set_index(["split", "model"])
    src = "data/results_v3/summary.csv"
    hr = s.loc["held_out_region"]
    sel = json.loads((V3 / "selection.json").read_text(encoding="utf-8"))
    best = json.loads((V3 / "model.json").read_text(encoding="utf-8"))["model"]
    put("val.model", best, MODELS[best].lower(), "data/results_v3/model.json")
    for k, col in [("f1", "f1_mean"), ("f1_sd", "f1_std"), ("precision", "precision_mean"), ("recall", "recall_mean")]:
        put(f"val.{k}", float(hr.loc[best, col]), f3(hr.loc[best, col]), src)
    put("val.f1_site", float(s.loc[("held_out_site", best), "f1_mean"]), f3(s.loc[("held_out_site", best), "f1_mean"]), src)
    put("val.f1_pixel", float(s.loc[("random_pixel", best), "f1_mean"]), f3(s.loc[("random_pixel", best), "f1_mean"]), src)
    put("val.rule_f1", float(hr.loc["published_rule", "f1_mean"]), f3(hr.loc["published_rule", "f1_mean"]), src)
    put("val.lr_f1", float(hr.loc["logistic_regression", "f1_mean"]), f3(hr.loc["logistic_regression", "f1_mean"]), src)
    put("val.rf_f1", float(hr.loc["random_forest", "f1_mean"]), f3(hr.loc["random_forest", "f1_mean"]), src)
    put("val.rf_f1_pixel", float(s.loc[("random_pixel", "random_forest"), "f1_mean"]),
        f3(s.loc[("random_pixel", "random_forest"), "f1_mean"]), src)
    T["F-R1"] = [{"model": MODELS[m], "key": m, "selected": m == best,
                  **{sp: round(float(s.loc[(sp, m), "f1_mean"]), 4) for sp in ["random_pixel", "held_out_site", "held_out_region"]},
                  "region_sd": round(float(hr.loc[m, "f1_std"]), 4)} for m in MODELS]
    T["T-R1"] = [{"model": MODELS[m], "selected": m == best,
                  **{c: round(float(hr.loc[m, c]), 4) for c in hr.columns}} for m in MODELS]
    fm = pd.read_csv(V3 / "fold_metrics.csv")
    fm = fm[(fm.split == "held_out_region") & (fm.model == best)]
    T["F-R2"] = [{"region": r.fold, "landfill_points": int(r.n_landfill), "other_points": int(r.n_other),
                  "precision": r.precision, "recall": r.recall, "f1": r.f1} for r in fm.itertuples()]
    worst = fm.loc[fm.f1.idxmin()]
    put("val.worst_region", worst.fold, worst.fold, "data/results_v3/fold_metrics.csv")
    put("val.worst_f1", float(worst.f1), f3(worst.f1), "data/results_v3/fold_metrics.csv")

    g = json.loads((GUJ / "summary.json").read_text(encoding="utf-8"))
    src = "data/gujarat_results_v3/summary.json"
    put("guj.sites", g["sites_counted"], str(g["sites_counted"]), src)
    put("guj.sites_found", g["sites_found"], str(g["sites_found"]), src)
    put("guj.km2", g["area_scored_km2"], n_(g["area_scored_km2"]), src)
    put("guj.pixels_scored", g["pixels_scored"], n_(g["pixels_scored"]), src)
    put("guj.pixels_scored_m", g["pixels_scored"], f"{g['pixels_scored'] / 1e6:.0f} million", src)
    put("guj.pixels_flagged", g["pixels_flagged"], n_(g["pixels_flagged"]), src)
    put("guj.km2_flagged", g["pixels_flagged"] / 1e4, n_(g["pixels_flagged"] / 1e4), src)
    put("guj.share_flagged", g["share_flagged"], pct(g["share_flagged"]), src)
    put("guj.alarms", g["alarms"], n_(g["alarms"]), src)
    put("guj.patches", g["patches_with_sites_left_in"], n_(g["patches_with_sites_left_in"]), src)
    put("guj.top50", g["site_patches_in_top_50"], str(g["site_patches_in_top_50"]), src)
    put("guj.top100", g["site_patches_in_top_100"], str(g["site_patches_in_top_100"]), src)
    put("guj.share_of_state", g["area_scored_km2"] / GUJARAT_KM2, pct(g["area_scored_km2"] / GUJARAT_KM2), src)
    rec = pd.read_csv(GUJ / "site_recall.csv")
    rec = rec[rec.in_recall == "yes"].copy()
    ranks = pd.read_csv(GUJ / "site_ranks.csv").sort_values("rank_with_sites_left_in").drop_duplicates("test_id")
    rec = rec.merge(ranks[["test_id", "rank_with_sites_left_in", "mean_score"]], on="test_id", how="left")
    put("guj.cities", rec.city.nunique(), str(rec.city.nunique()), "data/gujarat_results_v3/site_recall.csv")
    put("guj.boxes", len(pd.read_csv(GUJ / "areas.csv")), str(len(pd.read_csv(GUJ / "areas.csv"))), "data/gujarat_results_v3/areas.csv")
    put("guj.top200", int((ranks.rank_with_sites_left_in <= 200).sum()), str(int((ranks.rank_with_sites_left_in <= 200).sum())),
        "data/gujarat_results_v3/site_ranks.csv")
    in_sites = int(rec.pixels_flagged.sum())
    put("guj.site_px_share_of_flagged", in_sites / g["pixels_flagged"], pct(in_sites / g["pixels_flagged"]),
        "site_recall.csv pixels_flagged / summary.json pixels_flagged")
    put("guj.site_px_share_of_scored", rec.pixels.sum() / g["pixels_scored"], pct(rec.pixels.sum() / g["pixels_scored"], 2),
        "site_recall.csv pixels / summary.json pixels_scored")
    put("guj.sites_ha", float(rec.area_ha.sum()), n_(rec.area_ha.sum()), "data/gujarat_results_v3/site_recall.csv")
    raj = rec[rec.status == "missed"].iloc[0]
    put("guj.missed.name", raj.city, raj.city, "data/gujarat_results_v3/site_recall.csv")
    put("guj.missed.share", float(raj.share_flagged), pct(raj.share_flagged, 1), "data/gujarat_results_v3/site_recall.csv")
    put("guj.missed.max_score", float(raj.max_score), f2(raj.max_score), "data/gujarat_results_v3/site_recall.csv")
    put("guj.missed.rank", int(raj.rank_with_sites_left_in), n_(raj.rank_with_sites_left_in), "data/gujarat_results_v3/site_ranks.csv")
    T["T-R2"] = [{"id": r.test_id, "city": r.city, "name": r.site_name, "area_ha": r.area_ha,
                  "share_flagged": r.share_flagged, "status": r.status, "rank": int(r.rank_with_sites_left_in),
                  "max_score": r.max_score} for r in rec.sort_values("share_flagged", ascending=False).itertuples()]
    areas = pd.read_csv(GUJ / "areas.csv")
    T["F-R4"] = [{"box": r.city.capitalize(), "km2_scored": round(r.pixels_scored / 1e4), "share_flagged": r.share_flagged}
                 for r in areas.sort_values("share_flagged", ascending=False).itertuples()]
    put("guj.box_min", float(areas.share_flagged.min()), pct(areas.share_flagged.min()), "data/gujarat_results_v3/areas.csv")
    put("guj.box_max", float(areas.share_flagged.max()), pct(areas.share_flagged.max()), "data/gujarat_results_v3/areas.csv")
    put("guj.box_min_name", "", areas.loc[areas.share_flagged.idxmin(), "city"].capitalize(), "data/gujarat_results_v3/areas.csv")
    put("guj.box_max_name", "", areas.loc[areas.share_flagged.idxmax(), "city"].capitalize(), "data/gujarat_results_v3/areas.csv")
    alarms = pd.read_csv(GUJ / "alarms.csv")
    put("guj.alarm_median_ha", float(alarms.area_ha.median()), f"{alarms.area_ha.median():.1f}", "data/gujarat_results_v3/alarms.csv")
    a = alarms[alarms.blind_id == UNSEEN["blind_id"]].iloc[0]
    src = "data/gujarat_results_v3/alarms.csv"
    put("guj.unseen.rank", int(a["rank"]), str(int(a["rank"])), src)
    put("guj.unseen.score", float(a.mean_score), f2(a.mean_score), src)
    put("guj.unseen.area_ha", float(a.area_ha), f"{a.area_ha:.1f}", src)
    d = haversine_m(a.lon, a.lat, UNSEEN["lon"], UNSEEN["lat"])
    put("guj.unseen.dist_m", d, f"{d:.0f}", src)

    # Diagnostics on the training side.
    nb = pd.read_csv(AN / "diag_neighbours.csv")
    nb = nb[nb.features == "26 features"].set_index("class")["points with a landfill majority"]
    src = "data/analysis/diag_neighbours.csv"
    for k, c in [("landfill", "Landfill"), ("near", "Near-site background"), ("random", "Random background"),
                 ("bare", "Bare soil"), ("quarry", "Quarry"), ("ash", "Ash pond")]:
        put(f"diag.nn_{k}", float(nb[c]), pct(nb[c], 0 if nb[c] > 0.1 else 1), src)
    T["F-X2"] = [{"class": c, "share": float(v)} for c, v in nb.items()]
    auc = pd.read_csv(AN / "diag_feature_auc.csv")
    T["F-X1"] = auc.to_dict("records")
    la = auc.set_index("feature").loc["LST_anom"]
    for c in ["near_site", "random", "bare_soil", "quarry", "ash_pond"]:
        put(f"diag.auc_lstanom_{c}", float(la[c]), f"{la[c]:.2f}", "data/analysis/diag_feature_auc.csv")
    fl = pd.read_csv(AN / "diag_flagged_by_class.csv")
    fl = fl[fl.version.str.startswith("v3")].iloc[0]
    src = "data/analysis/diag_flagged_by_class.csv"
    for k, c in [("landfill", "Landfill"), ("near", "Near-site background"), ("random", "Random background"),
                 ("bare", "Bare soil"), ("quarry", "Quarry"), ("ash", "Ash pond")]:
        put(f"diag.fa_{k}", float(fl[c]), pct(fl[c], 0 if fl[c] > 0.1 else 1), src)
    T["F-X4"] = [{"class": c, "share": float(fl[c])} for c in fl.index[1:]]
    sg = pd.read_csv(AN / "diag_shap_groups.csv")
    sg = sg[sg.version.str.startswith("v3")].iloc[0]
    for g_ in GROUPS:
        put("diag.shap_" + g_.split()[0].replace("-", ""), float(sg[g_]), pct(sg[g_], 0), "data/analysis/diag_shap_groups.csv")
    sf = pd.read_csv(AN / "diag_shap_features.csv").sort_values("v3", ascending=False)
    T["F-X5"] = {"groups": [{"group": g_, "share": float(sg[g_])} for g_ in GROUPS],
                 "features": [{"feature": r.feature, "group": r.group, "share": float(r.v3)} for r in sf.head(8).itertuples()]}
    put("diag.top_feature_share", float(sf.iloc[0].v3), pct(sf.iloc[0].v3, 0), "data/analysis/diag_shap_features.csv")

    # Precision against rarity: validation rates and the Gujarat rate.
    R, F_val = float(fl["Landfill"]), float(fl["Random background"])
    F_guj = (g["pixels_flagged"] - in_sites) / (g["pixels_scored"] - int(rec.pixels.sum()))
    put("rare.fa_gujarat", F_guj, pct(F_guj), "flagged pixels outside the outlines / scored pixels outside them")
    rows = []
    for e in np.linspace(math.log10(2), 5, 25):
        p = 10 ** -e
        rows.append({"one_in": round(10 ** e), "validation_rates": round(p * R / (p * R + (1 - p) * F_val), 5),
                     "gujarat_rates": round(p * R / (p * R + (1 - p) * F_guj), 5)})
    T["F-X6"] = rows
    p = 0.001
    put("rare.precision_1000", p * R / (p * R + (1 - p) * F_val), pct(p * R / (p * R + (1 - p) * F_val), 0), "recall and random-background rate, diag_flagged_by_class.csv")
    put("rare.sites_one_in", g["pixels_scored"] / rec.pixels.sum(), n_(round(g["pixels_scored"] / rec.pixels.sum(), -2)), "scored pixels / pixels inside the 17 outlines")
    return oof, rec, alarms


def hand_check(alarms):
    b = pd.read_csv(GUJ / "blind_check.csv", keep_default_na=False)
    b["verdict"] = b.verdict.str.strip().str.lower().str.replace("look_alike", "lookalike")
    b["seen"] = b.seen.str.strip().str.lower()
    b.loc[b.seen == "", "seen"] = b.loc[b.seen == "", "verdict"]
    src = "data/gujarat_results_v3/blind_check.csv"
    done = b[b.verdict != ""]
    if len(done) < len(b):
        for k in ["checked", "dumps", "lookalikes", "unsure", "judged", "dump_share", "ci_low", "ci_high", "dumps_new", "dumps_known", "top_seen", "top_seen_n"]:
            put("check." + k, None, "pending", src)
        T["F-R7"], T["T-R3"] = [], []
        return b
    dumps, unsure = int((b.verdict == "dump").sum()), int((b.verdict == "unsure").sum())
    judged = len(b) - unsure
    lo, hi = wilson(dumps, judged)
    known = int(b[(b.verdict == "dump")].blind_id.isin(KNOWN_TO_CHECKER).sum())
    put("check.checked", len(b), str(len(b)), src)
    put("check.judged", judged, str(judged), src)
    put("check.dumps", dumps, str(dumps), src)
    put("check.lookalikes", int((b.verdict == "lookalike").sum()), str(int((b.verdict == "lookalike").sum())), src)
    put("check.unsure", unsure, str(unsure), src)
    put("check.dump_share", dumps / judged, pct(dumps / judged, 0), src)
    put("check.ci_low", lo, pct(lo, 0), src)
    put("check.ci_high", hi, pct(hi, 0), src)
    put("check.dumps_known", known, str(known), src)
    put("check.dumps_new", dumps - known, str(dumps - known), src)
    counts = b.seen.value_counts()
    small = counts[(counts < 3) & ~counts.index.isin(["dump", "unsure"])]
    b["seen_group"] = b.seen.where(~b.seen.isin(small.index), "other")
    cg = b.seen_group.value_counts()
    T["F-R7"] = [{"seen": SEEN_LABEL.get(k, k), "key": k, "alarms": int(v)} for k, v in cg.items()]
    top = cg[~cg.index.isin(["dump", "unsure"])]
    put("check.top_seen", top.index[0], SEEN_LABEL.get(top.index[0], top.index[0]).lower(), src)
    put("check.top_seen_n", int(top.iloc[0]), str(int(top.iloc[0])), src)
    for k, v in cg.items():
        put("check.seen." + k, int(v), str(int(v)), src)
    d = b[b.verdict == "dump"].merge(alarms, on="blind_id")
    T["T-R3"] = [{"blind_id": r.blind_id, "rank": int(r["rank"]), "city": r.city.capitalize(), "area_ha": r.area_ha,
                  "mean_score": r.mean_score, "known": KNOWN_TO_CHECKER.get(r.blind_id, "not known to the checker before")}
                 for _, r in d.sort_values("rank").iterrows()]

    path = AN / "diag_alarm_points.csv"
    if not path.exists():
        T["T-X1"] = []
        return b
    p = pd.read_csv(path, keep_default_na=False)
    p = p[(p.version == "v3") | (p.kind == "sealed_site")].copy()
    p = p.merge(b[["blind_id", "verdict", "seen_group"]].rename(columns={"blind_id": "id", "verdict": "v"}), on="id", how="left")
    p["what"] = np.where(p.kind == "sealed_site", "Known sites", np.where(p.v == "dump", "Alarms judged dumps",
                         np.where(p.v == "unsure", "", "Alarms judged look-alikes")))
    rows = []
    for what in ["Known sites", "Alarms judged dumps", "Alarms judged look-alikes"]:
        q = p[p.what == what]
        rows.append({"what": what, "centres": len(q), "median_novelty_pct": round(float(q.novelty_pct.median()), 1),
                     "beyond_99th": round(float((q.novelty_pct > 99).mean()), 3),
                     "nearest_is_landfill": int((q.nearest_class == "landfill").sum()),
                     "median_score": round(float(q.v3_score.median()), 3),
                     **{"shap_" + g_: round(float(q["shap_" + g_].mean()), 2) for g_ in GROUPS}})
    T["T-X1"] = rows
    src = "data/analysis/diag_alarm_points.csv"
    la = rows[2]
    put("alarm.la_n", la["centres"], str(la["centres"]), src)
    put("alarm.la_nearest_landfill", la["nearest_is_landfill"], str(la["nearest_is_landfill"]), src)
    put("alarm.la_novelty", la["median_novelty_pct"], f"{la['median_novelty_pct']:.0f}th", src)
    put("alarm.la_shap_thermal", la["shap_thermal"], f"+{la['shap_thermal']:.1f}", src)
    put("alarm.dump_shap_thermal", rows[1]["shap_thermal"], f"+{rows[1]['shap_thermal']:.1f}", src)
    other = lambda r: r["shap_pre-monsoon spectral"] + r["shap_winter spectral"] + r["shap_surroundings"]
    put("alarm.la_shap_other", other(la), f"+{other(la):.1f}", src)
    put("alarm.dump_shap_other", other(rows[1]), f"+{other(rows[1]):.1f}", src)
    put("alarm.site_shap_other", other(rows[0]), f"+{other(rows[0]):.1f}", src)
    put("alarm.site_shap_thermal", rows[0]["shap_thermal"], f"+{rows[0]['shap_thermal']:.1f}", src)
    return b


def new_cities():
    """The second blind test: sites in six further cities, sealed before their boxes were scored."""
    d = REPO / "data" / "gujarat_results_v3_new"
    g = json.loads((d / "summary.json").read_text(encoding="utf-8"))
    src = "data/gujarat_results_v3_new/summary.json"
    put("new.sites", g["sites_counted"], str(g["sites_counted"]), src)
    put("new.sites_found", g["sites_found"], str(g["sites_found"]), src)
    put("new.km2", g["area_scored_km2"], n_(g["area_scored_km2"]), src)
    put("new.share_flagged", g["share_flagged"], pct(g["share_flagged"]), src)
    put("new.alarms", g["alarms"], n_(g["alarms"]), src)
    put("new.top50", g["site_patches_in_top_50"], str(g["site_patches_in_top_50"]), src)
    put("new.top100", g["site_patches_in_top_100"], str(g["site_patches_in_top_100"]), src)
    rec = pd.read_csv(d / "site_recall.csv")
    ranks = pd.read_csv(d / "site_ranks.csv").sort_values("rank_with_sites_left_in").drop_duplicates("test_id").set_index("test_id")
    T["T-N1"] = [{"id": r.test_id, "city": r.city, "area_ha": r.area_ha, "share_flagged": r.share_flagged, "status": r.status,
                  "rank": int(ranks.loc[r.test_id, "rank_with_sites_left_in"]) if r.test_id in ranks.index else None}
                 for r in rec.sort_values("share_flagged", ascending=False).itertuples()]
    miss = rec[rec.status == "missed"].iloc[0]
    put("new.missed.name", miss.city, miss.city, "data/gujarat_results_v3_new/site_recall.csv")
    put("new.missed.share", float(miss.share_flagged), pct(miss.share_flagged, 0), "data/gujarat_results_v3_new/site_recall.csv")
    put("new.best_rank", int(ranks.rank_with_sites_left_in.min()), str(int(ranks.rank_with_sites_left_in.min())), "data/gujarat_results_v3_new/site_ranks.csv")
    put("new.best_name", "", ranks.rank_with_sites_left_in.idxmin() and ranks.sort_values("rank_with_sites_left_in").city.iloc[0].capitalize(), "data/gujarat_results_v3_new/site_ranks.csv")
    tot, found = K["guj.sites"]["v"] + g["sites_counted"], K["guj.sites_found"]["v"] + g["sites_found"]
    put("all.sites", tot, str(tot), "both test lists")
    put("all.sites_found", found, str(found), "both test lists")
    put("all.km2", K["guj.km2"]["v"] + g["area_scored_km2"], n_(K["guj.km2"]["v"] + g["area_scored_km2"]), "both scored areas")


# ---------------------------------------------------------------- feature explorer and PCA

def features():
    sel = json.loads((V3 / "selection.json").read_text(encoding="utf-8"))
    df, feats = load_tables(sel["feature_tables"], sel["extra_tables"])
    df = df.dropna(subset=feats).reset_index(drop=True)
    df["cls"] = class_of(df)
    assert len(df) == K["train.points"]["v"], "feature table does not match the out-of-fold table"
    auc = pd.read_csv(AN / "diag_feature_auc.csv").set_index("feature")
    group_of = {f: g for g, fs in GROUPS.items() for f in fs}
    out = {"classes": CLASSES, "class_labels": {c: LABEL[c] for c in CLASSES},
           "n": {c: int((df.cls == c).sum()) for c in CLASSES}, "groups": list(GROUPS), "features": []}
    for f in feats:
        x = df[f].to_numpy(float)
        lo, hi = np.percentile(x, [1, 99])
        edges = np.linspace(lo, hi, 41)
        info = FEATURE_INFO[f]
        row = {"name": f, "label": info[0], "unit": info[1], "definition": info[2], "group": group_of[f],
               "edges": [round(float(e), 5) for e in edges], "counts": {}, "median": {}, "q25": {}, "q75": {},
               "auc": {c: float(auc.loc[f, c]) for c in CLASSES[1:]}}
        for c in CLASSES:
            v = x[(df.cls == c).to_numpy()]
            row["counts"][c] = np.histogram(np.clip(v, lo, hi), edges)[0].tolist()
            q = np.percentile(v, [25, 50, 75])
            row["q25"][c], row["median"][c], row["q75"][c] = (round(float(t), 4) for t in q)
        out["features"].append(row)
    FILES[SITE / "data/features_hist.json"] = json.dumps(out, separators=(",", ":")).encode()

    # One real landfill row, for the "what one row is" table.
    r = df[df.cls == "landfill"].sort_values("point_id").iloc[0]
    T["T-D1"] = {"point_id": r.point_id, "state": r.state_iso, "place": r.group_id,
                 "values": [{"feature": f, "label": FEATURE_INFO[f][0], "unit": FEATURE_INFO[f][1],
                             "value": round(float(r[f]), 3 if abs(r[f]) < 10 else 1)} for f in feats]}

    # Principal components, as in diagnostics.md.
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    Z = StandardScaler().fit_transform(df[feats].to_numpy(float))
    pca = PCA(n_components=2, random_state=678).fit(Z)
    ev = pca.explained_variance_ratio_
    put("diag.pc1", float(ev[0]), pct(ev[0], 0), "computed as in data/analysis/diagnostics.md")
    put("diag.pc2", float(ev[1]), pct(ev[1], 0), "computed as in data/analysis/diagnostics.md")
    put("diag.pc12", float(ev.sum()), pct(ev.sum(), 0), "computed as in data/analysis/diagnostics.md")
    xy = pca.transform(Z)
    rng = np.random.default_rng(678)
    take = {"landfill": 1200, "near_site": 1200, "random": 800, "bare_soil": 479, "quarry": 360, "ash_pond": 900}
    rows = []
    for c, n in take.items():
        idx = np.flatnonzero((df.cls == c).to_numpy())
        idx = np.sort(rng.choice(idx, min(n, len(idx)), replace=False))
        rows += [{"c": c, "x": round(float(xy[i, 0]), 2), "y": round(float(xy[i, 1]), 2)} for i in idx]
    T["F-X3"] = rows


# ---------------------------------------------------------------- threshold slider and box maps

def threshold(oof, rec):
    ts = np.round(np.arange(0, 1.0001, 0.01), 2)
    val = {"regions": REGIONS, "classes": CLASSES, "n": {}, "flagged": {}}
    score = oof["gradient_boosting"].to_numpy(float)
    for r in REGIONS:
        val["n"][r], val["flagged"][r] = {}, {}
        for c in CLASSES:
            s = np.sort(score[((oof.region == r) & (oof.cls == c)).to_numpy()])
            val["n"][r][c] = int(len(s))
            val["flagged"][r][c] = (len(s) - np.searchsorted(s, ts - 1e-9, side="left")).tolist()
    i = 50
    P, Rr, F = [], [], []
    for r in REGIONS:
        tp = val["flagged"][r]["landfill"][i]
        fp = sum(val["flagged"][r][c][i] for c in CLASSES[1:])
        p = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / val["n"][r]["landfill"]
        P.append(p), Rr.append(rc), F.append(2 * p * rc / (p + rc) if p + rc else 0.0)
    # Scores in the table are stored to four decimals, so the curve can differ in the third decimal.
    got = [float(np.mean(v)) for v in (P, Rr, F)]
    want = [K[k]["v"] for k in ("val.precision", "val.recall", "val.f1")]
    assert all(abs(a - b) <= 0.002 for a, b in zip(got, want)), f"threshold curve does not reproduce the table: {got} vs {want}"
    val["published"] = {"t": 0.5, "precision": want[0], "recall": want[1], "f1": want[2]}

    import rasterio
    from PIL import Image
    from rasterio.features import geometry_mask
    from rasterio.warp import transform_geom
    sites = [f for f in json.load(open(REPO / "labels/gujarat_test_sites.geojson", encoding="utf-8"))["features"]
             if f["geometry"]["type"] != "Point"]
    edges = np.arange(0, 102)
    hist_all = np.zeros(101, np.int64)
    scored = 0
    site_hist, done, maps = {}, [], {}
    for tif in sorted((GUJ / "scores").glob("gujarat_*.tif")):
        city = tif.stem.replace("gujarat_", "")
        with rasterio.open(tif) as src:
            a, tr, crs = src.read(1), src.transform, src.crs
        h, w = a.shape
        xs = tr.c + tr.a * (np.arange(w) + 0.5)
        ys = tr.f + tr.e * (np.arange(h) + 0.5)
        fresh = np.ones((h, w), bool)
        for l, b_, r_, t_ in done:
            fresh[np.ix_((ys > b_) & (ys < t_), (xs > l) & (xs < r_))] = False
        done.append((tr.c, tr.f + tr.e * h, tr.c + tr.a * w, tr.f))
        valid = a != 255
        hist_all += np.histogram(a[fresh & valid], edges)[0]
        scored += int((fresh & valid).sum())
        outlines = []
        for f in sites:
            geom = transform_geom("EPSG:4326", crs, f["geometry"])
            m = geometry_mask([geom], (h, w), tr, invert=True)
            if not m.any():
                continue
            tid = f["properties"]["test_id"]
            if tid not in site_hist or site_hist[tid]["pixels"] < int(m.sum()):
                site_hist[tid] = {"pixels": int(m.sum()), "hist": np.histogram(a[m & valid], edges)[0]}
            rings = geom["coordinates"] if geom["type"] == "Polygon" else [p[0] for p in geom["coordinates"]]
            rings = rings[:1] if geom["type"] == "Polygon" else rings
            for ring in rings:
                outlines.append({"id": tid, "pts": [[round((x - tr.c) / tr.a / 5, 1), round((y - tr.f) / tr.e / 5, 1)] for x, y in ring]})
        # Flagged share in 50 m cells: orange with alpha = share flagged; grey where not scored.
        hh, ww = h // 5, w // 5
        blk = lambda m: m[:hh * 5, :ww * 5].reshape(hh, 5, ww, 5).mean(axis=(1, 3))
        share, miss = blk((a >= 50) & valid), blk(~valid)
        rgba = np.zeros((hh, ww, 4), np.uint8)
        rgba[..., :3] = (235, 104, 52)
        rgba[..., 3] = np.round(255 * np.sqrt(share)).astype(np.uint8)
        grey = miss > 0.5
        rgba[grey] = (137, 135, 129, 40)
        buf = io.BytesIO()
        Image.fromarray(rgba, "RGBA").save(buf, "PNG", optimize=True)
        FILES[SITE / f"img/boxes/{city}.png"] = buf.getvalue()
        maps[city] = {"w": ww, "h": hh, "outlines": outlines}
    assert scored == K["guj.pixels_scored"]["v"], f"scored pixels {scored} do not match the published total"
    flagged = hist_all[::-1].cumsum()[::-1]
    pub = K["guj.pixels_flagged"]["v"]
    diff = (int(flagged[50]) - pub) / pub
    put("thr.rounding_diff", diff, pct(abs(diff)), "score rasters at 50 against summary.json pixels_flagged")
    guj_sites = []
    for r in rec.itertuples():
        sh = site_hist[r.test_id]
        assert sh["pixels"] == r.pixels, f"{r.test_id}: outline pixels differ from site_recall.csv"
        guj_sites.append({"id": r.test_id, "city": r.city, "pixels": int(sh["hist"].sum()),
                          "flagged": sh["hist"][::-1].cumsum()[::-1].tolist()})
    out = {"t": ts.tolist(), "val": val,
           "guj": {"pixels_scored": scored, "flagged": flagged.tolist(), "sites": guj_sites,
                   "published": {"t": 0.5, "pixels_flagged": pub, "sites_found": K["guj.sites_found"]["v"]}}}
    FILES[SITE / "data/threshold.json"] = json.dumps(out, separators=(",", ":")).encode()
    FILES[SITE / "data/maps.json"] = json.dumps(maps, separators=(",", ":")).encode()
    MAPS.update(maps)
    found30 = sum(1 for s in guj_sites if s["flagged"][30] / s["pixels"] >= 0.5)
    put("thr.sites_at_030", found30, str(found30), "score rasters")
    put("thr.share_at_030", float(flagged[30] / scored), pct(flagged[30] / scored), "score rasters")
    found70 = sum(1 for s in guj_sites if s["flagged"][70] / s["pixels"] >= 0.5)
    put("thr.sites_at_070", found70, str(found70), "score rasters")
    put("thr.share_at_070", float(flagged[70] / scored), pct(flagged[70] / scored), "score rasters")


# ---------------------------------------------------------------- locator maps (inline SVG)

def rings_of(geom):
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    return [p[0] for p in polys]


def thin(ring, step):
    """Round to a grid of `step` degrees and drop repeats; None if the ring collapses."""
    out = []
    for x, y in ring:
        q = (round(x / step) * step, round(y / step) * step)
        if not out or q != out[-1]:
            out.append(q)
    return out if len(out) >= 4 else None


def svg_maps(rec):
    states = json.load(open(REPO / "data/boundaries/geoBoundaries-IND-ADM1_simplified.geojson", encoding="utf-8"))["features"]
    svgs = {}

    # Gujarat with the scored boxes and the sites.
    k, lat0 = 150, 22.3
    cx = math.cos(math.radians(lat0))
    W0, N0 = 68.0, 24.8
    X = lambda lon: (lon - W0) * cx * k
    Y = lambda lat: (N0 - lat) * k
    path = lambda ring, X, Y: "M" + "L".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in ring) + "Z"
    gj = next(f for f in states if f["properties"]["shapeISO"] == "IN-GJ")
    d = " ".join(path(r, X, Y) for r in (thin(r, 0.01) for r in rings_of(gj["geometry"])) if r)
    parts = [f'<svg class="map" viewBox="0 0 {X(74.6):.0f} {Y(19.9):.0f}" role="img" aria-label="Map of Gujarat with the 14 scored boxes and the known sites">',
             f'<path class="land" d="{d}"/>']
    boxes = json.loads((REPO / "labels/gujarat_boxes.json").read_text(encoding="utf-8"))["boxes_wsen"]
    left = {"Jamnagar", "Dwarka", "Bhuj", "Rajkot", "Surendranagar", "Mehsana", "Gandhinagar", "Ahmedabad"}
    for name, (w, s, e, n) in boxes.items():
        parts.append(f'<rect class="box" x="{X(w):.1f}" y="{Y(n):.1f}" width="{X(e) - X(w):.1f}" height="{Y(s) - Y(n):.1f}"/>')
        if name in left:
            parts.append(f'<text class="lbl" x="{X(w) - 4:.1f}" y="{Y((s + n) / 2) + 4:.1f}" text-anchor="end">{name}</text>')
        else:
            parts.append(f'<text class="lbl" x="{X(e) + 4:.1f}" y="{Y((s + n) / 2) + 4:.1f}">{name}</text>')
    test = pd.read_csv(REPO / "labels/gujarat_test_sites.csv").set_index("test_id")
    for r in rec.itertuples():
        x, y = X(test.loc[r.test_id, "lon"]), Y(test.loc[r.test_id, "lat"])
        if r.status == "found":
            parts.append(f'<circle class="found" cx="{x:.1f}" cy="{y:.1f}" r="5"><title>{html.escape(r.site_name)}: found</title></circle>')
        else:
            parts.append(f'<path class="missed" d="M{x - 6:.1f},{y - 6:.1f}l12,12m0,-12l-12,12"><title>{html.escape(r.site_name)}: missed</title></path>')
    parts.append(f'<circle class="unseen" cx="{X(UNSEEN["lon"]):.1f}" cy="{Y(UNSEEN["lat"]):.1f}" r="7"><title>Surendranagar: not on the list, found</title></circle>')
    lx, ly = X(68.15), Y(20.9)
    parts += [f'<g class="key" transform="translate({lx:.0f},{ly:.0f})">',
              '<rect class="box" x="0" y="-9" width="12" height="12"/><text class="lbl" x="18" y="2">Scored box</text>',
              '<circle class="found" cx="6" cy="20" r="5"/><text class="lbl" x="18" y="25">Known site, found</text>',
              '<path class="missed" d="M1,38l10,10m0,-10l-10,10"/><text class="lbl" x="18" y="48">Known site, missed</text>',
              '<circle class="unseen" cx="6" cy="66" r="6"/><text class="lbl" x="18" y="71">Site not on the list</text>', '</g></svg>']
    svgs["gujarat"] = "".join(parts)

    # India with the training places.
    k = 22
    cx = math.cos(math.radians(22))
    X2 = lambda lon: (lon - 67.5) * cx * k
    Y2 = lambda lat: (37.5 - lat) * k
    tint = {"Northern": "t1", "Central": "t2", "Eastern": "t3", "Western": "t3", "Southern": "t1", "North-Eastern": "t2"}
    parts = [f'<svg class="map" viewBox="0 0 {X2(97.8):.0f} {Y2(6.5):.0f}" role="img" aria-label="Map of India with the 86 training places and Gujarat held out">']
    for f in states:
        iso = f["properties"]["shapeISO"]
        if iso in ("IN-AN", "IN-LD"):
            continue
        d = " ".join(path(r, X2, Y2) for r in (thin(r, 0.05) for r in rings_of(f["geometry"])) if r)
        cls = "gujarat" if iso == "IN-GJ" else "state " + tint.get(ZONAL_COUNCILS.get(iso), "t1")
        parts.append(f'<path class="{cls}" d="{d}"/>')
    pts = pd.read_csv(REPO / "data/samples/points.csv")
    pl = pts[pts.kind == "site"].groupby("group_id")[["lon", "lat"]].mean()
    for r in pl.itertuples():
        parts.append(f'<circle class="place" cx="{X2(r.lon):.1f}" cy="{Y2(r.lat):.1f}" r="3"/>')
    for name, lon, lat in [("Northern", 75.2, 30.0), ("Central", 79.5, 24.6), ("Eastern", 85.8, 23.0), ("Western", 75.3, 19.3),
                           ("Southern", 77.6, 14.0), ("North-Eastern", 93.3, 26.0)]:
        parts.append(f'<text class="region" x="{X2(lon):.1f}" y="{Y2(lat):.1f}" text-anchor="middle">{name}</text>')
    parts.append(f'<text class="held" x="{X2(71.3):.1f}" y="{Y2(22.6):.1f}" text-anchor="middle">Gujarat</text>')
    parts.append(f'<text class="held small" x="{X2(71.3):.1f}" y="{Y2(22.6) + 13:.1f}" text-anchor="middle">held out</text>')
    parts.append("</svg>")
    svgs["india"] = "".join(parts)
    return svgs


# ---------------------------------------------------------------- generated tables

def td(v, cls=""):
    return f'<td class="{cls}">{v}</td>' if cls else f"<td>{v}</td>"


def table(head, rows, cls=""):
    h = "".join(f'<th class="{"num" if a else ""}">{html.escape(t)}</th>' for t, a in head)
    body = "".join("<tr" + (' class="sel"' if sel else "") + ">" + "".join(
        td(v, "num" if a else "") for v, (_, a) in zip(r, head)) + "</tr>" for sel, r in rows)
    return f'<div class="tablewrap"><table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{body}</tbody></table></div>'


def gen_table(tid):
    if tid == "T-D1":
        t = T[tid]
        rows = [(False, [f"<code>{v['feature']}</code>", html.escape(v["label"]), f"{v['value']:g}", v["unit"]]) for v in t["values"]]
        return table([("Feature", 0), ("What it is", 0), ("Value", 1), ("Unit", 0)], rows)
    if tid == "T-D3":
        rows = [(False, [r["region"]] + [n_(r[c]) for c in CLASSES] + [n_(sum(r[c] for c in CLASSES))]) for r in T[tid]]
        tot = [sum(r[c] for r in T[tid]) for c in CLASSES]
        rows.append((True, ["All regions"] + [n_(v) for v in tot] + [n_(sum(tot))]))
        return table([("Region", 0)] + [(LABEL[c], 1) for c in CLASSES] + [("Total", 1)], rows)
    if tid == "T-D4":
        rows = [(False, [r["id"], r["city"], html.escape(r["name"]), f"{r['area_ha']:.1f}"]) for r in sorted(T["T-R2"], key=lambda r: r["id"])]
        return table([("ID", 0), ("City", 0), ("Name on the list", 0), ("Area, ha", 1)], rows)
    if tid == "T-R1":
        pm = lambda r, k: f"{r[k + '_mean']:.3f} ± {r[k + '_std']:.3f}"
        rows = [(r["selected"], [r["model"] + (" (selected)" if r["selected"] else ""), pm(r, "precision"), pm(r, "recall"), pm(r, "f1")]) for r in T[tid]]
        return table([("Model", 0), ("Precision", 1), ("Recall", 1), ("F1", 1)], rows)
    if tid == "T-R2":
        st = lambda s: '<span class="ok">✓ found</span>' if s == "found" else '<span class="bad">✗ missed</span>'
        rows = [(r["status"] != "found", [r["id"], r["city"], f"{r['area_ha']:.1f}", pct(r["share_flagged"], 0), st(r["status"]),
                                          f"{r['rank']:,}"]) for r in T[tid]]
        return table([("Site", 0), ("City", 0), ("Area, ha", 1), ("Outline flagged", 1), ("Result", 0), ("Rank of its patch", 1)], rows)
    if tid == "T-N1":
        st = lambda s: '<span class="ok">✓ found</span>' if s == "found" else '<span class="bad">✗ missed</span>'
        rows = [(r["status"] != "found", [r["id"], r["city"], f"{r['area_ha']:.1f}", pct(r["share_flagged"], 0), st(r["status"]),
                                          f"{r['rank']:,}" if r["rank"] else "no patch"]) for r in T[tid]]
        return table([("Site", 0), ("City", 0), ("Area, ha", 1), ("Outline flagged", 1), ("Result", 0), ("Rank of its patch", 1)], rows)
    if tid == "T-R3":
        if not T[tid]:
            return '<p class="pendingnote">The hand check is not finished.</p>'
        rows = [(False, [r["blind_id"], str(r["rank"]), r["city"], f"{r['area_ha']:.1f}", f"{r['mean_score']:.2f}", r["known"]]) for r in T[tid]]
        return table([("Alarm", 0), ("Rank", 1), ("Box", 0), ("Area, ha", 1), ("Mean score", 1), ("Known beforehand?", 0)], rows)
    if tid == "T-X1":
        if not T[tid]:
            return '<p class="pendingnote">This analysis has not been run yet.</p>'
        sg = lambda v: f"{v:+.2f}"
        rows = [(False, [r["what"], str(r["centres"]), f"{r['median_novelty_pct']:.0f}", pct(r["beyond_99th"], 0),
                         f"{r['nearest_is_landfill']} of {r['centres']}", sg(r["shap_thermal"]), sg(r["shap_pre-monsoon spectral"]),
                         sg(r["shap_winter spectral"]), sg(r["shap_surroundings"])]) for r in T[tid]]
        return table([("Group", 0), ("Places", 1), ("Novelty, median percentile", 1), ("Beyond the 99th", 1),
                      ("Nearest training points are landfill", 1), ("Thermal", 1), ("Pre-monsoon", 1), ("Winter", 1), ("Surroundings", 1)], rows)
    if tid == "F-X1":
        cols = ["near_site", "random", "bare_soil", "quarry", "ash_pond"]
        out = ['<div class="tablewrap"><table class="heat"><thead><tr><th>Feature</th>'] + [f'<th class="num">{LABEL[c]}</th>' for c in cols] + ["</tr></thead><tbody>"]
        last = None
        for r in sorted(T[tid], key=lambda r: list(GROUPS).index(r["group"])):
            if r["group"] != last:
                out.append(f'<tr class="grp"><th colspan="6">{r["group"].capitalize()}</th></tr>')
                last = r["group"]
            cells = "".join(f'<td class="num" style="--a:{min(abs(r[c] - 0.5) / 0.45, 1):.2f}"><a href="data.html#f={r["feature"]}">{r[c]:.2f}</a></td>' for c in cols)
            out.append(f'<tr><th><code>{r["feature"]}</code></th>{cells}</tr>')
        return "".join(out) + "</tbody></table></div>"
    raise KeyError(tid)


def box_maps():
    """The flagged-pixel picture of every scored box, with the known outlines drawn on."""
    share = {r["box"].lower(): r["share_flagged"] for r in T["F-R4"]}
    out = ['<div class="boxes">']
    for city, m in MAPS.items():
        polys = "".join('<polygon points="' + " ".join(f"{x},{y}" for x, y in o["pts"]) + '"/>' for o in m["outlines"])
        out.append(f'<div><div class="boxmap"><img loading="lazy" width="{m["w"]}" height="{m["h"]}" src="site/img/boxes/{city}.png" '
                   f'alt="Flagged pixels in the {city.capitalize()} box"><svg viewBox="0 0 {m["w"]} {m["h"]}" preserveAspectRatio="none">{polys}</svg></div>'
                   f'<div class="boxname"><span>{city.capitalize()}</span><span>{pct(share[city])} flagged</span></div></div>')
    return "".join(out) + "</div>"


def table_view(tid):
    """The numbers behind a chart, as a collapsed table."""
    rows = T[tid]
    if isinstance(rows, dict):
        rows = rows["groups"]
    if not rows:
        return ""
    cols = [c for c in rows[0] if c not in ("key", "selected")]
    fmt = lambda v: (f"{v:,}" if isinstance(v, int) and not isinstance(v, bool) else f"{v:.3f}" if isinstance(v, float) else html.escape(str(v)))
    head = [(c.replace("_", " ").capitalize(), not isinstance(rows[0][c], str)) for c in cols]
    return ('<details class="tableview"><summary>Show the numbers</summary>'
            + table(head, [(False, [fmt(r[c]) for c in cols]) for r in rows]) + "</details>")


# ---------------------------------------------------------------- pages

SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Landfill detection in Gujarat</title>
<meta name="description" content="{desc}">
<script src="site/js/theme.js"></script>
<link rel="stylesheet" href="site/css/site.css">
</head>
<body data-page="{slug}">
<a class="skip" href="#main">Skip to the text</a>
<header class="top">
  <a class="brand" href="index.html"><span>Landfill detection, Gujarat<small>IIT Gandhinagar · ES 678 · 2026</small></span></a>
  <nav id="nav" aria-label="Pages">{nav}</nav>
  <div class="tools"><button class="theme" type="button" aria-label="Switch between light and dark">◐ Theme</button><button class="menu" aria-expanded="false" aria-controls="nav">Menu</button></div>
</header>
<main id="main">
<div class="pagehead"><div class="in">
  <p class="kicker">{kicker}</p>
  <h1>{h1}</h1>
  <p class="lede">{lede}</p>
  <nav class="onpage" aria-label="On this page"><b>On this page</b> {toc}</nav>
</div></div>
<article>
{body}
</article>
<nav class="pager" aria-label="Previous and next page">{prev}{next}</nav>
</main>
<footer class="foot">
  <p><a href="https://github.com/wre9-tesh/ML_Landfill_Detection">Repository</a> · {paper}<a href="project_guide_grader.pdf">Grader's manual</a> · <a href="reproduce.html#glossary">Glossary</a> · <a href="reproduce.html#ai-use">AI-use disclosure</a></p>
  <p class="small">Amitesh Kumar (24210011) · IIT Gandhinagar · ES 678 · Numbers filled from the result files by build_site_data.py · Contains modified Copernicus Sentinel data 2023 to 2024</p>
</footer>
<script src="site/vendor/d3.min.js" defer></script>
<script src="site/vendor/plot.min.js" defer></script>
<script src="site/js/common.js" defer></script>
{scripts}
</body>
</html>
"""


def build_pages(svgs):
    paper = '<a href="paper.pdf">Paper (PDF)</a> · ' if (DOCS / "paper.pdf").exists() else ""
    used, missing = set(), []

    def fill(m):
        kind, arg = m.group(1), m.group(2)
        try:
            if kind == "k":
                used.add(arg)
                e = K[arg]
                cls = ' class="pending"' if e["v"] is None else ""
                return f'<span data-k="{arg}"{cls}>{html.escape(str(e["s"]))}</span>'
            if kind == "table":
                return gen_table(arg)
            if kind == "tv":
                return table_view(arg)
            if kind == "gen":
                return {"boxes": box_maps}[arg]()
            if kind == "svg":
                return svgs[arg]
            if kind == "note":
                term, text = GLOSSARY[arg]
                return f'<aside class="note"><b>{html.escape(term)}.</b> {text}</aside>'
            if kind == "term":
                slug, _, text = arg.partition("|")
                GLOSSARY[slug]
                return f'<a class="term" href="reproduce.html#g-{slug}">{text or GLOSSARY[slug][0]}</a>'
        except KeyError:
            missing.append(m.group(0))
            return m.group(0)
        raise KeyError(kind)

    gl = "<dl class=\"glossary\">" + "".join(
        f'<dt id="g-{s}">{html.escape(t)}</dt><dd>{x}</dd>' for s, (t, x) in sorted(GLOSSARY.items(), key=lambda kv: kv[1][0].lower())) + "</dl>"
    for i, pg in enumerate(PAGES):
        body = (SRC / f"{pg['slug']}.html").read_text(encoding="utf-8").replace("{{glossary}}", gl)
        body = re.sub(r"\{\{(k|table|tv|svg|note|term|gen):([^}]+)\}\}", fill, body)
        parts = re.split(r'<h2 id="([^"]+)">(.*?)</h2>', body)
        toc_items = list(zip(parts[1::3], parts[2::3]))
        body = (f'<div class="intro">{parts[0]}</div>' if parts[0].strip() else "") + "".join(
            f'<section class="sec" id="{a}"><div class="sec-l"><span class="lab">§ {n:02d}</span><h2>{t}</h2></div><div class="sec-r">{c}</div></section>'
            for n, (a, t, c) in enumerate(zip(parts[1::3], parts[2::3], parts[3::3]), 1))
        toc = " ".join(f'<a href="#{a}">{re.sub("<[^>]+>", "", t)}</a>' for a, t in toc_items)
        nav = "".join(f'<a href="{p["slug"]}.html"' + (' aria-current="page"' if p is pg else "") + f'>{p["nav"]}</a>' for p in PAGES)
        prev = f'<a class="prev" href="{PAGES[i - 1]["slug"]}.html"><small>Previous</small>← {PAGES[i - 1]["nav"]}</a>' if i else "<span></span>"
        nxt = f'<a class="next" href="{PAGES[i + 1]["slug"]}.html"><small>Up next · page {i + 2}</small>{PAGES[i + 1]["nav"]} →</a>' if i + 1 < len(PAGES) else "<span></span>"
        scripts = "".join(f'<script src="site/js/{s}.js" defer></script>\n' for s in pg.get("scripts", ["charts"]))
        page = SHELL.format(title=pg["nav"], desc=html.escape(pg["lede"]), slug=pg["slug"], nav=nav, kicker=f"Page {i + 1} of {len(PAGES)} · {pg['nav']}",
                            h1=pg["h1"], lede=pg["lede"], toc=toc, body=body, prev=prev, next=nxt, paper=paper,
                            scripts=scripts)
        FILES[DOCS / f"{pg['slug']}.html"] = page.encode("utf-8")
    if missing:
        sys.exit("placeholders that cannot be filled: " + ", ".join(sorted(set(missing))))
    return used


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    oof, rec, alarms = numbers()
    hand_check(alarms)
    new_cities()
    features()
    threshold(oof, rec)
    svgs = svg_maps(rec)
    T["F-R6"] = [{"id": r["id"], "city": r["city"], "rank": r["rank"], "status": r["status"]} for r in sorted(T["T-R2"], key=lambda r: r["rank"])]
    T["F-R3"] = [{"id": r["id"], "site": f"{r['city']} ({r['id']})", "share_flagged": r["share_flagged"], "status": r["status"]} for r in T["T-R2"]]
    chips = SITE / "data/chips.json"
    T["chips"] = json.loads(chips.read_text(encoding="utf-8")) if chips.exists() else []
    b = pd.read_csv(GUJ / "blind_check.csv", keep_default_na=False)
    T["verdicts"] = {r.blind_id: {"verdict": r.verdict.strip().lower().replace("look_alike", "lookalike"),
                                  "seen": (r.seen.strip().lower() or r.verdict.strip().lower())} for r in b.itertuples() if r.verdict.strip()}
    used = build_pages(svgs)
    FILES[SITE / "data/site.json"] = (json.dumps(K, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    FILES[SITE / "data/tables.json"] = json.dumps(T, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    pending = sorted(k for k in used if K[k]["v"] is None)
    stale = [p for p, data in FILES.items() if not p.exists() or p.read_bytes() != data]
    if args.check:
        for p in stale:
            print(f"out of date: {p.relative_to(REPO)}")
        print(f"{len(FILES)} files checked, {len(stale)} out of date; pending numbers: {', '.join(pending) or 'none'}")
        return 1 if stale else 0
    for p, data in FILES.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists() or p.read_bytes() != data:
            p.write_bytes(data)
    print(f"wrote {len(stale)} of {len(FILES)} files; {len(K)} numbers, {len(used)} used in the pages; pending: {', '.join(pending) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
