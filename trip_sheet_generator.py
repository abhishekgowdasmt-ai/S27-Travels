import pandas as pd
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
import os


# -------------------------------------------------
# SAFE NUMBER HANDLER
# -------------------------------------------------
def safe_number(value):
    try:
        if pd.isna(value):
            return 0
        return float(str(value).strip())
    except:
        return 0


# -------------------------------------------------
# DYNAMIC TIME AND KM DIFFERENCE CALCULATORS
# -------------------------------------------------
def calculate_duration(start_time, end_time):
    def parse_to_minutes(time_val):
        if pd.isna(time_val):
            return None
        # Handle datetime/time objects directly
        if hasattr(time_val, "hour") and hasattr(time_val, "minute"):
            return time_val.hour * 60 + time_val.minute
            
        s = str(time_val).strip().upper()
        if not s:
            return None
            
        is_pm = "PM" in s
        is_am = "AM" in s
        
        s = s.replace("AM", "").replace("PM", "").strip()
        s = s.replace("..", ".").replace("::", ":")
        
        if ":" in s:
            parts = s.split(":")
        elif "." in s:
            parts = s.split(".")
        else:
            try:
                hours = int(s)
                minutes = 0
                parts = [hours, minutes]
            except:
                return None
                
        try:
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
        except ValueError:
            return None
            
        if hours <= 12:
            if is_pm and hours < 12:
                hours += 12
            elif is_am and hours == 12:
                hours = 0
                
        return hours * 60 + minutes

    start_mins = parse_to_minutes(start_time)
    end_mins = parse_to_minutes(end_time)
    
    if start_mins is None or end_mins is None:
        return ""
        
    diff = end_mins - start_mins
    if diff < 0:
        # Duty crossed midnight
        diff += 1440
        
    hrs = diff // 60
    mins = diff % 60
    return f"{hrs:02d}HRS {mins:02d}MIN"


def calculate_km_difference(start_km, end_km):
    try:
        if pd.isna(start_km) or pd.isna(end_km):
            return ""
        s_km = float(str(start_km).strip())
        e_km = float(str(end_km).strip())
        diff = e_km - s_km
        if diff < 0:
            return ""  # Invalid negative distance
        if diff == int(diff):
            return str(int(diff))
        return f"{diff:.1f}"
    except:
        return ""


# -------------------------------------------------
# MAIN PDF GENERATION FUNCTION
# -------------------------------------------------
def generate_trip_sheets(excel_file_path, output_pdf_path, watermark_image_path):

    df = pd.read_excel(excel_file_path)
    
    # Normalize column names (strip whitespace and uppercase)
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    # Map common variations of column names to ensure compatibility
    column_mapping = {
        "SL. NO": "SL NO",
        "SL.NO": "SL NO",
        "SR NO": "SL NO",
        "SR. NO": "SL NO",
        "SR.NO": "SL NO",
        "SERIAL NO": "SL NO",
        "END LOCATION": "END LOACTION",
        "TOTAL HRS": "TOTAL HRS SMT",
        "TOTAL HOURS": "TOTAL HRS SMT",
        "TOTAL SMT HRS": "TOTAL HRS SMT",
        "TOTAL KM": "SMT TOTAL KM",
        "TOTAL KMS": "SMT TOTAL KM",
        "TOTAL KM SMT": "SMT TOTAL KM",
        "RUNNING KM": "SMT TOTAL KM",
        "MOBILE NO": "MOBIL NO",
        "MOBILE NUMBER": "MOBIL NO",
        "DRIVER MOB": "MOBIL NO",
    }
    
    rename_dict = {}
    for col in df.columns:
        for variation, standard in column_mapping.items():
            if col == variation.upper():
                rename_dict[col] = standard.upper()
                break
    df = df.rename(columns=rename_dict)

    df = df[df["SL NO"].astype(str).str.isnumeric()]
    df = df.reset_index(drop=True)

    # ---------- WATERMARK ----------
    def draw_watermark(canvas, doc):
        if not os.path.exists(watermark_image_path):
            return

        canvas.saveState()
        canvas.setFillAlpha(0.07)

        img = ImageReader(watermark_image_path)
        w, h = A4

        img_w = 120 * mm
        img_h = 120 * mm

        canvas.drawImage(
            img,
            (w - img_w) / 2,
            (h - img_h) / 2 + 45 * mm,
            img_w,
            img_h,
            mask="auto"
        )

        canvas.restoreState()

    # ---------- DOCUMENT ----------
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="CompanyTitle",
        fontSize=16,
        alignment=1,
        fontName="Helvetica-Bold"
    ))

    styles.add(ParagraphStyle(
        name="CenterSmall",
        fontSize=9,
        alignment=1
    ))

    styles.add(ParagraphStyle(
        name="Label",
        fontSize=9,
        fontName="Helvetica-Bold"
    ))

    styles.add(ParagraphStyle(
        name="Value",
        fontSize=9
    ))

    styles.add(ParagraphStyle(
        name="SignatureRight",
        fontSize=9,
        fontName="Helvetica-Bold",
        alignment=2
    ))

    def P(text, style="Value"):
        return Paragraph("" if pd.isna(text) else str(text), styles[style])

    story = []

    # ---------- LOOP EACH RECORD ----------
    for _, r in df.iterrows():

        parking = safe_number(r.get("PARKING"))
        toll = safe_number(r.get("TOLL"))
        parking_toll = parking + toll

        total_hrs_val = r.get("TOTAL HRS SMT")
        if pd.isna(total_hrs_val) or str(total_hrs_val).strip() == "":
            total_hrs_val = calculate_duration(r.get("PICKUP TIME"), r.get("END TIME"))

        if pd.isna(total_hrs_val) or str(total_hrs_val).strip() == "":
            total_hrs_str = "<b>Total Hrs:</b>"
        else:
            total_hrs_str = f"<b>Total Hrs:</b> {total_hrs_val}"

        total_km_val = r.get("SMT TOTAL KM")
        if pd.isna(total_km_val) or str(total_km_val).strip() == "":
            total_km_val = calculate_km_difference(r.get("START KM"), r.get("END KM"))

        if pd.isna(total_km_val) or str(total_km_val).strip() == "":
            total_km_str = "<b>Total KMs:</b>"
        else:
            total_km_str = f"<b>Total KMs:</b> {total_km_val}"

        logo_widget = ""
        if os.path.exists(watermark_image_path):
            logo_widget = Image(watermark_image_path, width=24*mm, height=24*mm)

        table_data = [
            [logo_widget, P("S27 TRAVELS", "CompanyTitle"), "", "", ""],
            ["", P(
                "Kanakapura Road, Bangalore, India 560062",
                "CenterSmall"
            ), "", "", ""],
            ["", P("Mob. No.: 8904357810 / 9448828489", "CenterSmall"), "", "", ""],

            [P("Trip Sheet No:", "Label"), P(r["SL NO"]),
             P("TRIP SHEET", "Label"), P("Date:", "Label"), P(r["DATE"])],

            # ✅ FIXED HERE
            [P("Guest Name:", "Label"), P(r["EMP NAME"]), "", "", ""],

            [P("Cab Booked:", "Label"), P(r["CAB TYPE"]),
             P("Car No:", "Label"), P(r["CAB REG NO"]), ""],

            # ✅ FIXED HERE
            [P("Driver Name:", "Label"), P(r["NAME"]),
             P("Driver Mob:", "Label"), P(r["MOBIL NO"]), ""],

            [P("Reporting Time:", "Label"), P(r["PICKUP TIME"]),
             P("Duty Type:", "Label"), P(r["DUTY TYPE"]), ""],

            [P("Start Location:", "Label"), P(r["PLAND START"]),
             P("End Location:", "Label"), P(r["END LOACTION"]), ""],

            [P("Start Time:", "Label"), P(r["PICKUP TIME"]),
             P("End Time:", "Label"), P(r["END TIME"]),
             P(total_hrs_str)],

            [P("Start Km:", "Label"), P(r["START KM"]),
             P("End Km:", "Label"), P(r["END KM"]),
             P(total_km_str)],

            [P("Parking / Toll:", "Label"), P(parking_toll),
             P("Service City:", "Label"), P("Bengaluru"), ""],
        ]

        col_widths = [32*mm, 38*mm, 28*mm, 42*mm, 30*mm]
        table = Table(table_data, colWidths=col_widths)

        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.7, colors.black),

            ("SPAN", (0, 0), (0, 2)),
            ("SPAN", (1, 0), (-1, 0)),
            ("SPAN", (1, 1), (-1, 1)),
            ("SPAN", (1, 2), (-1, 2)),

            ("SPAN", (2, 3), (2, 3)),
            ("SPAN", (1, 4), (-1, 4)),
            ("SPAN", (3, 5), (-1, 5)),
            ("SPAN", (3, 6), (-1, 6)),
            ("SPAN", (3, 7), (-1, 7)),
            ("SPAN", (3, 8), (-1, 8)),
            ("SPAN", (3, 11), (-1, 11)),

            ("ALIGN", (0, 0), (-1, 2), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))

        story.append(table)

        # ---------- SIGNATURE ----------
        story.append(Spacer(1, 6 * mm))
        signature_table = Table(
            [[Paragraph("Signature", styles["SignatureRight"])]],
            colWidths=[170 * mm]
        )
        signature_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "RIGHT")
        ]))

        story.append(signature_table)
        story.append(PageBreak())

    # ---------- BUILD ----------
    doc.build(
        story,
        onFirstPage=draw_watermark,
        onLaterPages=draw_watermark
    )
