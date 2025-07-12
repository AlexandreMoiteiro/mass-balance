import streamlit as st
from fpdf import FPDF
import datetime
from pathlib import Path
import pytz

# -- Set Streamlit page config for pro look --
st.set_page_config(
    page_title="EASA Mass & Balance Planner",
    page_icon="✈️",
    layout="wide",
)

# -- CSS for EASA/pro look --
st.markdown("""
    <style>
        html, body, [class*="st-"] {
            font-family: 'Segoe UI', 'Arial', sans-serif;
            background: #f6f8fb;
        }
        .cockpit-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
            margin-bottom: 18px;
            font-size: 1.07em;
            background: #fff;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 14px #dadada80;
        }
        .cockpit-table th, .cockpit-table td {
            border: 1px solid #e0e5ef;
            padding: 10px 0 10px 0;
            text-align: center;
        }
        .cockpit-table th {
            background: #1a3257;
            color: #fff;
            font-weight: 600;
            letter-spacing: 1px;
        }
        .cockpit-table td:first-child, .cockpit-table th:first-child {
            text-align: left;
            padding-left: 18px;
        }
        .highlight-green {color: #00ba45; font-weight: 600;}
        .highlight-red {color: #e13d2b; font-weight: 600;}
        .highlight-orange {color: #e8870f; font-weight: 600;}
        .blue-remark {color: #1a3257; font-weight: 600;}
        .easa-alert {
            color: #e13d2b;
            background: #ffe6e0;
            border-left: 6px solid #e13d2b;
            padding: 8px 18px;
            margin-bottom: 10px;
            border-radius: 3px;
            font-size: 1em;
            font-weight: 600;
        }
        .sb-header {margin-bottom: 0.4em;}
    </style>
""", unsafe_allow_html=True)

# ========== DATA DEFINITIONS ==========
aircraft_data = {
    "Tecnam P2008": {
        "fuel_arm": 2.209,
        "pilot_arm": 1.800,
        "baggage_arm": 2.417,
        "max_takeoff_weight": 650,
        "max_fuel_volume": 124.0,
        "max_passenger_weight": 230,
        "max_baggage_weight": 20,
        "cg_limits": (1.841, 1.978),
        "fuel_density": 0.72,
        "units": {"weight": "kg", "arm": "m"}
    },
    "Cessna 150": {
        "fuel_arm": 42.0,
        "pilot_arm": 35.0,
        "baggage_arm": [70.0, 90.0],
        "max_takeoff_weight": 1600,
        "max_fuel_volume": 22.5,
        "max_passenger_weight": None,
        "max_baggage_weight": [120, 40],
        "cg_limits": None,
        "fuel_density": 6.0,
        "units": {"weight": "lb", "arm": "in"}
    },
    "Cessna 152": {
        "fuel_arm": 42.0,
        "pilot_arm": 39.0,
        "baggage_arm": [64.0, 84.0],
        "max_takeoff_weight": 1670,
        "max_fuel_volume": 26,
        "max_passenger_weight": None,
        "max_baggage_weight": [120, 40],
        "cg_limits": (31.0, 35.0),
        "fuel_density": 6.0,
        "units": {"weight": "lb", "arm": "in"}
    }
}

icons = {
    "Tecnam P2008": "tecnam_icon.png",
    "Cessna 150": "cessna_icon.png",
    "Cessna 152": "cessna_icon.png"
}
afm_files = {
    "Tecnam P2008": "Tecnam_P2008_AFM.pdf",
    "Cessna 150": "Cessna_150_AFM.pdf",
    "Cessna 152": "Cessna_152_AFM.pdf"
}

def get_limits_text(ac):
    units = ac["units"]["weight"]
    arm_unit = ac["units"]["arm"]
    lines = [
        f"Max Takeoff Weight: {ac['max_takeoff_weight']} {units}",
        f"Max Fuel Volume: {ac['max_fuel_volume']} {'L' if units == 'kg' else 'gal'}",
    ]
    if ac.get("max_passenger_weight"):
        lines.append(f"Max Pilot+Passenger: {ac['max_passenger_weight']} {units}")
    if isinstance(ac["max_baggage_weight"], list):
        lines.append(f"Max Baggage Area 1: {ac['max_baggage_weight'][0]} {units}")
        lines.append(f"Max Baggage Area 2: {ac['max_baggage_weight'][1]} {units}")
        lines.append("Max Total Baggage: 120 lb")
    else:
        lines.append(f"Max Baggage: {ac['max_baggage_weight']} {units}")
    if ac.get("cg_limits"):
        lines.append(f"CG Limits: {ac['cg_limits'][0]} to {ac['cg_limits'][1]} {arm_unit}")
    return "\n".join(lines)

def get_color(val, limit):
    if limit is None: return "black"
    if val > limit:
        return "#e13d2b"
    elif val > (limit * 0.97):
        return "#e8870f"
    else:
        return "#00ba45"

def get_cg_color(cg, limits):
    if not limits: return "black"
    mn, mx = limits
    margin = (mx - mn) * 0.06
    if cg < mn or cg > mx:
        return "#e13d2b"
    elif cg < mn + margin or cg > mx - margin:
        return "#e8870f"
    else:
        return "#00ba45"

def colorize(text, color, bold=True):
    style = f"color:{color};"
    if bold:
        style += "font-weight:600;"
    return f"<span style='{style}'>{text}</span>"

def utc_now():
    return datetime.datetime.now(pytz.UTC)

# ===== SIDEBAR: AIRCRAFT/AFM =====
with st.sidebar:
    st.markdown('<h3 class="sb-header">Aircraft</h3>', unsafe_allow_html=True)
    aircraft = st.selectbox("Type", list(aircraft_data.keys()))
    ac = aircraft_data[aircraft]
    icon_path = icons.get(aircraft)
    if icon_path and Path(icon_path).exists():
        st.image(icon_path, width=200)
    st.divider()
    st.markdown('<h4 class="sb-header">Operational Limits</h4>', unsafe_allow_html=True)
    st.info(get_limits_text(ac), icon="⚠️")
    afm_path = afm_files.get(aircraft)
    if afm_path and Path(afm_path).exists():
        with open(afm_path, "rb") as f:
            st.download_button("📥 Download AFM", f, file_name=afm_path, mime="application/pdf")
    st.markdown("")

# ===== PAGE TITLE =====
st.markdown(
    f"""<div style='text-align:center'>
        <span style='font-size:2.5em;font-weight:700;color:#1a3257'>{aircraft}</span><br>
        <span style='font-size:1.2em;color:#444'>EASA Mass & Balance Planner</span>
    </div>""",
    unsafe_allow_html=True,
)
st.markdown("")

fuel_mode = st.radio(
    "Fuel Input Mode",
    ["Automatic maximum fuel (default)", "Manual fuel volume"],
    horizontal=True,
    index=0
)

# ====== INPUTS ======
def input_field(label, key, val, units):
    return st.number_input(
        f"{label} ({units})",
        value=val,
        step=1.0,
        format="%.2f",
        key=key
    )

cols = st.columns(2, gap="large")
with cols[0]:
    st.markdown("**Enter Weights:**")
    if isinstance(ac['baggage_arm'], list):
        ew     = input_field("Empty Weight",      "ew",   0.0, ac['units']['weight'])
        ew_arm = input_field("Empty Weight Arm",  "ew_arm", 0.0, ac['units']['arm'])
        pilot  = input_field("Pilot & Passenger", "pilot",  0.0, ac['units']['weight'])
        bag1   = input_field("Baggage Area 1",    "bag1",   0.0, ac['units']['weight'])
        bag2   = input_field("Baggage Area 2",    "bag2",   0.0, ac['units']['weight'])
    else:
        ew     = input_field("Empty Weight",      "ew",   0.0, ac['units']['weight'])
        ew_arm = input_field("Empty Weight Arm",  "ew_arm", 0.0, ac['units']['arm'])
        pilot  = input_field("Pilot & Passenger", "pilot",  0.0, ac['units']['weight'])
        bag1   = input_field("Baggage",           "bag1",   0.0, ac['units']['weight'])
        bag2   = 0.0

fuel_density = ac['fuel_density']
units_wt = ac['units']['weight']
units_arm = ac['units']['arm']

with cols[1]:
    st.markdown("**Fuel Loading:**")
    if fuel_mode == "Automatic maximum fuel (default)":
        useful_load = ac['max_takeoff_weight'] - (ew + pilot + bag1 + bag2)
        fuel_weight_possible = max(0.0, useful_load)
        tank_capacity_weight = ac['max_fuel_volume'] * fuel_density
        if fuel_weight_possible <= tank_capacity_weight:
            fuel_weight = fuel_weight_possible
            fuel_vol = fuel_weight / fuel_density
            fuel_limit_by = "Maximum Weight"
        else:
            fuel_weight = tank_capacity_weight
            fuel_vol = ac['max_fuel_volume']
            fuel_limit_by = "Tank Capacity"
    else:
        fuel_vol = st.number_input("Fuel Volume", value=0.0, step=1.0, format="%.2f")
        fuel_weight = fuel_vol * fuel_density
        fuel_limit_by = "Manual Entry"

# ====== MOMENTS, CG, SUMMARY ======
m_empty = ew * ew_arm
m_pilot = pilot * ac['pilot_arm']
if isinstance(ac['baggage_arm'], list):
    m_bag1 = bag1 * ac['baggage_arm'][0]
    m_bag2 = bag2 * ac['baggage_arm'][1]
else:
    m_bag1 = bag1 * ac['baggage_arm']
    m_bag2 = 0.0
m_fuel = fuel_weight * ac['fuel_arm']

total_weight = ew + pilot + bag1 + bag2 + fuel_weight
total_moment = m_empty + m_pilot + m_bag1 + m_bag2 + m_fuel
cg = (total_moment / total_weight) if total_weight > 0 else 0
baggage_sum = bag1 + bag2

# ====== EASA/COCKPIT ALERTS ======
alert_list = []
if total_weight > ac['max_takeoff_weight']:
    alert_list.append("Total weight exceeds maximum takeoff weight!")
if isinstance(ac['baggage_arm'], list):
    if bag1 > ac['max_baggage_weight'][0]:
        alert_list.append("Baggage Area 1 exceeds limit!")
    if bag2 > ac['max_baggage_weight'][1]:
        alert_list.append("Baggage Area 2 exceeds limit!")
    if baggage_sum > 120:
        alert_list.append("Total baggage exceeds 120 lb limit!")
else:
    if bag1 > ac['max_baggage_weight']:
        alert_list.append("Baggage exceeds limit!")
if ac.get("max_passenger_weight") and pilot > ac["max_passenger_weight"]:
    alert_list.append("Pilot & Passenger exceed limit!")
if ac['cg_limits']:
    mn, mx = ac['cg_limits']
    if cg < mn or cg > mx:
        alert_list.append("CG outside safe envelope!")

# ========== MASS & BALANCE COCKPIT TABLE ==========
st.markdown("### Cockpit Mass & Balance Table")
def cockpit_table_html(items, units_wt, units_arm):
    table = '<table class="cockpit-table">'
    table += (
        "<tr>"
        "<th>Item</th>"
        f"<th>Weight ({units_wt})</th>"
        f"<th>Arm Position ({units_arm})</th>"
        f"<th>Moment ({units_wt}·{units_arm})</th>"
        "</tr>"
    )
    for i in items:
        table += f"<tr><td>{i[0]}</td><td>{i[1]:.2f}</td><td>{i[2]:.3f}</td><td>{i[3]:.2f}</td></tr>"
    table += "</table>"
    return table

if isinstance(ac['baggage_arm'], list):
    items = [
        ("Empty Weight", ew, ew_arm, m_empty),
        ("Pilot & Passenger", pilot, ac['pilot_arm'], m_pilot),
        ("Baggage Area 1", bag1, ac['baggage_arm'][0], m_bag1),
        ("Baggage Area 2", bag2, ac['baggage_arm'][1], m_bag2),
        ("Fuel", fuel_weight, ac['fuel_arm'], m_fuel),
    ]
else:
    items = [
        ("Empty Weight", ew, ew_arm, m_empty),
        ("Pilot & Passenger", pilot, ac['pilot_arm'], m_pilot),
        ("Baggage", bag1, ac['baggage_arm'], m_bag1),
        ("Fuel", fuel_weight, ac['fuel_arm'], m_fuel),
    ]
st.markdown(cockpit_table_html(items, units_wt, units_arm), unsafe_allow_html=True)

# ========== SUMMARY & HIGHLIGHTS ==========
fuel_str = (
    f"Fuel possible: {colorize(f'{fuel_vol:.1f} {'L' if units_wt=='kg' else 'gal'} / {fuel_weight:.1f} {units_wt}', '#1a3257')} "
    f"({'Limited by tank capacity' if fuel_limit_by == 'Tank Capacity' else 'Limited by maximum weight'})"
    if fuel_mode == "Automatic maximum fuel (default)"
    else f"Fuel: {colorize(f'{fuel_vol:.1f} {'L' if units_wt=='kg' else 'gal'} / {fuel_weight:.1f} {units_wt}', '#1a3257')}"
)
summary_str = (
    f"{fuel_str}<br>"
    f"Total Weight: {colorize(f'{total_weight:.2f}', get_color(total_weight, ac['max_takeoff_weight']))} {units_wt}<br>"
    f"Total Moment: {total_moment:.2f} {units_wt}·{units_arm}<br>"
)
if ac['cg_limits']:
    summary_str += (
        f"CG: {colorize(f'{cg:.3f}', get_cg_color(cg, ac['cg_limits']))} {units_arm}<br>"
        f"CG Limits: {ac['cg_limits'][0]:.3f} to {ac['cg_limits'][1]:.3f} {units_arm}"
    )
st.markdown(f"<div style='margin-bottom:10px;font-size:1.15em'>{summary_str}</div>", unsafe_allow_html=True)
for a in alert_list:
    st.markdown(f"<div class='easa-alert'>{a}</div>", unsafe_allow_html=True)

# ======= PDF EXPORT: EASA STYLE =======
def generate_pdf(aircraft, registration, mission_number, flight_datetime_utc,
                 ew, ew_arm, pilot, bag1, bag2, fuel_weight, fuel_vol,
                 m_empty, m_pilot, m_bag1, m_bag2, m_fuel,
                 total_weight, total_moment, cg, ac, fuel_limit_by, alert_list, baggage_sum):
    pdf = FPDF()
    pdf.add_page()
    # Title section
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(26, 50, 87)
    pdf.cell(0, 14, "MASS & BALANCE REPORT", ln=True, align='C')
    pdf.ln(2)
    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(70,70,70)
    pdf.cell(0, 9, f"Aircraft: {aircraft} ({registration})", ln=True)
    pdf.cell(0, 9, f"Mission Number: {mission_number}", ln=True)
    pdf.cell(0, 9, f"Flight (UTC): {flight_datetime_utc}", ln=True)
    pdf.cell(0, 9, "Operator: Sevenair Academy", ln=True)
    pdf.ln(4)
    # Limits
    pdf.set_font("Arial", 'B', 13)
    pdf.set_text_color(0, 90, 170)
    pdf.cell(0, 8, "Operational Limits:", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(30,30,30)
    for line in get_limits_text(ac).split('\n'):
        pdf.cell(0, 6, line, ln=True)
    pdf.ln(5)
    # Table
    pdf.set_font("Arial", 'B', 12)
    col_widths = [46, 36, 34, 56]
    headers = ["Item", f"Weight ({ac['units']['weight']})", f"Arm ({ac['units']['arm']})", f"Moment ({ac['units']['weight']}·{ac['units']['arm']})"]
    for h, w in zip(headers, col_widths):
        pdf.set_text_color(255,255,255)
        pdf.set_fill_color(26, 50, 87)
        pdf.cell(w, 8, h, border=1, align='C', fill=True)
    pdf.ln()
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(0,0,0)
    if isinstance(ac['baggage_arm'], list):
        rows = [
            ("Empty Weight", ew, ew_arm, m_empty),
            ("Pilot & Passenger", pilot, ac['pilot_arm'], m_pilot),
            ("Baggage Area 1", bag1, ac['baggage_arm'][0], m_bag1),
            ("Baggage Area 2", bag2, ac['baggage_arm'][1], m_bag2),
            ("Fuel", fuel_weight, ac['fuel_arm'], m_fuel),
        ]
    else:
        rows = [
            ("Empty Weight", ew, ew_arm, m_empty),
            ("Pilot & Passenger", pilot, ac['pilot_arm'], m_pilot),
            ("Baggage", bag1, ac['baggage_arm'], m_bag1),
            ("Fuel", fuel_weight, ac['fuel_arm'], m_fuel),
        ]
    for row in rows:
        pdf.set_fill_color(255,255,255)
        pdf.cell(col_widths[0], 8, str(row[0]), border=1)
        pdf.cell(col_widths[1], 8, f"{row[1]:.2f}", border=1, align='C')
        pdf.cell(col_widths[2], 8, f"{row[2]:.3f}", border=1, align='C')
        pdf.cell(col_widths[3], 8, f"{row[3]:.2f}", border=1, align='C')
        pdf.ln()
    pdf.ln(2)
    # Results/summary
    pdf.set_font("Arial", 'B', 12)
    color_tw = get_color(total_weight, ac['max_takeoff_weight'])
    cg_col = get_cg_color(cg, ac['cg_limits']) if ac['cg_limits'] else "black"
    # Fuel
    pdf.set_text_color(0, 100, 170)
    fuel_str = f"Fuel: {fuel_vol:.1f} {'L' if ac['units']['weight']=='kg' else 'gal'} / {fuel_weight:.1f} {ac['units']['weight']} ({'Limited by tank capacity' if fuel_limit_by == 'Tank Capacity' else 'Limited by maximum weight'})"
    pdf.cell(0, 8, fuel_str, ln=True)
    # Total Weight
    if color_tw == "#00ba45":
        pdf.set_text_color(0,186,69)
    elif color_tw == "#e8870f":
        pdf.set_text_color(232,135,15)
    elif color_tw == "#e13d2b":
        pdf.set_text_color(225,61,43)
    pdf.cell(0, 8, f"Total Weight: {total_weight:.2f} {ac['units']['weight']}", ln=True)
    pdf.set_text_color(0,0,0)
    pdf.cell(0, 8, f"Total Moment: {total_moment:.2f} {ac['units']['weight']}·{ac['units']['arm']}", ln=True)
    if ac['cg_limits']:
        if cg_col == "#00ba45":
            pdf.set_text_color(0,186,69)
        elif cg_col == "#e8870f":
            pdf.set_text_color(232,135,15)
        elif cg_col == "#e13d2b":
            pdf.set_text_color(225,61,43)
        pdf.cell(0, 8, f"CG: {cg:.3f} {ac['units']['arm']}", ln=True)
        pdf.set_text_color(0,0,0)
    pdf.ln(2)
    # Warnings/alerts
    if alert_list:
        pdf.set_font("Arial", 'B', 11)
        pdf.set_text_color(225,61,43)
        for a in list(dict.fromkeys(alert_list)):
            pdf.cell(0, 8, f"WARNING: {a}", ln=True)
        pdf.set_text_color(0,0,0)
    pdf.ln(4)
    pdf.set_font("Arial", 'I', 9)
    pdf.set_text_color(150,150,150)
    pdf.cell(0, 8, "Auto-generated by EASA Mass & Balance Planner (Streamlit)", ln=True)
    return pdf

# ====== PDF EXPORT FORM ======
with st.expander("📄 Generate EASA-style PDF Report"):
    registration = st.text_input("Aircraft registration", value="CS-XXX")
    mission_number = st.text_input("Mission number", value="001")
    utc_today = utc_now()
    default_datetime = utc_today.strftime("%Y-%m-%d %H:%M UTC")
    flight_datetime_utc = st.text_input("Scheduled flight date and time (UTC)", value=default_datetime)
    if st.button("Generate PDF with current values"):
        pdf = generate_pdf(
            aircraft, registration, mission_number, flight_datetime_utc,
            ew, ew_arm, pilot, bag1, bag2, fuel_weight, fuel_vol,
            m_empty, m_pilot, m_bag1, m_bag2, m_fuel, total_weight, total_moment, cg, ac, fuel_limit_by, alert_list, baggage_sum
        )
        pdf_file = f"MB_{registration}_{mission_number}.pdf"
        pdf.output(pdf_file)
        with open(pdf_file, "rb") as f:
            st.download_button("Download PDF", f, file_name=pdf_file, mime="application/pdf")
        st.success("PDF generated successfully!")

# ======= END OF APP =======


