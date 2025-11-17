# Scenario Editor GUI

Small Tkinter GUI to create or edit JSON files that follow the structure of `scenarioexample.json`.

How to run

1. Make sure you have Python 3 installed. Tkinter is included in standard CPython on Windows.
2. From the repository root (this project), run:

```bash
python gui/app.py
```

Features
- Edit `meta` fields: name, uniqueid, requiredver
- Add / Edit / Delete entries (id, text, rubi, level)
- Load existing JSON (will validate that `meta` and `entries` exist)
- Save / Save As / Export JSON

Notes
- No external dependencies required.
- The GUI stores entries as a dictionary keyed by string IDs (matching the example format).
