import streamlit as st
from fpdf import FPDF
import datetime
from pathlib import Path
import pytz

# === Aircraft DATA ===
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

# === SIDEBAR ===
with st.sidebar:
    aircraft = st.selectbox("Select Aircraft", list(aircraft_data.keys()))
    ac = aircraft_data[aircraft]
    icon_path = icons.get(aircraft)
    if icon_path and Path(icon_path).exists():
        st.image(icon_path, width=240)
    st.subheader("Operational Limits")
    st.text(get_limits_text(ac))
    afm_path = afm_files.get(aircraft)
    if afm_path and Path(afm_path).exists():
        with open(afm_path, "rb") as f:
            st.download_button("Download Aircraft Flight Manual (AFM)", f, file_name=afm_path, mime="application/pdf")

# === TOP: AIRCRAFT NAME ===
st.markdown(f"<h1 style='text-align:center'>{aircraft}</h1>", unsafe_allow_html=True)

# === FUEL MODE ===
fuel_mode = st.radio(
    "Fuel input mode",
    ["Automatic maximum fuel (default)", "Manual fuel volume"],
    horizontal=True,
    index=0
)

# === INPUTS (NO LIMIT, ONLY ALERT) ===
def input_field(label, key, minv, val, units, step=1.0, fmt="%.2f"):
    field = st.number_input(
        f"{label} ({units})",
        min_value=minv,
        value=val,
        step=step,
        format=fmt,
        key=key
    )
    return field

if isinstance(ac['baggage_arm'], list):
    cols = st.columns(6)
    ew        = input_field("Empty Weight",      "ew",     0.0, 0.0, ac['units']['weight'])
    ew_arm    = input_field("EW Arm",            "ew_arm", 0.0, 0.0, ac['units']['arm'], step=0.001, fmt="%.3f")
    pilot     = input_field("Pilot & Passenger", "pilot",  0.0, 0.0, ac['units']['weight'])
    bag1      = input_field("Baggage Area 1",    "bag1",   0.0, 0.0, ac['units']['weight'])
    bag2      = input_field("Baggage Area 2",    "bag2",   0.0, 0.0, ac['units']['weight'])
else:
    cols = st.columns(5)
    ew        = input_field("Empty Weight",      "ew",     0.0, 0.0, ac['units']['weight'])
    ew_arm    = input_field("EW Arm",            "ew_arm", 0.0, 0.0, ac['units']['arm'], step=0.001, fmt="%.3f")
    pilot     = input_field("Pilot & Passenger", "pilot",  0.0, 0.0, ac['units']['weight'])
    bag1      = input_field("Baggage",           "bag1",   0.0, 0.0, ac['units']['weight'])
    bag2      = 0.0

# === FUEL LOGIC ===
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
    fuel_vol = input_field("Fuel Volume", "fuel_vol", 0.0, 0.0, 'L' if units_wt=='kg' else 'gal')
    fuel_weight = fuel_vol * fuel_density
    fuel_limit_by = "Manual Entry"

# === CALCULATIONS ===
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

# === BAGGAGE SUM (for Cessnas) ===
baggage_total_limit_warning = False
baggage_sum = bag1 + bag2
if isinstance(ac['baggage_arm'], list):
    if baggage_sum > 120:
        baggage_total_limit_warning = True

# === ALERTS ===
cg_color = get_cg_color(cg, ac['cg_limits'])
alert_list = []
if total_weight > ac['max_takeoff_weight']:
    alert_list.append("TOTAL WEIGHT EXCEEDS MAXIMUM TAKEOFF WEIGHT!")
if isinstance(ac['baggage_arm'], list):
    if bag1 > ac['max_baggage_weight'][0]:
        alert_list.append("BAGGAGE AREA 1 EXCEEDS LIMIT!")
    if bag2 > ac['max_baggage_weight'][1]:
        alert_list.append("BAGGAGE AREA 2 EXCEEDS LIMIT!")
    if baggage_sum > 120:
        alert_list.append("TOTAL BAGGAGE EXCEEDS 120 LB LIMIT!")
else:
    if bag1 > ac['max_baggage_weight']:
        alert_list.append("BAGGAGE EXCEEDS LIMIT!")
if ac.get("max_passenger_weight") and pilot > ac["max_passenger_weight"]:
    alert_list.append("PILOT & PASSENGER EXCEED LIMIT!")
if ac['cg_limits']:
    mn, mx = ac['cg_limits']
    if cg < mn or cg > mx:
        alert_list.append("CG OUTSIDE SAFE ENVELOPE!")

# === TABLE AND SUMMARY ===
# (igual ao anterior)

# === PDF Export (compact, only one CG limits, correct code colors, NO input blocks) ===
def pdf_colored_cell(pdf, text, color="black", w=0, h=8, ln=1, align='L'):
    colors = {
        "red": (200,0,0), "orange": (220,150,0), "green": (0,140,0), "blue": (0,0,200), "black": (0,0,0)
    }
    r, g, b = colors.get(color, (0,0,0))
    pdf.set_text_color(r, g, b)
    pdf.cell(w, h, text, ln=ln, align=align)
    pdf.set_text_color(0,0,0)

def generate_pdf(aircraft, registration, mission_number, flight_datetime_utc,
                 ew, ew_arm, pilot, bag1, bag2, fuel_weight, fuel_vol,
                 m_empty, m_pilot, m_bag1, m_bag2, m_fuel,
                 total_weight, total_moment, cg, ac, cg_color, fuel_mode, fuel_limit_by, alert_list, baggage_sum):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 15)
    pdf.cell(0, 9, "Mass & Balance Report", ln=True, align='C')
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 7, f"Aircraft: {aircraft} ({registration})", ln=True)
    pdf.cell(0, 7, f"Mission Number: {mission_number}", ln=True)
    pdf.cell(0, 7, f"Flight (UTC): {flight_datetime_utc}", ln=True)
    pdf.cell(0, 7, "Operator: Sevenair Academy", ln=True)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "Operational Limits:", ln=True)
    pdf.set_font("Arial", '', 10)
    for line in get_limits_text(ac).split('\n'):
        pdf.cell(0, 5, line, ln=True)
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 11)
    # Table
    if isinstance(ac['baggage_arm'], list):
        pdf.cell(35, 7, "Item", 1, 0)
        pdf.cell(30, 7, f"Wgt ({ac['units']['weight']})", 1, 0)
        pdf.cell(26, 7, f"Arm ({ac['units']['arm']})", 1, 0)
        pdf.cell(36, 7, f"Moment ({ac['units']['weight']}·{ac['units']['arm']})", 1, 1)
        pdf.set_font("Arial", '', 10)
        pdf.cell(35, 7, "Empty Weight", 1, 0)
        pdf.cell(30, 7, f"{ew:.2f}", 1, 0, 'C')
        pdf.cell(26, 7, f"{ew_arm:.3f}", 1, 0, 'C')
        pdf.cell(36, 7, f"{m_empty:.2f}", 1, 1, 'C')
        pdf.cell(35, 7, "Pilot & Passenger", 1, 0)
        pdf.cell(30, 7, f"{pilot:.2f}", 1, 0, 'C')
        pdf.cell(26, 7, f"{ac['pilot_arm']:.3f}", 1, 0, 'C')
        pdf.cell(36, 7, f"{m_pilot:.2f}", 1, 1, 'C')
        pdf.cell(35, 7, "Baggage Area 1", 1, 0)
        pdf.cell(30, 7, f"{bag1:.2f}", 1, 0, 'C')
        pdf.cell(26, 7, f"{ac['baggage_arm'][0]:.3f}", 1, 0, 'C')
        pdf.cell(36, 7, f"{m_bag1:.2f}", 1, 1, 'C')
        pdf.cell(35, 7, "Baggage Area 2", 1, 0)
        pdf.cell(30, 7, f"{bag2:.2f}", 1, 0, 'C')
        pdf.cell(26, 7, f"{ac['baggage_arm'][1]:.3f}", 1, 0, 'C')
        pdf.cell(36, 7, f"{m_bag2:.2f}", 1, 1, 'C')
        pdf.cell(35, 7, "Fuel", 1, 0)
        pdf.cell(30, 7, f"{fuel_weight:.2f}", 1, 0, 'C')
        pdf.cell(26, 7, f"{ac['fuel_arm']:.3f}", 1, 0, 'C')
        pdf.cell(36, 7, f"{m_fuel:.2f}", 1, 1, 'C')
    else:
        pdf.cell(35, 7, "Item", 1, 0)
        pdf.cell(30, 7, f"Wgt ({ac['units']['weight']})", 1, 0)
        pdf.cell(26, 7, f"Arm ({ac['units']['arm']})", 1, 0)
        pdf.cell(36, 7, f"Moment ({ac['units']['weight']}·{ac['units']['arm']})", 1, 1)
        pdf.set_font("Arial", '', 10)
        pdf.cell(35, 7, "Empty Weight", 1, 0)
        pdf.cell(30, 7, f"{ew:.2f}", 1, 0, 'C')
        pdf.cell(26, 7, f"{ew_arm:.3f}", 1, 0, 'C')
        pdf.cell(36, 7, f"{m_empty:.2f}", 1, 1, 'C')
        pdf.cell(35, 7, "Pilot & Passenger", 1, 0)
        pdf.cell(30, 7, f"{pilot:.2f}", 1, 0, 'C')
        pdf.cell(26, 7, f"{ac['pilot_arm']:.3f}", 1, 0, 'C')
        pdf.cell(36, 7, f"{m_pilot:.2f}", 1, 1, 'C')
        pdf.cell(35, 7, "Baggage", 1, 0)
        pdf.cell(30, 7, f"{bag1:.2f}", 1, 0, 'C')
        pdf.cell(26, 7, f"{ac['baggage_arm']:.3f}", 1, 0, 'C')
        pdf.cell(36, 7, f"{m_bag1:.2f}", 1, 1, 'C')
        pdf.cell(35, 7, "Fuel", 1, 0)
        pdf.cell(30, 7, f"{fuel_weight:.2f}", 1, 0, 'C')
        pdf.cell(26, 7, f"{ac['fuel_arm']:.3f}", 1, 0, 'C')
        pdf.cell(36, 7, f"{m_fuel:.2f}", 1, 1, 'C')
    pdf.ln(2)
    # Color summary values according to limits!
    pdf.set_font("Arial", 'B', 11)
    color_tw = get_color(total_weight, ac['max_takeoff_weight'])
    color_fuel = "green" if ((fuel_limit_by in ["Tank Capacity", "Maximum Weight"]) and (fuel_weight <= tank_capacity_weight)) else "red"
    pdf_colored_cell(pdf, f"Fuel: {fuel_vol:.1f} {'L' if ac['units']['weight']=='kg' else 'gal'} / {fuel_weight:.1f} {ac['units']['weight']} ({'Limited by tank capacity' if fuel_limit_by == 'Tank Capacity' else 'Limited by maximum weight'})", color_fuel)
    pdf.ln(6)
    pdf_colored_cell(pdf, f"Total Weight: {total_weight:.2f} {ac['units']['weight']}", color_tw)
    pdf.ln(6)
    pdf.cell(0, 7, f"Total Moment: {total_moment:.2f} {ac['units']['weight']}·{ac['units']['arm']}", ln=True)
    if ac['cg_limits']:
        cg_col = get_cg_color(cg, ac['cg_limits'])
        pdf_colored_cell(pdf, f"CG: {cg:.3f} {ac['units']['arm']}", cg_col)
        pdf.ln(6)
    pdf.ln(1)
    if alert_list:
        pdf.set_font("Arial", 'B', 11)
        pdf.set_text_color(200,0,0)
        for a in list(dict.fromkeys(alert_list)): # unique only
            pdf.cell(0, 8, f"WARNING: {a}", ln=True)
        pdf.set_text_color(0,0,0)
    pdf.ln(1)
    pdf.set_font("Arial", 'I', 9)
    pdf.cell(0, 6, "Auto-generated by Mass & Balance Planner (Streamlit)", ln=True)
    return pdf

# === PDF FORM FIELDS ===
with st.expander("Generate PDF report"):
    registration = st.text_input("Aircraft registration", value="CS-XXX")
    mission_number = st.text_input("Mission number", value="001")
    utc_today = utc_now()
    default_datetime = utc_today.strftime("%Y-%m-%d %H:%M UTC")
    flight_datetime_utc = st.text_input("Scheduled flight date and time (UTC)", value=default_datetime)
    if st.button("Generate PDF with current values"):
        pdf = generate_pdf(
            aircraft, registration, mission_number, flight_datetime_utc,
            ew, ew_arm, pilot, bag1, bag2, fuel_weight, fuel_vol,
            m_empty, m_pilot, m_bag1, m_bag2, m_fuel, total_weight, total_moment, cg, ac, cg_color, fuel_mode, fuel_limit_by, alert_list, baggage_sum
        )
        pdf_file = f"MB_mission{mission_number}.pdf"
        pdf.output(pdf_file)
        with open(pdf_file, "rb") as f:
            st.download_button("Download PDF", f, file_name=pdf_file, mime="application/pdf")
        st.success("PDF generated successfully!")

