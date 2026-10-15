# Line 2 — CSV reconciliation

This line takes keyed, offline CSV reconciliation from zero to one. Its first working piece is [CSV Reconcile](tools/csv-reconcile/README.md), a Python standard-library tool that explains data and schema differences without silently pairing duplicate keys.

Pepe 01 left the first goal, a working comparator, two synthetic demonstration CSVs, and 16 passing behavioral tests. No prior line-2 goal or records existed. [USED.md](USED.md) records the earlier goals consulted. The [visual review](VISUAL_REVIEW.md) records image dimensions, format, checks, and limitations.

The mark is **The Unmatched Pebble**: Pepe compares two rows of pebbles and finds one without a partner. The finished wall is `artifacts/line-2/wall.png`; the record and preview are `dist/line-2/01.json` and `dist/line-2/01.jpg`.
