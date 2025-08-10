import requests
import streamlit as st
from streamlit_lottie import st_lottie
from PIL import Image


st.title("Calculadora de Hipoteca")

# Entradas del usuario
years = st.number_input("Años de la hipoteca:", min_value=1, max_value=40, value=20)
interest = st.number_input("Tipo de interés anual (%):", min_value=0.0, max_value=20.0, value=3.0, step=0.1)
principal = st.number_input("Importe total (€):", min_value=1000.0, max_value=1000000.0, value=150000.0, step=1000.0)


if st.button("Calcular"):
    n = int(years * 12)
    r = (interest / 100) / 12

    if r > 0:
        cuota = principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    else:
        cuota = principal / n

    total_pagado = cuota * n
    intereses_totales = total_pagado - principal

    st.write(f"**Cuota mensual:** {cuota:,.2f} €")
    st.write(f"**Intereses totales:** {intereses_totales:,.2f} €")


    