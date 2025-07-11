import streamlit as st
from fpdf import FPDF
import datetime
import pandas as pd
from pathlib import Path

# ===== Imagens dos aviões =====
icons = {
    "Tecnam P2008": "tecnam_icon.png",    # Imagem grande, boa qualidade!
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
        return f"<= {ac['max_takeoff_weight']} {units}"
    if item == "Pilot & Passenger":
        if ac.get('max_passenger_weight'):
            return f"<= {ac['max_passenger_weight']} {units}"
        return "-"
    if item == "Baggage Area 1":
        return f"<= {ac['max_baggage_weight'][0]} {units}"
    if item == "Baggage Area 2":
        return f"<= {ac['max_baggage_weight'][1]} {units}"
    if item == "Baggage":
        return f"<= {ac['max_baggage_weight']} {units}"
    if item == "Fuel":
        return f"<= {ac['max_fuel_volume']}L" if units == "kg" else f"<= {ac['max_fuel_volume']} gal"
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

# Sidebar com imagem grande da aeronave!
with st.sidebar:
    aircraft = st.selectbox("Escolha a aeronave", list(aircraft_data.keys()))
    ac = aircraft_data[aircraft]
    icon_path = icons.get(aircraft)
    if icon_path and Path(icon_path).exists():
        st.image(icon_path, width=260)
    st.subheader("Limites operacionais")
    st.text(get_limits_text(ac))
    st.markdown("---")
    st.caption("Versão Streamlit. Geração de relatório PDF disponível.")

# Topo central: avião grande e nome
col_img, col_nome = st.columns([1,2])
with col_img:
    if icon_path and Path(icon_path).exists():
        st.image(icon_path, width=180)
with col_nome:
    st.title(f"{aircraft}")

st.markdown("### Tabela de entrada Mass & Balance (tudo numa só linha, tipo Excel)")

# Tabela de entrada
if isinstance(ac['baggage_arm'], list):
    bag_labels = ["Baggage Area 1", "Baggage Area 2"]
    bag_limits = ac['max_baggage_weight']
    bag_arms = ac['baggage_arm']
else:
    bag_labels = ["Baggage"]
    bag_limits = [ac['max_baggage_weight']]
    bag_arms = [ac['baggage_arm']]

col1, col2, col3, col4, col5 = st.columns([2,2,2,2,2])

with col1:
    ew = st.number_input("Empty Weight", min_value=0.0, max_value=float(ac['max_takeoff_weight']), value=0.0, step=1.0, key="ew")
with col2:
    ew_arm = st.number_input("EW Arm", min_value=0.0, max_value=10.0 if ac['units']['arm']=='m' else 100.0, value=0.0, step=0.001, format="%.3f", key="ew_arm")
with col3:
    pilot = st.number_input("Pilot & Passenger", min_value=0.0, max_value=float(ac['max_passenger_weight']) if ac['max_passenger_weight'] else 200.0, value=0.0, step=1.0, key="pilot")
with col4:
    bag1 = st.number_input(bag_labels[0], min_value=0.0, max_value=float(bag_limits[0]), value=0.0, step=1.0, key="bag1")
with col5:
    bag2 = 0.0
    if len(bag_labels) > 1:
        bag2 = st.number_input(bag_labels[1], min_value=0.0, max_value=float(bag_limits[1]), value=0.0, step=1.0, key="bag2")

# Fuel abaixo
col_fuel1, col_fuel2 = st.columns([2,2])
with col_fuel1:
    fuel_vol = st.number_input("Fuel Volume", min_value=0.0, max_value=float(ac['max_fuel_volume']), value=0.0, step=1.0, key="fuel_vol")
with col_fuel2:
    st.markdown(f"Fuel Arm: <b>{ac['fuel_arm']:.3f} {ac['units']['arm']}</b>", unsafe_allow_html=True)

fuel_density = ac['fuel_density']
pilot_arm = ac['pilot_arm']
fw = fuel_vol * fuel_density
fuel_arm = ac["fuel_arm"]

m_empty = ew * ew_arm
m_pilot = pilot * pilot_arm
m_b1 = bag1 * bag_arms[0]
m_b2 = bag2 * (bag_arms[1] if len(bag_arms)>1 else 0)
m_fuel = fw * fuel_arm
total_wt = ew + pilot + bag1 + bag2 + fw
total_m = m_empty + m_pilot + m_b1 + m_b2 + m_fuel
cg = (total_m / total_wt) if total_wt else 0

max_wt = ac['max_takeoff_weight']
max_fuel_vol = ac['max_fuel_volume']
units_wt = ac['units']['weight']
units_arm = ac['units']['arm']

alerts = []
if ew > max_wt:
    alerts.append(f"Empty Weight excede o máximo permitido ({max_wt} {units_wt})")
if ac.get('max_passenger_weight') and pilot > ac['max_passenger_weight']:
    alerts.append(f"Pilot & Passenger excede o máximo permitido ({ac['max_passenger_weight']} {units_wt})")
if isinstance(ac['max_baggage_weight'], list):
    if bag1 > ac['max_baggage_weight'][0]:
        alerts.append(f"Baggage Area 1 excede o máximo ({ac['max_baggage_weight'][0]} {units_wt})")
    if len(bag_limits) > 1 and bag2 > ac['max_baggage_weight'][1]:
        alerts.append(f"Baggage Area 2 excede o máximo ({ac['max_baggage_weight'][1]} {units_wt})")
    if "Cessna" in aircraft and (bag1 + bag2) > 120:
        alerts.append(f"Combined baggage excede o máximo 120 lb")
else:
    if bag1 > ac['max_baggage_weight']:
        alerts.append(f"Baggage excede o máximo ({ac['max_baggage_weight']} {units_wt})")
useful = max_wt - (ew + pilot + bag1 + bag2)
fw_max = max(0.0, useful)
fv_max = fw_max / fuel_density if fuel_density else 0.0
limited_by = 'weight limit'
if fv_max > max_fuel_vol:
    fv_max = max_fuel_vol
    fw_max = fv_max * fuel_density
    limited_by = 'tank capacity'
if total_wt > max_wt:
    alerts.append(f"Total weight excede o máximo permitido ({max_wt} {units_wt})")

# Mostrar resumo igual ao Tkinter
st.markdown(
    f"""<div style="line-height:1.2">
    <span style='color:blue'><b>Fuel:</b> {fv_max:.1f} {'gal' if 'Cessna' in aircraft else 'L'} / {fw_max:.1f} {units_wt} ({limited_by})</span><br>
    <span style='color:{get_color(total_wt, max_wt)}'><b>Total Weight:</b> {total_wt:.2f} {units_wt}</span><br>
    <span style='color:black'><b>Total Moment:</b> {total_m:.2f} {units_wt}·{units_arm}</span><br>
    <span style='color:{get_cg_color(cg, ac)}'><b>CG:</b> {cg:.3f} {units_arm}</span><br>""",
    unsafe_allow_html=True
)
if ac['cg_limits']:
    mn, mx = ac['cg_limits']
    st.markdown(f"<b>Limites CG:</b> {mn:.3f} a {mx:.3f} {units_arm}", unsafe_allow_html=True)
if alerts:
    st.markdown("<span style='color:red'><b>Alertas:</b></span>", unsafe_allow_html=True)
    for alert in alerts:
        st.markdown(f"<span style='color:red'>{alert}</span>", unsafe_allow_html=True)

# Tabela de Mass & Balance já preenchida
rows = []
if isinstance(ac['baggage_arm'], list):
    rows = [
        ("Empty Weight", ew, ew_arm, m_empty, get_item_limit("Empty Weight", ac)),
        ("Pilot & Passenger", pilot, pilot_arm, m_pilot, get_item_limit("Pilot & Passenger", ac)),
        ("Baggage Area 1", bag1, bag_arms[0], m_b1, get_item_limit("Baggage Area 1", ac)),
        ("Baggage Area 2", bag2, bag_arms[1], m_b2, get_item_limit("Baggage Area 2", ac)),
        ("Fuel", fw, fuel_arm, m_fuel, get_item_limit("Fuel", ac)),
    ]
else:
    rows = [
        ("Empty Weight", ew, ew_arm, m_empty, get_item_limit("Empty Weight", ac)),
        ("Pilot & Passenger", pilot, pilot_arm, m_pilot, get_item_limit("Pilot & Passenger", ac)),
        ("Baggage", bag1, bag_arms[0], m_b1, get_item_limit("Baggage", ac)),
        ("Fuel", fw, fuel_arm, m_fuel, get_item_limit("Fuel", ac)),
    ]
df = pd.DataFrame({
    "Item": [r[0] for r in rows],
    f"Weight ({units_wt})": [f"{r[1]:.2f}" for r in rows],
    f"Arm ({units_arm})": [f"{r[2]:.3f}" for r in rows],
    f"Moment ({units_wt}·{units_arm})": [f"{r[3]:.2f}" for r in rows],
    "Limite": [r[4] for r in rows]
})
st.markdown("### Tabela detalhada de Mass & Balance")
st.dataframe(df, use_container_width=True)

# Geração de PDF igual
def generate_pdf(aircraft, registration, mission_number, ew, ew_arm, pilot, bag1, bag2, fuel_vol, cg, total_wt, total_m, alerts, fv_max, limited_by, ac, rows):
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
    for row in rows:
        item, wt, arm, mom, _ = row
        pdf.cell(60, 8, str(item), 1, 0)
        pdf.cell(32, 8, f"{wt:.2f}", 1, 0, 'C')
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
    pdf.cell(0, 8, f"- Maximum fuel onboard: {fv_max:.1f} {'gal' if 'Cessna' in aircraft else 'L'}, limited by {limited_by}.", ln=True)
    if ac['cg_limits']:
        mn, mx = ac['cg_limits']
        if cg < mn or cg > mx:
            pdf.cell(0, 8, "- CG is OUTSIDE the safe envelope!", ln=True)
        else:
            pdf.cell(0, 8, "- CG is WITHIN the safe envelope.", ln=True)
    if alerts:
        pdf.ln(2)
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(200,0,0)
        pdf.cell(0, 8, "Warnings:", ln=True)
        pdf.set_font("Arial", '', 12)
        for warning in alerts:
            pdf.multi_cell(0, 8, f"- {warning}")
        pdf.set_text_color(0,0,0)
    pdf.ln(6)
    pdf.set_font("Arial", 'I', 7)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 4, "Green: within operational limits. Red: exceeds operational limits.", ln=True, align='C')
    pdf.cell(0, 4, "Relatório gerado automaticamente pelo Mass & Balance Planner (Streamlit)", ln=True, align='C')
    return pdf

with st.expander("Gerar relatório PDF"):
    registration = st.text_input("Registro da aeronave", value="CS-XXX")
    mission_number = st.text_input("Número da missão", value="001")
    gerar_pdf = st.button("Gerar PDF com os valores atuais")

if gerar_pdf:
    pdf = generate_pdf(
        aircraft, registration, mission_number,
        ew, ew_arm, pilot, bag1, bag2, fuel_vol, cg, total_wt, total_m,
        alerts, fv_max, limited_by, ac, rows
    )
    pdf_file = f"MB_{aircraft.replace(' ','_')}_{mission_number}.pdf"
    pdf.output(pdf_file)
    with open(pdf_file, "rb") as f:
        st.download_button("Download PDF", f, file_name=pdf_file, mime="application/pdf")
    st.success("PDF gerado com sucesso!")

