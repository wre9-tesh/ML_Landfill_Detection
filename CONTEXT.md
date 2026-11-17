# Project context

Where the project stands and why, for anyone (person or AI assistant) picking it up. Updated 17 November 2026. Older hand-off notes, with the history of versions 1 and 2, are in [docs/context.md](docs/context.md).

## What this is

- **Course project:** ES 678 (graduate track), IIT Gandhinagar. Solo: Amitesh Kumar (24210011). **Due Tuesday 17 November 2026.**
- **Question:** can a model trained on Indian dumpsites outside Gujarat find Gujarat's dumpsites from free satellite data (Sentinel-2, Landsat, SRTM), and when it is wrong, why?
- **Framing:** a diagnostic study. The model finds the known sites but flags about 5% of the land; the write-up explains what it confuses with a dumpsite.
- **Repository:** `wre9-tesh/ML_Landfill_Detection`. Website: <https://wre9-tesh.github.io/ML_Landfill_Detection/> (GitHub Pages from `main`, folder `/docs`).

## Deliverables and status

| Deliverable | Status |
| --- | --- |
| Website (six pages, two interactions, light and dark) | Built, in `docs/`. Restyled after the author's Food Trade Networks site |
| Repository, reproducible, with README | Done. README has setup, run order, data access, AI-use disclosure, references |
| Four-page LaTeX paper (ES 678 template), with source and bibliography | **Not started in the repository.** No `paper/` folder yet |
| AI-use disclosure | Draft on the Reproduce page and in the README; the author accepted it "for now" and will edit it |
| GitHub Pages enabled, repository visible to graders | To be confirmed by the author |

## Results that everything else quotes

All from version 3 (gradient boosting, 26 features, threshold 0.5, tag `freeze-v3`).

| Result | Value | Source |
| --- | --- | --- |
| Training points | 34,345 (3,853 landfill) from 86 places in 26 states | `data/results_v3/` |
| Held-out-region F1 | 0.762 (precision 0.694, recall 0.865, SD 0.044) | `data/results_v3/summary.csv` |
| Gujarat, first list | 16 of 17 sites found; Rajkot missed at 48.6% of its outline | `data/gujarat_results_v3/` |
| Land flagged | 5.2% of 12,854 km² (14 boxes), 7,801 alarm patches | same |
| Known sites in the top 50 / 100 / 200 patches | 5 / 8 / 9 | same |
| Surendranagar (in no list) | alarm rank 4 of 7,801 | `alarms.csv`, blind id A065 |
| Hand check of the top 100 alarms | 5 dumps, 94 look-alikes, 1 unsure. Of the 5, 3 were not known beforehand | `blind_check.csv` |
| What the look-alikes were | bare soil 46, fields or grass 19, buildings 16, industrial 5, other 8 | same |
| Second blind test, six new cities | 5 of 6 found (Porbandar missed); 4.0% of 5,244 km² flagged | `data/gujarat_results_v3_new/` |
| Both lists together | 21 of 23 | |

Diagnostics (`data/analysis/`): `LST_anom` is the strongest single feature and carries a third of the model; look-alikes are flagged four to six times as often as ordinary land; the Gujarat false alarms are not unusual pixels (none beyond the 99th percentile of training, 80 of 94 nearest to training landfills) and are pushed over the threshold mainly by temperature.

## Rules that must not be broken

1. **No Gujarat data in training.** Not pixels, not hand-check verdicts, not false alarms as negatives.
2. **Freeze before scoring.** Each model is committed and tagged (`freeze-v1`, `-v2`, `-v3`) before Gujarat is scored; `score_gujarat.py` refuses to run otherwise. Version 3 is the last model.
3. **Test lists are sealed by commit before scoring.** First list: `8711855` (11 Nov). New-cities list: `fc81cd5`, scored in `4265a04`.
4. **The earlier versions are disclosed.** The paper and website present version 3 only, but both carry a short statement that it is the third model scored on the first 17 sites, and the website has "How we got here" (one paragraph and a table). Versions 1 and 2 stay in the repository.
5. **The hand check keeps its denominator.** The site leads with the three new dumpsites, at the author's request, and still states that 94 of the 100 alarms were other land. The error analysis depends on it.
6. **Words:** "model score", not confidence or probability; "flagged", "found", "alarm patch"; unscored land is "not scored", never "clean". Only about 6.6% of Gujarat was scored.
7. **No private data in the repository:** no email address, no Earth Engine project ID, no keys.

## How the website is built

- Page text: `site_src/*.html`, with placeholders such as `{{k:guj.sites_found}}`, `{{table:T-R1}}`, `{{note:ndvi}}`.
- `python scripts/build_site_data.py` reads the result files, fills every number, and writes `docs/*.html` and `docs/site/data/*`. `--check` writes nothing and fails if anything is out of date. **Never edit `docs/*.html` by hand.**
- Fixed text (page list, the 26 feature descriptions, the glossary): `scripts/site_text.py`.
- `python scripts/make_chips.py` cuts the image chips; it needs the Gujarat rasters, so only the author can run it. Chips are committed.
- Styles `docs/site/css/site.css`; scripts `docs/site/js/` (charts, feature explorer, threshold slider, gallery). D3, Observable Plot and the three fonts (Inter Tight, JetBrains Mono, Instrument Serif) are copied into `docs/site/`; nothing loads from other servers.
- Definitions are collapsible boxes under the paragraph that uses the term.
- Preview: `python -m http.server 8000 --directory docs`.
- The original specification is `docs/website_plan.md` (its "As built" note lists the differences).

## Working setup

- **Author's machine:** Windows PowerShell, repository at `D:\COursework\ML\project\ML_Landfill_Detection`. The Gujarat feature rasters exist only there (`data\gujarat\`, `data\gujarat_x\`, `data\gujarat_new\`, `data\gujarat_new_x\`; all git-ignored). Earth Engine fetches, exports, scoring and chips are run there.
- **Assistant:** works on branch `claude/dazzling-mayer-jw7pqk`; the author pulls it or merges it into `main` by pull request. The assistant cannot push tags. Pull requests are opened only when the author asks.
- **Run order and setup:** see [README.md](README.md). Step-by-step manuals: `docs/project_guide_grader.pdf`, `docs/project_guide_technical.pdf`, `docs/project_guide_plain.pdf` (sources in `docs/guide/`, rendered with `node docs/guide/render.js`).
- **Author's preferences:** short, direct answers; a small checklist when asked what remains.

## Open items

- [ ] Paper: add the ES 678 LaTeX starter package (for example in `paper/`), write the four pages, copy the PDF to `docs/paper.pdf` (the site footer then links it automatically on the next build).
- [ ] References: the titles of Bhajantri and Mandpe (2026, *Applied Geomatics* 18:88) and Gibellini and others (2025, arXiv:2502.06607) are missing on the site and in the README; Agrawal and others and the Campania paper are unverified and not cited.
- [ ] AI-use disclosure: author's final wording, then the same text in the paper, README and site.
- [ ] The three PDF guides still mark the version 3 hand check and the alarm diagnostics as pending, and do not mention the new-cities test.
- [ ] Rajkot: the site says the reason for the miss is not established. Change it only if the chip shows a reason.
- [ ] Confirm GitHub Pages is serving `main` `/docs` and that graders can open the repository.
- [ ] Submit the site address, repository address and paper on the course portal.
