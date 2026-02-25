# TTG — Time Table Generator (Streamlit)

A fully serverless version of the TTG academic scheduling system built with **Streamlit**.
No separate API server needed — everything runs in a single Python process.

## ✨ Features
- 8-page UI: Faculty, Subjects, Rooms, Sections, Time Slots, Generate, Export
- CSP solver (AC-3 + Backtracking) runs inline — no background workers
- SQLite database (auto-created on first run)
- Export to **PDF** and **Excel** with direct download buttons

## ▶️ Run Locally

```powershell
cd ttg-streamlit
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open http://localhost:8501 in your browser.

## 🚀 Deploy to Streamlit Community Cloud (Free)

1. Push this repository to GitHub
2. Go to https://share.streamlit.io → **New app**
3. Select your repo → set **Main file path** to `ttg-streamlit/streamlit_app.py`
4. Click **Deploy** — done!

> **Note**: On Streamlit Cloud the SQLite DB is reset on each redeploy (ephemeral filesystem).
  For persistent data, set the `TTG_DB_PATH` environment variable to a path in a mounted volume,
  or swap `database.py` to use a free-tier PostgreSQL (e.g. Neon, Supabase).

## 📂 Project Structure

```
ttg-streamlit/
├── streamlit_app.py      # Main Streamlit app (all 8 pages)
├── requirements.txt      # Python dependencies
├── .streamlit/
│   └── config.toml       # Dark purple theme
└── app/
    ├── database.py       # SQLAlchemy + st.cache_resource engine
    ├── models/           # ORM models
    ├── crud/             # CRUD operations
    ├── scheduler/        # CSP solver (AC-3 + Backtracking)
    └── export/           # PDF + Excel exporters
```
