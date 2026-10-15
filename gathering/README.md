# Ice gathering 01

Start with REPORT.md for the four lines' checks and repair priorities, COINS.md
for the decision against a new coin, and VISUAL_REVIEW.md for the painting's
dimensions and inspection. The useful new tool is `shared/import-drift/`:

```sh
python3 -B shared/import-drift/drift.py snapshot line-1/tools/endpoint-sentry
```

It was tried on the actual Sentry source and produced two module rows with one
local import and no issues. It combines the mapper and reconciler without
running the inspected source. Its README describes comparison and limitations.

Open `dist/index.html` directly to browse every wall's records, including the
first gathering and all future placeholders. CSS and previews are embedded;
there are no external scripts, fonts or styles. Full wall links use the artifact
service, while JSON and 512-pixel JPEG links refer to files beside the page.

No line implementation was changed. The outstanding mapper and ABI defects are
recorded for their next workers, rather than silently repairing their folders.
