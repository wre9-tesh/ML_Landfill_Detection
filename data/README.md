# Data

| Path | Source | Licence |
| --- | --- | --- |
| `boundaries/geoBoundaries-IND-ADM1_simplified.geojson` | [geoBoundaries](https://www.geoboundaries.org) gbOpen IND ADM1 (36 states and union territories), built from [DataMeet India](https://github.com/datameet/maps) and Election Commission of India boundaries; metadata in `boundaries/geoBoundaries-IND-ADM1-metaData.json`. SHA-256 `4c63fe43294a391e8f2de4e9f86f3edb60f8688275b9fee90c61fb2aa0c26061` | CC BY 2.5 IN |
| `raw/export.json` | Raw Overpass API response for the query in `docs/phase1_labels.md`; OSM snapshot `2026-11-03T06:27:06Z` (`osm3s.timestamp_osm_base`) | © OpenStreetMap contributors, ODbL 1.0 |
| `raw/osm_landfill_india.geojson` | The same response converted to GeoJSON by overpass-turbo; input to `scripts/osm_to_screening.py` | © OpenStreetMap contributors, ODbL 1.0 |

The state boundaries are used only to assign each site to a state, for the leave-one-state-out folds and to keep Gujarat out of training.
