from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
from io import BytesIO
from typing import Dict, Any, List

def render_plate_pdf(title: str, grid: Dict[str, Any]):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    width, height = landscape(A4)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(20*mm, height - 15*mm, title)

    rows = int(grid.get("rows", 4))
    cols = int(grid.get("cols", 6))
    cells: List[Dict[str, Any]] = grid.get("cells", [])

    labels = [["" for _ in range(cols)] for _ in range(rows)]
    ctrl = [[False for _ in range(cols)] for _ in range(rows)]
    for cell in cells:
        r = int(cell.get("r", 0))
        cidx = int(cell.get("c", 0))
        lab = str(cell.get("label", ""))
        is_ctrl = bool(cell.get("control", False)) or (lab.strip().upper()=="CONTROL")
        labels[r][cidx] = "CONTROL" if is_ctrl else lab
        ctrl[r][cidx] = is_ctrl

    table_w = width - 40*mm
    table_h = height - 60*mm
    x0 = 20*mm
    y0 = (height - table_h)/2 - 10*mm
    if y0 < 20*mm: y0 = 20*mm

    cell_w = table_w / cols
    cell_h = table_h / rows

    for r in range(rows):
        for cidx in range(cols):
            x = x0 + cidx * cell_w
            y = y0 + (rows-1-r) * cell_h
            c.setLineWidth(1)
            c.setStrokeColor(colors.black)
            fill = colors.Color(1,0.95,0.8) if ctrl[r][cidx] else colors.whitesmoke
            c.setFillColor(fill)
            c.rect(x, y, cell_w, cell_h, stroke=1, fill=1)

            c.setFillColor(colors.black)
            lab = labels[r][cidx]
            c.setFont("Helvetica", 9)
            if "/" in lab and lab != "CONTROL":
                a, b = lab.split("/", 1)
                c.drawCentredString(x + cell_w/2, y + cell_h/2 + 3, a.strip())
                c.drawCentredString(x + cell_w/2, y + cell_h/2 - 10, b.strip())
            else:
                c.setFont("Helvetica-Bold", 10 if lab=="CONTROL" else 9)
                c.drawCentredString(x + cell_w/2, y + cell_h/2 - 4, lab.strip())

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    for i, rl in enumerate(["A","B","C","D"][:rows]):
        y = y0 + (rows-1-i) * cell_h + cell_h/2 - 4
        c.drawRightString(x0 - 5, y, rl)
    for j in range(cols):
        x = x0 + j * cell_w + cell_w/2
        c.drawCentredString(x, y0 - 12, str(j+1))

    c.showPage()
    c.save()
    buf.seek(0)
    return buf

def render_stocks_pdf(settings, others, plan):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=15*mm, rightMargin=15*mm, topMargin=12*mm, bottomMargin=12*mm)
    styles = getSampleStyleSheet()
    elems = []

    title_text = "Stock solutions plan (basis: {:.6f} mmol/well; fixed 0.8 mL stocks)".format(float(settings.get("mmol_limitant_per_well", 0.0005)))
    title = Paragraph(title_text, styles["Title"])
    elems.append(title)
    elems.append(Spacer(1, 6))

    def table_from_rows(title, rows):
        data = [["ID/Name","MW","Uses","eq","Stock M","µL/well","Total mg (for 0.8 mL)","Total mL"]]
        for r in rows:
            data.append([r.get("id_or_name",""), r.get("mw_g_mol",""), r.get("uses",""), r.get("eq",""),
                         r.get("stock_M",""), r.get("per_well_uL",""), r.get("total_mass_mg",""), r.get("total_volume_mL","")])
        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0), colors.lightgrey),
            ("GRID",(0,0),(-1,-1), 0.25, colors.grey),
            ("FONTSIZE",(0,0),(-1,-1),8),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE")
        ]))
        elems.append(Paragraph(title, styles["Heading3"]))
        elems.append(t)
        elems.append(Spacer(1,6))

    table_from_rows("Aryl bromides", plan["totals"]["aryl"])
    table_from_rows("Alkyl bromides", plan["totals"]["alkyl"])
    table_from_rows("Other reagents", plan["totals"]["others"])

    if plan["totals"].get("mixed"):
        mix = plan["totals"]["mixed"]
        elems.append(Paragraph(mix["title"], styles["Heading3"]))
        info = [["Per-well (µL)", "Final volume (mL)"], [mix.get("per_well_uL",""), mix.get("total_volume_mL","")]]
        ti = Table(info)
        ti.setStyle(TableStyle([("GRID",(0,0),(-1,-1), 0.25, colors.grey), ("FONTSIZE",(0,0),(-1,-1),9)]))
        elems.append(ti)

        comp = [["Component","MW","Mix conc (M)","Mass for 0.8 mL (mg)"]]
        for c in mix["components"]:
            comp.append([c.get("name",""), c.get("mw_g_mol",""), c.get("mix_conc_M",""), c.get("total_mass_mg","")])
        tc = Table(comp, repeatRows=1)
        tc.setStyle(TableStyle([("GRID",(0,0),(-1,-1), 0.25, colors.grey), ("FONTSIZE",(0,0),(-1,-1),9), ("BACKGROUND",(0,0),(-1,0), colors.lightgrey)]))
        elems.append(Spacer(1,6))
        elems.append(tc)

    elems.append(Spacer(1,8))
    elems.append(Paragraph("Per-well pipetting grids (µL per well), ordered by plate and A1→A6, B1→B6, C1→C6, D1→D6", styles["Heading3"]))

    for grid in plan["grids"]:
        elems.append(Spacer(1,4))
        elems.append(Paragraph(f"Plate {grid['plate']}", styles["Heading4"]))
        cols = grid["columns"]
        rows = grid["rows"]
        data = [cols] + [[str(r.get(c, "")) for c in cols] for r in rows]
        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([
            ("GRID",(0,0),(-1,-1), 0.25, colors.grey),
            ("FONTSIZE",(0,0),(-1,-1),7),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("BACKGROUND",(0,0),(-1,0), colors.lightgrey),
        ]))
        elems.append(t)


    # --- Summaries by chemical (Aryl / Alkyl) ---
    elems.append(Spacer(1,8))
    elems.append(Paragraph("Well summary by chemical", styles["Heading2"]))

    def add_summary_table(title, mapping):
        elems.append(Paragraph(title, styles["Heading3"]))
        rows = [["Chemical", "Plates → Wells"]]
        # Sort chemicals alpha
        for chem in sorted(mapping.keys(), key=lambda x: (len(x), x)):
            plate_map = mapping[chem]
            # sort by plate number
            parts = []
            for pnum in sorted(plate_map.keys()):
                wells = plate_map[pnum]
                parts.append(f"Plate {pnum} (" + ", ".join(wells) + ")")
            rows.append([chem, ";  ".join(parts)])
        t = Table(rows, repeatRows=1, colWidths=[60*mm, None])
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0), colors.lightgrey),
            ("GRID",(0,0),(-1,-1), 0.25, colors.grey),
            ("FONTSIZE",(0,0),(-1,-1),8),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ]))
        elems.append(t)
        elems.append(Spacer(1,6))

    # Expect plan to be passed from caller (render_stocks_pdf signature already has it)
    # Here we re-use 'plan' from the function args
    add_summary_table("Aryl IDs", plan.get("summaries", {}).get("aryl", {}))
    add_summary_table("Alkyl IDs", plan.get("summaries", {}).get("alkyl", {}))

    doc.build(elems)
    buf.seek(0)
    return buf
