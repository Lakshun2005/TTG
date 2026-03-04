"""
TTG — Time Table Generator  (Streamlit Serverless App)
=======================================================
Run locally:  streamlit run streamlit_app.py
Deploy:       Push this ttg-streamlit/ folder to GitHub, then connect to
              https://share.streamlit.io and point it at streamlit_app.py
"""

import sys, os
# Make sure the app/ package is importable when running from this directory
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

# ── Bootstrap DB ────────────────────────────────────────────────────────────
from app.database import init_db, get_session
init_db()  # idempotent — creates tables if they don't exist

# ── ORM models imported for convenience ─────────────────────────────────────
from app.models.faculty import Faculty
from app.models.subject import Subject
from app.models.room import Room
from app.models.section import Section
from app.models.timeslot import Timeslot
from app.models.associations import SectionSubject, FacultyAvailability
from app.models.timetable import TimetableGeneration, TimetableEntry
from sqlalchemy.orm import joinedload

# ── CRUD ─────────────────────────────────────────────────────────────────────
from app.crud.faculty import crud_faculty
from app.crud.section import crud_section
from app.crud.timeslot import crud_timeslot

# ── Scheduler + Exporters ────────────────────────────────────────────────────
from app.scheduler.timetable_builder import run_generation
from app.export.pdf_exporter import generate_section_pdf, generate_faculty_pdf
from app.export.excel_exporter import generate_full_excel
from app.validator import validate_before_generation

# ── Ensure DB tables exist (critical on Streamlit Cloud) ─────────────────────
init_db()

# ──────────────────────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TTG — Time Table Generator",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #13001f 0%, #1a0030 100%);
    border-right: 1px solid #7c3aed44;
}
[data-testid="stSidebar"] .stRadio label {
    color: #c4b5fd !important;
    font-weight: 500;
    padding: 4px 0;
}

/* Cards */
.ttg-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #7c3aed33;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    transition: box-shadow .2s;
}
.ttg-card:hover { box-shadow: 0 0 0 2px #7c3aed55; }

/* Stat chips */
.stat-row { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; }
.stat-chip {
    background: linear-gradient(135deg, #7c3aed22, #7c3aed44);
    border: 1px solid #7c3aed66;
    border-radius: 10px;
    padding: .7rem 1.2rem;
    flex: 1;
    min-width: 120px;
    text-align: center;
}
.stat-chip .val { font-size: 2rem; font-weight: 700; color: #a78bfa; line-height:1; }
.stat-chip .lbl { font-size: .78rem; color: #94a3b8; margin-top: .25rem; }

/* Timetable grid */
.tt-grid table { width: 100%; border-collapse: collapse; font-size: .82rem; }
.tt-grid th {
    background: #7c3aed;
    color: white;
    padding: 8px 6px;
    text-align: center;
    font-weight: 600;
}
.tt-grid td {
    border: 1px solid #2d2d4a;
    padding: 6px 8px;
    text-align: center;
    vertical-align: middle;
    color: #e2e8f0;
    min-width: 110px;
}
.tt-grid tr:nth-child(even) td { background: #1a1a2e; }
.tt-grid tr:nth-child(odd) td  { background: #16213e; }
.tt-grid td.period-cell { font-weight: 700; color: #c4b5fd; background:#13001f !important; }
.tt-grid .entry-badge {
    background: #7c3aed22;
    border: 1px solid #7c3aed55;
    border-radius: 6px;
    padding: 4px 2px;
    line-height: 1.5;
}
.section-tag { display: inline-block; background:#7c3aed; color:#fff; border-radius:4px; padding:1px 6px; font-size:.7rem; font-weight:600; margin-bottom:2px; }

/* Badges */
.badge-success { background:#14532d22; border:1px solid #166534; color:#86efac; border-radius:6px; padding:2px 8px; font-size:.78rem; }
.badge-pending { background:#78350f22; border:1px solid #92400e; color:#fcd34d; border-radius:6px; padding:2px 8px; font-size:.78rem; }
.badge-failed  { background:#7f1d1d22; border:1px solid #991b1b; color:#fca5a5; border-radius:6px; padding:2px 8px; font-size:.78rem; }
.badge-running { background:#1e3a5f22; border:1px solid #1e40af; color:#93c5fd; border-radius:6px; padding:2px 8px; font-size:.78rem; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar navigation
# ──────────────────────────────────────────────────────────────────────────────
PAGES = {
    "🏠 Dashboard":         "dashboard",
    "👨‍🏫 Faculty":           "faculty",
    "📚 Subjects":          "subjects",
    "🏫 Rooms":             "rooms",
    "🗂 Sections":          "sections",
    "🕐 Time Slots":        "timeslots",
    "⚡ Generate Timetable":"generate",
    "📥 Export":            "export",
}

with st.sidebar:
    st.markdown("## 📅 TTG")
    st.markdown("<p style='color:#94a3b8;font-size:.85rem;margin-top:-.5rem'>Smart Academic Scheduling</p>", unsafe_allow_html=True)
    st.markdown("---")
    page_label = st.radio("Navigation", list(PAGES.keys()), label_visibility="collapsed")
    page = PAGES[page_label]
    st.markdown("---")
    debug_mode = st.checkbox("🐛 Debug Mode", value=False, help="Show detailed logs")
    st.session_state["debug_mode"] = debug_mode
    st.markdown("<p style='color:#64748b;font-size:.7rem'>Powered by CSP + GA Solver · SQLite · Streamlit</p>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────────────────────
def fmt_time(t):
    if t is None:
        return ""
    return t.strftime("%H:%M") if hasattr(t, "strftime") else str(t)


def status_badge(status: str) -> str:
    cls = {"success": "badge-success", "pending": "badge-pending",
           "failed": "badge-failed", "running": "badge-running"}.get(status, "badge-pending")
    return f'<span class="{cls}">{status.upper()}</span>'


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "dashboard":
    st.title("🏠 Dashboard")
    db = get_session()
    try:
        n_faculty   = db.query(Faculty).count()
        n_subjects  = db.query(Subject).count()
        n_rooms     = db.query(Room).count()
        n_sections  = db.query(Section).count()
        n_timeslots = db.query(Timeslot).count()
        n_gen       = db.query(TimetableGeneration).count()
        active_gen  = db.query(TimetableGeneration).filter(TimetableGeneration.is_active == True).first()
    finally:
        db.close()

    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-chip"><div class="val">{n_faculty}</div><div class="lbl">Faculty</div></div>
        <div class="stat-chip"><div class="val">{n_subjects}</div><div class="lbl">Subjects</div></div>
        <div class="stat-chip"><div class="val">{n_rooms}</div><div class="lbl">Rooms</div></div>
        <div class="stat-chip"><div class="val">{n_sections}</div><div class="lbl">Sections</div></div>
        <div class="stat-chip"><div class="val">{n_timeslots}</div><div class="lbl">Time Slots</div></div>
        <div class="stat-chip"><div class="val">{n_gen}</div><div class="lbl">Generations</div></div>
    </div>
    """, unsafe_allow_html=True)

    if active_gen:
        st.success(f"✅ Active timetable: **{active_gen.id[:8]}…** (generated {active_gen.completed_at})")
    else:
        st.info("ℹ️ No active timetable yet. Go to ⚡ Generate Timetable to create one.")

    st.markdown("### 📋 Quick Start Guide")
    steps = [
        ("1️⃣", "**🕐 Time Slots**", "Add time slots (or bulk-generate them)"),
        ("2️⃣", "**🏫 Rooms**",      "Add classrooms and labs"),
        ("3️⃣", "**👨‍🏫 Faculty**",   "Add faculty and set their availability"),
        ("4️⃣", "**📚 Subjects**",   "Add subjects (mark lab subjects)"),
        ("5️⃣", "**🗂 Sections**",   "Add sections and assign subject+faculty pairs"),
        ("6️⃣", "**⚡ Generate**",   "Run the CSP solver to create the timetable"),
        ("7️⃣", "**📥 Export**",     "Download PDF or Excel export"),
    ]
    for icon, title, desc in steps:
        st.markdown(f"{icon} {title} — {desc}")


# ══════════════════════════════════════════════════════════════════════════════
# FACULTY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "faculty":
    st.title("👨‍🏫 Faculty Management")
    db = get_session()
    try:
        faculty_list = crud_faculty.get_all(db)
    finally:
        db.close()

    # Add Faculty
    with st.expander("➕ Add New Faculty", expanded=False):
        with st.form("add_faculty_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            name       = c1.text_input("Name*")
            spec       = c2.text_input("Subject Specialization*")
            dept       = c3.text_input("Department*")
            max_hours  = c4.number_input("Max hrs/week", 1, 40, 20)
            submitted  = st.form_submit_button("Add Faculty", type="primary")
            if submitted:
                if not all([name, spec, dept]):
                    st.error("Name, subject specialization, and department are required.")
                else:
                    db2 = get_session()
                    try:
                        crud_faculty.create(db2, {"name": name, "subject_specialization": spec, "department": dept, "max_hours_per_week": int(max_hours)})
                        st.success(f"Faculty **{name}** added!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        db2.close()

    # List & Manage
    if not faculty_list:
        st.info("No faculty added yet.")
    else:
        for f in faculty_list:
            with st.container():
                st.markdown(f"""
                <div class="ttg-card">
                    <strong>{f.name}</strong> &nbsp;·&nbsp; <span style="color:#94a3b8">{f.department}</span><br>
                    <small style="color:#64748b">Specialization: {f.subject_specialization} &nbsp;|&nbsp; Max {f.max_hours_per_week} hrs/week</small>
                </div>""", unsafe_allow_html=True)

                col_edit, col_del = st.columns([1, 1])
                with col_edit:
                    with st.popover("✏️ Edit"):
                        with st.form(f"edit_fac_{f.id}"):
                            e_name  = st.text_input("Name", value=f.name)
                            e_spec  = st.text_input("Specialization", value=f.subject_specialization)
                            e_dept  = st.text_input("Department", value=f.department)
                            e_hours = st.number_input("Max hrs/week", 1, 40, int(f.max_hours_per_week))
                            if st.form_submit_button("Save"):
                                db_edit = get_session()
                                try:
                                    crud_faculty.update(db_edit, f.id, {"name": e_name, "subject_specialization": e_spec, "department": e_dept, "max_hours_per_week": e_hours})
                                    st.success("Updated!")
                                    st.rerun()
                                finally:
                                    db_edit.close()

                with col_del:
                    if st.button("🗑 Delete", key=f"del_fac_{f.id}", type="secondary"):
                        db5 = get_session()
                        try:
                            crud_faculty.delete(db5, f.id)
                            st.success("Faculty deleted.")
                            st.rerun()
                        finally:
                            db5.close()


# ══════════════════════════════════════════════════════════════════════════════
# SUBJECTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "subjects":
    st.title("📚 Subjects")
    db = get_session()
    try:
        from app.crud.base import CRUDBase
        from app.models.subject import Subject as SubjectModel
        crud_subject = CRUDBase(SubjectModel)
        subjects = crud_subject.get_all(db)
    finally:
        db.close()

    with st.expander("➕ Add New Subject", expanded=False):
        with st.form("add_subject_form", clear_on_submit=True):
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            name     = c1.text_input("Name*")
            code     = c2.text_input("Code*")
            credits  = c3.number_input("Credits", 1, 10, 3)
            hpw      = c4.number_input("Hrs/week", 1, 20, 3)
            semester = c5.number_input("Semester", 1, 12, 1)
            req_lab  = c6.checkbox("Requires Lab")
            submitted = st.form_submit_button("Add Subject", type="primary")
            if submitted:
                if not all([name, code]):
                    st.error("Name and code are required.")
                else:
                    db2 = get_session()
                    try:
                        crud_subject.create(db2, {
                            "name": name, "code": code, "credits": int(credits),
                            "hours_per_week": int(hpw), "semester": int(semester),
                            "requires_lab": req_lab
                        })
                        st.success(f"Subject **{name}** added!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        db2.close()

    if not subjects:
        st.info("No subjects added yet.")
    else:
        for s in subjects:
            lab_tag = ' &nbsp;<span style="background:#9333ea;color:#fff;border-radius:4px;padding:1px 6px;font-size:.72rem">LAB</span>' if s.requires_lab else ""
            st.markdown(f"""
            <div class="ttg-card">
                <strong>{s.name}</strong>{lab_tag} &nbsp;·&nbsp;
                <code style="background:#7c3aed22;padding:1px 6px;border-radius:4px">{s.code}</code><br>
                <small style="color:#94a3b8">
                    Credits: {s.credits} &nbsp;|&nbsp; Hrs/week: {s.hours_per_week}
                    &nbsp;|&nbsp; Semester: {s.semester}
                </small>
            </div>""", unsafe_allow_html=True)
            
            col_edit, col_del = st.columns([1, 1])
            with col_edit:
                with st.popover("✏️ Edit"):
                    with st.form(f"edit_sub_{s.id}"):
                        e_name = st.text_input("Name", value=s.name)
                        e_code = st.text_input("Code", value=s.code)
                        e_cred = st.number_input("Credits", 1, 10, int(s.credits))
                        e_hpw  = st.number_input("Hrs/week", 1, 20, int(s.hours_per_week))
                        e_sem  = st.number_input("Semester", 1, 12, int(s.semester))
                        e_lab  = st.checkbox("Requires Lab", value=s.requires_lab)
                        if st.form_submit_button("Save"):
                            db_edit = get_session()
                            try:
                                crud_subject.update(db_edit, s.id, {
                                    "name": e_name, "code": e_code, "credits": e_cred,
                                    "hours_per_week": e_hpw, "semester": e_sem, "requires_lab": e_lab
                                })
                                st.success("Updated!")
                                st.rerun()
                            finally:
                                db_edit.close()

            with col_del:
                if st.button("🗑 Delete", key=f"del_sub_{s.id}", type="secondary"):
                    db2 = get_session()
                    try:
                        crud_subject.delete(db2, s.id)
                        st.rerun()
                    finally:
                        db2.close()


# ══════════════════════════════════════════════════════════════════════════════
# ROOMS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "rooms":
    st.title("🏫 Rooms")
    db = get_session()
    try:
        from app.crud.base import CRUDBase
        from app.models.room import Room as RoomModel
        crud_room = CRUDBase(RoomModel)
        rooms = crud_room.get_all(db)
    finally:
        db.close()

    with st.expander("➕ Add New Room", expanded=False):
        with st.form("add_room_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            name       = c1.text_input("Room Name*")
            capacity   = c2.number_input("Capacity", 10, 500, 60)
            room_type  = c3.selectbox("Type", ["classroom", "lab"])
            submitted  = st.form_submit_button("Add Room", type="primary")
            if submitted:
                if not name:
                    st.error("Room name is required.")
                else:
                    db2 = get_session()
                    try:
                        crud_room.create(db2, {"name": name, "capacity": int(capacity), "room_type": room_type})
                        st.success(f"Room **{name}** added!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        db2.close()

    if not rooms:
        st.info("No rooms added yet.")
    else:
        cols = st.columns(3)
        for i, r in enumerate(rooms):
            icon = "🔬" if r.room_type == "lab" else "🏫"
            with cols[i % 3]:
                st.markdown(f"""
                <div class="ttg-card">
                    {icon} <strong>{r.name}</strong><br>
                    <small style="color:#94a3b8">
                        {r.room_type.capitalize()} · Capacity: {r.capacity}
                    </small>
                </div>""", unsafe_allow_html=True)
                if st.button("🗑 Delete", key=f"del_room_{r.id}"):
                    db2 = get_session()
                    try:
                        crud_room.delete(db2, r.id)
                        st.rerun()
                    finally:
                        db2.close()


# ══════════════════════════════════════════════════════════════════════════════
# SECTIONS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "sections":
    st.title("🗂 Sections")
    db = get_session()
    try:
        sections = crud_section.get_all(db)
        subjects = db.query(Subject).all()
        faculty_list = crud_faculty.get_all(db)
    finally:
        db.close()

    with st.expander("➕ Add New Section", expanded=False):
        with st.form("add_section_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            name      = c1.text_input("Section Name*")
            semester  = c2.number_input("Semester", 1, 12, 1)
            students  = c3.number_input("Student Count", 1, 200, 60)
            submitted = st.form_submit_button("Add Section", type="primary")
            if submitted:
                if not name:
                    st.error("Section name is required.")
                else:
                    db2 = get_session()
                    try:
                        crud_section.create(db2, {"name": name, "semester": int(semester), "student_count": int(students)})
                        st.success(f"Section **{name}** added!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        db2.close()

    if not sections:
        st.info("No sections added yet.")
    else:
        subj_map    = {s.id: s for s in subjects}
        faculty_map = {f.id: f for f in faculty_list}
        subj_opts   = {s.name: s.id for s in subjects}
        fac_opts    = {"(None)": None, **{f.name: f.id for f in faculty_list}}

        for sec in sections:
            with st.expander(f"🗂 {sec.name}  —  Semester {sec.semester}, {sec.student_count} students"):
                # Current assignments
                db2 = get_session()
                try:
                    assignments = crud_section.get_subjects(db2, sec.id)
                finally:
                    db2.close()

                if assignments:
                    st.markdown("**Assigned Subjects:**")
                    for a in assignments:
                        fac_name = a.faculty.name if a.faculty else "*(no faculty)*"
                        sub_name = a.subject.name if a.subject else "?"
                        c1, c2 = st.columns([5, 1])
                        c1.markdown(f"• **{sub_name}** &nbsp;→&nbsp; {fac_name}")
                        if c2.button("Remove", key=f"rm_ss_{sec.id}_{a.subject_id}"):
                            db3 = get_session()
                            try:
                                crud_section.remove_subject(db3, sec.id, a.subject_id)
                                st.rerun()
                            finally:
                                db3.close()
                else:
                    st.info("No subjects assigned yet.")

                # Assign new
                st.markdown("**Assign Subject + Faculty:**")
                with st.form(f"assign_subj_{sec.id}", clear_on_submit=True):
                    cs1, cs2 = st.columns(2)
                    sel_subj = cs1.selectbox("Subject", list(subj_opts.keys()), key=f"ss_{sec.id}")
                    sel_fac  = cs2.selectbox("Faculty", list(fac_opts.keys()), key=f"sf_{sec.id}")
                    if st.form_submit_button("Assign", type="primary"):
                        db4 = get_session()
                        try:
                            crud_section.assign_subject(db4, sec.id, subj_opts[sel_subj], fac_opts[sel_fac])
                            st.success("Assigned!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                        finally:
                            db4.close()

                if st.button("🗑 Delete Section", key=f"del_sec_{sec.id}", type="secondary"):
                    db5 = get_session()
                    try:
                        crud_section.delete(db5, sec.id)
                        st.rerun()
                    finally:
                        db5.close()


# ══════════════════════════════════════════════════════════════════════════════
# TIME SLOTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "timeslots":
    st.title("🕐 Time Slots")
    db = get_session()
    try:
        timeslots = db.query(Timeslot).order_by(Timeslot.day_of_week, Timeslot.period_number).all()
    finally:
        db.close()

    tab1, tab2 = st.tabs(["🚀 Bulk Generate", "➕ Add Single"])

    with tab1:
        st.markdown("Quickly generate a full week's time slots by specifying the schedule structure.")
        with st.form("bulk_gen_form"):
            c1, c2, c3 = st.columns(3)
            ppd      = c1.number_input("Periods per day", 1, 12, 6)
            start_hr = c2.number_input("Start hour (24h)", 7, 12, 9)
            dur      = c3.number_input("Period duration (min)", 30, 120, 60)
            if st.form_submit_button("🚀 Generate Time Slots", type="primary"):
                db2 = get_session()
                try:
                    result = crud_timeslot.bulk_generate(db2, int(ppd), int(start_hr), int(dur))
                    st.success(f"✅ Generated {len(result)} time slots!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    db2.close()

    with tab2:
        with st.form("add_ts_form", clear_on_submit=True):
            DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            c1, c2, c3, c4 = st.columns(4)
            day    = c1.selectbox("Day", DAYS)
            period = c2.number_input("Period #", 1, 12, 1)
            start  = c3.time_input("Start Time")
            end    = c4.time_input("End Time")
            if st.form_submit_button("Add Slot", type="primary"):
                db2 = get_session()
                try:
                    crud_timeslot.create(db2, {
                        "day_of_week": day, "period_number": int(period),
                        "start_time": start, "end_time": end
                    })
                    st.success("Time slot added!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    db2.close()

    if timeslots:
        st.markdown("### Current Time Slots")
        # Pivot by day
        DAYS_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        by_day = {}
        for ts in timeslots:
            by_day.setdefault(ts.day_of_week, []).append(ts)

        for day in DAYS_ORDER:
            if day not in by_day:
                continue
            st.markdown(f"**{day}**")
            for ts in by_day[day]:
                c1, c2 = st.columns([5, 1])
                c1.markdown(f"Period {ts.period_number}: `{fmt_time(ts.start_time)}–{fmt_time(ts.end_time)}`")
                if c2.button("🗑", key=f"del_ts_{ts.id}"):
                    db2 = get_session()
                    try:
                        crud_timeslot.delete(db2, ts.id)
                        st.rerun()
                    finally:
                        db2.close()
    else:
        st.info("No time slots yet. Use Bulk Generate above.")


# ══════════════════════════════════════════════════════════════════════════════
# GENERATE TIMETABLE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "generate":
    st.title("⚡ Generate Timetable")

    db = get_session()
    try:
        generations = db.query(TimetableGeneration).order_by(TimetableGeneration.created_at.desc()).all()
    finally:
        db.close()

    st.markdown("Choose an algorithm and click **Generate** to create a conflict-free timetable.")

    algo_col, btn_col = st.columns([2, 1])
    with algo_col:
        algorithm = st.selectbox(
            "Scheduling Algorithm",
            ["CSP (Backtracking + AC3)", "Genetic Algorithm"],
            help="CSP is exact but slower on large inputs. GA is heuristic-based and faster on complex schedules."
        )
    algo_key = "csp" if "CSP" in algorithm else "ga"

    with btn_col:
        st.markdown("<br>", unsafe_allow_html=True)
        run_clicked = st.button("⚡ Generate Timetable", type="primary")

    if run_clicked:
        # Step 1: Auto-assign subjects to sections
        db_auto = get_session()
        try:
            from app.auto_assigner import auto_assign
            num_created, assign_msgs = auto_assign(db_auto)
            if num_created > 0:
                st.info(f"🤖 Auto-assigned {num_created} subject-faculty-section mapping(s):")
                for msg in assign_msgs:
                    st.caption(msg)
            elif assign_msgs and any("⚠️" in m for m in assign_msgs):
                for msg in assign_msgs:
                    if "⚠️" in msg:
                        st.warning(msg)
        except Exception as e:
            st.warning(f"Auto-assign skipped: {e}")
        finally:
            db_auto.close()

        # Step 2: Pre-generation validation
        db_val = get_session()
        try:
            is_valid, val_errors = validate_before_generation(db_val)
        finally:
            db_val.close()

        if not is_valid:
            st.error("❌ Cannot generate timetable. Please fix the following issues:")
            for ve in val_errors:
                st.warning(f"⚠️ {ve}")
            st.stop()

        db2 = get_session()
        try:
            gen = TimetableGeneration(status="pending")
            db2.add(gen)
            db2.commit()
            db2.refresh(gen)
            gen_id = gen.id
        except Exception as e:
            st.error(f"❌ Could not create generation record: {e}")
            db2.close()
            st.stop()
        finally:
            db2.close()

        spinner_msg = "🔄 Running Genetic Algorithm…" if algo_key == "ga" else "🔄 Solving constraint satisfaction problem…"
        with st.spinner(spinner_msg):
            db3 = get_session()
            try:
                run_generation(db3, gen_id, algorithm=algo_key)
            except Exception as e:
                st.error(f"❌ Solver crashed: {e}")
            finally:
                db3.close()

        # Reload
        db4 = get_session()
        try:
            gen_result = db4.query(TimetableGeneration).filter(TimetableGeneration.id == gen_id).first()
            status = gen_result.status if gen_result else "unknown"
            err    = gen_result.error_message if gen_result else ""
        finally:
            db4.close()

        if status == "success":
            st.success("✅ Timetable generated successfully!")
        else:
            st.error(f"❌ Generation failed: {err}")
        st.rerun()

    # List all generations
    if generations:
        st.markdown("### Past Generations")
        for gen in generations:
            badge = status_badge(gen.status)
            ts_str = gen.created_at.strftime("%Y-%m-%d %H:%M") if gen.created_at else "—"
            active_str = " 🟢 **ACTIVE**" if gen.is_active else ""
            st.markdown(f"""
            <div class="ttg-card">
                <code>{gen.id[:8]}…</code> &nbsp; {badge} &nbsp; {active_str}
                <br><small style="color:#64748b">{ts_str}</small>
                {"<br><small style='color:#f87171'>" + (gen.error_message or "") + "</small>" if gen.error_message else ""}
            </div>""", unsafe_allow_html=True)

            c1, c2, c3 = st.columns([2, 2, 2])
            if gen.status == "success" and not gen.is_active:
                if c1.button("✅ Activate", key=f"act_{gen.id}"):
                    db5 = get_session()
                    try:
                        db5.query(TimetableGeneration).update({"is_active": False}, synchronize_session=False)
                        g = db5.query(TimetableGeneration).filter(TimetableGeneration.id == gen.id).first()
                        g.is_active = True
                        db5.commit()
                        st.success("Generation activated!")
                        st.rerun()
                    finally:
                        db5.close()

            if gen.status == "success":
                if c2.button("👁 View Timetable", key=f"view_{gen.id}"):
                    st.session_state["view_gen_id"] = gen.id

            if c3.button("🗑 Delete", key=f"del_gen_{gen.id}"):
                db6 = get_session()
                try:
                    g = db6.query(TimetableGeneration).filter(TimetableGeneration.id == gen.id).first()
                    if g:
                        db6.delete(g)
                        db6.commit()
                    st.rerun()
                finally:
                    db6.close()

        # Inline viewer
        view_gen_id = st.session_state.get("view_gen_id")
        if view_gen_id:
            db7 = get_session()
            try:
                entries = db7.query(TimetableEntry).options(
                    joinedload(TimetableEntry.section),
                    joinedload(TimetableEntry.subject),
                    joinedload(TimetableEntry.faculty),
                    joinedload(TimetableEntry.room),
                    joinedload(TimetableEntry.timeslot),
                ).filter(TimetableEntry.generation_id == view_gen_id).all()
            finally:
                db7.close()

            if entries:
                DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                sections_in_gen = sorted(set(e.section.name for e in entries))
                max_period = max(e.timeslot.period_number for e in entries)

                st.markdown(f"#### 📋 Timetable Preview — `{view_gen_id[:8]}…`")
                sel_sec = st.selectbox("View section:", sections_in_gen)
                sec_entries = [e for e in entries if e.section.name == sel_sec]
                grid = {(e.timeslot.day_of_week, e.timeslot.period_number): e for e in sec_entries}

                header_cells = "".join(f"<th>{d}</th>" for d in DAYS)
                rows = f"<tr><th>Period</th>{header_cells}</tr>"
                for p in range(1, max_period + 1):
                    cells = f'<td class="period-cell">P{p}</td>'
                    for d in DAYS:
                        e = grid.get((d, p))
                        if e:
                            cells += f'<td><div class="entry-badge">{e.subject.code}<br><small>{e.faculty.name}</small><br><small>{e.room.name}</small></div></td>'
                        else:
                            cells += "<td>—</td>"
                    rows += f"<tr>{cells}</tr>"

                st.markdown(f'<div class="tt-grid"><table>{rows}</table></div>', unsafe_allow_html=True)
    else:
        st.info("No timetable generations yet. Click **Run CSP Solver** above.")


# ══════════════════════════════════════════════════════════════════════════════
# EXPORT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "export":
    st.title("📥 Export Timetable")

    db = get_session()
    try:
        active_gen = db.query(TimetableGeneration).filter(TimetableGeneration.is_active == True).first()
        if active_gen:
            all_entries = db.query(TimetableEntry).options(
                joinedload(TimetableEntry.section),
                joinedload(TimetableEntry.subject),
                joinedload(TimetableEntry.faculty),
                joinedload(TimetableEntry.room),
                joinedload(TimetableEntry.timeslot),
            ).filter(TimetableEntry.generation_id == active_gen.id).all()
        else:
            all_entries = []

        sections_list = db.query(Section).all()
        faculty_list  = crud_faculty.get_all(db)
    finally:
        db.close()

    if not active_gen:
        st.warning("⚠️ No active timetable. Go to ⚡ Generate Timetable and activate one first.")
    else:
        st.success(f"Active timetable: **{active_gen.id[:8]}…** ({len(all_entries)} entries)")

        st.markdown("---")
        st.markdown("### 📊 Excel Export (Full Timetable)")
        if all_entries:
            excel_buf = generate_full_excel(all_entries)
            st.download_button(
                "⬇️ Download Excel",
                data=excel_buf,
                file_name=f"timetable_{active_gen.id[:8]}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        else:
            st.info("No entries to export.")

        st.markdown("---")
        st.markdown("### 📄 PDF Export — By Section")
        for sec in sections_list:
            sec_entries = [e for e in all_entries if e.section_id == sec.id]
            if sec_entries:
                pdf_buf = generate_section_pdf(sec_entries, sec.name)
                st.download_button(
                    f"⬇️ {sec.name} PDF",
                    data=pdf_buf,
                    file_name=f"timetable_{sec.name}.pdf",
                    mime="application/pdf",
                    key=f"pdf_sec_{sec.id}"
                )

        st.markdown("---")
        st.markdown("### 📄 PDF Export — By Faculty")
        for fac in faculty_list:
            fac_entries = [e for e in all_entries if e.faculty_id == fac.id]
            if fac_entries:
                pdf_buf = generate_faculty_pdf(fac_entries, fac.name)
                st.download_button(
                    f"⬇️ {fac.name} PDF",
                    data=pdf_buf,
                    file_name=f"timetable_{fac.name}.pdf",
                    mime="application/pdf",
                    key=f"pdf_fac_{fac.id}"
                )
