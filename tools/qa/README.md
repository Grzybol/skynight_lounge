# Local Garden Bounty QA harness

Headless Chrome CDP script used to exercise `/dev-preview` when the Cursor
browser tools are unavailable.

Port `3010` is often blocked on Windows by Hyper-V excluded ranges
(`2978–3077`). This machine served the tester on `4010`.

```powershell
cd frontend\apps\poc
..\..\node_modules\.bin\vite.cmd --host 127.0.0.1 --port 4010

# in another shell, from the repo root:
node tools/qa/chrome_devpreview_qa.mjs
```

Screenshots and `report.json` land in `tools/qa/output/` (gitignored).

Headless Chrome can stall Pixi `requestAnimationFrame` loops, so a stuck
`Machine bet` / unresolved Action is **not** by itself proof of a production
hang. Treat idle layout, HUD copy, and production-route behaviour as the
reliable evidence.
