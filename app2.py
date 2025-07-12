import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
from pathlib import Path
import pytz

# ===== DATA =====
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
        return "red"
    elif val > (limit * 0.95):
        return "orange"
    else:
        return "green"

def get_cg_color(cg, limits):
    if not limits: return "black"
    mn, mx = limits
    margin = (mx - mn) * 0.05
    if cg < mn or cg > mx:
        return "red"
    elif cg < mn + margin or cg > mx - margin:
        return "orange"
    else:
        return "green"

def colorize(text, color, bold=True):
    style = f"color:{color};"
    if bold:
        style += "font-weight:bold;"
    return f"<span style='{style}'>{text}</span>"

def utc_now():
    return datetime.datetime.now(pytz.UTC)

# ====== Custom CSS ======
st.markdown("""
<style>
body {background: #f2f7fa;}
.header-main {
    background: linear-gradient(90deg, #0f2642 60%, #196ab3 100%);
    color: white;
    padding: 1.5em 0 0.7em 0;
    text-align: center;
    font-size: 2.2em;
    font-weight: bold;
    letter-spacing: 2px;
    border-radius: 0 0 16px 16px;
    box-shadow: 0 2px 18px #1251a430;
    margin-bottom: 12px;
}
.summary-card {
    background: #e7f1fa;
    border-radius: 10px;
    padding: 1.2em 1.3em 0.2em 1.3em;
    margin-bottom: 1.3em;
    box-shadow: 0 1px 8px #b2c7df45;
}
.cockpit-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
    margin-bottom: 14px;
    font-family: Arial, "Segoe UI", Helvetica, sans-serif;
}
.cockpit-table th, .cockpit-table td {
    border: 1px solid #bbb;
    padding: 9px 0 9px 0;
    text-align: center;
    font-size: 16px;
}
.cockpit-table th {
    background: #ebf1fb;
    font-weight: bold;
}
.cockpit-table td:first-child, .cockpit-table th:first-child {
    text-align: left;
    padding-left: 14px;
}
.cockpit-alert {
    color:#b30000;
    font-size:16px;
    font-weight:bold;
    margin-bottom:7px;
    letter-spacing: 1px;
}
</style>
<div class="header-main">
    ✈️ Mass & Balance Cockpit Planner
</div>
""", unsafe_allow_html=True)

# ====== SIDEBAR ======
with st.sidebar:
    st.header("Aircraft Profile")
    aircraft = st.selectbox("Select Aircraft", list(aircraft_data.keys()))
    ac = aircraft_data[aircraft]
    icon_path = icons.get(aircraft)
    if icon_path and Path(icon_path).exists():
        st.image(icon_path, width=230)
    st.write("### Operational Limits")
    st.markdown(f"<div style='color:#003566;font-size:15px'>{get_limits_text(ac)}</div>", unsafe_allow_html=True)
    afm_path = afm_files.get(aircraft)
    if afm_path and Path(afm_path).exists():
        with open(afm_path, "rb") as f:
            st.download_button("📕 Download AFM", f, file_name=afm_path, mime="application/pdf")

# ====== MAIN PANEL ======
st.write("### Aircraft Loading")

fuel_mode = st.radio(
    "Fuel Input Mode",
    ["Automatic maximum fuel (default)", "Manual fuel volume"],
    horizontal=True,
    index=0,
    help="Choose 'Manual' to specify fuel quantity, otherwise the app will auto-calculate max safe fuel load."
)

def input_field(label, key, val, units, help_text=""):
    return st.number_input(
        f"{label} ({units})",
        value=val,
        step=1.0,
        format="%.2f",
        key=key,
        help=help_text
    )

# Input fields - use columns for a modern, cockpit-style grid
input_cols = st.columns(3)
if isinstance(ac['baggage_arm'], list):
    ew        = input_cols[0].number_input("Empty Weight",  value=0.0, step=1.0, format="%.2f", key="ew")
    ew_arm    = input_cols[1].number_input("Empty Weight Arm", value=0.0, step=0.01, format="%.3f", key="ew_arm")
    pilot     = input_cols[2].number_input("Pilot & Passenger", value=0.0, step=1.0, format="%.2f", key="pilot")
    bag1      = st.number_input("Baggage Area 1", value=0.0, step=1.0, format="%.2f", key="bag1")
    bag2      = st.number_input("Baggage Area 2", value=0.0, step=1.0, format="%.2f", key="bag2")
else:
    ew        = input_cols[0].number_input("Empty Weight",  value=0.0, step=1.0, format="%.2f", key="ew")
    ew_arm    = input_cols[1].number_input("Empty Weight Arm", value=0.0, step=0.01, format="%.3f", key="ew_arm")
    pilot     = input_cols[2].number_input("Pilot & Passenger", value=0.0, step=1.0, format="%.2f", key="pilot")
    bag1      = st.number_input("Baggage", value=0.0, step=1.0, format="%.2f", key="bag1")
    bag2      = 0.0

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
    fuel_vol = st.number_input("Fuel Volume", value=0.0, step=1.0, format="%.2f", key="fuel_vol")
    fuel_weight = fuel_vol * fuel_density
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

# ====== SUMMARY CARDS ======
st.markdown('<div class="summary-card">', unsafe_allow_html=True)
sc1, sc2, sc3, sc4 = st.columns([1,1,1,1.2])
sc1.metric("Total Weight", f"{total_weight:.1f} {units_wt}", 
    delta=f"Max {ac['max_takeoff_weight']} {units_wt}", 
    delta_color="inverse" if total_weight > ac['max_takeoff_weight'] else "off")
sc2.metric("CG", f"{cg:.3f} {units_arm}", 
    delta=f"{ac['cg_limits'][0]}–{ac['cg_limits'][1]} {units_arm}" if ac['cg_limits'] else "N/A",
    delta_color="inverse" if ac['cg_limits'] and (cg < ac['cg_limits'][0] or cg > ac['cg_limits'][1]) else "off")
sc3.metric("Fuel", f"{fuel_vol:.1f} {'L' if units_wt=='kg' else 'gal'}",
    delta=f"{fuel_weight:.1f} {units_wt}",
    help="Current fuel load (volume and weight)")
sc4.metric("Baggage", f"{baggage_sum:.1f} {units_wt}", 
    delta=f"Max {ac['max_baggage_weight']}" if isinstance(ac['max_baggage_weight'], (int, float)) else f"Areas 1/2: {ac['max_baggage_weight']}", 
    help="Sum of all baggage areas")
st.markdown('</div>', unsafe_allow_html=True)

# Show alerts
if alert_list:
    for a in alert_list:
        st.markdown(f"<div class='cockpit-alert'>⚠️ {a}</div>", unsafe_allow_html=True)
else:
    st.success("✅ All values within limits. Ready for flight.")

# ====== MASS & BALANCE TABLE ======
st.write("### Mass & Balance Table")
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

# ====== PDF COCKPIT (unchanged from your logic) ======
def generate_pdf(aircraft, registration, mission_number, flight_datetime_utc,
                 ew, ew_arm, pilot, bag1, bag2, fuel_weight, fuel_vol,
                 m_empty, m_pilot, m_bag1, m_bag2, m_fuel,
                 total_weight, total_moment, cg, ac, fuel_limit_by, alert_list, baggage_sum):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", 'B', 17)
    pdf.cell(0, 12, "Mass & Balance Report", ln=True, align='C')
    pdf.ln(2)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, f"Aircraft: {aircraft} ({registration})", ln=True)
    pdf.cell(0, 8, f"Mission Number: {mission_number}", ln=True)
    pdf.cell(0, 8, f"Flight (UTC): {flight_datetime_utc}", ln=True)
    pdf.cell(0, 8, "Operator: Sevenair Academy", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "Operational Limits:", ln=True)
    pdf.set_font("Arial", '', 11)
    for line in get_limits_text(ac).split('\n'):
        pdf.cell(0, 6, line, ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    # TABELA
    col_widths = [46, 36, 34, 56]
    headers = ["Item", f"Weight ({ac['units']['weight']})", f"Arm ({ac['units']['arm']})", f"Moment ({ac['units']['weight']}·{ac['units']['arm']})"]
    for h, w in zip(headers, col_widths):
        pdf.cell(w, 8, h, border=1, align='C')
    pdf.ln()
    pdf.set_font("Arial", '', 11)
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
        pdf.cell(col_widths[0], 8, str(row[0]), border=1)
        pdf.cell(col_widths[1], 8, f"{row[1]:.2f}", border=1, align='C')
        pdf.cell(col_widths[2], 8, f"{row[2]:.3f}", border=1, align='C')
        pdf.cell(col_widths[3], 8, f"{row[3]:.2f}", border=1, align='C')
        pdf.ln()
    pdf.ln(2)
    # RESUMO
    pdf.set_font("Arial", 'B', 12)
    color_tw = get_color(total_weight, ac['max_takeoff_weight'])
    cg_col = get_cg_color(cg, ac['cg_limits']) if ac['cg_limits'] else "black"
    # Fuel
    fuel_str = f"Fuel: {fuel_vol:.1f} {'L' if ac['units']['weight']=='kg' else 'gal'} / {fuel_weight:.1f} {ac['units']['weight']} ({'Limited by tank capacity' if fuel_limit_by == 'Tank Capacity' else 'Limited by maximum weight'})"
    pdf.set_text_color(0,140,0)
    pdf.cell(0, 8, fuel_str, ln=True)
    # Total Weight
    if color_tw == "green":
        pdf.set_text_color(0,140,0)
    elif color_tw == "orange":
        pdf.set_text_color(220,150,0)
    elif color_tw == "red":
        pdf.set_text_color(200,0,0)
    pdf.cell(0, 8, f"Total Weight: {total_weight:.2f} {ac['units']['weight']}", ln=True)
    pdf.set_text_color(0,0,0)
    pdf.cell(0, 8, f"Total Moment: {total_moment:.2f} {ac['units']['weight']}·{ac['units']['arm']}", ln=True)
    if ac['cg_limits']:
        if cg_col == "green":
            pdf.set_text_color(0,140,0)
        elif cg_col == "orange":
            pdf.set_text_color(220,150,0)
        elif cg_col == "red":
            pdf.set_text_color(200,0,0)
        pdf.cell(0, 8, f"CG: {cg:.3f} {ac['units']['arm']}", ln=True)
        pdf.set_text_color(0,0,0)
    pdf.ln(2)
    # ALERTAS finais (proporcionais)
    if alert_list:
        pdf.set_font("Arial", 'B', 11)
        pdf.set_text_color(200,0,0)
        for a in list(dict.fromkeys(alert_list)):
            pdf.cell(0, 8, f"WARNING: {a}", ln=True)
        pdf.set_text_color(0,0,0)
    pdf.ln(4)
    pdf.set_font("Arial", 'I', 9)
    pdf.cell(0, 8, "Auto-generated by Mass & Balance Planner (Streamlit)", ln=True)
    return pdf

# ====== PDF EXPORT ======
with st.expander("📝 Generate PDF report"):
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
        pdf_file = f"MB_mission{mission_number}.pdf"
        pdf.output(pdf_file)
        with open(pdf_file, "rb") as f:
            st.download_button("⬇️ Download PDF", f, file_name=pdf_file, mime="application/pdf")
        st.success("PDF generated successfully!")

# ========== END ==========
