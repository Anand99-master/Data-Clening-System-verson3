# Data Cleaning Automation Tool

An automated data-cleaning application (Python + Pandas + Streamlit + Plotly)
that profiles raw datasets, detects data-quality issues, applies configurable
cleaning rules, validates business rules, generates a data-quality score,
and exports cleaned datasets with a full audit log.

Built from the system architecture: Upload → Profile → Detect Problems →
User Selects Rules → Clean → Validate → Generate Report → Download.

## Two modes — built for both non-technical and power users

**Simple mode (default, what opens first)** — no jargon, no configuration:
1. Upload your Excel/CSV file
2. See a plain-English list of problems found ("🔁 3 duplicate rows",
   "✏️ inconsistent spelling in City")
3. Click **one button** — "✨ Clean My Data Now"
4. See what changed, in plain English, plus a 0-100% quality score with a
   friendly rating (Excellent / Good / Needs review)
5. Download the cleaned file as Excel or CSV

The one-click clean (`modules/auto_clean.py`) only applies changes that are
safe to automate: trims spaces, removes exact duplicate rows, fixes obvious
spelling/capitalization inconsistencies, converts numbers/dates stored as
text, and fills missing values with the median (numbers) or most common
value (text). Unusual values ("outliers") are flagged for you to look at —
never silently removed.

**Advanced mode** — toggle "🛠️ Advanced / power-user mode" in the sidebar
to get the full toolkit: column-by-column control over every cleaning
strategy, business-rule validation, AI-suggested cleaning actions, a custom
rules editor, database connections, and support for very large CSVs via
chunked processing. This is the same feature set described below.

## Features (Phase 1 + 2 + 3 + 4 of the roadmap)

- **File Upload** — .csv, .xlsx, .xls
- **Data Profiling** — per-column type / missing / unique health check
- **Missing Values** — Remove / Mean / Median / Mode / Custom value
- **Duplicates** — exact (keep first/last/none) + optional fuzzy-match detection
- **Extra Spaces** — trims leading/trailing/inner whitespace
- **Text Standardization** — detects case/spacing variants ("Ahemdabad" vs
  "Ahmedabad") and lets you apply or ignore each suggestion; plus a JSON
  rules engine (`config/cleaning_rules.json`) for known corrections
- **Data Type Detection & Conversion** — text → integer/float, currency-aware
  (₹29,600 → 29600)
- **Date Cleaning** — parses messy date formats, standardizes to `YYYY-MM-DD`,
  flags invalid dates instead of dropping them silently
- **Outlier Detection** — IQR / Z-score / Percentile methods, flag-only
  (never auto-deleted)
- **Business Rule Validation** — e.g. `Quantity × Price = Sales`, flags
  mismatched rows with Expected/Actual/Difference
- **Data Quality Score** — Completeness, Accuracy, Consistency, Uniqueness,
  Validity + overall %
- **Before vs After** comparison table
- **Cleaning Log** — timestamped audit trail of every transformation
- **Export** — cleaned data as Excel/CSV, report as Excel/PDF

### Phase 3 — Dashboard

- **Charts** — missing-values-by-column bar chart, column-type pie chart,
  numeric correlation heatmap (Plotly, in the "📊 Charts" expander)
- **Interactive controls** — outlier method/threshold, duplicate keep
  strategy, missing-value strategy, type targets — all selectable per
  column before running the pipeline
- Quality-score gauge + per-metric progress bars, Before/After table

### Phase 4 — Advanced

- **AI Recommendations** (`modules/ai_recommendations.py`) — sends the
  data profile (never the raw data) to Claude, which suggests which of
  the tool's *existing deterministic modules* to run and on which
  columns. The AI never cleans data itself — "Clean Recommended Issues"
  routes every suggestion back through the same pandas-based functions
  used elsewhere. Requires an Anthropic API key (paste into the sidebar
  field, or set `ANTHROPIC_API_KEY`).
- **Custom Rules** (`modules/rules_manager.py`) — build your own
  find-and-replace rules per column from the UI; persisted to
  `config/cleaning_rules.json` so they carry over between sessions.
- **Database Connection** (`modules/db_handler.py`) — load a table in
  from SQLite or PostgreSQL (any SQLAlchemy URL) as the working
  dataset, and write the cleaned result back to a table when you're
  done. Pick "Database" as the data source in the sidebar.
- **Large Files** (`modules/large_file_handler.py`) — for CSVs too big
  to load fully into memory, pick "Large CSV (chunked mode)" in the
  sidebar. It streams the file in configurable chunks, computing
  missing-value counts and numeric means in a first pass, then trims
  spaces and fills missing numeric values in a second streaming pass —
  writing straight to an output file so the whole dataset never has to
  fit in RAM at once. Exact-duplicate removal and full-dataset outlier
  detection aren't available in this mode (they need the whole
  dataset) — use regular File Upload mode for those once the data fits
  in memory, or after chunked pre-cleaning has shrunk it.

## Setup

```bash
cd data-cleaning-system
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (usually http://localhost:8501).

## Project structure

```
data-cleaning-system/
├── app.py                     # Streamlit UI — wires all modules together
├── modules/
│   ├── file_handler.py        # Module 1 — upload & read
│   ├── profiling.py           # Module 3 — per-column health check
│   ├── missing_values.py      # Module 4
│   ├── duplicates.py          # Module 5 (+ fuzzy matching)
│   ├── text_cleaning.py       # Module 6 — trim spaces
│   ├── standardization.py     # Module 7 & 11 — text std + rules engine
│   ├── type_conversion.py     # Module 8
│   ├── date_cleaning.py       # Module 9
│   ├── outlier_detection.py   # Module 10
│   ├── validation.py          # Module 13 & 14
│   ├── report.py              # Module 15, 16, 17 — score/compare/export
│   ├── db_handler.py          # Phase 4 — SQLite/PostgreSQL connector
│   ├── ai_recommendations.py  # Phase 4 — AI-suggested cleaning actions
│   ├── large_file_handler.py  # Phase 4 — chunked processing for big CSVs
│   ├── rules_manager.py       # Phase 4 — custom rules editor + persistence
│   └── auto_clean.py          # Simple mode — one-click pipeline + plain-English issue scanner
├── utils/
│   ├── logger.py
│   └── helpers.py
├── config/
│   └── cleaning_rules.json    # example standardization rules
├── data/
│   ├── input/
│   └── output/
└── requirements.txt
```

## Notes on design decisions (per the architecture doc)

- **Nothing is auto-deleted.** Outliers, fuzzy duplicates, and standardization
  suggestions are surfaced to the user with explicit apply/ignore actions
  (Module 22 — "System identifies problems and User decides").
- **Missing-value detection** recognizes NULL, blank, N/A, NA, `-`, Unknown,
  `?` and common variants before any imputation strategy runs.
- **Type conversion is currency-aware** — strips `₹ $ € £ ,` before parsing
  numbers.
- Every cleaning action is written to the in-memory `CleaningLogger`, which
  backs both the on-screen "Cleaning Log" panel and the exported reports.

## Ideas for going further

- Swap the fuzzy-matching threshold / add phonetic matching (e.g. Soundex)
- Add authentication/multi-user support if this moves beyond a personal tool
- Parallelize the large-file chunked pass (currently single-threaded)
- Add a duplicate-detection strategy for chunked mode based on row hashing
  (compute a hash per row in pass 1, flag repeats in pass 2) instead of
  requiring the full dataset in memory
