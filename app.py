
import streamlit as st
import datetime

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

st.title("Mass & Balance Planner")

aircraft = st.selectbox("Selecione a Aeronave", list(aircraft_data.keys()))
data = aircraft_data[aircraft]

mission_number = st.text_input("Missão Nº", "")
registration = st.text_input("Matrícula", "CS-ABC")
flight_date = st.date_input("Data do Voo", datetime.date.today())
flight_time = st.time_input("Hora do Voo", datetime.datetime.now().time())

empty_weight = st.number_input("Peso da aeronave vazia", min_value=0.0)
empty_arm = st.number_input("Braço da aeronave vazia", min_value=0.0)
pilot_weight = st.number_input("Peso do piloto", min_value=0.0)
fuel_volume = st.number_input("Volume de combustível", min_value=0.0, max_value=data["max_fuel_volume"])
baggage_weight = st.number_input("Peso da bagagem", min_value=0.0)

fuel_weight = fuel_volume * data["fuel_density"]

# Momentos
moment_empty = empty_weight * empty_arm
moment_pilot = pilot_weight * data["pilot_arm"]
moment_fuel = fuel_weight * data["fuel_arm"]
moment_baggage = baggage_weight * (data["baggage_arm"] if isinstance(data["baggage_arm"], float) else data["baggage_arm"][0])

total_weight = empty_weight + pilot_weight + fuel_weight + baggage_weight
total_moment = moment_empty + moment_pilot + moment_fuel + moment_baggage
cg = total_moment / total_weight if total_weight else 0

st.markdown("---")
st.write(f"**Peso Total:** {total_weight:.2f} {data['units']['weight']}")
st.write(f"**Momento Total:** {total_moment:.2f}")
st.write(f"**Centro de Gravidade (CG):** {cg:.3f} {data['units']['arm']}")

if data["cg_limits"]:
    if data["cg_limits"][0] <= cg <= data["cg_limits"][1]:
        st.success("CG dentro dos limites.")
    else:
        st.error("CG fora dos limites!")

report = f"""
MASS & BALANCE REPORT

Aeronave: {aircraft}
Matrícula: {registration}
Missão Nº: {mission_number}
Data do Voo: {flight_date}
Hora do Voo: {flight_time}

Peso Vazio: {empty_weight} x {empty_arm} = {moment_empty:.2f}
Piloto: {pilot_weight} x {data["pilot_arm"]} = {moment_pilot:.2f}
Combustível: {fuel_weight:.1f} x {data["fuel_arm"]} = {moment_fuel:.2f}
Bagagem: {baggage_weight} x {data["baggage_arm"]} = {moment_baggage:.2f}

Peso Total: {total_weight:.2f}
Momento Total: {total_moment:.2f}
CG: {cg:.3f} {data['units']['arm']}
"""

st.download_button("📄 Baixar Relatório", report, file_name="relatorio_MB.txt")

