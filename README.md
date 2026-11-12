# Living Dex

Personal living form dex + shiny living form dex tracker, laid out for Pokémon Home.

- `index.html`, `css/`, `js/` — the app (static, runs on GitHub Pages)
- `data/dex.json` — every slot, built from PokeAPI data by `tools/build_data.py`
- `js/firebase-config.js` — paste your Firebase web config here to turn on cloud sync
- `firestore.rules` — paste into Firebase → Firestore → Rules so only you can read/write your data

Until Firebase is configured, progress saves in the browser only — use Settings → Export backup.
