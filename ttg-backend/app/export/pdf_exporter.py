from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def generate_section_pdf(entries: list, section_name: str) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"Timetable — {section_name}", styles["Title"]))
    elements.append(Spacer(1, 12))

    if not entries:
        elements.append(Paragraph("No timetable entries found.", styles["Normal"]))
        doc.build(elements)
        buffer.seek(0)
        return buffer

    max_period = max(e.timeslot.period_number for e in entries)
    grid = {(e.timeslot.day_of_week, e.timeslot.period_number): e for e in entries}

    header = ["Period"] + DAYS
    table_data = [header]
    for period in range(1, max_period + 1):
        row = [str(period)]
        for day in DAYS:
            entry = grid.get((day, period))
            if entry:
                row.append(f"{entry.subject.code}\n{entry.faculty.name}\n{entry.room.name}")
            else:
                row.append("")
        table_data.append(row)

    t = Table(table_data, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_faculty_pdf(entries: list, faculty_name: str) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"Timetable — {faculty_name}", styles["Title"]))
    elements.append(Spacer(1, 12))

    if not entries:
        elements.append(Paragraph("No timetable entries found.", styles["Normal"]))
        doc.build(elements)
        buffer.seek(0)
        return buffer

    max_period = max(e.timeslot.period_number for e in entries)
    grid = {(e.timeslot.day_of_week, e.timeslot.period_number): e for e in entries}

    header = ["Period"] + DAYS
    table_data = [header]
    for period in range(1, max_period + 1):
        row = [str(period)]
        for day in DAYS:
            entry = grid.get((day, period))
            if entry:
                row.append(f"{entry.subject.code}\n{entry.section.name}\n{entry.room.name}")
            else:
                row.append("")
        table_data.append(row)

    t = Table(table_data, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer
