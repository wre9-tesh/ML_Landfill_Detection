# Freeze, version 3

Written on 14 November 2026, before any version 3 feature was fetched. The rules below are
fixed now; the section "Frozen model" is filled in after training and before Gujarat is scored.

## Why a third version

Versions 1 and 2 flag the known Gujarat sites (16 and 15 of 17) but rank them far below
false alarms: blue roofs and water in version 1, large bare-land patches in version 2. Both
models see one pixel on one date. Version 3 gives the model two things the only field-verified
Sentinel-2 system (Kruse et al. 2023) relied on: a second date and the pixel's surroundings.

## What changes

- **Ten fetched features** (`gee_features.py --stack extra`):
  - `B2_w B11_w NDVI_w NDBI_w BSI_w`: the Sentinel-2 median for 15 November 2023 to
    14 February 2024, the winter crop season.
  - `NDVI_ctx NDBI_ctx BSI_ctx`: mean of the pre-monsoon index within 150 m.
  - `NDVI_sd B11_sd`: standard deviation of the pre-monsoon value within 50 m.
- **Four differences**, computed from the above: `dNDVI` and `dBSI` (winter minus
  pre-monsoon), `NDVI_rel` and `NDBI_rel` (pixel minus its 150 m mean).
- Twenty-six features in all. Training points are the version 2 set (the original points plus
  the near-site background).

## What does not change

- Training uses no Gujarat data. The false alarms checked in Gujarat for versions 1 and 2
  are not used as training examples, because that would train on the test state.
- The nine models, scikit-learn defaults, class-balanced weights, threshold 0.5, no tuning.
- Headline split: held-out region. Selection rule: best mean F1 on it, as in version 2.
- The sealed test list, the found rule (at least half of an outline's scored pixels flagged),
  the alarm definition (touching flagged pixels, at least 1 ha) and Surat LF-3 left out.

## Rules fixed for version 3

- Alarms are ranked by mean score, as in version 1. Ranking by area times score in version 2
  put the largest bare-land patches first.
- Reported for Gujarat: sites found of 17, share of area flagged, number of alarm patches, and
  how many sealed sites stand in the top 50, 100 and 200 patches when left in the list.
- Version 3 counts as an improvement only if more sealed sites stand in the top 100 patches
  than in version 2 (4) with no fewer than 15 of 17 found. Otherwise it is reported as a
  third negative result.
- Versions 1 and 2 stay in the paper whatever version 3 shows.

## Known limits, stated in advance

- The winter composite is from the season before the pre-monsoon one, so a site that opened
  or was capped between them is described inconsistently.
- Neighbourhood features are computed on a 10 m grid in geographic coordinates for both the
  training points and the Gujarat boxes; they are still features of pixels, not of whole sites.
- Three versions have now been scored on the same 17 sites. The test set is no longer unseen
  in the strict sense, and the paper says so.

## Frozen model

To be filled in after training: selected model, held-out-region scores, commit and tag `freeze-v3`.
