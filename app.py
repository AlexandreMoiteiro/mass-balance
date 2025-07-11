import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from fpdf import FPDF
import pandas as pd
import datetime
from pathlib import Path

# Aircraft icons - must be present in your project folder!
icons = {
    "Tecnam P2008": "tecnam_icon.png",
    "Cessna 150": "cessna_icon.png",
    "Cessna 152": "cessna_icon.png"
}

# Aircraft data (just as before)
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
    units = ac["units"]["weight"]
    parts = [
        f"Max Takeoff Weight: {ac['max_takeoff_weight']} {units}",
        f"Max Fuel Volume: {ac['max_fuel_volume']} {'L' if units == 'kg' else 'gal'}"
    ]
    if ac['max_passenger_weight']:
        parts.append(f"Max Pilot+Passenger: {ac['max_passenger_weight']} {units}")
    if isinstance(ac['max_baggage_weight'], list):
        parts.append(
            f"Max Baggage:\n Area1: {ac['max_baggage_weight'][0]} {units}\n Area2: {ac['max_baggage_weight'][1]} {units}"
        )
        if 'Cessna' in ac['units']['arm']:
            parts.append("Combined baggage max: 120 lb")
    else:
        parts.append(f"Max Baggage: {ac['max_baggage_weight']} {units}")
    if ac['cg_limits']:
        parts.append(f"CG Limits: {ac['cg_limits'][0]} to {ac['cg_limits'][1]} {ac['units']['arm']}")
    return "\n".join(parts)

def get_item_limit(item, ac):
    units = ac['units']['weight']
    if item == "Empty Weight":
        return f"≤ {ac['max_takeoff_weight']} {units}"
    if item == "Pilot & Passenger":
        if ac.get('max_passenger_weight'):
            return f"≤ {ac['max_passenger_weight']} {units}"
        return "-"
    if item == "Baggage Area 1":
        return f"≤ {ac['max_baggage_weight'][0]} {units}"
    if item == "Baggage Area 2":
        return f"≤ {ac['max_baggage_weight'][1]} {units}"
    if item == "Baggage":
        return f"≤ {ac['max_baggage_weight']} {units}"
    if item == "Fuel":
        return f"≤ {ac['max_fuel_volume']}L" if units == "kg" else f"≤ {ac['max_fuel_volume']} gal"
    return "-"

def get_color(val, limit, margin=0.05):
    if limit is None: return "black"
    if val > limit:
        return "red"
    elif val > (limit * (1 - margin)):
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

# === SIDEBAR: Aircraft and image ===
with st.sidebar:
    aircraft = st.selectbox("Select Aircraft", list(aircraft_data.keys()))
    ac = aircraft_data[aircraft]
    icon_path = icons.get(aircraft)
    if icon_path and Path(icon_path).exists():
        st.image(icon_path, width=220)
    st.subheader("Operational Limits")
    st.text(get_limits_text(ac))
    st.caption("Streamlit version. PDF report available.")

# === MAIN: AG-GRID TABLE FOR MASS & BALANCE ===
st.title("Mass & Balance Planner")
st.write("Enter all weights directly in the table. Calculations update instantly. (This is an interactive table, like Excel!)")

# Table configuration based on aircraft
if isinstance(ac['baggage_arm'], list):
    rowdata = [
        {"Item": "Empty Weight", "Weight": 0.0, "Arm": 0.0, "Limit": ac['max_takeoff_weight']},
        {"Item": "Pilot & Passenger", "Weight": 0.0, "Arm": ac['pilot_arm'], "Limit": ac['max_passenger_weight'] or None},
        {"Item": "Baggage Area 1", "Weight": 0.0, "Arm": ac['baggage_arm'][0], "Limit": ac['max_baggage_weight'][0]},
        {"Item": "Baggage Area 2", "Weight": 0.0, "Arm": ac['baggage_arm'][1], "Limit": ac['max_baggage_weight'][1]},
        {"Item": "Fuel Volume", "Weight": 0.0, "Arm": ac['fuel_arm'], "Limit": ac['max_fuel_volume']},
    ]
else:
    rowdata = [
        {"Item": "Empty Weight", "Weight": 0.0, "Arm": 0.0, "Limit": ac['max_takeoff_weight']},
        {"Item": "Pilot & Passenger", "Weight": 0.0, "Arm": ac['pilot_arm'], "Limit": ac['max_passenger_weight'] or None},
        {"Item": "Baggage", "Weight": 0.0, "Arm": ac['baggage_arm'], "Limit": ac['max_baggage_weight']},
        {"Item": "Fuel Volume", "Weight": 0.0, "Arm": ac['fuel_arm'], "Limit": ac['max_fuel_volume']},
    ]

df = pd.DataFrame(rowdata)

# Editable grid
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_column("Weight", editable=True, type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=2)
gb.configure_column("Arm", editable=("Empty Weight" in df["Item"].values), type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=3)
gb.configure_column("Limit", editable=False)
gb.configure_column("Item", editable=False)
grid_options = gb.build()

grid_return = AgGrid(
    df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    allow_unsafe_jscode=True,
    fit_columns_on_grid_load=True,
    theme="streamlit"
)

df = grid_return['data']

# Compute Fuel Weight if fuel is entered in volume
fuel_density = ac["fuel_density"]
for idx, row in df.iterrows():
    if "Fuel" in row["Item"]:
        fuel_vol = row["Weight"]
        fuel_weight = fuel_vol * fuel_density
        df.at[idx, "Weight"] = fuel_weight

# Calculate moments
moments = []
for idx, row in df.iterrows():
    moments.append(row["Weight"] * row["Arm"])
df["Moment"] = moments

# Total
total_weight = df["Weight"].sum()
total_moment = df["Moment"].sum()
cg = total_moment / total_weight if total_weight else 0.0

st.write("### Results")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Weight", f"{total_weight:.2f} {ac['units']['weight']}", delta=None)
col2.metric("Total Moment", f"{total_moment:.2f} {ac['units']['weight']}·{ac['units']['arm']}")
col3.metric("CG", f"{cg:.3f} {ac['units']['arm']}", delta=None)
if ac["cg_limits"]:
    mn, mx = ac["cg_limits"]
    if cg < mn or cg > mx:
        col4.markdown(f"<span style='color:red'><b>CG out of limits!</b></span>", unsafe_allow_html=True)
    else:
        col4.markdown(f"<span style='color:green'><b>CG within limits</b></span>", unsafe_allow_html=True)

# Show the editable table again for clarity
st.write("### Editable Mass & Balance Table")
st.dataframe(df, use_container_width=True)

# --- PDF GENERATION ---
def generate_pdf(df, ac, aircraft, registration, mission_number, cg, total_weight, total_moment):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Mass & Balance Report", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.ln(2)
    flight_date = datetime.datetime.now().strftime("%d/%m/%Y")
    flight_time = datetime.datetime.now().strftime("%H:%M")
    pdf.cell(0, 8, f"Aircraft: {aircraft} ({registration})", ln=True)
    pdf.cell(0, 8, "Operator: Sevenair Academy", ln=True)
    pdf.cell(0, 8, f"Mission Number: {mission_number}", ln=True)
    pdf.cell(0, 8, f"Date: {flight_date}", ln=True)
    pdf.cell(0, 8, f"Time: {flight_time}", ln=True)
    pdf.ln(3)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "Operational Limits:", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 6, f"- Max Takeoff Weight: {ac['max_takeoff_weight']} {ac['units']['weight']}", ln=True)
    pdf.cell(0, 6, f"- Max Fuel Volume: {ac['max_fuel_volume']} {'L' if ac['units']['weight'] == 'kg' else 'gal'}", ln=True)
    if ac.get('max_passenger_weight'):
        pdf.cell(0, 6, f"- Max Pilot & Passenger: {ac['max_passenger_weight']} {ac['units']['weight']}", ln=True)
    if isinstance(ac['max_baggage_weight'], list):
        pdf.cell(0, 6, f"- Max Baggage Area 1: {ac['max_baggage_weight'][0]} {ac['units']['weight']}", ln=True)
        pdf.cell(0, 6, f"- Max Baggage Area 2: {ac['max_baggage_weight'][1]} {ac['units']['weight']}", ln=True)
    else:
        pdf.cell(0, 6, f"- Max Baggage: {ac['max_baggage_weight']} {ac['units']['weight']}", ln=True)
    if ac['cg_limits']:
        mn, mx = ac['cg_limits']
        pdf.cell(0, 6, f"- CG Limits: {mn} to {mx} {ac['units']['arm']}", ln=True)
    pdf.ln(3)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(60, 8, "Item", 1, 0, 'C')
    pdf.cell(32, 8, f"Weight ({ac['units']['weight']})", 1, 0, 'C')
    pdf.cell(28, 8, f"Arm ({ac['units']['arm']})", 1, 0, 'C')
    pdf.cell(38, 8, f"Moment ({ac['units']['weight']}·{ac['units']['arm']})", 1, 1, 'C')
    pdf.set_font("Arial", '', 12)
    for _, row in df.iterrows():
        pdf.cell(60, 8, str(row["Item"]), 1, 0)
        pdf.cell(32, 8, f"{row['Weight']:.2f}", 1, 0, 'C')
        pdf.cell(28, 8, f"{row['Arm']:.3f}", 1, 0, 'C')
        pdf.cell(38, 8, f"{row['Moment']:.2f}", 1, 1, 'C')
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    if total_weight > ac['max_takeoff_weight']:
        pdf.set_text_color(200,0,0)
    else:
        pdf.set_text_color(0,150,0)
    pdf.cell(0, 8, f"Total Weight: {total_weight:.2f} {ac['units']['weight']}", ln=True)
    pdf.set_text_color(0,0,0)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, f"Total Moment: {total_moment:.2f} {ac['units']['weight']}·{ac['units']['arm']}", ln=True)
    cg_color = (0,150,0)
    if ac['cg_limits']:
        mn, mx = ac['cg_limits']
        if cg < mn or cg > mx:
            cg_color = (200,0,0)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(*cg_color)
    pdf.cell(0, 8, f"CG: {cg:.3f} {ac['units']['arm']}", ln=True)
    pdf.set_text_color(0,0,0)
    pdf.ln(2)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, f"- Fuel onboard: {df.loc[df['Item'].str.contains('Fuel'), 'Weight'].values[0]:.1f} {ac['units']['weight']}", ln=True)
    pdf.ln(6)
    pdf.set_font("Arial", 'I', 7)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 4, "Green: within operational limits. Red: exceeds operational limits.", ln=True, align='C')
    pdf.cell(0, 4, "Report auto-generated by Mass & Balance Planner (Streamlit)", ln=True, align='C')
    return pdf

with st.expander("Generate PDF report"):
    registration = st.text_input("Aircraft registration", value="CS-XXX")
    mission_number = st.text_input("Mission number", value="001")
    if st.button("Generate PDF with current values"):
        pdf = generate_pdf(df, ac, aircraft, registration, mission_number, cg, total_weight, total_moment)
        pdf_file = f"MB_{aircraft.replace(' ','_')}_{mission_number}.pdf"
        pdf.output(pdf_file)
        with open(pdf_file, "rb") as f:
            st.download_button("Download PDF", f, file_name=pdf_file, mime="application/pdf")
        st.success("PDF generated successfully!")


