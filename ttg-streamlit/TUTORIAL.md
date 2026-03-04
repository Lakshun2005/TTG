# TTG — Time Table Generator: Tutorial Guide

A beginner-friendly guide to install, run, and deploy the AI Timetable Generator.

---

## 1. Prerequisites

| Requirement | Version |
|-------------|---------|
| **Python** | 3.9 or higher |
| **pip** | Latest |
| **Git** | (optional, for deployment) |

### Install Python
- **Windows:** Download from [python.org](https://www.python.org/downloads/) and check "Add Python to PATH" during installation.
- **macOS:** `brew install python`
- **Linux:** `sudo apt install python3 python3-pip`

Verify installation:
```bash
python --version
pip --version
```

---

## 2. Installation

### Clone or Download the Project
```bash
git clone https://github.com/Lakshun2005/TTG.git
cd TTG/ttg-streamlit
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

This installs: `streamlit`, `sqlalchemy`, `pydantic`, `reportlab`, `openpyxl`, `pytest`, `numpy`.

---

## 3. Running the Application Locally

```bash
streamlit run streamlit_app.py
```

The terminal will display:
```
  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

Open **http://localhost:8501** in your browser.

---

## 4. Using the Application

Follow these steps in order:

### Step 1: Add Time Slots (🕐)
- Navigate to **Time Slots** in the sidebar
- Use **Bulk Generate** to create a weekly schedule (e.g., 6 periods/day, starting 9 AM, 60 min each)

### Step 2: Add Rooms (🏫)
- Navigate to **Rooms**
- Add classrooms and labs with their seating capacity

### Step 3: Add Faculty (👨‍🏫)
- Navigate to **Faculty**
- Add teachers with their **Subject Specialization** (this must match the subject they'll teach)

### Step 4: Add Subjects (📚)
- Navigate to **Subjects**
- Add subjects with code, credits, hours/week, semester, and lab requirement

### Step 5: Create Sections & Assign (🗂)
- Navigate to **Sections**
- Create student sections (e.g., "Section A", 60 students)
- **Assign Subject + Faculty** pairs to each section

### Step 6: Generate Timetable (⚡)
- Navigate to **Generate Timetable**
- Choose an algorithm:
  - **CSP (Backtracking + AC3):** Exact solver, guarantees optimal solution
  - **Genetic Algorithm:** Heuristic solver, faster on large/complex schedules
- Click **Generate Timetable**
- If successful, click **Activate** and then **View Timetable**

### Step 7: Export (📥)
- Navigate to **Export**
- Download the timetable as **Excel** or **PDF** (by section or by faculty)

---

## 5. Running Tests

```bash
pytest tests/ -v
```

This validates:
- Constraint solver logic (no double-booking)
- CRUD operations (Faculty/Subject create, read, update, delete)
- End-to-end flow (data input → generate → valid timetable)

---

## 6. Deploying Online (Streamlit Community Cloud)

### Steps:
1. Push the `ttg-streamlit/` folder to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click **New app**
5. Select your repository and branch
6. Set the main file path to `streamlit_app.py`
7. Click **Deploy**

Your app will be live at `https://your-app-name.streamlit.app`

### Using PostgreSQL (Optional)
For production, set the `DATABASE_URL` environment variable in Streamlit Cloud's **Secrets** section:
```toml
DATABASE_URL = "postgresql://user:password@host:5432/dbname"
```

---

## 7. Project Structure

```
ttg-streamlit/
├── streamlit_app.py          # Main Streamlit application (UI router)
├── requirements.txt          # Python dependencies
├── TUTORIAL.md               # This guide
├── app/
│   ├── __init__.py
│   ├── database.py           # SQLAlchemy engine & session setup
│   ├── data_handler.py       # Session context manager
│   ├── logger.py             # Centralized logging
│   ├── models/               # ORM models
│   │   ├── faculty.py
│   │   ├── subject.py
│   │   ├── room.py
│   │   ├── section.py
│   │   ├── timeslot.py
│   │   ├── associations.py   # FacultySubject, SectionSubject, FacultyAvailability
│   │   └── timetable.py      # TimetableGeneration, TimetableEntry
│   ├── crud/                 # CRUD operations
│   │   ├── base.py           # Generic CRUD with logging & error handling
│   │   ├── faculty.py
│   │   ├── section.py
│   │   └── timeslot.py
│   ├── scheduler/            # Scheduling engines
│   │   ├── csp_solver.py     # CSP with Backtracking + AC3
│   │   ├── ga_solver.py      # Genetic Algorithm solver
│   │   ├── constraints.py    # Constraint checker
│   │   ├── domain_builder.py # Variable & domain construction
│   │   └── timetable_builder.py  # Orchestration pipeline
│   └── export/               # Export modules
│       ├── pdf_exporter.py
│       └── excel_exporter.py
└── tests/                    # Test suite
    ├── conftest.py
    ├── test_solver.py
    ├── test_api.py
    └── test_flow.py
```

---

## 8. Architecture Overview

```
┌─────────────────────────┐
│     Streamlit UI        │   ← User interface (forms, tables, charts)
├─────────────────────────┤
│     CRUD Layer          │   ← Create/Read/Update/Delete with logging
├─────────────────────────┤
│   Scheduling Engine     │   ← CSP Solver OR Genetic Algorithm
│   ┌───────┐ ┌────────┐  │
│   │  CSP  │ │   GA   │  │
│   └───────┘ └────────┘  │
├─────────────────────────┤
│   SQLAlchemy ORM        │   ← Data models & relationships
├─────────────────────────┤
│   SQLite / PostgreSQL   │   ← Persistent storage
└─────────────────────────┘
```

### Scheduling Algorithm Details

**CSP (Constraint Satisfaction Problem):**
- Uses Backtracking Search with AC-3 arc consistency
- MRV (Minimum Remaining Values) heuristic for variable selection
- LCV (Least Constraining Value) for value ordering
- Forward checking for early pruning

**Genetic Algorithm:**
- Chromosome = array of (timeslot_id, room_id) per scheduling variable
- Tournament selection, uniform crossover, random mutation
- Hard constraints enforced via large fitness penalties
- Soft constraints reward schedule diversity

### Data Flow
```
User Input → Validator → CRUD → Database → Domain Builder → Solver → Timetable Entries → Export
```

---

## 9. Troubleshooting

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| **"No section-subject assignments found"** | No subjects assigned to sections | Go to Sections → expand a section → Assign Subject + Faculty |
| **"No valid slots for subject_id=…"** | Room capacity too small, or no matching room type (lab vs classroom) | Add rooms with sufficient capacity, or add a lab room for lab subjects |
| **"No valid timetable found"** | Too few timeslots for the required hours | Add more timeslots or reduce subject hours_per_week |
| **ModuleNotFoundError** | Missing dependencies | Run `pip install -r requirements.txt` |
| **Port 8501 already in use** | Another Streamlit instance is running | Kill the process: `taskkill /f /im streamlit.exe` (Windows) or `kill -9 $(lsof -ti:8501)` (Linux/Mac) |
| **Database locked** | Multiple processes accessing SQLite | Restart the app; consider using PostgreSQL for production |

### Debug Mode
Enable **🐛 Debug Mode** in the sidebar to see detailed logs. Check the `ttg.log` file in the project root for full debug output.

### Running Tests
```bash
pytest tests/ -v
```
If tests fail, check `ttg.log` for detailed error traces.
