import streamlit as st
from fpdf import FPDF
import datetime
from pathlib import Path

# --- Data and Files ---
icons = {
    "Tecnam P2008": "tecnam_icon.png",
    "Cessna 150": "cessna_icon.png",
    "Cessna 152": "cessna_icon.png"
}
manuals = {
    "Tecnam P2008": "om_tecnam_p2008.pdf",
    "Cessna 150": "om_cessna_150.pdf",
    "Cessna 152": "om_cessna_152.pdf"
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
        "max_fuel_volume": 24.5,
        "max_passenger_weight": None,
        "max_baggage_weight": [120, 40],
        "cg_limits": None,
        "fuel_density": 6.0,
        "units": {"weight": "lb", "arm": "in"}
    }
}
def get_limits_text(ac):
    u = ac["units"]
    txt = f"Max Takeoff Weight: {ac['max_takeoff_weight']} {u['weight']}\n"
    txt += f"Max Fuel Volume: {ac['max_fuel_volume']} {'L' if u['weight']=='kg' else 'gal'}\n"
    if ac['max_passenger_weight']:
        txt += f"Max Pilot+Passenger: {ac['max_passenger_weight']} {u['weight']}\n"
    if isinstance(ac['max_baggage_weight'], list):
        txt += f"Max Baggage Area 1: {ac['max_baggage_weight'][0]} {u['weight']}\n"
        txt += f"Max Baggage Area 2: {ac['max_baggage_weight'][1]} {u['weight']}\n"
        if 'Cessna' in u['arm']:
            txt += "Combined baggage max: 120 lb\n"
    else:
        txt += f"Max Baggage: {ac['max_baggage_weight']} {u['weight']}\n"
    if ac['cg_limits']:
        txt += f"CG Limits: {ac['cg_limits'][0]} to {ac['cg_limits'][1]} {u['arm']}"
    return txt.strip()
def get_item_limit(item, ac):
    u = ac['units']['weight']
    if item == "Empty Weight":
        return f"≤ {ac['max_takeoff_weight']} {u}"
    if item == "Pilot & Passenger":
        if ac.get('max_passenger_weight'):
            return f"≤ {ac['max_passenger_weight']} {u}"
        return "-"
    if item == "Baggage Area 1":
        return f"≤ {ac['max_baggage_weight'][0]} {u}"
    if item == "Baggage Area 2":
        return f"≤ {ac['max_baggage_weight'][1]} {u}"
    if item == "Baggage":
        return f"≤ {ac['max_baggage_weight']} {u}"
    if item == "Fuel":
        return f"≤ {ac['max_fuel_volume']}L" if u == "kg" else f"≤ {ac['max_fuel_volume']} gal"
    return "-"
def get_color(val, limit):
    if limit is None: return "black"
    if val > limit:
        return "red"
    elif val > (limit * 0.95):
        return "orange"
    else:
        return "green"
def get_cg_color(cg, ac):
    if not ac['cg_limits']:
        return "gray"
    mn, mx = ac['cg_limits']
    margin = (mx - mn) * 0.05
    if cg < mn or cg > mx:
        return "red"
    elif cg < mn + margin or cg > mx - margin:
        return "orange"
    else:
        return "green"

# --- SIDEBAR ---
with st.sidebar:
    aircraft = st.selectbox("Select Aircraft", list(aircraft_data.keys()))
    ac = aircraft_data[aircraft]
    icon_path = icons.get(aircraft)
    if icon_path and Path(icon_path).exists():
        st.image(icon_path, width=220)
    st.subheader("Operational Limits")
    st.text(get_limits_text(ac))
    # Download OM file for the selected aircraft
    man_path = manuals.get(aircraft)
    if man_path and Path(man_path).exists():
        with open(man_path, "rb") as f:
            st.download_button(f"Download {aircraft} OM", f, file_name=man_path)
    st.markdown("---")

# --- Top center: Aircraft name ---
st.markdown(f"<h1 style='text-align:center'>{aircraft}</h1>", unsafe_allow_html=True)

# --- TABLE-STYLE INPUTS (auto/manual fuel option) ---
st.markdown("")

col_fuelopt, col_space = st.columns([2,10])
with col_fuelopt:
    fuel_mode = st.radio("Fuel Calculation", ["Auto Maximum", "Manual"], index=0, help="Auto: system computes max fuel. Manual: you set fuel volume.")

# For Cessnas, baggage is split
is_baggage_split = isinstance(ac['baggage_arm'], list)
col1, col2, col3, col4, col5, col6 = st.columns([2,2,2,2,2,2]) if is_baggage_split else st.columns([2,2,2,2,2])

with col1:
    ew = st.number_input("Empty Weight", min_value=0.0, max_value=float(ac['max_takeoff_weight']), value=0.0, step=1.0, format="%.2f")
with col2:
    ew_arm = st.number_input("EW Arm", min_value=0.0, max_value=10.0 if ac['units']['arm']=='m' else 100.0, value=0.0, step=0.001, format="%.3f")
with col3:
    pilot = st.number_input("Pilot & Passenger", min_value=0.0, max_value=float(ac['max_passenger_weight']) if ac['max_passenger_weight'] else 200.0, value=0.0, step=1.0, format="%.2f")
if is_baggage_split:
    with col4:
        bag1 = st.number_input("Baggage Area 1", min_value=0.0, max_value=float(ac['max_baggage_weight'][0]), value=0.0, step=1.0, format="%.2f")
    with col5:
        bag2 = st.number_input("Baggage Area 2", min_value=0.0, max_value=float(ac['max_baggage_weight'][1]), value=0.0, step=1.0, format="%.2f")
else:
    with col4:
        bag1 = st.number_input("Baggage", min_value=0.0, max_value=float(ac['max_baggage_weight']), value=0.0, step=1.0, format="%.2f")
    bag2 = 0.0

# Fuel calculation
fuel_density = ac['fuel_density']
max_fuel_vol = ac['max_fuel_volume']
if fuel_mode == "Auto Maximum":
    useful_load = ac['max_takeoff_weight'] - (ew + pilot + bag1 + bag2)
    fw_max = max(0.0, useful_load)
    fv_max = min(max_fuel_vol, fw_max / fuel_density) if fuel_density > 0 else 0.0
    fuel_vol = fv_max
    fuel_weight = fuel_vol * fuel_density
else:
    with col5 if not is_baggage_split else col6:
        fuel_vol = st.number_input("Fuel Volume", min_value=0.0, max_value=max_fuel_vol, value=0.0, step=1.0, format="%.2f")
    fuel_weight = fuel_vol * fuel_density

# --- Calculations ---
pilot_arm = ac['pilot_arm']
fuel_arm = ac['fuel_arm']
m_empty = ew * ew_arm
m_pilot = pilot * pilot_arm
if is_baggage_split:
    bag_arms = ac['baggage_arm']
    m_b1 = bag1 * bag_arms[0]
    m_b2 = bag2 * bag_arms[1]
    m_baggage = m_b1 + m_b2
else:
    m_b1 = bag1 * ac['baggage_arm']
    m_b2 = 0.0
    m_baggage = m_b1
m_fuel = fuel_weight * fuel_arm

total_weight = ew + pilot + bag1 + bag2 + fuel_weight
total_moment = m_empty + m_pilot + m_baggage + m_fuel
cg = (total_moment / total_weight) if total_weight > 0 else 0

# --- Table ---
st.markdown("### Mass & Balance Table")
if is_baggage_split:
    items = ["Empty Weight", "Pilot & Passenger", "Baggage Area 1", "Baggage Area 2", "Fuel"]
    weights = [ew, pilot, bag1, bag2, fuel_weight]
    arms = [ew_arm, pilot_arm, bag_arms[0], bag_arms[1], fuel_arm]
    moments = [m_empty, m_pilot, m_b1, m_b2, m_fuel]
    limits = [
        get_item_limit("Empty Weight", ac),
        get_item_limit("Pilot & Passenger", ac),
        get_item_limit("Baggage Area 1", ac),
        get_item_limit("Baggage Area 2", ac),
        get_item_limit("Fuel", ac)
    ]
else:
    items = ["Empty Weight", "Pilot & Passenger", "Baggage", "Fuel"]
    weights = [ew, pilot, bag1, fuel_weight]
    arms = [ew_arm, pilot_arm, ac['baggage_arm'], fuel_arm]
    moments = [m_empty, m_pilot, m_b1, m_fuel]
    limits = [
        get_item_limit("Empty Weight", ac),
        get_item_limit("Pilot & Passenger", ac),
        get_item_limit("Baggage", ac),
        get_item_limit("Fuel", ac)
    ]
for i in range(len(items)):
    row = st.columns([2,2,2,2,2])
    row[0].write(items[i])
    row[1].write(f"{weights[i]:.2f}")
    row[2].write(f"{arms[i]:.3f}")
    row[3].write(f"{moments[i]:.2f}")
    row[4].write(limits[i])

# --- Summary ---
cg_color = get_cg_color(cg, ac) if ac['cg_limits'] else "gray"
units_wt = ac['units']['weight']
units_arm = ac['units']['arm']
st.markdown("---")
if fuel_mode == "Auto Maximum":
    fuel_info = f"{fuel_vol:.1f} {'L' if units_wt=='kg' else 'gal'} / {fuel_weight:.1f} {units_wt} (auto maximum)"
else:
    fuel_info = f"{fuel_vol:.1f} {'L' if units_wt=='kg' else 'gal'} / {fuel_weight:.1f} {units_wt} (manual input)"
st.markdown(
    f"<b>Fuel:</b> <span style='color:blue'>{fuel_info}</span><br>"
    f"<b>Total Weight:</b> <span style='color:{get_color(total_weight, ac['max_takeoff_weight'])}'>{total_weight:.2f} {units_wt}</span><br>"
    f"<b>Total Moment:</b> {total_moment:.2f} {units_wt}·{units_arm}<br>"
    f"<b>CG:</b> <span style='color:{cg_color}'>{cg:.3f} {units_arm}</span>"
    + (f"<br><b>CG Limits:</b> {ac['cg_limits'][0]:.3f} to {ac['cg_limits'][1]:.3f} {units_arm}" if ac['cg_limits'] else ""),
    unsafe_allow_html=True
)
if ac['cg_limits']:
    if cg_color == "red":
        st.error("CG is OUTSIDE the safe envelope!")
    elif cg_color == "orange":
        st.warning("CG is close to the limit!")
    else:
        st.success("CG is WITHIN the safe envelope.")

# --- PDF Export ---
def generate_pdf(aircraft, registration, mission_number, flight_date, flight_time,
                 items, weights, arms, moments, limits, fuel_info,
                 total_weight, total_moment, cg, ac, cg_color):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Mass & Balance Report", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, f"Aircraft: {aircraft} ({registration})", ln=True)
    pdf.cell(0, 8, f"Mission Number: {mission_number}", ln=True)
    pdf.cell(0, 8, f"Date: {flight_date}   Time: {flight_time}", ln=True)
    pdf.cell(0, 8, "Operator: Sevenair Academy", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(45, 8, "Item", 1, 0)
    pdf.cell(32, 8, f"Weight ({ac['units']['weight']})", 1, 0)
    pdf.cell(28, 8, f"Arm ({ac['units']['arm']})", 1, 0)
    pdf.cell(38, 8, f"Moment ({ac['units']['weight']}·{ac['units']['arm']})", 1, 0)
    pdf.cell(37, 8, "Limit", 1, 1)
    pdf.set_font("Arial", '', 12)
    for item, w, a, m, l in zip(items, weights, arms, moments, limits):
        pdf.cell(45, 8, str(item), 1, 0)
        pdf.cell(32, 8, f"{w:.2f}", 1, 0, 'C')
        pdf.cell(28, 8, f"{a:.3f}", 1, 0, 'C')
        pdf.cell(38, 8, f"{m:.2f}", 1, 0, 'C')
        pdf.cell(37, 8, l, 1, 1, 'C')
    pdf.ln(3)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, f"Fuel: {fuel_info}", ln=True)
    pdf.cell(0, 8, f"Total Weight: {total_weight:.2f} {ac['units']['weight']}", ln=True)
    pdf.cell(0, 8, f"Total Moment: {total_moment:.2f} {ac['units']['weight']}·{ac['units']['arm']}", ln=True)
    if ac['cg_limits']:
        if cg_color == "red":
            pdf.set_text_color(200,0,0)
        elif cg_color == "orange":
            pdf.set_text_color(220,150,0)
        else:
            pdf.set_text_color(0,120,0)
        pdf.cell(0, 8, f"CG: {cg:.3f} {ac['units']['arm']}", ln=True)
        pdf.set_text_color(0,0,0)
        pdf.cell(0, 8, f"CG Limits: {ac['cg_limits'][0]:.3f} to {ac['cg_limits'][1]:.3f} {ac['units']['arm']}", ln=True)
        if cg_color == "red":
            pdf.cell(0, 8, "CG is OUTSIDE the safe envelope!", ln=True)
        elif cg_color == "orange":
            pdf.cell(0, 8, "CG is close to the limit!", ln=True)
        else:
            pdf.cell(0, 8, "CG is WITHIN the safe envelope.", ln=True)
    pdf.ln(2)
    pdf.set_font("Arial", 'I', 9)
    pdf.cell(0, 7, "Auto-generated by Mass & Balance Planner (Streamlit)", ln=True)
    return pdf

with st.expander("Generate PDF report"):
    registration = st.text_input("Aircraft registration", value="CS-XXX")
    mission_number = st.text_input("Mission number", value="001")
    now = datetime.datetime.now()
    flight_date = st.text_input("Flight date", value=now.strftime("%d/%m/%Y"))
    flight_time = st.text_input("Flight time", value=now.strftime("%H:%M"))
    if st.button("Generate PDF with current values"):
        pdf = generate_pdf(
            aircraft, registration, mission_number, flight_date, flight_time,
            items, weights, arms, moments, limits, fuel_info,
            total_weight, total_moment, cg, ac, cg_color
        )
        pdf_file = f"MB_{aircraft.replace(' ','_')}_{mission_number}_{flight_date.replace('/','')}.pdf"
        pdf.output(pdf_file)
        with open(pdf_file, "rb") as f:
            st.download_button("Download PDF", f, file_name=pdf_file, mime="application/pdf")
        st.success("PDF generated successfully!")


