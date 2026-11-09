# Dumpsite project — checklist to Nov 17

Oct 27, 2026 · @VXCIO · revised Nov 3, 2026 for the late start and Nov 4, 2026 for Gate 1 and the model rules

> Exported 31 Oct 2026 from the Claude Docs checklist (revision 7): https://claude.ai/artifact/G9CZC7b3Ew6kSD9A16DLLP. The doc still has the original Oct 27 dates; this file has the revised ones.

Work started on Nov 3 rather than Oct 27, leaving 15 days instead of 22. Phase 2 shrinks because its code is written during Phase 1; the rest of the time comes from the scope cuts under Slack. On Nov 4, Gate 1 moved to Fri Nov 6, which leaves Phase 2 a single day.

| Phase | Dates | Gate |
| --- | --- | --- |
| 1 Labels | Tue Nov 3 – Fri Nov 6 | Fri Nov 6: Gujarat list sealed and pushed; India screening stops wherever it has reached |
| 2 Features and models | Sat Nov 7 | Sat Nov 7: leave-one-state-out results for every model |
| Diwali | Sun Nov 8 | |
| 3 Freeze, then Gujarat | Mon Nov 9 – Tue Nov 10 | Tue Nov 10: results frozen and not revisited |
| 4 Depth analysis and paper | Wed Nov 11 – Sat Nov 14 | |
| 5 Site, repo, submit | Sun Nov 15 – Tue Nov 17 | Submit Tue Nov 17 |

## Phase 1 — labels (Nov 3 – 6)

The only input nothing downstream can fix. Gate 1 is Fri Nov 6, 2026: the Gujarat list is sealed and pushed, and India screening stops wherever it has reached. Step-by-step instructions are in [phase1_labels.md](phase1_labels.md).

### India training labels

- [x] Export OSM `landuse=landfill` nodes, ways and relations for India with the query in [phase1_labels.md](phase1_labels.md). Overpass is blocked from Claude's workspace, so run it in your browser at overpass-turbo.eu and upload the GeoJSON, or run `scripts/osm_to_screening.py` yourself.
- [ ] Check `labels/osm_excluded.csv`: the script drops anything tagged disused, abandoned or with an end date, anything with "quarry" in its name, and sites in Dadra and Nagar Haveli and Daman and Diu.
- [ ] Check the Agrawal et al. (2026) supplementary file for the Appendix B 80-site list, 15 minutes at most. Don't email the author: a reply would not arrive in time.
- [ ] Add the 53 Madhya Pradesh sites from Bhajantri & Mandpe (2026).
- [ ] Move every Gujarat site found in any of these sources into the test set, not the training set. The script already does this for OSM.
- [ ] Screen each remaining site by eye in Google Earth Pro, in `screen_order`, against the imagery closest to March–May 2024. Record a keep/drop decision per site in `labels/india_screening.csv` — this file is a paper figure later.
- [ ] Screen until Friday evening; there is no fixed target. Note the per-state counts; leave-one-state-out needs at least four or five states with real coverage.

### Negatives

- [ ] Random pixels drawn from the same training states, matched roughly to the positive count.
- [ ] About 100 hand-checked look-alikes: quarries, bare soil, construction sites, dry riverbeds, brick kilns. Record which class each one is — the failure audit in Phase 4 reads this column. Sites dropped while screening as `quarry`, `kiln`, `bare_soil`, `construction` or `riverbed` count towards this.

### Gujarat test labels (sealed)

- [ ] Put your 14 known sites across 10 cities into a `gujarat_test` folder in Google Earth Pro, named `City | site name`, with outlines where you can.
- [ ] Get to 20+ from the GPCB annual report under the SWM Rules, NGT filings, the SBM-U / DRAP dashboards and `labels/gujarat_osm_candidates.kml`.
- [ ] Confirm each one by eye.
- [ ] Save as `labels/gujarat_test.kml`, convert it with `scripts/kml_to_csv.py --kind gujarat`, commit both files and push by Fri Nov 6. Do not open them again until Nov 9.

### In parallel: code (Claude)

- [x] `scripts/build_samples.py`: screening decisions to sample points (written Nov 4; see [phase2_features.md](phase2_features.md)).
- [x] `scripts/gee_features.py`: the Phase 2 feature stack, sampled at those points (written Nov 4).
- [ ] First real run on about 100 screened rows, Thu Nov 5: you run both scripts and push `data/samples/` and `data/features/`.
- [ ] Model and validation code: the nine models, the three splits, per-fold metrics and the selection rule below; dry run on the Nov 5 features.

### Fallback

If you reach Friday evening, Nov 6, with fewer than 200 screened India sites, stop screening and proceed anyway. Report the number you got and treat the shortfall as a stated limitation. Do not let this phase eat into Phase 2.

## Phase 2 — features and models (Nov 7)

One day, which works only because the code is written and dry-run during Phase 1. Gate 2 is Sat Nov 7, 2026: leave-one-state-out results in hand for every model.

### Feature stack in GEE

Implemented in `scripts/gee_features.py`; the processing details are in [phase2_features.md](phase2_features.md).

- [ ] Sentinel-2 surface reflectance, 2024 pre-monsoon, cloud filter under 10%, median composite. Bands 3, 4, 8, 11.
- [ ] NDVI and NDBI computed from those bands.
- [ ] Landsat 8/9 LST, same 2024 pre-monsoon window, median composite, resampled to 10 m.
- [ ] LST anomaly: the pixel's LST minus the mean over a 2 km neighbourhood. This is the feature that should travel across states better than an absolute cut-off.
- [ ] SRTM elevation and slope.
- [ ] Export the sampled feature table for all training points and all negatives. Sample, do not export rasters — you only need rasters for Gujarat in Phase 3.

### Models

Fixed on Nov 4, before any results. No hyperparameter tuning: scikit-learn defaults except where stated, with class-balanced weights so that every model is compared at a 0.5 probability threshold.

- [ ] Flag-nothing reference. Trivial, but it anchors the precision discussion and takes five minutes.
- [ ] Threshold rule using the published Madhya Pradesh cut-offs (NDBI > 0.028, NDVI < 0.15, LST > 37.0 °C), cited to Bhajantri & Mandpe (2026).
- [ ] The same rule recalibrated on your training states: the three cut-offs refitted inside each round.
- [ ] Logistic regression on standardised features.
- [ ] Decision tree, fully grown: the single-tree reference, low bias and high variance.
- [ ] Bagged trees: 200 fully grown trees.
- [ ] Random forest: 500 trees; also record its out-of-bag score.
- [ ] AdaBoost: 200 stumps (scikit-learn's SAMME).
- [ ] Gradient boosting: scikit-learn defaults (100 trees of depth 3, learning rate 0.1). Its leaf values are the single Newton step derived in the course notes.

### Validation

Rules fixed on Nov 4, before any results:

- [ ] Leave-one-state-out as the headline. A state with at least 10 kept places (distinct `group_id`s) is its own validation fold; smaller states are in the training data of every fold and are never scored. If fewer than five states qualify, the folds are the Zonal Council regions instead (Northern, Central, Eastern, Western, Southern, North-Eastern), so no grouping is chosen after seeing results.
- [ ] Random-pixel split and site-grouped split computed too, reported only as contrast. These are the first two rungs of the Phase 4 ablation, so compute them now while the pipeline is open.
- [ ] Features: the twelve in `docs/phase2_features.md` (B2, B3, B4, B8, B11, NDVI, NDBI, BSI, LST, LST_anom, elev, slope). BSI and B2 were added on Nov 9, before any model was run. Every model in the comparison uses all twelve; the feature sets in the Phase 4 feature ablation are fixed here and are never used to choose the primary model.
- [ ] Report precision, recall and F1 per fold, not just the mean. Fold variance is a result in itself.
- [ ] Selection rule for the primary model: the best mean leave-one-state-out F1. If a simpler model is within one standard deviation (across folds) of the best, take the simpler one. Simplest first: published threshold rule, recalibrated threshold rule, logistic regression, decision tree, bagged trees, random forest, AdaBoost, gradient boosting.

### Risks this week

GEE export limits and the 30 m to 10 m LST resampling are where days disappear. Sort the Contributor tier on Nov 3, not during this phase. If the LST anomaly turns out expensive to compute at scale, drop the neighbourhood size to 1 km rather than dropping the feature.

## Phase 3 — freeze, then Gujarat (Nov 9 – 10)

Two days is enough because by now there are no decisions left, only a run. Gate 3 is Tue Nov 10, 2026: results frozen and not revisited.

### Freeze checklist (Nov 9, before anything else)

- [ ] Pick the one model you will report as primary, based on leave-one-state-out results alone, using the selection rule fixed in Phase 2.
- [ ] Fix its hyperparameters, its decision threshold, and the feature list.
- [ ] Fix how a Gujarat site counts as found: a flagged pixel inside its outline, or within a stated radius of its pin.
- [ ] Apply the same 1 ha minimum to Gujarat: sites under 1 ha stay on the list but are left out of the recall count and reported separately.
- [ ] Commit all of it. Tag the commit and push the tag before scoring Gujarat. The tag is your evidence, on the website and in the paper, that the freeze happened before the test, and the push gives it a GitHub timestamp.
- [ ] Write down, now, what result would count as failure. Deciding this after seeing Gujarat is how a negative result gets quietly reframed as a success.

### The Gujarat pass (Nov 9 – 10)

- [ ] Build the same feature stack over the Gujarat test districts.
- [ ] Score every pixel. This is the real-rarity test — no balanced sampling, no restriction to candidate areas.
- [ ] Report recall against your sealed site list.
- [ ] Take the top 100 scoring candidates, strip the scores, and check them by eye in random order. Blind means you do not know which rank you are looking at while you judge.
- [ ] Record each one as dumpsite, look-alike (with class), or unclear. That gives you precision at the top of the ranking, which is the number that actually matters operationally.

### The rule for this phase

If the Gujarat numbers are bad, they are the result. Write them up. A threshold retuned after seeing them makes every number in the paper unverifiable, and the rubric does not reward accuracy as a standalone criterion anyway. Threshold sensitivity on Gujarat is allowed in Phase 4 as a post-hoc analysis that selects nothing.

## Phase 4 — depth analysis and paper (Nov 11 – 14)

Four pages including references, two columns, the course LaTeX template adapted from NeurIPS 2026.

### Depth analysis

- [ ] Split ablation. Here the thing changed is the evaluation, not the model. Same model, four evaluation designs: random pixel, held-out site, held-out state, Gujarat. One table or one chart showing the metric falling as validation gets honest. Prioritise this — it is the result that makes the paper interesting whether or not the model works. Run it for every model, so the drop from random pixel to held-out state can be compared between bagging and boosting, and add the random forest's out-of-bag score as an extra rung: it is a random-pixel estimate in disguise.
- [ ] Feature ablation. An ablation removes one part of the method and re-measures, so you can say what each part contributes. Retrain the frozen primary model, with the same settings, on each feature set below and report leave-one-state-out F1 (mean and SD across folds) next to the full model. Gujarat numbers for these rows are post-hoc and select nothing; the frozen full model stays the reported result.
  - A0 full: all twelve features (the frozen model)
  - A1 published: NDVI, NDBI, LST only, the inputs of the published threshold rule
  - A2 published + BSI: NDVI, NDBI, BSI, LST
  - A3 no BSI: full minus BSI and B2, the original ten
  - A4 no thermal: full minus LST and LST_anom
  - A5 no terrain: full minus elev and slope
  If time is short, keep A0, A1 and A4: they answer whether more features than the published three help, and whether the expensive thermal features earn their place.
- [ ] Precision versus prevalence. Derive what your measured TPR and FPR imply for precision at realistic dumpsite prevalence, and contrast with precision measured on a balanced test set. Use pixel counts rather than percentages — it reads more clearly.
- [ ] Threshold sensitivity on Gujarat, post-hoc, explicitly selecting nothing.
- [ ] Failure audit. Break the false positives down by look-alike class and by region, using the class column from Phase 1.

### Paper

- [ ] Set up the LaTeX template on day one of this phase, not day four. Template surprises at four pages are real.
- [ ] Draft in this order: methods, results, limitations, discussion, introduction, abstract. The introduction is easiest to write once you know what you found.
- [ ] Budget: roughly half a page introduction, one page methods, one and a half pages results and ablation, half a page limitations and discussion, half a page references.
- [ ] Two figures maximum at four pages. The split ablation is one of them. The second is either the Gujarat candidate map or the precision-prevalence curve.
- [ ] State the AI tools used and the kinds of assistance, as the course requires.
- [ ] Cite Bhajantri & Mandpe (2026) where their cut-offs serve as the baseline, and every other external source.

## Phase 5 — website, repo, submit (Nov 15 – 17)

Submission is Tue Nov 17, 2026. Sun Nov 15 is for the results map and the repo, Mon Nov 16 for the clean-clone check and otherwise spare.

### Presentation website

There is no viva. The work is presented through a website, alongside the four-page paper, which is still required.

- [ ] Static site on GitHub Pages, built from the frozen Phase 3 output. No backend, no live inference, so nothing can break during the presentation.
- [ ] No image upload. The model reads 12 values per 10 m pixel (Sentinel-2 bands including shortwave infrared, Landsat temperature, terrain), which a screenshot does not contain; an image classifier would be a different, unevaluated model.
- [ ] Map: the model score over the Gujarat test districts, the sealed test sites marked found or missed, and the top alarms with their blind-check verdicts. Clicking a spot or pasting coordinates shows the score, the 12 feature values and what is on the ground.
- [ ] Call the number a model score, not a confidence or probability, and show next to it what precision it implies at realistic prevalence.
- [ ] Story sections: the question; the freeze and the held-out state; the split ablation chart; a precision-versus-prevalence slider; a gallery of look-alikes the model confused with dumps.
- [ ] The Gujarat scoring step exports the score map as tiles for the site.
- [ ] Claude builds the site; you write the text and check it. The paper comes first if time runs short.
- [ ] Stretch, only if everything else is done: an Earth Engine App that scores any clicked point in India live.

### Repository

- [ ] Code, the label files, the frozen model, and the environment spec.
- [ ] README with the exact run order and a one-line statement of what the freeze tag means.
- [ ] Check the repo runs from a clean clone. Reproducibility is 5 marks and is the cheapest 5 on the sheet.

### Submit

- [ ] Paper PDF, source and reproducibility materials, through the portal.
- [ ] Re-read the submission page for anything the proposal form did not mention.
- [ ] Website link in the submission. Rehearse the walkthrough: when the freeze happened, why the split ablation matters, and why most high scores are still false alarms at real prevalence.

## Standing items

No fixed date, but each one blocks something if left.

- [ ] Put the GEE project on the Contributor tier (1,000 EECU-hours a month). Do this before the first Earth Engine run on Nov 5.
- [ ] Check the registered project title still matches the proposal as submitted. If it does not, ask the course staff now rather than at submission.
- [ ] Keep a running note of AI tools used and what for, so the disclosure is not reconstructed from memory on Nov 14.
- [ ] Update the project plan doc, which still describes the earlier replication design and a Nov 10 deadline.

### Slack

The late start has already used up the first round of cuts: no 300-site target, about 100 look-alikes instead of 300, no email for Appendix B, and Claude builds the website. Gate 1 then moved a day, to Fri Nov 6, leaving Phase 2 a single day; that only works if both scripts have run on real data by Nov 5. Nov 8 is Diwali, and Mon Nov 16 is the only spare day. If a gate slips by more than a day, cut further rather than spending Nov 16: drop the recalibrated threshold rule, drop the second figure, or reduce the blind eye check from 100 candidates to 50. Do not cut the split ablation or the freeze.
