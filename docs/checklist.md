# Dumpsite project — checklist to Nov 17

Oct 27, 2026 · @VXCIO

> Exported 31 Oct 2026 from the Claude Docs checklist (revision 7): https://claude.ai/artifact/G9CZC7b3Ew6kSD9A16DLLP

## Phase 1 — labels (Oct 27 – Nov 2)

The only input nothing downstream can fix. Gate 1 is Nov 2, 2026: both label sets exist and the Gujarat one is closed.

### India training labels

- [ ] Export OSM `landuse=landfill` polygons for India. Overpass and the Geofabrik downloads are blocked from Claude's workspace, so run this locally (query below) or download the India `.osm.pbf` extract and filter with osmium.
- [ ] Drop anything tagged disused, abandoned or `landuse=quarry`.
- [ ] Pull the 80-site list from Agrawal et al. (2026) Appendix B — supplementary file first, email the corresponding author if it is not there.
- [ ] Add the 53 Madhya Pradesh sites from Bhajantri & Mandpe (2026).
- [ ] Move every Gujarat site found in any of these sources into the test set, not the training set.
- [ ] Screen each remaining site by eye in Google Earth Pro. Record a keep/drop decision per site — this file is a paper figure later.
- [ ] Target 300+ active sites across several states. Note the per-state counts; leave-one-state-out needs at least four or five states with real coverage.

### Negatives

- [ ] Random pixels drawn from the same training states, matched roughly to the positive count.
- [ ] 300 hand-checked look-alikes: quarries, bare soil, construction sites, dry riverbeds, brick kilns. Record which class each one is — the failure audit in Phase 4 reads this column.

### Gujarat test labels (sealed)

- [ ] Write up your 14 known sites across 10 cities with coordinates and city names.
- [ ] Get to 20+ from the GPCB annual report under the SWM Rules, NGT filings, and the SBM-U / DRAP dashboards.
- [ ] Confirm each one by eye.
- [ ] Save to a file, commit it, and do not open it again until Nov 9.

### Overpass query to run locally

```
[out:json][timeout:600];
area["ISO3166-1"="IN"][admin_level=2]->.in;
(
  way["landuse"="landfill"](area.in);
  relation["landuse"="landfill"](area.in);
);
out geom;
```

Paste it into overpass-turbo.eu and export as GeoJSON. If it times out, split by state with a smaller area filter.

### Fallback

If you reach Nov 2 with fewer than 200 screened India sites, stop screening and proceed anyway. Report the number you got and treat the shortfall as a stated limitation. Do not let this phase eat into Phase 2.

## Phase 2 — features and models (Nov 3 – 7)

The week with the most ways to lose time. Gate 2 is Nov 7, 2026: leave-one-state-out results in hand for all four models.

### Feature stack in GEE

- [ ] Sentinel-2 surface reflectance, 2024 pre-monsoon, cloud filter under 10%, median composite. Bands 3, 4, 8, 11.
- [ ] NDVI and NDBI computed from those bands.
- [ ] Landsat 8/9 LST, same 2024 pre-monsoon window, median composite, resampled to 10 m.
- [ ] LST anomaly: the pixel's LST minus the mean over a 2 km neighbourhood. This is the feature that should travel across states better than an absolute cut-off.
- [ ] SRTM elevation and slope.
- [ ] Export the sampled feature table for all training points and all negatives. Sample, do not export rasters — you only need rasters for Gujarat in Phase 3.

### Models

- [ ] Flag-nothing reference. Trivial, but it anchors the precision discussion and takes five minutes.
- [ ] Threshold rule using the published Madhya Pradesh cut-offs (NDBI > 0.028, NDVI < 0.15, LST > 37.0 °C), cited to Bhajantri & Mandpe (2026).
- [ ] The same rule recalibrated on your training states.
- [ ] Logistic regression.
- [ ] Random forest.

### Validation

- [ ] Leave-one-state-out as the headline. One fold per state with enough sites.
- [ ] Random-pixel split and site-grouped split computed too, reported only as contrast. These are the first two rungs of the Phase 4 ablation, so compute them now while the pipeline is open.
- [ ] Report precision, recall and F1 per fold, not just the mean. Fold variance is a result in itself.

### Risks this week

GEE export limits and the 30 m to 10 m LST resampling are where days disappear. Sort the Contributor tier before the phase starts, not during it. If the LST anomaly turns out expensive to compute at scale, drop the neighbourhood size to 1 km rather than dropping the feature.

## Phase 3 — freeze, then Gujarat (Nov 9 – 11)

Three days is enough because by now there are no decisions left, only a run. Gate 3 is Nov 11, 2026: results frozen and not revisited.

### Freeze checklist (Nov 9, before anything else)

- [ ] Pick the one model you will report as primary, based on leave-one-state-out results alone.
- [ ] Fix its hyperparameters, its decision threshold, and the feature list.
- [ ] Commit all of it. Tag the commit. The tag is your evidence at the viva that the freeze happened before the test.
- [ ] Write down, now, what result would count as failure. Deciding this after seeing Gujarat is how a negative result gets quietly reframed as a success.

### The Gujarat pass (Nov 10 – 11)

- [ ] Build the same feature stack over the Gujarat test districts.
- [ ] Score every pixel. This is the real-rarity test — no balanced sampling, no restriction to candidate areas.
- [ ] Report recall against your sealed site list.
- [ ] Take the top 100 scoring candidates, strip the scores, and check them by eye in random order. Blind means you do not know which rank you are looking at while you judge.
- [ ] Record each one as dumpsite, look-alike (with class), or unclear. That gives you precision at the top of the ranking, which is the number that actually matters operationally.

### The rule for this phase

If the Gujarat numbers are bad, they are the result. Write them up. A threshold retuned after seeing them makes every number in the paper unverifiable, and the rubric does not reward accuracy as a standalone criterion anyway. Threshold sensitivity on Gujarat is allowed in Phase 4 as a post-hoc analysis that selects nothing.

## Phase 4 — depth analysis and paper (Nov 12 – 15)

Four pages including references, two columns, the course LaTeX template adapted from NeurIPS 2026.

### Depth analysis

- [ ] Split ablation. Same model, four evaluation designs: random pixel, held-out site, held-out state, Gujarat. One table or one chart showing the metric falling as validation gets honest. Prioritise this — it is the result that makes the paper interesting whether or not the model works.
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

## Phase 5 — site, repo, submit (Nov 16 – 17)

Submission is Nov 17, 2026.

### Results map

- [ ] Static page, GitHub Pages plus Leaflet, built from the frozen Phase 3 output. No backend, no live inference.
- [ ] Gujarat candidates as a GeoJSON. Click a point for the Sentinel-2 chip, the model score, NDVI / NDBI / LST values, and the blind-check verdict.
- [ ] Keep it to one day. It is not in the rubric except as reproducibility support, and the paper comes first.

### Repository

- [ ] Code, the label files, the frozen model, and the environment spec.
- [ ] README with the exact run order and a one-line statement of what the freeze tag means.
- [ ] Check the repo runs from a clean clone. Reproducibility is 5 marks and is the cheapest 5 on the sheet.

### Submit

- [ ] Paper PDF, source and reproducibility materials, through the portal.
- [ ] Re-read the submission page for anything the proposal form did not mention.
- [ ] Prepare for the individual defense: be ready to say exactly when the freeze happened and why the ablation matters.

## Standing items

No fixed date, but each one blocks something if left.

- [ ] Put the GEE project on the Contributor tier (1,000 EECU-hours a month). Do this before Phase 2 starts.
- [ ] Check the registered project title still matches the proposal as submitted. If it does not, ask the course staff now rather than at submission.
- [ ] Keep a running note of AI tools used and what for, so the disclosure is not reconstructed from memory on Nov 15.
- [ ] Update the project plan doc, which still describes the earlier replication design and a Nov 10 deadline.

### Slack

This plan has one spare day, the Diwali buffer on Nov 8. That is thin. If a gate slips by more than a day, cut scope rather than the buffer: drop the recalibrated threshold rule, drop the second figure, or reduce the blind eye check from 100 candidates to 50. Do not cut the split ablation or the freeze.
