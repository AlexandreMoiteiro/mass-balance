import streamlit as st
from fpdf import FPDF
import datetime
import pandas as pd
from pathlib import Path

# === AIRCRAFT ICONS (put these PNGs in your project root, or replace with image links) ===
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

def get_color(total, limit, margin=0.05):
    if total > limit:
        return "red"
    elif total > (limit * (1 - margin)):
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

# --- SIDEBAR with selection and aircraft image ---
with st.sidebar:
    aircraft = st.selectbox("Select Aircraft", list(aircraft_data.keys()))
    ac = aircraft_data[aircraft]
    icon_path = icons.get(aircraft)
    if icon_path and Path(icon_path).exists():
        st.image(icon_path, width=200)
    st.subheader("Operational Limits")
    st.text(get_limits_text(ac))
    st.markdown("---")
    st.caption("Streamlit version. PDF report available.")

# --- MAIN: TABLE-STYLE DATA ENTRY ---
st.title("Mass & Balance Planner")
st.write("Aircraft mass & balance calculator. All input fields are in the table below, just like on the Tkinter app.")

columns = [
    "Item", f"Weight ({ac['units']['weight']})", f"Arm ({ac['units']['arm']})", f"Moment ({ac['units']['weight']}·{ac['units']['arm']})", "Limit"
]

rows = []
# Build the row structure and use st.number_input for inline editing!
if isinstance(ac['baggage_arm'], list):
    table_rows = [
        {
            "Item": "Empty Weight",
            "weight_key": "ew", "arm_key": "ew_arm",
            "weight_val": 0.0, "arm_val": 0.0,
            "fixed_arm": False,
            "limit": get_item_limit("Empty Weight", ac)
        },
        {
            "Item": "Pilot & Passenger",
            "weight_key": "pilot", "arm_key": None,
            "weight_val": 0.0, "arm_val": ac["pilot_arm"],
            "fixed_arm": True,
            "limit": get_item_limit("Pilot & Passenger", ac)
        },
        {
            "Item": "Baggage Area 1",
            "weight_key": "bag1", "arm_key": None,
            "weight_val": 0.0, "arm_val": ac["baggage_arm"][0],
            "fixed_arm": True,
            "limit": get_item_limit("Baggage Area 1", ac)
        },
        {
            "Item": "Baggage Area 2",
            "weight_key": "bag2", "arm_key": None,
            "weight_val": 0.0, "arm_val": ac["baggage_arm"][1],
            "fixed_arm": True,
            "limit": get_item_limit("Baggage Area 2", ac)
        },
        {
            "Item": "Fuel",
            "weight_key": "fuel_vol", "arm_key": None,
            "weight_val": 0.0, "arm_val": ac["fuel_arm"],
            "fixed_arm": True,
            "limit": get_item_limit("Fuel", ac)
        }
    ]
else:
    table_rows = [
        {
            "Item": "Empty Weight",
            "weight_key": "ew", "arm_key": "ew_arm",
            "weight_val": 0.0, "arm_val": 0.0,
            "fixed_arm": False,
            "limit": get_item_limit("Empty Weight", ac)
        },
        {
            "Item": "Pilot & Passenger",
            "weight_key": "pilot", "arm_key": None,
            "weight_val": 0.0, "arm_val": ac["pilot_arm"],
            "fixed_arm": True,
            "limit": get_item_limit("Pilot & Passenger", ac)
        },
        {
            "Item": "Baggage",
            "weight_key": "bag1", "arm_key": None,
            "weight_val": 0.0, "arm_val": ac["baggage_arm"],
            "fixed_arm": True,
            "limit": get_item_limit("Baggage", ac)
        },
        {
            "Item": "Fuel",
            "weight_key": "fuel_vol", "arm_key": None,
            "weight_val": 0.0, "arm_val": ac["fuel_arm"],
            "fixed_arm": True,
            "limit": get_item_limit("Fuel", ac)
        }
    ]

# --- INSTANTIATE STREAMLIT INPUTS IN THE TABLE ---
input_vals = {}
# Use st.form to avoid rerun on every keystroke
with st.form("mb_table_form"):
    st.write("**Enter your values in the editable table below:**")
    header_cols = st.columns(len(columns))
    for i, col in enumerate(columns):
        header_cols[i].markdown(f"**{col}**")
    row_vars = []
    for row in table_rows:
        cols = st.columns(len(columns))
        # Item
        cols[0].write(row["Item"])
        # Weight input
        min_weight = 0.0
        if row["Item"] == "Empty Weight":
            max_weight = float(ac['max_takeoff_weight'])
        elif row["Item"] == "Pilot & Passenger":
            max_weight = float(ac['max_passenger_weight']) if ac['max_passenger_weight'] else 200.0
        elif "Baggage" in row["Item"]:
            if "Area 1" in row["Item"]:
                max_weight = ac["max_baggage_weight"][0]
            elif "Area 2" in row["Item"]:
                max_weight = ac["max_baggage_weight"][1]
            else:
                max_weight = ac["max_baggage_weight"]
        elif row["Item"] == "Fuel":
            max_weight = float(ac["max_fuel_volume"])
        else:
            max_weight = 9999
        val = cols[1].number_input(
            "", min_value=min_weight, max_value=max_weight, step=1.0,
            value=0.0, format="%.2f", key=row["weight_key"]
        )
        input_vals[row["weight_key"]] = val
        # Arm input or label
        if row["fixed_arm"]:
            cols[2].write(f"{row['arm_val']:.3f}")
            input_vals[row["arm_key"] or (row["Item"].lower().replace(" ", "_")+"_arm")] = row["arm_val"]
        else:
            val_arm = cols[2].number_input(
                "", min_value=0.0, max_value=10.0 if ac["units"]["arm"]=="m" else 100.0,
                value=0.0, format="%.3f", key=row["arm_key"]
            )
            input_vals[row["arm_key"]] = val_arm
        # Placeholder for moment
        cols[3].write("—")
        # Limit
        cols[4].write(row["limit"])
        row_vars.append(cols)
    submit = st.form_submit_button("Calculate")

# --- CALCULATE AND SHOW IN THE TABLE ---
ew = input_vals.get("ew", 0.0)
ew_arm = input_vals.get("ew_arm", 0.0)
pilot = input_vals.get("pilot", 0.0)
pilot_arm = ac["pilot_arm"]
if isinstance(ac["baggage_arm"], list):
    bag1 = input_vals.get("bag1", 0.0)
    bag2 = input_vals.get("bag2", 0.0)
    bag_arms = ac["baggage_arm"]
else:
    bag1 = input_vals.get("bag1", 0.0)
    bag2 = 0.0
    bag_arms = [ac["baggage_arm"], 0.0]
fuel_vol = input_vals.get("fuel_vol", 0.0)
fuel_density = ac["fuel_density"]
fw = fuel_vol * fuel_density
fuel_arm = ac["fuel_arm"]

m_empty = ew * ew_arm
m_pilot = pilot * pilot_arm
m_b1 = bag1 * bag_arms[0]
m_b2 = bag2 * bag_arms[1]
m_fuel = fw * fuel_arm

total_wt = ew + pilot + bag1 + bag2 + fw
total_m = m_empty + m_pilot + m_b1 + m_b2 + m_fuel
cg = (total_m / total_wt) if total_wt else 0

max_wt = ac['max_takeoff_weight']
units_wt = ac['units']['weight']
units_arm = ac['units']['arm']

# Show the moments and actual values directly IN the table!
moments = [m_empty, m_pilot, m_b1]
moment_idx = 0
if isinstance(ac["baggage_arm"], list):
    moments = [m_empty, m_pilot, m_b1, m_b2, m_fuel]
else:
    moments = [m_empty, m_pilot, m_b1, m_fuel]

# Re-print table with calculated moments
st.write("### Mass & Balance Table with Results")
header_cols = st.columns(len(columns))
for i, col in enumerate(columns):
    header_cols[i].markdown(f"**{col}**")
for idx, row in enumerate(table_rows):
    cols = st.columns(len(columns))
    cols[0].write(row["Item"])
    # Weight
    val = input_vals[row["weight_key"]]
    cols[1].write(f"{val:.2f}")
    # Arm
    armval = row["arm_val"] if row["fixed_arm"] else input_vals.get(row["arm_key"], 0.0)
    cols[2].write(f"{armval:.3f}")
    # Moment
    moment = moments[idx]
    cols[3].write(f"{moment:.2f}")
    # Limit
    cols[4].write(row["limit"])

# --- SUMMARY ---
st.markdown("----")
st.markdown(
    f"""<div style="line-height:1.2">
    <span style='color:blue'><b>Max usable fuel:</b> {fuel_vol:.1f} {'gal' if 'Cessna' in aircraft else 'L'} / {fw:.1f} {units_wt}</span><br>
    <span style='color:{get_color(total_wt, max_wt)}'><b>Total Weight:</b> {total_wt:.2f} {units_wt}</span><br>
    <span style='color:black'><b>Total Moment:</b> {total_m:.2f} {units_wt}·{units_arm}</span><br>
    <span style='color:{get_cg_color(cg, ac)}'><b>CG:</b> {cg:.3f} {units_arm}</span><br>""",
    unsafe_allow_html=True
)
if ac['cg_limits']:
    mn, mx = ac['cg_limits']
    st.markdown(f"<b>CG Limits:</b> {mn:.3f} to {mx:.3f} {units_arm}", unsafe_allow_html=True)

# --- PDF GENERATION, as before ---
def generate_pdf(aircraft, registration, mission_number, ew, ew_arm, pilot, bag1, bag2, fuel_vol, cg, total_wt, total_m, ac, moments, table_rows):
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
    for i, row in enumerate(table_rows):
        item = row["Item"]
        weight = input_vals.get(row["weight_key"], 0.0)
        arm = row["arm_val"] if row["fixed_arm"] else input_vals.get(row["arm_key"], 0.0)
        mom = moments[i]
        pdf.cell(60, 8, str(item), 1, 0)
        pdf.cell(32, 8, f"{weight:.2f}", 1, 0, 'C')
        pdf.cell(28, 8, f"{arm:.3f}", 1, 0, 'C')
        pdf.cell(38, 8, f"{mom:.2f}", 1, 1, 'C')
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    if total_wt > ac['max_takeoff_weight']:
        pdf.set_text_color(200,0,0)
    else:
        pdf.set_text_color(0,150,0)
    pdf.cell(0, 8, f"Total Weight: {total_wt:.2f} {ac['units']['weight']}", ln=True)
    pdf.set_text_color(0,0,0)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, f"Total Moment: {total_m:.2f} {ac['units']['weight']}·{ac['units']['arm']}", ln=True)
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
    pdf.cell(0, 8, f"- Fuel onboard: {fuel_vol:.1f} {'gal' if 'Cessna' in aircraft else 'L'} / {fw:.1f} {ac['units']['weight']}", ln=True)
    pdf.cell(0, 8, f"- CG: {cg:.3f} {ac['units']['arm']}", ln=True)
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
        ew, ew_arm, pilot, bag1, bag2, fuel_vol, cg, total_wt, total_m,
        ac, moments, table_rows
    )
    pdf_file = f"MB_{aircraft.replace(' ','_')}_{mission_number}.pdf"
    pdf.output(pdf_file)
    with open(pdf_file, "rb") as f:
        st.download_button("Download PDF", f, file_name=pdf_file, mime="application/pdf")
    st.success("PDF generated successfully!")


