import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
import pandas as pd
from fpdf import FPDF
import datetime
from pathlib import Path

# Aircraft data
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
        "units": {"weight": "kg", "arm": "m"},
        "icon": "tecnam_icon.png"
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
        "units": {"weight": "lb", "arm": "in"},
        "icon": "cessna_icon.png"
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
        "units": {"weight": "lb", "arm": "in"},
        "icon": "cessna_icon.png"
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

def get_color(val, limit):
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

# --- Sidebar: Aircraft selection and image ---
with st.sidebar:
    aircraft = st.selectbox("Select Aircraft", list(aircraft_data.keys()))
    ac = aircraft_data[aircraft]
    icon_path = ac.get("icon")
    if icon_path and Path(icon_path).exists():
        st.image(icon_path, width=200)
    st.subheader("Operational Limits")
    st.text(get_limits_text(ac))
    st.markdown("---")
    st.caption("Streamlit version. PDF report available.")

st.title("Mass & Balance Planner")
st.write("Edit your values **directly in the table below**. No fields above, everything in one grid, as in the desktop version.")

# --- Build the DataFrame for editing ---
if isinstance(ac['baggage_arm'], list):
    data = [
        {"Item": "Empty Weight", "Weight": 0.0, "Arm": 0.0, "Limit": ac['max_takeoff_weight']},
        {"Item": "Pilot & Passenger", "Weight": 0.0, "Arm": ac['pilot_arm'], "Limit": ac['max_passenger_weight'] or ""},
        {"Item": "Baggage Area 1", "Weight": 0.0, "Arm": ac['baggage_arm'][0], "Limit": ac['max_baggage_weight'][0]},
        {"Item": "Baggage Area 2", "Weight": 0.0, "Arm": ac['baggage_arm'][1], "Limit": ac['max_baggage_weight'][1]},
        {"Item": "Fuel", "Weight": 0.0, "Arm": ac['fuel_arm'], "Limit": ac['max_fuel_volume']},
    ]
else:
    data = [
        {"Item": "Empty Weight", "Weight": 0.0, "Arm": 0.0, "Limit": ac['max_takeoff_weight']},
        {"Item": "Pilot & Passenger", "Weight": 0.0, "Arm": ac['pilot_arm'], "Limit": ac['max_passenger_weight'] or ""},
        {"Item": "Baggage", "Weight": 0.0, "Arm": ac['baggage_arm'], "Limit": ac['max_baggage_weight']},
        {"Item": "Fuel", "Weight": 0.0, "Arm": ac['fuel_arm'], "Limit": ac['max_fuel_volume']},
    ]

df = pd.DataFrame(data)

# --- AGGRID: Editable table! ---
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_columns(['Weight', 'Arm'], editable=True)
gb.configure_columns(['Item', 'Limit'], editable=False)
gb.configure_columns(['Arm'], cellEditor='agNumberCellEditor', cellEditorParams={'precision': 3})
gb.configure_columns(['Weight'], cellEditor='agNumberCellEditor', cellEditorParams={'precision': 2})
gb.configure_grid_options(domLayout='normal', stopEditingWhenCellsLoseFocus=True)
gridOptions = gb.build()

grid_return = AgGrid(
    df,
    gridOptions=gridOptions,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    fit_columns_on_grid_load=True,
    allow_unsafe_jscode=False,
    enable_enterprise_modules=False,
    theme="balham",
    reload_data=False
)

edited_df = grid_return["data"]

# --- Calculation logic ---
moments = []
for idx, row in edited_df.iterrows():
    moments.append(row['Weight'] * row['Arm'])

edited_df['Moment'] = [f"{m:.2f}" for m in moments]

total_weight = sum(edited_df['Weight'])
total_moment = sum(moments)
cg = (total_moment / total_weight) if total_weight else 0.0

# --- Show calculation below the table ---
units_wt = ac['units']['weight']
units_arm = ac['units']['arm']

colr, colr2, colr3, colr4 = st.columns(4)
colr[0].markdown(f"<b>Total Weight:</b> <span style='color:{get_color(total_weight, ac['max_takeoff_weight'])}'>{total_weight:.2f} {units_wt}</span>", unsafe_allow_html=True)
colr2[0].markdown(f"<b>Total Moment:</b> {total_moment:.2f} {units_wt}·{units_arm}")
colr3[0].markdown(f"<b>CG:</b> <span style='color:{get_cg_color(cg, ac)}'>{cg:.3f} {units_arm}</span>", unsafe_allow_html=True)
if ac['cg_limits']:
    colr4[0].markdown(f"<b>CG Limits:</b> {ac['cg_limits'][0]:.3f} to {ac['cg_limits'][1]:.3f} {units_arm}")

# --- PDF GENERATION ---
def generate_pdf(aircraft, registration, mission_number, edited_df, moments, total_weight, total_moment, cg, ac):
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
    pdf.cell(0, 6, f"- Maximum Takeoff Weight: {ac['max_takeoff_weight']} {ac['units']['weight']}", ln=True)
    if ac.get('max_passenger_weight'):
        pdf.cell(0, 6, f"- Maximum Pilot & Passenger: {ac['max_passenger_weight']} {ac['units']['weight']}", ln=True)
    if isinstance(ac['max_baggage_weight'], list):
        pdf.cell(0, 6, f"- Maximum Baggage Area 1: {ac['max_baggage_weight'][0]} {ac['units']['weight']}", ln=True)
        pdf.cell(0, 6, f"- Maximum Baggage Area 2: {ac['max_baggage_weight'][1]} {ac['units']['weight']}", ln=True)
    else:
        pdf.cell(0, 6, f"- Maximum Baggage: {ac['max_baggage_weight']} {ac['units']['weight']}", ln=True)
    pdf.cell(0, 6, f"- Maximum Fuel Volume: {ac['max_fuel_volume']} {'L' if ac['units']['weight'] == 'kg' else 'gal'}", ln=True)
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
    for idx, row in edited_df.iterrows():
        pdf.cell(60, 8, str(row["Item"]), 1, 0)
        pdf.cell(32, 8, f"{row['Weight']:.2f}", 1, 0, 'C')
        pdf.cell(28, 8, f"{row['Arm']:.3f}", 1, 0, 'C')
        pdf.cell(38, 8, f"{moments[idx]:.2f}", 1, 1, 'C')
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
    pdf.ln(6)
    pdf.set_font("Arial", 'I', 7)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 4, "Green: within operational limits. Red: exceeds operational limits.", ln=True, align='C')
    pdf.cell(0, 4, "Report auto-generated by Mass & Balance Planner (Streamlit)", ln=True, align='C')
    return pdf

with st.expander("Generate PDF report"):
    registration = st.text_input("Aircraft registration", value="CS-XXX")
    mission_number = st.text_input("Mission number", value="001")
    gerar_pdf = st.button("Generate PDF with current values")

if gerar_pdf:
    pdf = generate_pdf(
        aircraft, registration, mission_number,
        edited_df, moments, total_weight, total_moment, cg, ac
    )
    pdf_file = f"MB_{aircraft.replace(' ','_')}_{mission_number}.pdf"
    pdf.output(pdf_file)
    with open(pdf_file, "rb") as f:
        st.download_button("Download PDF", f, file_name=pdf_file, mime="application/pdf")
    st.success("PDF generated successfully!")


