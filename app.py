import streamlit as st
from fpdf import FPDF
import datetime
from pathlib import Path

# Aircraft icons (images must be in your project folder!)
icons = {
    "Tecnam P2008": "tecnam_icon.png",
    "Cessna 150": "cessna_icon.png",
    "Cessna 152": "cessna_icon.png"
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
    }
    # You can add more aircraft here following the pattern
}

def get_limits_text(ac):
    units = ac["units"]["weight"]
    lines = [
        f"Max Takeoff Weight: {ac['max_takeoff_weight']} {units}",
        f"Max Fuel Volume: {ac['max_fuel_volume']} L",
        f"Max Pilot+Passenger: {ac['max_passenger_weight']} {units}",
        f"Max Baggage: {ac['max_baggage_weight']} {units}",
        f"CG Limits: {ac['cg_limits'][0]} to {ac['cg_limits'][1]} {ac['units']['arm']}"
    ]
    return "\n".join(lines)

def get_color(val, limit):
    if val > limit:
        return "red"
    elif val > (limit * 0.95):
        return "orange"
    else:
        return "green"

def get_cg_color(cg, limits):
    mn, mx = limits
    margin = (mx - mn) * 0.05
    if cg < mn or cg > mx:
        return "red"
    elif cg < mn + margin or cg > mx - margin:
        return "orange"
    else:
        return "green"

# --- Sidebar: Aircraft selection and image ---
with st.sidebar:
    aircraft = st.selectbox("Select Aircraft", list(aircraft_data.keys()))
    ac = aircraft_data[aircraft]
    icon_path = icons.get(aircraft)
    if icon_path and Path(icon_path).exists():
        st.image(icon_path, width=250)
    st.subheader("Operational Limits")
    st.text(get_limits_text(ac))
    st.caption("Streamlit version. PDF report available.")

# --- Top center: Aircraft name ---
st.markdown(f"<h1 style='text-align:center'>{aircraft}</h1>", unsafe_allow_html=True)

# --- TABLE-STYLE UI: Inputs all in a single row, just like Tkinter ---
st.markdown("#### All entries below are in line, just like your Tkinter app. Fuel is always calculated automatically.")

col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
with col1:
    ew = st.number_input("Empty Weight", min_value=0.0, max_value=float(ac['max_takeoff_weight']), value=0.0, step=1.0, format="%.2f")
with col2:
    ew_arm = st.number_input("EW Arm", min_value=0.0, max_value=10.0, value=0.0, step=0.001, format="%.3f")
with col3:
    pilot = st.number_input("Pilot & Passenger", min_value=0.0, max_value=float(ac['max_passenger_weight']), value=0.0, step=1.0, format="%.2f")
with col4:
    baggage = st.number_input("Baggage", min_value=0.0, max_value=float(ac['max_baggage_weight']), value=0.0, step=1.0, format="%.2f")
with col5:
    st.markdown("<br>Fuel is auto", unsafe_allow_html=True)

# --- Fuel calculation (always auto) ---
useful_load = ac['max_takeoff_weight'] - (ew + pilot + baggage)
fw_max = max(0.0, useful_load)
fv_max = min(ac['max_fuel_volume'], fw_max / ac['fuel_density'])
fuel_weight = fv_max * ac['fuel_density']

# --- Calculations ---
m_empty = ew * ew_arm
m_pilot = pilot * ac['pilot_arm']
m_baggage = baggage * ac['baggage_arm']
m_fuel = fuel_weight * ac['fuel_arm']
total_weight = ew + pilot + baggage + fuel_weight
total_moment = m_empty + m_pilot + m_baggage + m_fuel
cg = (total_moment / total_weight) if total_weight > 0 else 0

# --- Table with results ---
st.markdown("### Mass & Balance Table")
result_cols = st.columns([2, 2, 2, 2, 2])
result_cols[0].write("**Item**")
result_cols[1].write("**Weight (kg)**")
result_cols[2].write("**Arm (m)**")
result_cols[3].write("**Moment (kg·m)**")
result_cols[4].write("**Limit**")

items = ["Empty Weight", "Pilot & Passenger", "Baggage", "Fuel"]
weights = [ew, pilot, baggage, fuel_weight]
arms = [ew_arm, ac['pilot_arm'], ac['baggage_arm'], ac['fuel_arm']]
moments = [m_empty, m_pilot, m_baggage, m_fuel]
limits = [
    f"≤ {ac['max_takeoff_weight']} kg",
    f"≤ {ac['max_passenger_weight']} kg",
    f"≤ {ac['max_baggage_weight']} kg",
    f"≤ {ac['max_fuel_volume']} L"
]
for i in range(4):
    row = st.columns([2,2,2,2,2])
    row[0].write(items[i])
    row[1].write(f"{weights[i]:.2f}")
    row[2].write(f"{arms[i]:.3f}")
    row[3].write(f"{moments[i]:.2f}")
    row[4].write(limits[i])

# --- Summary, like the Tkinter bottom area ---
cg_color = get_cg_color(cg, ac['cg_limits'])
st.markdown("---")
st.markdown(
    f"<b>Fuel possible:</b> <span style='color:blue'>{fv_max:.1f} L / {fuel_weight:.1f} kg</span> (tank/weight limited)<br>"
    f"<b>Total Weight:</b> <span style='color:{get_color(total_weight, ac['max_takeoff_weight'])}'>{total_weight:.2f} kg</span><br>"
    f"<b>Total Moment:</b> {total_moment:.2f} kg·m<br>"
    f"<b>CG:</b> <span style='color:{cg_color}'>{cg:.3f} m</span><br>"
    f"<b>CG Limits:</b> {ac['cg_limits'][0]:.3f} to {ac['cg_limits'][1]:.3f} m",
    unsafe_allow_html=True
)
if cg_color == "red":
    st.error("CG is OUTSIDE the safe envelope!")
elif cg_color == "orange":
    st.warning("CG is close to the limit!")
else:
    st.success("CG is WITHIN the safe envelope.")

# --- PDF Export (igual ao Tkinter) ---
def generate_pdf(aircraft, registration, mission_number, flight_date, flight_time,
                 ew, ew_arm, pilot, baggage, fuel_weight, fv_max,
                 m_empty, m_pilot, m_baggage, m_fuel, total_weight, total_moment, cg, ac, cg_color):
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
    pdf.cell(40, 8, "Item", 1, 0)
    pdf.cell(35, 8, "Weight (kg)", 1, 0)
    pdf.cell(30, 8, "Arm (m)", 1, 0)
    pdf.cell(40, 8, "Moment (kg·m)", 1, 0)
    pdf.cell(35, 8, "Limit", 1, 1)
    pdf.set_font("Arial", '', 12)
    items = ["Empty Weight", "Pilot & Passenger", "Baggage", "Fuel"]
    weights = [ew, pilot, baggage, fuel_weight]
    arms = [ew_arm, ac['pilot_arm'], ac['baggage_arm'], ac['fuel_arm']]
    moments = [m_empty, m_pilot, m_baggage, m_fuel]
    limits = [
        f"≤ {ac['max_takeoff_weight']} kg",
        f"≤ {ac['max_passenger_weight']} kg",
        f"≤ {ac['max_baggage_weight']} kg",
        f"≤ {ac['max_fuel_volume']} L"
    ]
    for item, w, a, m, l in zip(items, weights, arms, moments, limits):
        pdf.cell(40, 8, item, 1, 0)
        pdf.cell(35, 8, f"{w:.2f}", 1, 0, 'C')
        pdf.cell(30, 8, f"{a:.3f}", 1, 0, 'C')
        pdf.cell(40, 8, f"{m:.2f}", 1, 0, 'C')
        pdf.cell(35, 8, l, 1, 1, 'C')
    pdf.ln(3)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, f"Fuel possible: {fv_max:.1f} L / {fuel_weight:.1f} kg", ln=True)
    pdf.cell(0, 8, f"Total Weight: {total_weight:.2f} kg", ln=True)
    pdf.cell(0, 8, f"Total Moment: {total_moment:.2f} kg·m", ln=True)
    if cg_color == "red":
        pdf.set_text_color(200,0,0)
    elif cg_color == "orange":
        pdf.set_text_color(220,150,0)
    else:
        pdf.set_text_color(0,120,0)
    pdf.cell(0, 8, f"CG: {cg:.3f} m", ln=True)
    pdf.set_text_color(0,0,0)
    pdf.cell(0, 8, f"CG Limits: {ac['cg_limits'][0]:.3f} to {ac['cg_limits'][1]:.3f} m", ln=True)
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

# --- PDF FORM FIELDS ---
with st.expander("Generate PDF report"):
    registration = st.text_input("Aircraft registration", value="CS-XXX")
    mission_number = st.text_input("Mission number", value="001")
    now = datetime.datetime.now()
    flight_date = st.text_input("Flight date", value=now.strftime("%d/%m/%Y"))
    flight_time = st.text_input("Flight time", value=now.strftime("%H:%M"))
    if st.button("Generate PDF with current values"):
        pdf = generate_pdf(
            aircraft, registration, mission_number, flight_date, flight_time,
            ew, ew_arm, pilot, baggage, fuel_weight, fv_max,
            m_empty, m_pilot, m_baggage, m_fuel, total_weight, total_moment, cg, ac, cg_color
        )
        pdf_file = f"MB_{aircraft.replace(' ','_')}_{mission_number}_{flight_date.replace('/','')}.pdf"
        pdf.output(pdf_file)
        with open(pdf_file, "rb") as f:
            st.download_button("Download PDF", f, file_name=pdf_file, mime="application/pdf")
        st.success("PDF generated successfully!")


