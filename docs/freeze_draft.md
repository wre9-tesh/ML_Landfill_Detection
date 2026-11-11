# Freeze draft

Provisional, from the data pushed on Nov 11, 2026. More sites may still be added; if they are, the sampler, the fetch and the models are rerun and this page is filled in again. Nothing here is final until the commit is tagged, and the tag must be pushed before Gujarat is scored. After the tag, no site, feature, model or threshold changes.

## What the rules give

| Item | Value | Where it comes from |
| --- | --- | --- |
| Training data | 86 landfill places (75 hand-drawn, 11 OSM) and 60 look-alike places, none in Gujarat; 9,470 points with all features | `data/samples/samples_summary.txt` |
| Folds | The six Zonal Council regions, because only Maharashtra has 10 or more places | rule fixed Nov 4 |
| Best mean held-out-region F1 | Gradient boosting, 0.865 (SD 0.058) | `data/results/results.md` |
| **Primary model** | **Logistic regression on standardised features**, F1 0.848 (SD 0.037). It is the simplest model at or above 0.807, which is one SD below the best | selection rule fixed Nov 4 |
| Features | All twelve | fixed Nov 9 |
| Threshold | 0.5 on the model score | fixed Nov 4 |
| Scoring area | A box 15 km beyond the test sites of each of the 13 test cities, scored locally | decided Nov 11 |

The primary model's held-out-region precision is 0.832 and recall 0.883. It flags 5.1% of random background points, 20% of ash-pond points, 39% of bare-soil points and 43% of quarry points. With that recall and that background rate, precision would be about 15% if 1 pixel in 100 were landfill and about 2% at 1 in 1,000.

## Still to decide before the tag

- [ ] **How a Gujarat site counts as found.** Proposal: at least one flagged pixel inside its outline. The share of each outline that is flagged is reported next to it either way.
- [ ] **Surat LF-3** has a pin and no outline, so it cannot be scored. Outline it, or leave it out and say so.
- [ ] **What counts as failure**, in one sentence, written by you: ______
- [ ] Approve the table above, or rerun after adding sites.

## Tagging

```bash
git tag -a freeze-v1 -m "Freeze before Gujarat scoring"
```

```bash
git push origin freeze-v1
```
