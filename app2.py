import streamlit as st
from fpdf import FPDF
import datetime
import pytz
from pathlib import Path

# Minimal theme config
st.set_page_config(
    page_title="Mass & Balance Planner",
    page_icon="✈️",
    layout="wide"
)

# Minimal, super-clean CSS
st.markdown("""
    <style>
        html, body, [class*="st-"] {
            font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
            background: #fafbfc;
        }
        .main-title {
            text-align: center;
            font-size: 2.3em;
            color: #183a6d;
            font-weight: 800;
            margin-top: 0.5em;
            margin-bottom: 0.2em;
            letter-spacing: -0.5px;
        }
        .subtitle {
            text-align: center;
            font-size: 1.04em;
            color: #3d485a;
            margin-bottom: 2.3em;
            font-weight: 400;
        }
        .cockpit-table {
            width: 100%;
            border-collapse: collapse;
            border-radius: 12px;
            background: #fff;
            box-shadow: 0 3px 18px 0 rgba(24,65,135,0.04);
        }
        .cockpit-table th {
            background: #183a6d;
            color: #fff;
            font-weight: 600;
            border: none;
            padding: 13px 0;
            font-size: 1.06em;
        }
        .cockpit-table td {
            border: none;
            padding: 13px 0;
            text-align: center;
            font-size: 1.03em;
            color: #2b3240;
        }
        .cockpit-table tr:nth-child(even) {
            background: #f5f7fa;
        }
        .cockpit-table td:first-child {
            text-align: left;
            padding-left: 20px;
            font-weight: 500;
        }
        .stButton>button, .stDownloadButton>button {
            background: #183a6d;
            color: #fff;
            font-weight: 600;
            border-radius: 7px;
            padding: 0.6em 1.8em;
            border: none;
            box-shadow: 0 2px 8px #183a6d16;
            font-size: 1.04em;
        }
        .stButton>button:hover, .stDownloadButton>button:hover {
            background: #22488c;
            color: #fff;
        }
        .stSidebar {
            background: #f6f8fa;
            border-right: none;
        }
        .info {
            color: #183a6d;
            font-weight: 500;
        }
        .alert {
            color: #d33;
            font-size: 1.09em;
            font-weight: 600;
            margin-top: 8px;
            background: #fff8f8;
            border-radius: 7px;
            padding: 7px 16px;
        }
        .credit-tiny {
            display: block;
            text-align: center;
            color: #adb4be;
            font-size: 0.92em;
            margin: 40px 0 10px 0;
            letter-spacing: 0.05em;
            user-select: none;
        }
    </style>
""", unsafe_allow_html=True)

# ---- Aircraft Data ----
aircraft_data = {
    "Tecnam P2008": {
        "fuel_arm": 2.209, "pilot_arm": 1.800, "baggage_arm": 2.417,
        "max_takeoff_weight": 650, "max_fuel_volume": 124.0, "max_passenger_weight": 230, "max_baggage_weight": 20,
        "cg_limits": (1.841, 1.978), "fuel_density": 0.72, "units": {"weight": "kg", "arm": "m"}
    },
    "Cessna 150": {
        "fuel_arm": 42.0, "pilot_arm": 35.0, "baggage_arm": [70.0, 90.0],
        "max_takeoff_weight": 1600, "max_fuel_volume": 22.5, "max_passenger_weight": None, "max_baggage_weight": [120, 40],
        "cg_limits": None, "fuel_density": 6.0, "units": {"weight": "lb", "arm": "in"}
    },
    "Cessna 152": {
        "fuel_arm": 42.0, "pilot_arm": 39.0, "baggage_arm": [64.0, 84.0],
        "max_takeoff_weight": 1670, "max_fuel_volume": 26, "max_passenger_weight": None, "max_baggage_weight": [120, 40],
        "cg_limits": (31.0, 35.0), "fuel_density": 6.0, "units": {"weight": "lb", "arm": "in"}
    }
}
icons = {"Tecnam P2008": "tecnam_icon.png", "Cessna 150": "cessna_icon.png", "Cessna 152": "cessna_icon.png"}
afm_files = {"Tecnam P2008": "Tecnam_P2008_AFM.pdf", "Cessna 150": "Cessna_150_AFM.pdf", "Cessna 152": "Cessna_152_AFM.pdf"}

def get_limits_text(ac):
    units = ac["units"]["weight"]; arm_unit = ac["units"]["arm"]
    lines = [f"Max Takeoff Weight: {ac['max_takeoff_weight']} {units}",
             f"Max Fuel Volume: {ac['max_fuel_volume']} {'L' if units == 'kg' else 'gal'}"]
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

def colorize(text, color, bold=True):
    style = f"color:{color};" + ("font-weight:600;" if bold else "")
    return f"<span style='{style}'>{text}</span>"

def get_color(val, limit):
    if limit is None: return "#444"
    if val > limit: return "#d23232"
    elif val > (limit * 0.97): return "#e8870f"
    else: return "#183a6d"

def get_cg_color(cg, limits):
    if not limits: return "#444"
    mn, mx = limits; margin = (mx - mn) * 0.06
    if cg < mn or cg > mx: return "#d23232"
    elif cg < mn + margin or cg > mx - margin: return "#e8870f"
    else: return "#183a6d"

def utc_now():
    return datetime.datetime.now(pytz.UTC)

# ---- Sidebar ----
with st.sidebar:
    st.title("Aircraft")
    aircraft = st.selectbox("Type", list(aircraft_data.keys()))
    ac = aircraft_data[aircraft]
    st.markdown("**Operational Limits:**")
    st.info(get_limits_text(ac))
    afm_path = afm_files.get(aircraft)
    if afm_path and Path(afm_path).exists():
        with open(afm_path, "rb") as f:
            st.download_button("Download Aircraft Manual (AFM)", f, file_name=afm_path, mime="application/pdf")

# ---- Main Title ----
st.markdown(f"<div class='main-title'>{aircraft} Mass & Balance Planner</div>", unsafe_allow_html=True)
st.markdown(f"<div class='subtitle'>Minimal, clean and modern mass & balance tool for small aircraft</div>", unsafe_allow_html=True)

# ---- Inputs ----
fuel_mode = st.radio("Fuel Mode", ["Automatic maximum fuel (default)", "Manual fuel volume"], horizontal=True)
with st.expander("Weights and Loading", expanded=True):
    cols = st.columns(3)
    with cols[0]:
        ew = st.number_input("Empty Weight", value=0.0, step=1.0, format="%.2f")
        ew_arm = st.number_input("Empty Weight Arm", value=0.0, step=1.0, format="%.3f")
    with cols[1]:
        pilot = st.number_input("Pilot & Passenger", value=0.0, step=1.0, format="%.2f")
        if isinstance(ac['baggage_arm'], list):
            bag1 = st.number_input("Baggage Area 1", value=0.0, step=1.0, format="%.2f")
            bag2 = st.number_input("Baggage Area 2", value=0.0, step=1.0, format="%.2f")
        else:
            bag1 = st.number_input("Baggage", value=0.0, step=1.0, format="%.2f")
            bag2 = 0.0
    with cols[2]:
        if fuel_mode.startswith("Auto"):
            fuel_density = ac['fuel_density']
            units_wt = ac['units']['weight']
            units_arm = ac['units']['arm']
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
            fuel_weight = fuel_vol * ac['fuel_density']
            fuel_limit_by = "Manual Entry"

# ---- Calculations ----
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

# ---- Alerts / Warnings ----
alert_list = []
if total_weight > ac['max_takeoff_weight']:
    alert_list.append("Total weight exceeds maximum takeoff weight!")
if isinstance(ac['baggage_arm'], list):
    if bag1 > ac['max_baggage_weight'][0]: alert_list.append("Baggage Area 1 exceeds limit!")
    if bag2 > ac['max_baggage_weight'][1]: alert_list.append("Baggage Area 2 exceeds limit!")
    if baggage_sum > 120: alert_list.append("Total baggage exceeds 120 lb limit!")
else:
    if bag1 > ac['max_baggage_weight']: alert_list.append("Baggage exceeds limit!")
if ac.get("max_passenger_weight") and pilot > ac["max_passenger_weight"]:
    alert_list.append("Pilot & Passenger exceed limit!")
if ac['cg_limits']:
    mn, mx = ac['cg_limits']
    if cg < mn or cg > mx: alert_list.append("CG outside safe envelope!")

# ---- Cockpit Table ----
def cockpit_table_html(items, units_wt, units_arm):
    table = '<table class="cockpit-table">'
    table += (
        "<tr>"
        "<th>Item</th>"
        f"<th>Weight ({units_wt})</th>"
        f"<th>Arm ({units_arm})</th>"
        f"<th>Moment</th>"
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
st.markdown("#### Mass & Balance Summary")
st.markdown(cockpit_table_html(items, ac['units']['weight'], ac['units']['arm']), unsafe_allow_html=True)

# ---- Summary and Alerts ----
summary_str = (
    f"**Fuel:** <span class='info'>{fuel_vol:.1f} {'L' if ac['units']['weight']=='kg' else 'gal'} / {fuel_weight:.1f} {ac['units']['weight']}</span>  "
    f"({'Limited by tank' if fuel_limit_by=='Tank Capacity' else 'Limited by weight'})<br>"
    f"**Total Weight:** {colorize(f'{total_weight:.2f}', get_color(total_weight, ac['max_takeoff_weight']))} {ac['units']['weight']}<br>"
    f"**Total Moment:** {total_moment:.2f} {ac['units']['weight']}·{ac['units']['arm']}<br>"
)
if ac['cg_limits']:
    summary_str += (
        f"**CG:** {colorize(f'{cg:.3f}', get_cg_color(cg, ac['cg_limits']))} {ac['units']['arm']}<br>"
        f"**CG Limits:** {ac['cg_limits'][0]:.3f} to {ac['cg_limits'][1]:.3f} {ac['units']['arm']}"
    )
st.markdown(summary_str, unsafe_allow_html=True)
if alert_list:
    st.markdown(f"<div class='alert'>{'<br>'.join(alert_list)}</div>", unsafe_allow_html=True)

# ---- PDF Export ----
def generate_pdf(aircraft, registration, mission_number, flight_datetime_utc,
                 ew, ew_arm, pilot, bag1, bag2, fuel_weight, fuel_vol,
                 m_empty, m_pilot, m_bag1, m_bag2, m_fuel,
                 total_weight, total_moment, cg, ac, fuel_limit_by, alert_list, baggage_sum):
    pdf = FPDF()
    pdf.add_page()
    # Minimal header
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(24,58,109)
    pdf.cell(0, 10, "Mass & Balance Report", ln=True, align='C')
    pdf.ln(2)
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(70,70,70)
    pdf.cell(0, 8, f"Aircraft: {aircraft} ({registration})", ln=True)
    pdf.cell(0, 8, f"Mission Number: {mission_number}", ln=True)
    pdf.cell(0, 8, f"Flight (UTC): {flight_datetime_utc}", ln=True)
    pdf.cell(0, 8, "Operator: [Your Club/School]", ln=True)
    pdf.ln(2)
    # Limits
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(24,58,109)
    pdf.cell(0, 8, "Operational Limits:", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(60,60,60)
    for line in get_limits_text(ac).split('\n'):
        pdf.cell(0, 6, line, ln=True)
    pdf.ln(2)
    # Table
    pdf.set_font("Arial", 'B', 11)
    headers = ["Item", f"Weight ({ac['units']['weight']})", f"Arm ({ac['units']['arm']})", "Moment"]
    col_widths = [46, 34, 32, 52]
    for h, w in zip(headers, col_widths):
        pdf.set_text_color(255,255,255)
        pdf.set_fill_color(24,58,109)
        pdf.cell(w, 8, h, border=0, align='C', fill=True)
    pdf.ln()
    pdf.set_font("Arial", '', 10)
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
        for v, w in zip(row, col_widths):
            pdf.cell(w, 8, f"{v:.2f}" if isinstance(v, float) else str(v), border=0, align='C')
        pdf.ln()
    pdf.ln(2)
    # Summary
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(24,58,109)
    fuel_str = f"Fuel: {fuel_vol:.1f} {'L' if ac['units']['weight']=='kg' else 'gal'} / {fuel_weight:.1f} {ac['units']['weight']} ({'Limited by tank' if fuel_limit_by=='Tank Capacity' else 'Limited by weight'})"
    pdf.cell(0, 8, fuel_str, ln=True)
    pdf.set_text_color(30,30,30)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, f"Total Weight: {total_weight:.2f} {ac['units']['weight']}", ln=True)
    pdf.cell(0, 8, f"Total Moment: {total_moment:.2f} {ac['units']['weight']}·{ac['units']['arm']}", ln=True)
    if ac['cg_limits']:
        pdf.cell(0, 8, f"CG: {cg:.3f} {ac['units']['arm']}", ln=True)
    pdf.ln(1)
    if alert_list:
        pdf.set_font("Arial", 'B', 10)
        pdf.set_text_color(210,50,50)
        for a in list(dict.fromkeys(alert_list)):
            pdf.cell(0, 8, f"WARNING: {a}", ln=True)
    # Tiny credit
    pdf.set_y(-18)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(173,180,190)
    pdf.cell(0, 8, "Website by Your Name", ln=True, align='C')
    return pdf

with st.expander("Generate PDF Report"):
    registration = st.text_input("Aircraft registration", value="CS-XXX")
    mission_number = st.text_input("Mission number", value="001")
    utc_today = utc_now()
    default_datetime = utc_today.strftime("%Y-%m-%d %H:%M UTC")
    flight_datetime_utc = st.text_input("Scheduled flight date/time (UTC)", value=default_datetime)
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
        st.success("PDF generated!")

# ---- Minimal tiny credit at the bottom ----
st.markdown("<span class='credit-tiny'>Website by Your Name</span>", unsafe_allow_html=True)




