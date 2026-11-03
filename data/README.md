# Data

| Path | Source | Licence |
| --- | --- | --- |
| `boundaries/geoBoundaries-IND-ADM1_simplified.geojson` | [geoBoundaries](https://www.geoboundaries.org) gbOpen IND ADM1 (36 states and union territories), built from [DataMeet India](https://github.com/datameet/maps) and Election Commission of India boundaries; metadata in `boundaries/geoBoundaries-IND-ADM1-metaData.json`. SHA-256 `4c63fe43294a391e8f2de4e9f86f3edb60f8688275b9fee90c61fb2aa0c26061` | CC BY 2.5 IN |
| `raw/osm_landfill_india.geojson` | OpenStreetMap `landuse=landfill` export via Overpass (query in `docs/phase1_labels.md`) | © OpenStreetMap contributors, ODbL 1.0 |

The state boundaries are used only to assign each site to a state, for the leave-one-state-out folds and to keep Gujarat out of training.
