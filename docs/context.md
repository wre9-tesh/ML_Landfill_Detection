# Project context

Hand-off notes for picking this project up in a new session. Written Tue Nov 10, 2026, evening. The plan of record is `docs/checklist.md`; this file says where things stand and why.

## The project

ES 678, graduate track, solo. Detect landfills and dumpsites in Gujarat from free satellite data. Train only on Indian sites outside Gujarat, freeze every choice, then test once on Gujarat.

**Due Tue Nov 17, 2026.** Deliverables:

- A four-page paper in the course LaTeX template (adapted from NeurIPS 2026).
- The repo, reproducible from a clean clone.
- The depth analysis (graduate track).
- A presentation website. There is no viva; the website replaces it. The paper is still required and comes first if time runs short.

**Research questions**

1. Does a model trained outside Gujarat find Gujarat's dumpsites?
2. How much does the validation design change the score (random pixel → held-out site → held-out state → Gujarat)?
3. What precision does the model have when dumpsites are rare? A published 93% on a balanced test becomes about 12% precision at 1% prevalence.

## Where things stand

| Item | Status |
| --- | --- |
| OSM screening | Done, pushed to main (commit `6b95c7d`). 12 kept sites in 10 states; 72 drops, of which 45 are look-alikes (ash_pond 27, quarry 10, bare_soil 8). The rows under 1 ha were deleted, which is fine. Row 855 is junk (an "a" in several columns) and must be deleted. |
| Own training sites | About 75 outlined in Google Earth, outside Gujarat. To be sent as `labels/extra_sites.kml` on Nov 11. With the OSM 12, about 87 sites, inside the 80–120 target. |
| Gujarat test list | 14 own sites in 10 cities plus 2 from OSM (Pirana in Ahmedabad, and Vadodara). Target 20 or more. To be sent as `labels/gujarat_test.kml` on Nov 11. The rest of the 47 OSM Gujarat candidates were fly-ash ponds and coal piles. |
| Earth Engine | Works on the user's Windows machine. The `--limit 50` test passed on Nov 10: all 12 features filled (B2 mean 0.109, LST 41.5 °C, LST_anom mean −0.65 because the first points were mostly ash ponds). |
| Model script | Not written yet. Claude writes it on Nov 11 while the full feature fetch runs. |
| Outline merging | Not written yet: extra sites within 500 m of each other become one place, and any within 500 m of a kept OSM site are flagged so the user picks one outline. |
| Gujarat scoring script | Not written yet. The approach and the scoring area are open (see below). |
| Website, README, depth analysis | Not started. |

## Schedule

| Day | User | Claude |
| --- | --- | --- |
| Wed 11 | Morning: push `gujarat_test.kml`, `extra_sites.kml`, any `lookalikes.kml`, and the screening CSV without row 855. Midday: pull, run the full fetch, push `data/features/`. Evening: approve the freeze draft, write the failure criterion, tag and push the freeze. | Seal the Gujarat list in its own commit, convert and merge sites, run the sampler, push points. Write the model script during the fetch. Run the models; send the results table and a filled-in freeze draft. |
| Thu 12 | Score Gujarat in Earth Engine; blind-check the top 100 alarms. | Gujarat scoring script; recall against the sealed list. |
| Fri 13 | Start the paper. | Depth analysis: split ablation, feature ablation, precision against prevalence, failure audit. |
| Sat 14 – Sun 15 | Write the paper. | Build the website at the same time; figures; README. |
| Mon 16 | Spare. | Spare. |
| Tue 17 | Submit. | Fixes. |

If a day slips, cut in this order: results map, recalibrated threshold rule, second figure, feature ablation down to A0/A1/A4, blind check from 100 to 50. Never cut the freeze or the split ablation.

## Decisions already made

These were fixed before any results and must not change after seeing them.

**Labels**

- A site counts if active dumping is visible in March–May 2024 imagery. If only 2023 and 2025 exist, keep it when active on both and outline only the area that is waste on both. Active in only one of them → `unsure`, unless Sentinel-2 from April 2024 settles it.
- Minimum 1 ha of visible waste, measured on the waste, not the compound. Smaller is `drop`, `too_small`. The same rule applies to Gujarat: sites under 1 ha stay on the list but are left out of recall and reported separately.
- Biomining areas are included while waste is still there; finished, levelled ground is not.
- Small green patches stay inside outlines. Large ones at the edge are routed around; large interior ones are handled by splitting the site into several outlines.
- A site in both OSM and the user's list is entered once: OSM `keep` if its outline is good; otherwise OSM `drop`, `mislocated`, plus the user's outline named `fix NNNN`.
- Drop classes that become look-alikes: quarry (includes mine, ore, spoil, coal overburden), kiln, bare_soil, construction, riverbed, ash_pond, industrial (slag, coal, stockyards, red mud, gypsum). Drops with no points: not_visible, inactive, mislocated, too_small, other.
- The Gujarat list holds confirmed dumps only; non-dumps are skipped, not labelled. Nothing from Gujarat is ever used in training.

**Features (12)**, March–May 2024 medians: Sentinel-2 B2, B3, B4, B8, B11; NDVI, NDBI, BSI; Landsat 8/9 LST and LST_anom (LST minus the land mean within 2 km, water excluded); SRTM elevation and slope. BSI and B2 were added on Nov 9, before any model was run.

**Models (9)**, scikit-learn defaults, class-balanced, threshold 0.5, no tuning: flag-nothing reference; published threshold rule (NDBI > 0.028, NDVI < 0.15, LST > 37.0 °C); recalibrated threshold rule; logistic regression; decision tree; bagged trees (200); random forest (500, plus out-of-bag score); AdaBoost (200 stumps, SAMME); gradient boosting (100 trees, depth 3, learning rate 0.1).

**Validation**

- Headline is leave-one-state-out. A state needs 10 or more kept places to be its own fold. If fewer than 5 states qualify, which is likely, the folds are the Zonal Council regions.
- Random-pixel and site-grouped splits are computed as contrast.
- Precision, recall and F1 are reported per fold.
- Selection: the best mean leave-one-state-out F1. If a simpler model is within one SD of it, take the simpler one. Order from simplest: published rule, recalibrated rule, logistic regression, tree, bagging, random forest, AdaBoost, gradient boosting.

**Ablations**

- Split ablation: the same model under random pixel, held-out site, held-out state and Gujarat.
- Feature ablation: the frozen model retrained on A0 (all 12), A1 (NDVI, NDBI, LST), A2 (A1 + BSI), A3 (the original 10, without BSI and B2), A4 (no thermal), A5 (no terrain). These never choose the model.

**Freeze**: tag the commit and push the tag before Gujarat is scored.

## Open decisions for the freeze (Nov 11)

- Which model, its features and threshold (from the selection rule).
- How a Gujarat site counts as found. The proposal is any flagged pixel inside its outline.
- **The scoring area.** The plan says every pixel of the test districts, which is tens of gigabytes if exported. There are two options:
  - Convert the model into Earth Engine and score whole districts there. This is easy for tree ensembles and logistic regression, harder for gradient boosting and AdaBoost.
  - Export the 12 features for a buffer of about 10 km around each test city and score them locally. This works for any model, at roughly 75 MB per city.

  Pick one before scoring.
- One sentence on what result counts as failure.

## Website

Static site on GitHub Pages, built from the frozen outputs. There is no image upload: the model reads 12 values per 10 m pixel, which a screenshot doesn't contain.

It shows:
- a clickable Gujarat score map, with the test sites marked found or missed and the top alarms with their blind-check verdicts;
- the split-ablation chart;
- a precision-versus-prevalence slider;
- a gallery of look-alikes the model confused with dumps.

Call the number a "model score", not a confidence. A live Earth Engine App is a stretch goal only.

## Working setup

- **Repo:** `wre9-tesh/ML_Landfill_Detection`.
  - The user pushes to `main`. Claude works on `claude/pensive-mayer-93qak9`, and the user gets those changes with `git pull origin claude/pensive-mayer-93qak9`. PRs #1–#6 are merged.
  - The branch's last commit (`8012784`, website in the checklist) is not on main yet, and main's `6b95c7d` is not on the branch.
- **User's machine:** Windows PowerShell, repo at `D:\COursework\ML\project\ML_Landfill_Detection`.
  - The `earthengine` command is not on PATH. Use `python -m pip install earthengine-api` and `python -c "import ee; ee.Authenticate()"`.
  - Feature fetch: `python scripts/gee_features.py --project <id>`. It caches fetched points in `data/features/cache.csv`.
- **Run order:**
  1. `scripts/osm_to_screening.py` (done)
  2. `scripts/kml_to_csv.py <file> --kind gujarat|extra|lookalike`
  3. `scripts/build_samples.py`
  4. `scripts/gee_features.py`
  5. Models (to come)
  6. Freeze
  7. Gujarat scoring (to come)
- **Docs:**
  - `docs/checklist.md`: the plan of record.
  - `docs/phase1_labels.md`: labelling rules.
  - `docs/phase2_features.md`: sampling and features.
  - `data/README.md`: sources and licences.
- **Pages (private):**
  - Proposal: https://claude.ai/artifact/LFQg1EbYhc9SqZAA2Gn5oF
  - Checklist: https://claude.ai/artifact/LcQnEBbirVd1bGze7qrBwp (still shows the old dates).
- **References to verify before the paper:** Agrawal et al., and the journal version of Bhajantri & Mandpe. Only the preprint of the latter was found.
