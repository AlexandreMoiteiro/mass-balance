import streamlit as st
from fpdf import FPDF
import datetime
from pathlib import Path
import pytz

# ======= THEME AND STYLE =======
st.set_page_config(
    page_title="Mass & Balance Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

def inject_css():
    st.markdown("""
        <style>
        html, body, [class*="css"]  { font-family: 'Segoe UI', Arial, Helvetica, sans-serif; }
        .easa-header {
            font-size: 2.7rem;
            font-weight: 700;
            color: #195ba6;
            letter-spacing: 2px;
            margin-bottom: 0.5rem;
        }
        .easa-section-title {
            font-size: 1.28rem;
            font-weight: 600;
            color: #195ba6;
            margin: 1.5rem 0 0.7rem 0;
        }
        .easa-summary {
            font-size: 1.15rem;
            font-weight: 500;
            background: #f0f4fa;
            border-radius: 8px;
            padding: 0.8em 1.2em;
            margin-bottom: 1em;
        }
        .easa-alert {
            color: #b30000;
            background: #fbe8e7;
            font-size: 1rem;
            font-weight: 500;
            padding: 0.4em 1em;
            border-radius: 7px;
            margin-bottom: 6px;
            border-left: 4px solid #c1272d;
        }
        .easa-table {
            background: #fff;
            border-radius: 10px;
            box-shadow: 0 2px 12px #0001;
            margin-bottom: 20px;
            width: 100%;
        }
        .easa-table th, .easa-table td {
            font-size: 1.07rem;
            padding: 0.7em 0.8em;
        }
        .easa-table th {
            background: #f5f8fb;
            color: #195ba6;
            font-weight: 600;
        }
        .easa-table tr:not(:last-child) td {
            border-bottom: 1px solid #e5e8ee;
        }
        .easa-limit-ok { color: #2c7c1a; font-weight:600; }
        .easa-limit-warn { color: #ff9000; font-weight:600; }
        .easa-limit-bad { color: #b30000; font-weight:600; }
        .easa-label {
            font-size: 0.97rem;
            color: #144377;
        }
        .stDownloadButton { margin-top: 15px !important; }
        .easa-pdf-footer { font-size:10px;color:#195ba6;opacity:0.8;}
        </style>
    """, unsafe_allow_html=True)

inject_css()

# ====== AIRCRAFT DATA =======
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
    if limit is None: return "easa-limit-ok"
    if val > limit:
        return "easa-limit-bad"
    elif val > (limit * 0.95):
        return "easa-limit-warn"
    else:
        return "easa-limit-ok"

def get_cg_color(cg, limits):
    if not limits: return "easa-limit-ok"
    mn, mx = limits
    margin = (mx - mn) * 0.05
    if cg < mn or cg > mx:
        return "easa-limit-bad"
    elif cg < mn + margin or cg > mx - margin:
        return "easa-limit-warn"
    else:
        return "easa-limit-ok"

def colorize(text, class_, bold=True):
    weight = 'font-weight:bold;' if bold else ''
    return f"<span class='{class_}' style='{weight}'>{text}</span>"

def utc_now():
    return datetime.datetime.now(pytz.UTC)

# ====== SIDEBAR ======
with st.sidebar:
    st.markdown('<span class="easa-header">✈️ Mass & Balance</span>', unsafe_allow_html=True)
    aircraft = st.selectbox("Aircraft Type", list(aircraft_data.keys()))
    ac = aircraft_data[aircraft]
    icon_path = icons.get(aircraft)
    if icon_path and Path(icon_path).exists():
        st.image(icon_path, width=180)
    st.markdown('<div class="easa-section-title">Operational Limits</div>', unsafe_allow_html=True)
    st.info(get_limits_text(ac))
    afm_path = afm_files.get(aircraft)
    if afm_path and Path(afm_path).exists():
        with open(afm_path, "rb") as f:
            st.download_button("Download Aircraft Flight Manual (AFM)", f, file_name=afm_path, mime="application/pdf")

# ====== TOP: AIRCRAFT NAME ======
st.markdown(f"<div class='easa-header' style='text-align:center'>{aircraft}</div>", unsafe_allow_html=True)
st.write("")  # Spacer

fuel_mode = st.radio(
    "Fuel Input Mode",
    ["Automatic maximum fuel (default)", "Manual fuel volume"],
    horizontal=True,
    index=0
)

def input_field(label, key, val, units, helptext=None):
    return st.number_input(
        f"{label} ({units})",
        value=val,
        step=1.0,
        format="%.2f",
        key=key,
        help=helptext
    )

st.markdown('<div class="easa-section-title">Input Masses</div>', unsafe_allow_html=True)

# ====== INPUTS ======
cols = st.columns(3)
with cols[0]:
    ew = input_field(
        "Empty Weight", "ew", 0.0, ac['units']['weight'],
        helptext="You can find the aircraft's empty weight and its arm on the Weight & Balance sheet in FlightLogger."
    )
    ew_arm = input_field(
        "Empty Weight Arm", "ew_arm", 0.0, ac['units']['arm'],
        helptext="You can find the aircraft's empty weight and its arm on the Weight & Balance sheet in FlightLogger."
    )
with cols[1]:
    pilot = input_field("Pilot & Passenger", "pilot", 0.0, ac['units']['weight'], helptext="Occupants weight (total)")
    if isinstance(ac['baggage_arm'], list):
        bag1 = input_field("Baggage Area 1", "bag1", 0.0, ac['units']['weight'])
        bag2 = input_field("Baggage Area 2", "bag2", 0.0, ac['units']['weight'])
    else:
        bag1 = input_field("Baggage", "bag1", 0.0, ac['units']['weight'])
        bag2 = 0.0
with cols[2]:
    if fuel_mode == "Automatic maximum fuel (default)":
        st.markdown('<span class="easa-label">Fuel will be maximized as per limitations.</span>', unsafe_allow_html=True)
    else:
        fuel_vol = st.number_input("Fuel Volume", value=0.0, step=1.0, format="%.2f")
        fuel_density = ac['fuel_density']
        fuel_weight = fuel_vol * fuel_density

# ====== CALCULATIONS ======
fuel_density = ac['fuel_density']
units_wt = ac['units']['weight']
units_arm = ac['units']['arm']

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
    fuel_limit_by = "Manual Entry"

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

# ====== ALERTS ======
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

# ====== SUMMARY ======
fuel_str = (
    f"Fuel possible: {colorize(f'{fuel_vol:.1f} {'L' if units_wt=='kg' else 'gal'} / {fuel_weight:.1f} {units_wt}', 'easa-limit-ok', bold=True)} "
    f"({'Limited by tank capacity' if fuel_limit_by == 'Tank Capacity' else 'Limited by maximum weight'})"
    if fuel_mode == "Automatic maximum fuel (default)"
    else f"Fuel: {colorize(f'{fuel_vol:.1f} {'L' if units_wt=='kg' else 'gal'} / {fuel_weight:.1f} {units_wt}', 'easa-limit-ok', bold=True)}"
)

summary_str = (
    f"{fuel_str}<br>"
    f"Total Weight: {colorize(f'{total_weight:.2f}', get_color(total_weight, ac['max_takeoff_weight']))} {units_wt}<br>"
    f"Total Moment: <b>{total_moment:.2f}</b> {units_wt}·{units_arm}<br>"
)
if ac['cg_limits']:
    summary_str += f"CG: {colorize(f'{cg:.3f}', get_cg_color(cg, ac['cg_limits']))} {units_arm}<br>"
    summary_str += f"CG Limits: {ac['cg_limits'][0]:.3f} to {ac['cg_limits'][1]:.3f} {units_arm}"

st.markdown(f'<div class="easa-summary">{summary_str}</div>', unsafe_allow_html=True)

for a in alert_list:
    st.markdown(f'<div class="easa-alert">{a}</div>', unsafe_allow_html=True)

# ====== TABLE (styled HTML for Streamlit) ======
def cockpit_table_html(items, units_wt, units_arm):
    table = '<table class="easa-table">'
    table += (
        "<tr>"
        "<th>Item</th>"
        f"<th>Weight ({units_wt})</th>"
        f"<th>Arm ({units_arm})</th>"
        f"<th>Moment ({units_wt}·{units_arm})</th>"
        "</tr>"
    )
    for i in items:
        table += f"<tr><td>{i[0]}</td><td>{i[1]:.2f}</td><td>{i[2]:.3f}</td><td>{i[3]:.2f}</td></tr>"
    table += "</table>"
    return table

st.markdown('<div class="easa-section-title">Mass & Balance Table</div>', unsafe_allow_html=True)
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

# ====== PDF GENERATION ======
def generate_pdf(aircraft, registration, mission_number, flight_datetime_utc,
                 ew, ew_arm, pilot, bag1, bag2, fuel_weight, fuel_vol,
                 m_empty, m_pilot, m_bag1, m_bag2, m_fuel,
                 total_weight, total_moment, cg, ac, fuel_limit_by, alert_list, baggage_sum):

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()
    # Header (Blue bar)
    pdf.set_fill_color(25, 91, 166)
    pdf.rect(0, 0, 210, 19, 'F')
    pdf.set_font("Arial", 'B', 19)
    pdf.set_text_color(255,255,255)
    pdf.set_xy(10,7)
    pdf.cell(0, 8, "MASS & BALANCE REPORT", ln=True, align='L')
    pdf.set_text_color(0,0,0)
    pdf.set_xy(10,20)
    pdf.ln(6)
    pdf.set_font("Arial", 'B', 13)
    pdf.cell(0, 9, f"{aircraft}  |  {registration}", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 7, f"Mission Number: {mission_number}", ln=True)
    pdf.cell(0, 7, f"Flight (UTC): {flight_datetime_utc}", ln=True)
    pdf.cell(0, 7, "Operator: Sevenair Academy", ln=True)
    pdf.ln(3)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "Operational Limits:", ln=True)
    pdf.set_font("Arial", '', 10)
    for line in get_limits_text(ac).split('\n'):
        pdf.cell(0, 5, line, ln=True)
    pdf.ln(3)
    pdf.set_font("Arial", 'B', 11)
    col_widths = [45, 36, 34, 55]
    headers = ["Item", f"Weight ({ac['units']['weight']})", f"Arm ({ac['units']['arm']})", f"Moment ({ac['units']['weight']}·{ac['units']['arm']})"]
    for h, w in zip(headers, col_widths):
        pdf.cell(w, 8, h, border=1, align='C')
    pdf.ln()
    pdf.set_font("Arial", '', 10)
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
        for val, w in zip(row, col_widths):
            if isinstance(val, str):
                pdf.cell(w, 8, val, border=1)
            else:
                pdf.cell(w, 8, f"{val:.2f}" if isinstance(val, float) else str(val), border=1, align='C')
        pdf.ln()
    pdf.ln(2)
    # Summary
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(25, 91, 166)
    fuel_str = f"Fuel: {fuel_vol:.1f} {'L' if ac['units']['weight']=='kg' else 'gal'} / {fuel_weight:.1f} {ac['units']['weight']} ({'Limited by tank capacity' if fuel_limit_by == 'Tank Capacity' else 'Limited by maximum weight'})"
    pdf.cell(0, 8, fuel_str, ln=True)
    pdf.set_text_color(0,0,0)
    pdf.cell(0, 8, f"Total Weight: {total_weight:.2f} {ac['units']['weight']}", ln=True)
    pdf.cell(0, 8, f"Total Moment: {total_moment:.2f} {ac['units']['weight']}·{ac['units']['arm']}", ln=True)
    if ac['cg_limits']:
        pdf.cell(0, 8, f"CG: {cg:.3f} {ac['units']['arm']}", ln=True)
    pdf.ln(1)
    if alert_list:
        pdf.set_font("Arial", 'B', 10)
        pdf.set_text_color(200,0,0)
        for a in list(dict.fromkeys(alert_list)):
            pdf.cell(0, 7, f"WARNING: {a}", ln=True)
        pdf.set_text_color(0,0,0)
    pdf.ln(7)
    # Aviation-style footer (Alexandre Moiteiro, cross-check/disclaimer)
    pdf.set_y(-22)
    pdf.set_font("Arial", 'I', 9)
    pdf.set_text_color(25,91,166)
    pdf.multi_cell(
        0, 7,
        "This document is for assistance and cross-checking only. It does not replace your responsibility to perform and verify your own calculations before flight.\n"
        "Program © Alexandre Moiteiro",
        align='C'
    )
    pdf.set_text_color(0,0,0)
    return pdf

# ====== PDF EXPORT FORM ======
st.markdown('<div class="easa-section-title">PDF Report</div>', unsafe_allow_html=True)
with st.expander("Generate PDF report", expanded=False):
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

