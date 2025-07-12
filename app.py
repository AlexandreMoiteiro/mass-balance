import streamlit as st
from fpdf import FPDF
import datetime
from pathlib import Path

# === Aircraft DATA (arms, weights, baggage areas, etc) ===
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
        "baggage_arm": [70.0, 90.0],  # Area 1, Area 2
        "max_takeoff_weight": 1600,
        "max_fuel_volume": 22.5,
        "max_passenger_weight": None,
        "max_baggage_weight": [120, 40],  # Area 1, Area 2
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
    units = ac["units"]["weight"]
    lines = [
        f"Max Takeoff Weight: {ac['max_takeoff_weight']} {units}",
        f"Max Fuel Volume: {ac['max_fuel_volume']} {'L' if units == 'kg' else 'gal'}",
    ]
    if ac.get("max_passenger_weight"):
        lines.append(f"Max Pilot+Passenger: {ac['max_passenger_weight']} {units}")
    if isinstance(ac["max_baggage_weight"], list):
        lines.append(f"Max Baggage Area 1: {ac['max_baggage_weight'][0]} {units}")
        lines.append(f"Max Baggage Area 2: {ac['max_baggage_weight'][1]} {units}")
        if sum(ac["max_baggage_weight"]) < 120 and units == "lb":
            lines.append("Combined baggage max: 120 lb")
    else:
        lines.append(f"Max Baggage: {ac['max_baggage_weight']} {units}")
    if ac.get("cg_limits"):
        lines.append(f"CG Limits: {ac['cg_limits'][0]} to {ac['cg_limits'][1]} {ac['units']['arm']}")
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

# === Top center: Aircraft name ===
st.markdown(f"<h1 style='text-align:center'>{aircraft}</h1>", unsafe_allow_html=True)

# === FUEL MODE ===
fuel_mode = st.radio(
    "Fuel input mode",
    ["Automatic maximum fuel (default)", "Manual fuel volume"],
    horizontal=True,
    index=0
)

# === INPUTS ===
if isinstance(ac['baggage_arm'], list):
    # Two baggage areas (Cessna)
    col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 2, 2])
    with col1:
        ew = st.number_input(
            f"Empty Weight ({ac['units']['weight']})",
            min_value=0.0,
            max_value=float(ac['max_takeoff_weight']),
            value=0.0, step=1.0, format="%.2f")
    with col2:
        ew_arm = st.number_input(
            f"EW Arm ({ac['units']['arm']})",
            min_value=0.0,
            max_value=200.0 if ac['units']['arm'] == "in" else 10.0,
            value=0.0, step=0.001, format="%.3f")
    with col3:
        pilot = st.number_input(
            f"Pilot & Passenger ({ac['units']['weight']})",
            min_value=0.0,
            max_value=400.0,  # No explicit limit
            value=0.0, step=1.0, format="%.2f")
    with col4:
        bag1 = st.number_input(
            f"Baggage Area 1 ({ac['units']['weight']})",
            min_value=0.0,
            max_value=float(ac['max_baggage_weight'][0]),
            value=0.0, step=1.0, format="%.2f")
    with col5:
        bag2 = st.number_input(
            f"Baggage Area 2 ({ac['units']['weight']})",
            min_value=0.0,
            max_value=float(ac['max_baggage_weight'][1]),
            value=0.0, step=1.0, format="%.2f")
else:
    # Tecnam P2008
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
    with col1:
        ew = st.number_input(
            f"Empty Weight ({ac['units']['weight']})",
            min_value=0.0,
            max_value=float(ac['max_takeoff_weight']),
            value=0.0, step=1.0, format="%.2f")
    with col2:
        ew_arm = st.number_input(
            f"EW Arm ({ac['units']['arm']})",
            min_value=0.0,
            max_value=10.0,
            value=0.0, step=0.001, format="%.3f")
    with col3:
        pilot = st.number_input(
            f"Pilot & Passenger ({ac['units']['weight']})",
            min_value=0.0,
            max_value=float(ac['max_passenger_weight']),
            value=0.0, step=1.0, format="%.2f")
    with col4:
        bag1 = st.number_input(
            f"Baggage ({ac['units']['weight']})",
            min_value=0.0,
            max_value=float(ac['max_baggage_weight']),
            value=0.0, step=1.0, format="%.2f")
    bag2 = 0.0  # Not used

# === Fuel calculation, limitation logic ===
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
        fuel_limit_by = "Maximum weight"
    else:
        fuel_weight = tank_capacity_weight
        fuel_vol = ac['max_fuel_volume']
        fuel_limit_by = "Tank capacity"
    fuel_note = "(auto-calculated for max weight/tank)"
else:
    fuel_vol = st.number_input(
        f"Fuel Volume ({'L' if units_wt=='kg' else 'gal'})",
        min_value=0.0, max_value=float(ac['max_fuel_volume']),
        value=0.0, step=1.0, format="%.2f"
    )
    fuel_weight = fuel_vol * fuel_density
    fuel_limit_by = "Manual entry"
    fuel_note = ""

# === Calculations ===
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

# === Table with results (no limits column) ===
st.markdown("### Mass & Balance Table")
if isinstance(ac['baggage_arm'], list):
    table_cols = st.columns([2, 2, 2, 2, 2, 2])
    table_cols[0].write("**Item**")
    table_cols[1].write(f"**Weight ({units_wt})**")
    table_cols[2].write(f"**Arm ({units_arm})**")
    table_cols[3].write(f"**Moment ({units_wt}·{units_arm})**")
    items = [
        ("Empty Weight", ew, ew_arm, m_empty),
        ("Pilot & Passenger", pilot, ac['pilot_arm'], m_pilot),
        ("Baggage Area 1", bag1, ac['baggage_arm'][0], m_bag1),
        ("Baggage Area 2", bag2, ac['baggage_arm'][1], m_bag2),
        ("Fuel", fuel_weight, ac['fuel_arm'], m_fuel),
    ]
    for i, (item, w, a, m) in enumerate(items):
        row = st.columns([2,2,2,2,2,2])
        row[0].write(item)
        row[1].write(f"{w:.2f}")
        row[2].write(f"{a:.3f}")
        row[3].write(f"{m:.2f}")
else:
    table_cols = st.columns([2, 2, 2, 2, 2])
    table_cols[0].write("**Item**")
    table_cols[1].write(f"**Weight ({units_wt})**")
    table_cols[2].write(f"**Arm ({units_arm})**")
    table_cols[3].write(f"**Moment ({units_wt}·{units_arm})**")
    items = [
        ("Empty Weight", ew, ew_arm, m_empty),
        ("Pilot & Passenger", pilot, ac['pilot_arm'], m_pilot),
        ("Baggage", bag1, ac['baggage_arm'], m_bag1),
        ("Fuel", fuel_weight, ac['fuel_arm'], m_fuel),
    ]
    for i, (item, w, a, m) in enumerate(items):
        row = st.columns([2,2,2,2,2])
        row[0].write(item)
        row[1].write(f"{w:.2f}")
        row[2].write(f"{a:.3f}")
        row[3].write(f"{m:.2f}")

# === Summary ===
cg_color = get_cg_color(cg, ac['cg_limits'])
st.markdown("---")
if fuel_mode == "Automatic maximum fuel (default)":
    fuel_summary = f"Fuel possible: <span style='color:blue'>{fuel_vol:.1f} {'L' if units_wt=='kg' else 'gal'} / {fuel_weight:.1f} {units_wt}</span> <span style='font-size:95%'>({fuel_limit_by})</span>"
else:
    fuel_summary = f"Fuel: <span style='color:blue'>{fuel_vol:.1f} {'L' if units_wt=='kg' else 'gal'} / {fuel_weight:.1f} {units_wt}</span>"

st.markdown(
    f"{fuel_summary}<br>"
    f"<b>Total Weight:</b> <span style='color:{get_color(total_weight, ac['max_takeoff_weight'])}'>{total_weight:.2f} {units_wt}</span><br>"
    f"<b>Total Moment:</b> {total_moment:.2f} {units_wt}·{units_arm}<br>"
    + (f"<b>CG:</b> <span style='color:{cg_color}'>{cg:.3f} {units_arm}</span><br>" if ac['cg_limits'] else "")
    + (f"<b>CG Limits:</b> {ac['cg_limits'][0]:.3f} to {ac['cg_limits'][1]:.3f} {units_arm}" if ac['cg_limits'] else ""),
    unsafe_allow_html=True
)
if ac['cg_limits']:
    if cg_color == "red":
        st.error("CG is OUTSIDE the safe envelope!")
    elif cg_color == "orange":
        st.warning("CG is close to the limit!")
    else:
        st.success("CG is WITHIN the safe envelope.")

# === PDF Export ===
def generate_pdf(aircraft, registration, mission_number, flight_date, flight_time,
                 ew, ew_arm, pilot, bag1, bag2, fuel_weight, fuel_vol,
                 m_empty, m_pilot, m_bag1, m_bag2, m_fuel,
                 total_weight, total_moment, cg, ac, cg_color, fuel_mode, fuel_limit_by):
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

    if isinstance(ac['baggage_arm'], list):
        # Cessna 150/152
        pdf.cell(38, 8, "Item", 1, 0)
        pdf.cell(32, 8, f"Weight ({ac['units']['weight']})", 1, 0)
        pdf.cell(28, 8, f"Arm ({ac['units']['arm']})", 1, 0)
        pdf.cell(40, 8, f"Moment ({ac['units']['weight']}·{ac['units']['arm']})", 1, 1)
        pdf.set_font("Arial", '', 12)
        pdf.cell(38, 8, "Empty Weight", 1, 0)
        pdf.cell(32, 8, f"{ew:.2f}", 1, 0, 'C')
        pdf.cell(28, 8, f"{ew_arm:.3f}", 1, 0, 'C')
        pdf.cell(40, 8, f"{m_empty:.2f}", 1, 1, 'C')
        pdf.cell(38, 8, "Pilot & Passenger", 1, 0)
        pdf.cell(32, 8, f"{pilot:.2f}", 1, 0, 'C')
        pdf.cell(28, 8, f"{ac['pilot_arm']:.3f}", 1, 0, 'C')
        pdf.cell(40, 8, f"{m_pilot:.2f}", 1, 1, 'C')
        pdf.cell(38, 8, "Baggage Area 1", 1, 0)
        pdf.cell(32, 8, f"{bag1:.2f}", 1, 0, 'C')
        pdf.cell(28, 8, f"{ac['baggage_arm'][0]:.3f}", 1, 0, 'C')
        pdf.cell(40, 8, f"{m_bag1:.2f}", 1, 1, 'C')
        pdf.cell(38, 8, "Baggage Area 2", 1, 0)
        pdf.cell(32, 8, f"{bag2:.2f}", 1, 0, 'C')
        pdf.cell(28, 8, f"{ac['baggage_arm'][1]:.3f}", 1, 0, 'C')
        pdf.cell(40, 8, f"{m_bag2:.2f}", 1, 1, 'C')
        pdf.cell(38, 8, "Fuel", 1, 0)
        pdf.cell(32, 8, f"{fuel_weight:.2f}", 1, 0, 'C')
        pdf.cell(28, 8, f"{ac['fuel_arm']:.3f}", 1, 0, 'C')
        pdf.cell(40, 8, f"{m_fuel:.2f}", 1, 1, 'C')
    else:
        # Tecnam P2008
        pdf.cell(38, 8, "Item", 1, 0)
        pdf.cell(32, 8, f"Weight ({ac['units']['weight']})", 1, 0)
        pdf.cell(28, 8, f"Arm ({ac['units']['arm']})", 1, 0)
        pdf.cell(40, 8, f"Moment ({ac['units']['weight']}·{ac['units']['arm']})", 1, 1)
        pdf.set_font("Arial", '', 12)
        pdf.cell(38, 8, "Empty Weight", 1, 0)
        pdf.cell(32, 8, f"{ew:.2f}", 1, 0, 'C')
        pdf.cell(28, 8, f"{ew_arm:.3f}", 1, 0, 'C')
        pdf.cell(40, 8, f"{m_empty:.2f}", 1, 1, 'C')
        pdf.cell(38, 8, "Pilot & Passenger", 1, 0)
        pdf.cell(32, 8, f"{pilot:.2f}", 1, 0, 'C')
        pdf.cell(28, 8, f"{ac['pilot_arm']:.3f}", 1, 0, 'C')
        pdf.cell(40, 8, f"{m_pilot:.2f}", 1, 1, 'C')
        pdf.cell(38, 8, "Baggage", 1, 0)
        pdf.cell(32, 8, f"{bag1:.2f}", 1, 0, 'C')
        pdf.cell(28, 8, f"{ac['baggage_arm']:.3f}", 1, 0, 'C')
        pdf.cell(40, 8, f"{m_bag1:.2f}", 1, 1, 'C')
        pdf.cell(38, 8, "Fuel", 1, 0)
        pdf.cell(32, 8, f"{fuel_weight:.2f}", 1, 0, 'C')
        pdf.cell(28, 8, f"{ac['fuel_arm']:.3f}", 1, 0, 'C')
        pdf.cell(40, 8, f"{m_fuel:.2f}", 1, 1, 'C')
    pdf.ln(3)
    pdf.set_font("Arial", 'B', 12)
    fuel_str = f"Fuel: {fuel_vol:.1f} {'L' if ac['units']['weight']=='kg' else 'gal'} / {fuel_weight:.1f} {ac['units']['weight']} ({fuel_limit_by})"
    pdf.cell(0, 8, fuel_str, ln=True)
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

# === PDF FORM FIELDS ===
with st.expander("Generate PDF report"):
    registration = st.text_input("Aircraft registration", value="CS-XXX")
    mission_number = st.text_input("Mission number", value="001")
    now = datetime.datetime.now()
    flight_date = st.text_input("Flight date", value=now.strftime("%d/%m/%Y"))
    flight_time = st.text_input("Flight time", value=now.strftime("%H:%M"))
    if st.button("Generate PDF with current values"):
        pdf = generate_pdf(
            aircraft, registration, mission_number, flight_date, flight_time,
            ew, ew_arm, pilot, bag1, bag2, fuel_weight, fuel_vol,
            m_empty, m_pilot, m_bag1, m_bag2, m_fuel, total_weight, total_moment, cg, ac, cg_color, fuel_mode, fuel_limit_by
        )
        pdf_file = f"MB_{aircraft.replace(' ','_')}_{mission_number}_{flight_date.replace('/','')}.pdf"
        pdf.output(pdf_file)
        with open(pdf_file, "rb") as f:
            st.download_button("Download PDF", f, file_name=pdf_file, mime="application/pdf")
        st.success("PDF generated successfully!")


