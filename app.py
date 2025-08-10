# =============================
# IMPORTS Y CONFIGURACIÓN INICIAL
# =============================
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Calculadora de Hipotecas", layout="centered")

# =============================
# SIDEBAR DE NAVEGACIÓN
# =============================
st.sidebar.title("Menú")
pagina = st.sidebar.radio(
    "Ir a:",
    ("Hipoteca Fija", "Hipoteca Mixta", "Comparativa Fija vs Mixta")
)

# =============================
# 1. PÁGINA HIPOTECA FIJA
# =============================
if pagina == "Hipoteca Fija":
    st.title("Calculadora de Hipoteca Fija")
    years = st.number_input("Años de la hipoteca:", min_value=1, max_value=40, value=20)
    interest = st.number_input("Tipo de interés anual (%):", min_value=0.0, max_value=20.0, value=3.0, step=0.1)
    principal = st.number_input("Importe total (€):", min_value=1000.0, max_value=1000000.0, value=150000.0, step=1000.0)

    if st.button("Calcular", key="calcular_fija"):
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

        # -------- CUADRO DE AMORTIZACIÓN FIJA --------
        cuadro = []
        pendiente = principal
        for year in range(1, years + 1):
            intereses_anual = 0
            capital_anual = 0
            for mes in range(12):
                interes_mes = pendiente * r
                capital_mes = cuota - interes_mes
                intereses_anual += interes_mes
                capital_anual += capital_mes
                pendiente -= capital_mes
                if pendiente < 0:
                    pendiente = 0
            cuadro.append({
                "Año": year,
                "Cuota total pagada": cuota * 12,
                "Intereses pagados": intereses_anual,
                "Capital amortizado": capital_anual,
                "Capital pendiente": max(pendiente, 0)
            })

        df_cuadro = pd.DataFrame(cuadro)
        st.write("### Cuadro de amortización (anual)")
        st.dataframe(df_cuadro.style.format({
            "Cuota total pagada": "{:,.2f} €",
            "Intereses pagados": "{:,.2f} €",
            "Capital amortizado": "{:,.2f} €",
            "Capital pendiente": "{:,.2f} €"
        }))

# =============================
# 2. PÁGINA HIPOTECA MIXTA
# =============================
elif pagina == "Hipoteca Mixta":
    st.title("Calculadora de Hipoteca Mixta")
    years_fixed = st.number_input("Años a tipo fijo:", min_value=1, max_value=40, value=10)
    years_total = st.number_input("Años totales de la hipoteca:", min_value=years_fixed, max_value=40, value=20)
    tipo_fijo = st.number_input("Tipo de interés fijo (%):", min_value=0.0, max_value=20.0, value=2.0, step=0.1)
    euribor = st.number_input("Euribor estimado para los años variables (%):", min_value=-2.0, max_value=10.0, value=2.0, step=0.1)
    diferencial = st.number_input("Diferencial sobre euribor (%):", min_value=0.0, max_value=5.0, value=1.0, step=0.1)
    principal = st.number_input("Importe total (€):", min_value=1000.0, max_value=1000000.0, value=150000.0, step=1000.0)

    if st.button("Calcular", key="calcular_mixta"):
        n_fijo = int(years_fixed * 12)
        n_var = int((years_total - years_fixed) * 12)
        r_fijo = (tipo_fijo / 100) / 12
        r_var = ((euribor + diferencial) / 100) / 12

        # Cuota durante años fijos (como si toda la hipoteca fuera a ese plazo)
        cuota_fija = principal * (r_fijo * (1 + r_fijo) ** (n_fijo + n_var)) / ((1 + r_fijo) ** (n_fijo + n_var) - 1)
        pendiente = principal
        intereses_mixta = 0

        # Simula pagos durante años fijos
        for _ in range(n_fijo):
            interes = pendiente * r_fijo
            amortizacion = cuota_fija - interes
            pendiente -= amortizacion
            intereses_mixta += interes

        # Cuota durante años variables
        if r_var > 0:
            cuota_variable = pendiente * (r_var * (1 + r_var) ** n_var) / ((1 + r_var) ** n_var - 1)
        else:
            cuota_variable = pendiente / n_var

        # Simula pagos durante años variables
        for _ in range(n_var):
            interes = pendiente * r_var
            amortizacion = cuota_variable - interes
            pendiente -= amortizacion
            intereses_mixta += interes

        st.write(f"**Cuota mensual (fijo):** {cuota_fija:,.2f} €")
        st.write(f"**Cuota mensual (variable):** {cuota_variable:,.2f} €")
        st.write(f"**Intereses totales:** {intereses_mixta:,.2f} €")

        # -------- CUADRO DE AMORTIZACIÓN MIXTA --------
        cuadro = []
        pendiente = principal
        for year in range(1, years_total + 1):
            intereses_anual = 0
            capital_anual = 0
            for mes in range(12):
                if year <= years_fixed:
                    interes_mes = pendiente * r_fijo
                    cuota_mes = cuota_fija
                else:
                    interes_mes = pendiente * r_var
                    cuota_mes = cuota_variable
                capital_mes = cuota_mes - interes_mes
                intereses_anual += interes_mes
                capital_anual += capital_mes
                pendiente -= capital_mes
                if pendiente < 0:
                    pendiente = 0
            cuadro.append({
                "Año": year,
                "Cuota total pagada": cuota_mes * 12,
                "Intereses pagados": intereses_anual,
                "Capital amortizado": capital_anual,
                "Capital pendiente": max(pendiente, 0)
            })

        df_cuadro = pd.DataFrame(cuadro)
        st.write("### Cuadro de amortización (anual)")
        st.dataframe(df_cuadro.style.format({
            "Cuota total pagada": "{:,.2f} €",
            "Intereses pagados": "{:,.2f} €",
            "Capital amortizado": "{:,.2f} €",
            "Capital pendiente": "{:,.2f} €"
        }))

# =============================
# 3. PÁGINA COMPARATIVA FIJA VS MIXTA
# =============================
else:
    st.title("Comparativa Hipoteca Fija vs Mixta")
    st.write("Introduce los parámetros para comparar ambas opciones:")

    # Parámetros comunes
    principal = st.number_input("Importe total (€):", min_value=1000.0, max_value=1000000.0, value=150000.0, step=1000.0)

    # Fija
    years_fija = st.number_input("Años hipoteca fija:", min_value=1, max_value=40, value=20)
    tipo_fijo = st.number_input("Tipo interés fija (%):", min_value=0.0, max_value=20.0, value=3.0, step=0.1)

    # Mixta
    years_fixed = st.number_input("Años fijos (mixta):", min_value=1, max_value=40, value=10)
    years_total = st.number_input("Años totales (mixta):", min_value=years_fixed, max_value=40, value=20)
    tipo_fijo_mixta = st.number_input("Tipo fijo (mixta) (%):", min_value=0.0, max_value=20.0, value=2.0, step=0.1)
    euribor = st.number_input("Euribor estimado (mixta) (%):", min_value=-2.0, max_value=10.0, value=2.0, step=0.1)
    diferencial = st.number_input("Diferencial (mixta) (%):", min_value=0.0, max_value=5.0, value=1.0, step=0.1)

    if st.button("Comparar"):
        # Fija
        n_fija = int(years_fija * 12)
        r_fija = (tipo_fijo / 100) / 12
        cuota_fija = principal * (r_fija * (1 + r_fija) ** n_fija) / ((1 + r_fija) ** n_fija - 1)
        intereses_fija = 0
        intereses_acum_fija = []
        pendiente_fija = principal

        for i in range(n_fija):
            interes = pendiente_fija * r_fija
            amortizacion = cuota_fija - interes
            pendiente_fija -= amortizacion
            intereses_fija += interes
            if (i+1) % 12 == 0:
                intereses_acum_fija.append( ((i+1)//12, intereses_fija) )

        # Mixta
        n_fijo = int(years_fixed * 12)
        n_var = int((years_total - years_fixed) * 12)
        r_fijo_mixta = (tipo_fijo_mixta / 100) / 12
        r_var_mixta = ((euribor + diferencial) / 100) / 12

        cuota_fija_mixta = principal * (r_fijo_mixta * (1 + r_fijo_mixta) ** (n_fijo + n_var)) / ((1 + r_fijo_mixta) ** (n_fijo + n_var) - 1)
        pendiente = principal
        intereses_mixta = 0
        intereses_acum_mixta = []

        # Fase fija
        for i in range(n_fijo):
            interes = pendiente * r_fijo_mixta
            amortizacion = cuota_fija_mixta - interes
            pendiente -= amortizacion
            intereses_mixta += interes
            if (i+1) % 12 == 0:
                intereses_acum_mixta.append( ((i+1)//12, intereses_mixta) )

        # Fase variable
        if r_var_mixta > 0:
            cuota_variable = pendiente * (r_var_mixta * (1 + r_var_mixta) ** n_var) / ((1 + r_var_mixta) ** n_var - 1)
        else:
            cuota_variable = pendiente / n_var

        for i in range(n_var):
            interes = pendiente * r_var_mixta
            amortizacion = cuota_variable - interes
            pendiente -= amortizacion
            intereses_mixta += interes
            if (i+1+n_fijo) % 12 == 0:
                intereses_acum_mixta.append( ((i+1+n_fijo)//12, intereses_mixta) )

        st.write(f"**Intereses totales fija:** {intereses_fija:,.2f} €")
        st.write(f"**Intereses totales mixta:** {intereses_mixta:,.2f} €")

        # Gráfico de intereses acumulados
        años_fija = [x[0] for x in intereses_acum_fija]
        int_fija = [x[1] for x in intereses_acum_fija]
        años_mixta = [x[0] for x in intereses_acum_mixta]
        int_mixta = [x[1] for x in intereses_acum_mixta]

        st.write("### Intereses acumulados por año")
        fig, ax = plt.subplots(figsize=(10,5))
        ax.plot(años_fija, int_fija, label="Fija")
        ax.plot(años_mixta, int_mixta, label="Mixta")
        ax.set_xlabel("Año")
        ax.set_ylabel("Intereses acumulados (€)")
        ax.legend()
        st.pyplot(fig)
