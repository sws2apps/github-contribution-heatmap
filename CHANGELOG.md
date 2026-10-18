# Changelog

## 2026-10-18 — Mercator server release

- Render the verified amCharts Mercator geometry used by the contributor-map widget, with visible license attribution in both variants and themes.
- Resolve island part IDs to their country; keep outline IDs unique. Prefer exact ISO country lookup before fuzzy matching, fixing Niger/Nigeria ambiguity.
- Validation: all 256 existing location cases pass; 3 renderer/route tests cover every path in both themes/variants, empty data, attribution, unique IDs and refresh forwarding. Chrome image rendering checked at 375px and 1440px. `pip check` passes.
- Deployment pending at commit creation; GitHub Pages is a separate frontend and does not update this Vercel service.
