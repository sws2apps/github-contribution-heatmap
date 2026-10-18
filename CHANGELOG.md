# Changelog

## 2026-10-18 — Mercator server release

- Render the verified amCharts Mercator geometry used by the contributor-map widget, with visible license attribution in both variants and themes.
- Resolve island part IDs to their country; keep outline IDs unique. Prefer exact ISO country lookup before fuzzy matching, fixing Niger/Nigeria ambiguity.
- Validation: all 256 existing location cases pass; 3 renderer/route tests cover every path in both themes/variants, empty data, attribution, unique IDs and refresh forwarding. Chrome image rendering checked at 375px and 1440px. `pip check` passes.
- Deployment pending at commit creation; GitHub Pages is a separate frontend and does not update this Vercel service.

## Deployment verification

- Server code commit: `c5bdb8837f01b7eb83695a5a53f403394192a52f`. Production deployment: `7160566917`, success.
- Verified at `2026-10-18T20:52:38Z`: https://github-contribution-heatmap.vercel.app/api/heatmap?repo=sws2apps/organized-app and its GitHub Camo image both contain `data-map-version="mercator-v2"`. The actual Organized README image also decoded successfully in Chrome. No README URL change or cache purge was necessary.
- This documentation commit follows the verified code deployment.

## 2026-10-18 — Taller README card

- Increase list card from 1200×520 to 1200×600 (2:1); use the full 660-unit map column and reduce the gap below the header. Map renders approximately 26% larger without distorting geography. Map-only variant unchanged.
- Validation: 256 location cases and 3 rendering tests pass; light/dark image rendering visually checked in Chrome at 375, 768 and 1440 pixels. Deployment pending at commit creation.
