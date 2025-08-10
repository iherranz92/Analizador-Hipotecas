# =============================
# IMPORTS Y CONFIGURACIÓN INICIAL
# =============================
import streamlit as st
import numpy as np
import pandas as pd
import plotly
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(page_title="Calculadora de Hipotecas", layout="centered")

# =============================
# SIDEBAR DE NAVEGACIÓN
# =============================
st.sidebar.title("Menú")
pagina = st.sidebar.radio(
    "Ir a:",
    (
        "Inicio",
        "Hipoteca Fija",
        "Hipoteca Mixta",
        "Comparativa Fija vs Mixta",
        "Amortización Anticipada",
        "Comparador de Ofertas",
        "Bonificaciones",
        "Subrogación",
        "Glosario"
    )
)

# =============================
# FUNCIONES AUXILIARES
# =============================
def cuadro_amortizacion_fija(principal, years, r, cuota):
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
    return pd.DataFrame(cuadro)

def cuadro_amortizacion_mixta(principal, years_fixed, years_total, r_fijo, r_var, cuota_fija, cuota_variable):
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
    return pd.DataFrame(cuadro)

def descargar_df(df):
    output = BytesIO()
    df.to_excel(output, index=False)
    return output.getvalue()

def plot_evolucion_plotly(df, titulo):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Año"], y=df["Capital pendiente"],
        mode="lines+markers", name="Capital pendiente"
    ))
    fig.add_trace(go.Scatter(
        x=df["Año"], y=df["Intereses pagados"].cumsum(),
        mode="lines+markers", name="Intereses acumulados"
    ))
    fig.update_layout(
        title=titulo,
        xaxis_title="Año",
        yaxis_title="€",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

# =============================
# 0. PÁGINA INICIO
# =============================
if pagina == "Inicio":
    st.title("Bienvenido a la Calculadora y Analizador de Hipotecas 🏡")
    st.markdown("""
    Esta herramienta te permite analizar y comparar diferentes tipos de hipotecas, simular escenarios y tomar decisiones informadas.

    ### ¿Qué puedes hacer aquí?
    """)

    st.markdown("""
    - **Hipoteca Fija**  
      Calcula cuota, intereses y cuadro de amortización para hipotecas a tipo fijo.

    - **Hipoteca Mixta**  
      Simula hipotecas con años fijos y años variables.

    - **Comparativa Fija vs Mixta**  
      Compara ambos tipos con gráficos y cuadro de intereses.

    - **Amortización Anticipada**  
      Descubre cuánto puedes ahorrar amortizando antes de tiempo.

    - **Comparador de Ofertas**  
      Introduce varias ofertas de bancos y compara cuotas e intereses totales.

    - **Bonificaciones**  
      Analiza si compensa contratar productos vinculados para rebajar el tipo de interés.

    - **Subrogación**  
      Comprueba si te conviene cambiar tu hipoteca a otro banco.

    - **Glosario**  
      Consulta los conceptos clave del mundo hipotecario y consejos útiles.
    """)

    st.info("Navega por las secciones desde el menú lateral izquierdo. ¡Empieza a analizar tu hipoteca ahora!")

# =============================
# 1. PÁGINA HIPOTECA FIJA
# =============================
elif pagina == "Hipoteca Fija":
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

        df_cuadro = cuadro_amortizacion_fija(principal, years, r, cuota)
        st.write("### Cuadro de amortización (anual)")
        st.dataframe(df_cuadro.style.format({
            "Cuota total pagada": "{:,.2f} €",
            "Intereses pagados": "{:,.2f} €",
            "Capital amortizado": "{:,.2f} €",
            "Capital pendiente": "{:,.2f} €"
        }), use_container_width=True)

        st.download_button(
            label="Descargar cuadro (Excel)",
            data=descargar_df(df_cuadro),
            file_name="cuadro_amortizacion_fija.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.write("### Evolución de capital pendiente e intereses")
        plot_evolucion_plotly(df_cuadro, "Evolución Hipoteca Fija")

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

        cuota_fija = principal * (r_fijo * (1 + r_fijo) ** (n_fijo + n_var)) / ((1 + r_fijo) ** (n_fijo + n_var) - 1)
        pendiente = principal
        intereses_mixta = 0

        for _ in range(n_fijo):
            interes = pendiente * r_fijo
            amortizacion = cuota_fija - interes
            pendiente -= amortizacion
            intereses_mixta += interes

        if r_var > 0:
            cuota_variable = pendiente * (r_var * (1 + r_var) ** n_var) / ((1 + r_var) ** n_var - 1)
        else:
            cuota_variable = pendiente / n_var

        for _ in range(n_var):
            interes = pendiente * r_var
            amortizacion = cuota_variable - interes
            pendiente -= amortizacion
            intereses_mixta += interes

        st.write(f"**Cuota mensual (fijo):** {cuota_fija:,.2f} €")
        st.write(f"**Cuota mensual (variable):** {cuota_variable:,.2f} €")
        st.write(f"**Intereses totales:** {intereses_mixta:,.2f} €")

        df_cuadro = cuadro_amortizacion_mixta(principal, years_fixed, years_total, r_fijo, r_var, cuota_fija, cuota_variable)
        st.write("### Cuadro de amortización (anual)")
        st.dataframe(df_cuadro.style.format({
            "Cuota total pagada": "{:,.2f} €",
            "Intereses pagados": "{:,.2f} €",
            "Capital amortizado": "{:,.2f} €",
            "Capital pendiente": "{:,.2f} €"
        }), use_container_width=True)

        st.download_button(
            label="Descargar cuadro (Excel)",
            data=descargar_df(df_cuadro),
            file_name="cuadro_amortizacion_mixta.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.write("### Evolución de capital pendiente e intereses")
        plot_evolucion_plotly(df_cuadro, "Evolución Hipoteca Mixta")

# =============================
# 3. PÁGINA COMPARATIVA FIJA VS MIXTA
# =============================
elif pagina == "Comparativa Fija vs Mixta":
    st.title("Comparativa Hipoteca Fija vs Mixta")
    st.write("Introduce los parámetros para comparar ambas opciones:")

    principal = st.number_input("Importe total (€):", min_value=1000.0, max_value=1000000.0, value=150000.0, step=1000.0)
    years_fija = st.number_input("Años hipoteca fija:", min_value=1, max_value=40, value=20)
    tipo_fijo = st.number_input("Tipo interés fija (%):", min_value=0.0, max_value=20.0, value=3.0, step=0.1)
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
        df_fija = cuadro_amortizacion_fija(principal, years_fija, r_fija, cuota_fija)
        intereses_fija = df_fija["Intereses pagados"].sum()

        # Mixta
        n_fijo = int(years_fixed * 12)
        n_var = int((years_total - years_fixed) * 12)
        r_fijo_mixta = (tipo_fijo_mixta / 100) / 12
        r_var_mixta = ((euribor + diferencial) / 100) / 12
        cuota_fija_mixta = principal * (r_fijo_mixta * (1 + r_fijo_mixta) ** (n_fijo + n_var)) / ((1 + r_fijo_mixta) ** (n_fijo + n_var) - 1)
        if r_var_mixta > 0:
            pendiente = principal
            for _ in range(n_fijo):
                interes = pendiente * r_fijo_mixta
                amortizacion = cuota_fija_mixta - interes
                pendiente -= amortizacion
            cuota_variable = pendiente * (r_var_mixta * (1 + r_var_mixta) ** n_var) / ((1 + r_var_mixta) ** n_var - 1)
        else:
            cuota_variable = 0
        df_mixta = cuadro_amortizacion_mixta(principal, years_fixed, years_total, r_fijo_mixta, r_var_mixta, cuota_fija_mixta, cuota_variable)
        intereses_mixta = df_mixta["Intereses pagados"].sum()

        st.write(f"**Intereses totales fija:** {intereses_fija:,.2f} €")
        st.write(f"**Intereses totales mixta:** {intereses_mixta:,.2f} €")

        st.write("### Intereses acumulados por año")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_fija["Año"], y=df_fija["Intereses pagados"].cumsum(),
            mode="lines+markers", name="Fija"
        ))
        fig.add_trace(go.Scatter(
            x=df_mixta["Año"], y=df_mixta["Intereses pagados"].cumsum(),
            mode="lines+markers", name="Mixta"
        ))
        fig.update_layout(
            title="Intereses acumulados por año",
            xaxis_title="Año",
            yaxis_title="Intereses acumulados (€)",
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

# =============================
# 4. PÁGINA AMORTIZACIÓN ANTICIPADA
# =============================
elif pagina == "Amortización Anticipada":
    st.title("¿Cuánto compensa amortizar anticipadamente?")
    st.write("Simula cuánto te ahorras en intereses si haces una amortización anticipada en una hipoteca fija.")

    years = st.number_input("Años de la hipoteca:", min_value=1, max_value=40, value=20, key="aa_years")
    interest = st.number_input("Tipo de interés anual (%):", min_value=0.0, max_value=20.0, value=3.0, step=0.1, key="aa_interest")
    principal = st.number_input("Importe total (€):", min_value=1000.0, max_value=1000000.0, value=150000.0, step=1000.0, key="aa_principal")
    year_amort = st.number_input("Año en que amortizas:", min_value=1, max_value=years, value=5)
    importe_amort = st.number_input("Importe a amortizar (€):", min_value=100.0, max_value=principal, value=10000.0, step=500.0)
    tipo_amort = st.radio("¿Qué quieres reducir?", ("Plazo", "Cuota"))

    if st.button("Simular ahorro"):
        n = int(years * 12)
        r = (interest / 100) / 12
        cuota = principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
        pendiente = principal
        intereses_sin_amort = 0

        for i in range(n):
            interes = pendiente * r
            amort = cuota - interes
            intereses_sin_amort += interes
            pendiente -= amort
            if (i+1) % 12 == 0:
                pass
        intereses_totales_sin_amort = intereses_sin_amort

        pendiente = principal
        intereses_con_amort = 0
        meses_amort = int((year_amort - 1) * 12)
        for i in range(meses_amort):
            interes = pendiente * r
            amort = cuota - interes
            intereses_con_amort += interes
            pendiente -= amort

        pendiente -= importe_amort
        if pendiente < 0:
            pendiente = 0

        if tipo_amort == "Plazo":
            meses_restantes = 0
            while pendiente > 0:
                interes = pendiente * r
                amort = cuota - interes
                intereses_con_amort += interes
                pendiente -= amort
                meses_restantes += 1
                if pendiente < 0:
                    pendiente = 0
            total_meses = meses_amort + meses_restantes
            st.write(f"**Nuevo plazo:** {total_meses//12} años y {total_meses%12} meses")
        else:
            n_rest = n - meses_amort
            if r > 0:
                nueva_cuota = pendiente * (r * (1 + r) ** n_rest) / ((1 + r) ** n_rest - 1)
            else:
                nueva_cuota = pendiente / n_rest
            for i in range(n_rest):
                interes = pendiente * r
                amort = nueva_cuota - interes
                intereses_con_amort += interes
                pendiente -= amort
                if pendiente < 0:
                    pendiente = 0
            st.write(f"**Nueva cuota:** {nueva_cuota:,.2f} €")

        intereses_totales_con_amort = intereses_con_amort
        ahorro = intereses_totales_sin_amort - intereses_totales_con_amort

        st.write(f"**Intereses totales SIN amortizar:** {intereses_totales_sin_amort:,.2f} €")
        st.write(f"**Intereses totales CON amortización:** {intereses_totales_con_amort:,.2f} €")
        st.write(f"### **¡Ahorro en intereses! → {ahorro:,.2f} €**")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["Sin amortizar", "Con amortización"],
            y=[intereses_totales_sin_amort, intereses_totales_con_amort],
            marker_color=["red", "green"]
        ))
        fig.update_layout(
            yaxis_title="Intereses totales (€)",
            title="Comparativa de intereses totales",
            hovermode="x"
        )
        st.plotly_chart(fig, use_container_width=True)

# =============================
# 5. PÁGINA COMPARADOR DE OFERTAS
# =============================
elif pagina == "Comparador de Ofertas":
    st.title("Comparador de Ofertas de Hipoteca")
    st.write("Introduce varias ofertas para comparar cuota, intereses totales y más.")

    num_ofertas = st.number_input("¿Cuántas ofertas quieres comparar?", min_value=2, max_value=5, value=2)
    data = []
    for i in range(int(num_ofertas)):
        st.subheader(f"Oferta {i+1}")
        tipo = st.selectbox(f"Tipo de hipoteca {i+1}", ["Fija", "Mixta"], key=f"tipo_{i}")
        principal = st.number_input(f"Importe total {i+1} (€):", min_value=1000.0, max_value=1000000.0, value=150000.0, step=1000.0, key=f"principal_{i}")
        years = st.number_input(f"Años {i+1}:", min_value=1, max_value=40, value=20, key=f"years_{i}")

        if tipo == "Fija":
            interest = st.number_input(f"Interés anual fija {i+1} (%):", min_value=0.0, max_value=20.0, value=3.0, step=0.1, key=f"int_fija_{i}")
            n = int(years * 12)
            r = (interest / 100) / 12
            cuota = principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1) if r > 0 else principal / n
            total_pagado = cuota * n
            intereses_totales = total_pagado - principal
        else:
            years_fixed = st.number_input(f"Años fijos {i+1}:", min_value=1, max_value=years, value=10, key=f"yf_{i}")
            tipo_fijo = st.number_input(f"Interés fijo {i+1} (%):", min_value=0.0, max_value=20.0, value=2.0, step=0.1, key=f"tf_{i}")
            euribor = st.number_input(f"Euribor variable {i+1} (%):", min_value=-2.0, max_value=10.0, value=2.0, step=0.1, key=f"e_{i}")
            diferencial = st.number_input(f"Diferencial {i+1} (%):", min_value=0.0, max_value=5.0, value=1.0, step=0.1, key=f"d_{i}")
            n_fijo = int(years_fixed * 12)
            n_var = int((years - years_fixed) * 12)
            r_fijo = (tipo_fijo / 100) / 12
            r_var = ((euribor + diferencial) / 100) / 12
            cuota_fija = principal * (r_fijo * (1 + r_fijo) ** (n_fijo + n_var)) / ((1 + r_fijo) ** (n_fijo + n_var) - 1)
            pendiente = principal
            intereses_mixta = 0
            for _ in range(n_fijo):
                interes = pendiente * r_fijo
                amortizacion = cuota_fija - interes
                pendiente -= amortizacion
                intereses_mixta += interes
            cuota_variable = pendiente * (r_var * (1 + r_var) ** n_var) / ((1 + r_var) ** n_var - 1) if r_var > 0 else pendiente / n_var
            for _ in range(n_var):
                interes = pendiente * r_var
                amortizacion = cuota_variable - interes
                pendiente -= amortizacion
                intereses_mixta += interes
            cuota = cuota_fija
            intereses_totales = intereses_mixta

        data.append({
            "Tipo": tipo,
            "Importe": principal,
            "Años": years,
            "Cuota inicial": cuota,
            "Intereses totales": intereses_totales
        })

    if st.button("Comparar ofertas"):
        df = pd.DataFrame(data)
        st.write("### Comparativa de ofertas")
        st.dataframe(df.style.format({
            "Importe": "{:,.2f} €",
            "Cuota inicial": "{:,.2f} €",
            "Intereses totales": "{:,.2f} €"
        }), use_container_width=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[f"Oferta {i+1}" for i in range(len(df))],
            y=df["Intereses totales"],
            marker_color="skyblue"
        ))
        fig.update_layout(
            xaxis_title="Oferta",
            yaxis_title="Intereses totales (€)",
            title="Comparativa de Intereses Totales",
            hovermode="x"
        )
        st.plotly_chart(fig, use_container_width=True)

# =============================
# 6. PÁGINA BONIFICACIONES
# =============================
elif pagina == "Bonificaciones":
    st.title("¿Compensa aceptar bonificaciones en tu hipoteca fija?")

    years = st.number_input("Años de la hipoteca:", min_value=1, max_value=40, value=20, key="boni_years")
    interest = st.number_input("Tipo de interés SIN bonificaciones (%):", min_value=0.0, max_value=20.0, value=3.0, step=0.1, key="boni_interest")
    principal = st.number_input("Importe total (€):", min_value=1000.0, max_value=1000000.0, value=150000.0, step=1000.0, key="boni_principal")

    opciones = ["Seguro de vida", "Seguro de hogar", "Seguro de vivienda", "Nómina", "Gastos anuales", "Fondo", "Otro"]
    bonis = st.multiselect("Selecciona las bonificaciones que quieres analizar:", opciones)

    bonificaciones = []
    for b in bonis:
        st.subheader(f"{b}")
        if b == "Otro":
            nombre = st.text_input("Nombre de la bonificación", key=f"boni_nombre_{b}")
        else:
            nombre = b
        sobrecoste = st.number_input(f"Sobrecoste anual de {nombre} (€):", min_value=0.0, value=0.0, step=50.0, key=f"boni_sc_{b}")
        bonifica = st.number_input(f"Bonificación en el tipo de interés de {nombre} (%):", min_value=0.0, max_value=2.0, value=0.1, step=0.01, key=f"boni_b_{b}")
        bonificaciones.append({
            "nombre": nombre,
            "sobrecoste": sobrecoste,
            "bonifica": bonifica
        })

    if st.button("Calcular si compensa"):
        n = int(years * 12)
        r_sin = (interest / 100) / 12
        cuota_sin = principal * (r_sin * (1 + r_sin) ** n) / ((1 + r_sin) ** n - 1)
        pendiente_sin = principal

        intereses_anuales_sin = []
        for year in range(1, years + 1):
            intereses_anual = 0
            for mes in range(12):
                interes_mes = pendiente_sin * r_sin
                capital_mes = cuota_sin - interes_mes
                intereses_anual += interes_mes
                pendiente_sin -= capital_mes
                if pendiente_sin < 0:
                    pendiente_sin = 0
            intereses_anuales_sin.append(intereses_anual)

        total_bonificacion = sum(b["bonifica"] for b in bonificaciones)
        total_sobrecoste_anual = sum(b["sobrecoste"] for b in bonificaciones)
        r_con = ((interest - total_bonificacion) / 100) / 12
        cuota_con = principal * (r_con * (1 + r_con) ** n) / ((1 + r_con) ** n - 1)
        pendiente_con = principal

        intereses_anuales_con = []
        for year in range(1, years + 1):
            intereses_anual = 0
            for mes in range(12):
                interes_mes = pendiente_con * r_con
                capital_mes = cuota_con - interes_mes
                intereses_anual += interes_mes
                pendiente_con -= capital_mes
                if pendiente_con < 0:
                    pendiente_con = 0
            intereses_anuales_con.append(intereses_anual)

        intereses_ahorrados_anual = np.array(intereses_anuales_sin) - np.array(intereses_anuales_con)
        ahorro_neto_anual = intereses_ahorrados_anual - total_sobrecoste_anual

        df = pd.DataFrame({
            "Año": np.arange(1, years+1),
            "Intereses ahorrados ese año": intereses_ahorrados_anual,
            "Sobrecoste anual": [total_sobrecoste_anual]*years,
            "Ahorro neto anual": ahorro_neto_anual
        })

        st.write(f"**Intereses totales SIN bonificaciones:** {sum(intereses_anuales_sin):,.2f} €")
        st.write(f"**Intereses totales CON bonificaciones:** {sum(intereses_anuales_con):,.2f} €")
        st.write(f"**Sobrecoste anual total por bonificaciones:** {total_sobrecoste_anual:,.2f} €")

        st.write("### Evolución del ahorro neto anual")
        st.dataframe(df.style.format({
            "Intereses ahorrados ese año": "{:,.2f} €",
            "Sobrecoste anual": "{:,.2f} €",
            "Ahorro neto anual": "{:,.2f} €"
        }), use_container_width=True)

        st.write("### Gráfico de ahorro neto anual")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["Año"], y=df["Ahorro neto anual"],
            mode="lines+markers", name="Ahorro neto anual", line=dict(color="green")
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.update_layout(
            title="¿En qué año deja de compensar la bonificación?",
            xaxis_title="Año",
            yaxis_title="Ahorro neto anual (€)",
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

# =============================
# 7. PÁGINA SUBROGACIÓN
# =============================
elif pagina == "Subrogación":
    st.title("¿Compensa subrogar tu hipoteca fija?")

    st.markdown("""
    Compara el coste y el ahorro de cambiar tu hipoteca fija a otra entidad, teniendo en cuenta los gastos de subrogación.
    """)

    # Datos de la hipoteca actual
    st.header("Tu hipoteca actual")
    importe_inicial = st.number_input("Importe inicial de la hipoteca (€):", min_value=1000.0, max_value=1000000.0, value=150000.0, step=1000.0)
    años_totales = st.number_input("Años totales de la hipoteca:", min_value=1, max_value=40, value=20)
    tipo_actual = st.number_input("Tipo de interés actual (%):", min_value=0.0, max_value=20.0, value=3.0, step=0.1)
    año_actual = st.number_input("Año en el que estás:", min_value=1, max_value=años_totales, value=7)

    n_total = int(años_totales * 12)
    n_pasados = int((año_actual - 1) * 12)
    r_actual = (tipo_actual / 100) / 12
    cuota_actual = importe_inicial * (r_actual * (1 + r_actual) ** n_total) / ((1 + r_actual) ** n_total - 1) if r_actual > 0 else importe_inicial / n_total
    pendiente = importe_inicial
    for _ in range(n_pasados):
        interes_mes = pendiente * r_actual
        capital_mes = cuota_actual - interes_mes
        pendiente -= capital_mes
        if pendiente < 0:
            pendiente = 0

    st.write(f"**Capital pendiente estimado:** {pendiente:,.2f} €")

    # Datos de la hipoteca alternativa
    st.header("Hipoteca alternativa (tras subrogación)")
    tipo_nuevo = st.number_input("Tipo de interés alternativo (%):", min_value=0.0, max_value=20.0, value=2.0, step=0.1)
    años_restantes = st.number_input("Plazo restante (años):", min_value=1, max_value=40, value=años_totales - año_actual + 1)
    gastos_subrogacion = st.number_input("Coste de subrogación (€):", min_value=0.0, max_value=20000.0, value=1500.0, step=100.0)

    if st.button("Comparar escenarios"):
        n_restantes = int(años_restantes * 12)
        # Escenario 1: No subrogas
        cuota_restante = cuota_actual
        intereses_restantes = 0
        cap_pend = pendiente
        for _ in range(n_restantes):
            interes_mes = cap_pend * r_actual
            capital_mes = cuota_restante - interes_mes
            intereses_restantes += interes_mes
            cap_pend -= capital_mes
            if cap_pend < 0:
                cap_pend = 0
        total_restante = intereses_restantes + pendiente

        # Escenario 2: Subrogas
        r_nuevo = (tipo_nuevo / 100) / 12
        cuota_nueva = pendiente * (r_nuevo * (1 + r_nuevo) ** n_restantes) / ((1 + r_nuevo) ** n_restantes - 1) if r_nuevo > 0 else pendiente / n_restantes
        intereses_nuevos = 0
        cap_pend = pendiente
        for _ in range(n_restantes):
            interes_mes = cap_pend * r_nuevo
            capital_mes = cuota_nueva - interes_mes
            intereses_nuevos += interes_mes
            cap_pend -= capital_mes
            if cap_pend < 0:
                cap_pend = 0
        total_nuevo = intereses_nuevos + pendiente + gastos_subrogacion

        ahorro_total = total_restante - total_nuevo

        st.write(f"**Escenario 1: No subrogas**")
        st.write(f"- Cuota mensual: {cuota_restante:,.2f} €")
        st.write(f"- Intereses por pagar: {intereses_restantes:,.2f} €")
        st.write(f"- Total a pagar (incluyendo capital): {total_restante:,.2f} €")

        st.write(f"**Escenario 2: Subrogas**")
        st.write(f"- Nueva cuota mensual: {cuota_nueva:,.2f} €")
        st.write(f"- Intereses por pagar: {intereses_nuevos:,.2f} €")
        st.write(f"- Total a pagar (capital + intereses + gastos): {total_nuevo:,.2f} €")
        st.write(f"### **Ahorro total con la subrogación: {ahorro_total:,.2f} €**")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["No subrogas", "Subrogas"],
            y=[total_restante, total_nuevo],
            marker_color=["red", "green"],
            name="Total a pagar"
        ))
        fig.add_trace(go.Bar(
            x=["No subrogas", "Subrogas"],
            y=[intereses_restantes, intereses_nuevos],
            marker_color=["orange", "blue"],
            name="Intereses"
        ))
        fig.add_trace(go.Bar(
            x=["No subrogas", "Subrogas"],
            y=[0, gastos_subrogacion],
            marker_color="gray",
            name="Gastos subrogación"
        ))
        fig.update_layout(
            barmode="overlay",
            yaxis_title="Total a pagar (€)",
            title="¿Compensa subrogar?",
            hovermode="x"
        )
        st.plotly_chart(fig, use_container_width=True)

# =============================
# 8. PÁGINA GLOSARIO MEJORADO
# =============================
elif pagina == "Glosario":
    st.title("Glosario Hipotecario y Consejos Útiles")

    st.markdown("""
    ### Términos básicos

    **TIN (Tipo de Interés Nominal):**  
    Porcentaje que el banco aplica al dinero que te presta. Solo tiene en cuenta los intereses, no comisiones ni otros gastos.

    **TAE (Tasa Anual Equivalente):**  
    Refleja el coste real de la hipoteca porque incluye el TIN, comisiones, gastos y la frecuencia de los pagos. Útil para comparar ofertas.

    **Euríbor:**  
    Índice de referencia para la mayoría de hipotecas variables y mixtas en España. Es el tipo de interés al que los bancos europeos se prestan dinero entre sí.

    **Diferencial:**  
    Porcentaje fijo que se suma al Euríbor para calcular el tipo de interés de tu hipoteca variable o mixta. Ejemplo: si el Euríbor está en 2% y tu diferencial es 1%, pagarás un 3%.

    **Cuota:**  
    Pago mensual que haces al banco. Incluye parte de intereses y parte de devolución del capital.

    **Capital pendiente:**  
    Dinero que aún debes devolver al banco en cada momento de la vida de la hipoteca.

    **Amortización:**  
    Proceso de devolver el dinero prestado. Cada cuota amortiza (reduce) una parte del capital y paga intereses.

    **Amortización anticipada:**  
    Pago extra que haces para reducir el capital pendiente antes de tiempo. Puede servir para reducir la cuota mensual o el plazo de la hipoteca.

    **Bonificación:**  
    Descuento en el tipo de interés que te ofrece el banco si contratas productos adicionales (seguros, nómina, fondos, etc). Ojo: a veces, el coste de estos productos supera el ahorro en intereses.

    **Hipoteca fija:**  
    El tipo de interés no cambia durante toda la vida del préstamo. La cuota mensual es siempre la misma.

    **Hipoteca variable:**  
    El tipo de interés puede cambiar periódicamente (normalmente cada 6 o 12 meses), en función del Euríbor y el diferencial.

    **Hipoteca mixta:**  
    Combina un periodo inicial a tipo fijo (por ejemplo, 10 años) y el resto a tipo variable (Euríbor + diferencial).

    **Subrogación:**  
    Cambiar tu hipoteca de un banco a otro para mejorar condiciones (tipo de interés, plazo, etc). Suele tener un coste, pero puede ahorrar mucho dinero si las condiciones son mejores.

    **Comisión de apertura:**  
    Cantidad que cobra el banco al formalizar la hipoteca.

    **Comisión de amortización anticipada:**  
    Penalización (porcentaje) que cobra el banco si devuelves parte o toda la hipoteca antes de tiempo.

    **Vinculación:**  
    Productos adicionales que el banco te exige contratar para darte mejores condiciones en la hipoteca (seguros, nómina, tarjetas...).

    **Gastos de subrogación:**  
    Costes administrativos, notariales, de tasación, etc. al cambiar la hipoteca de banco.

    **Fondo de inversión:**  
    Producto financiero donde puedes invertir dinero, a veces exigido como condición de bonificación.

    ---

    ### Consejos útiles

    - **Compara siempre la TAE, no solo el TIN.**
    - **Lee la letra pequeña de las bonificaciones:** calcula si realmente te sale a cuenta.
    - **Pregunta por las comisiones de amortización anticipada y subrogación.**
    - **Simula diferentes escenarios:** ¿qué pasa si subes el Euríbor? ¿y si amortizas anticipadamente?
    - **No te fijes solo en la cuota:** valora el coste total de los intereses a lo largo de la vida de la hipoteca.
    - **Pregunta por la vinculación:** a veces, el banco exige domiciliar la nómina, contratar seguros, tarjetas, etc.
    - **Ten en cuenta tus planes de vida:** si vas a vender la casa antes de acabar la hipoteca, una fija puede no compensar.
    - **Consulta siempre con un asesor independiente si tienes dudas.**
    """)

    st.info("¿Tienes dudas? Busca términos en este glosario o consulta con un asesor independiente antes de firmar.")
