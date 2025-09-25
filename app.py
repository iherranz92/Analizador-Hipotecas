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
@st.cache_data(show_spinner=False)
def cuadro_amortizacion_fija(principal, years, r, cuota):
    cuadro = []
    pendiente = principal
    for year in range(1, years + 1):
        intereses_anual = 0.0
        capital_anual = 0.0
        for _ in range(12):
            interes_mes = pendiente * r
            capital_mes = cuota - interes_mes
            intereses_anual += interes_mes
            capital_anual += capital_mes
            pendiente -= capital_mes
            if pendiente < 0:
                pendiente = 0.0
        cuadro.append({
            "Año": year,
            "Cuota total pagada": cuota * 12,
            "Intereses pagados": intereses_anual,
            "Capital amortizado": capital_anual,
            "Capital pendiente": max(pendiente, 0.0)
        })
    return pd.DataFrame(cuadro)

@st.cache_data(show_spinner=False)
def cuadro_amortizacion_mixta(principal, years_fixed, years_total, r_fijo, r_var, cuota_fija, cuota_variable):
    cuadro = []
    pendiente = principal
    for year in range(1, years_total + 1):
        intereses_anual = 0.0
        capital_anual = 0.0
        for _ in range(12):
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
                pendiente = 0.0
        cuadro.append({
            "Año": year,
            "Cuota total pagada": cuota_mes * 12,
            "Intereses pagados": intereses_anual,
            "Capital amortizado": capital_anual,
            "Capital pendiente": max(pendiente, 0.0)
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
# =============================
# 1. PÁGINA HIPOTECA FIJA (mejorada)
# =============================
elif pagina == "Hipoteca Fija":
    st.title("Calculadora de Hipoteca Fija")
    st.info("Introduce los datos de tu hipoteca fija para calcular la cuota mensual, los intereses totales y ver el cuadro de amortización.")
    st.divider()

    years = st.number_input(
        "Años de la hipoteca:",
        min_value=1, max_value=40, value=20,
        help="Plazo total de devolución del préstamo en años."
    )
    interest = st.number_input(
        "Tipo de interés anual (%):",
        min_value=-2.0, max_value=20.0, value=3.0, step=0.1,
        help="Porcentaje fijo que aplicará el banco cada año sobre el capital pendiente."
    )
    principal = st.number_input(
        "Importe total (€):",
        min_value=1000.0, max_value=1_000_000.0, value=150000.0, step=1000.0,
        help="Cantidad total que te presta el banco."
    )

    # Validaciones y avisos
    if interest < 0:
        st.warning("Tienes un tipo negativo. Revisa que sea lo que quieres simular.")
    if years > 35:
        st.info("Plazos muy largos suelen implicar intereses totales elevados.")
    if principal > 600_000:
        st.info("Importes muy altos: comprueba límites/reglas de tu entidad.")

    st.divider()

    if st.button("Calcular", key="calcular_fija"):
        n = int(years * 12)
        r = (interest / 100) / 12

        if n <= 0:
            st.error("Plazo inválido.")
        else:
            cuota = principal / n if r == 0 else principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
            total_pagado = cuota * n
            intereses_totales = total_pagado - principal

            st.success("¡Cálculo realizado con éxito!")
            # Métricas principales
            c1, c2 = st.columns(2)
            c1.metric("Cuota mensual", f"{cuota:,.2f} €")
            c2.metric("Intereses totales", f"{intereses_totales:,.2f} €")

            st.divider()
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

            st.divider()
            st.write("### Evolución de capital pendiente e intereses")
            plot_evolucion_plotly(df_cuadro, "Evolución Hipoteca Fija")


# =============================
# 2. PÁGINA HIPOTECA MIXTA
# =============================
# =============================
# 2. PÁGINA HIPOTECA MIXTA (mejorada)
# =============================
elif pagina == "Hipoteca Mixta":
    st.title("Calculadora de Hipoteca Mixta")
    st.info("Simula una hipoteca con años a tipo fijo y años a tipo variable. Calcula cuotas, intereses y cuadro de amortización.")
    st.divider()

    years_fixed = st.number_input(
        "Años a tipo fijo:", min_value=1, max_value=40, value=10,
        help="Número de años iniciales con interés fijo."
    )
    years_total = st.number_input(
        "Años totales de la hipoteca:", min_value=years_fixed, max_value=40, value=20,
        help="Duración total de la hipoteca en años."
    )
    tipo_fijo = st.number_input(
        "Tipo de interés fijo (%):", min_value=-2.0, max_value=20.0, value=2.0, step=0.1,
        help="Interés aplicado durante los años fijos."
    )
    euribor = st.number_input(
        "Euribor estimado para los años variables (%):", min_value=-3.0, max_value=10.0, value=2.0, step=0.1,
        help="Estimación del Euríbor durante la fase variable."
    )
    diferencial = st.number_input(
        "Diferencial sobre euribor (%):", min_value=0.0, max_value=5.0, value=1.0, step=0.1,
        help="Porcentaje fijo que se suma al Euríbor en la fase variable."
    )
    principal = st.number_input(
        "Importe total (€):", min_value=1000.0, max_value=1_000_000.0, value=150000.0, step=1000.0,
        help="Cantidad total prestada por el banco."
    )

    # Validaciones y avisos
    if years_total < years_fixed:
        st.error("Los años totales no pueden ser menores que los años fijos.")
    if tipo_fijo < 0:
        st.warning("Tipo fijo negativo: escenario poco común, revisa el dato.")
    if euribor + diferencial < 0:
        st.info("Euríbor + diferencial negativo: podría dar cuotas menores; revisa si tu contrato tiene suelo.")

    st.divider()

    if st.button("Calcular", key="calcular_mixta"):
        n_fijo = int(years_fixed * 12)
        n_var = int((years_total - years_fixed) * 12)
        r_fijo = (tipo_fijo / 100) / 12
        r_var = ((euribor + diferencial) / 100) / 12

        if n_fijo + n_var <= 0:
            st.error("Plazo inválido.")
        else:
            # Cuota fase fija calculada a plazo completo (método clásico de mixtas comerciales)
            cuota_fija = principal / (n_fijo + n_var) if r_fijo == 0 else principal * (r_fijo * (1 + r_fijo) ** (n_fijo + n_var)) / ((1 + r_fijo) ** (n_fijo + n_var) - 1)

            pendiente = principal
            intereses_mixta = 0.0

            # Simula años fijos
            for _ in range(n_fijo):
                interes = pendiente * r_fijo
                amortizacion = cuota_fija - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            # Cuota variable con capital remanente
            if n_var > 0:
                cuota_variable = pendiente / n_var if r_var == 0 else pendiente * (r_var * (1 + r_var) ** n_var) / ((1 + r_var) ** n_var - 1)
            else:
                cuota_variable = 0.0

            # Simula años variables
            for _ in range(n_var):
                interes = pendiente * r_var
                amortizacion = cuota_variable - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            st.success("¡Cálculo realizado con éxito!")
            # Métricas principales
            c1, c2, c3 = st.columns(3)
            c1.metric("Cuota fija", f"{cuota_fija:,.2f} €")
            c2.metric("Cuota variable", f"{cuota_variable:,.2f} €")
            c3.metric("Intereses totales", f"{intereses_mixta:,.2f} €")

            st.divider()
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

            st.divider()
            st.write("### Evolución de capital pendiente e intereses")
            plot_evolucion_plotly(df_cuadro, "Evolución Hipoteca Mixta")
# =============================
# 2. PÁGINA HIPOTECA MIXTA (mejorada)
# =============================
elif pagina == "Hipoteca Mixta":
    st.title("Calculadora de Hipoteca Mixta")
    st.info("Simula una hipoteca con años a tipo fijo y años a tipo variable. Calcula cuotas, intereses y cuadro de amortización.")
    st.divider()

    years_fixed = st.number_input(
        "Años a tipo fijo:", min_value=1, max_value=40, value=10,
        help="Número de años iniciales con interés fijo."
    )
    years_total = st.number_input(
        "Años totales de la hipoteca:", min_value=years_fixed, max_value=40, value=20,
        help="Duración total de la hipoteca en años."
    )
    tipo_fijo = st.number_input(
        "Tipo de interés fijo (%):", min_value=-2.0, max_value=20.0, value=2.0, step=0.1,
        help="Interés aplicado durante los años fijos."
    )
    euribor = st.number_input(
        "Euribor estimado para los años variables (%):", min_value=-3.0, max_value=10.0, value=2.0, step=0.1,
        help="Estimación del Euríbor durante la fase variable."
    )
    diferencial = st.number_input(
        "Diferencial sobre euribor (%):", min_value=0.0, max_value=5.0, value=1.0, step=0.1,
        help="Porcentaje fijo que se suma al Euríbor en la fase variable."
    )
    principal = st.number_input(
        "Importe total (€):", min_value=1000.0, max_value=1_000_000.0, value=150000.0, step=1000.0,
        help="Cantidad total prestada por el banco."
    )

    # Validaciones y avisos
    if years_total < years_fixed:
        st.error("Los años totales no pueden ser menores que los años fijos.")
    if tipo_fijo < 0:
        st.warning("Tipo fijo negativo: escenario poco común, revisa el dato.")
    if euribor + diferencial < 0:
        st.info("Euríbor + diferencial negativo: podría dar cuotas menores; revisa si tu contrato tiene suelo.")

    st.divider()

    if st.button("Calcular", key="calcular_mixta"):
        n_fijo = int(years_fixed * 12)
        n_var = int((years_total - years_fixed) * 12)
        r_fijo = (tipo_fijo / 100) / 12
        r_var = ((euribor + diferencial) / 100) / 12

        if n_fijo + n_var <= 0:
            st.error("Plazo inválido.")
        else:
            # Cuota fase fija calculada a plazo completo (método clásico de mixtas comerciales)
            cuota_fija = principal / (n_fijo + n_var) if r_fijo == 0 else principal * (r_fijo * (1 + r_fijo) ** (n_fijo + n_var)) / ((1 + r_fijo) ** (n_fijo + n_var) - 1)

            pendiente = principal
            intereses_mixta = 0.0

            # Simula años fijos
            for _ in range(n_fijo):
                interes = pendiente * r_fijo
                amortizacion = cuota_fija - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            # Cuota variable con capital remanente
            if n_var > 0:
                cuota_variable = pendiente / n_var if r_var == 0 else pendiente * (r_var * (1 + r_var) ** n_var) / ((1 + r_var) ** n_var - 1)
            else:
                cuota_variable = 0.0

            # Simula años variables
            for _ in range(n_var):
                interes = pendiente * r_var
                amortizacion = cuota_variable - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            st.success("¡Cálculo realizado con éxito!")
            # Métricas principales
            c1, c2, c3 = st.columns(3)
            c1.metric("Cuota fija", f"{cuota_fija:,.2f} €")
            c2.metric("Cuota variable", f"{cuota_variable:,.2f} €")
            c3.metric("Intereses totales", f"{intereses_mixta:,.2f} €")

            st.divider()
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

            st.divider()
            st.write("### Evolución de capital pendiente e intereses")
            plot_evolucion_plotly(df_cuadro, "Evolución Hipoteca Mixta")
# =============================
# 2. PÁGINA HIPOTECA MIXTA (mejorada)
# =============================
elif pagina == "Hipoteca Mixta":
    st.title("Calculadora de Hipoteca Mixta")
    st.info("Simula una hipoteca con años a tipo fijo y años a tipo variable. Calcula cuotas, intereses y cuadro de amortización.")
    st.divider()

    years_fixed = st.number_input(
        "Años a tipo fijo:", min_value=1, max_value=40, value=10,
        help="Número de años iniciales con interés fijo."
    )
    years_total = st.number_input(
        "Años totales de la hipoteca:", min_value=years_fixed, max_value=40, value=20,
        help="Duración total de la hipoteca en años."
    )
    tipo_fijo = st.number_input(
        "Tipo de interés fijo (%):", min_value=-2.0, max_value=20.0, value=2.0, step=0.1,
        help="Interés aplicado durante los años fijos."
    )
    euribor = st.number_input(
        "Euribor estimado para los años variables (%):", min_value=-3.0, max_value=10.0, value=2.0, step=0.1,
        help="Estimación del Euríbor durante la fase variable."
    )
    diferencial = st.number_input(
        "Diferencial sobre euribor (%):", min_value=0.0, max_value=5.0, value=1.0, step=0.1,
        help="Porcentaje fijo que se suma al Euríbor en la fase variable."
    )
    principal = st.number_input(
        "Importe total (€):", min_value=1000.0, max_value=1_000_000.0, value=150000.0, step=1000.0,
        help="Cantidad total prestada por el banco."
    )

    # Validaciones y avisos
    if years_total < years_fixed:
        st.error("Los años totales no pueden ser menores que los años fijos.")
    if tipo_fijo < 0:
        st.warning("Tipo fijo negativo: escenario poco común, revisa el dato.")
    if euribor + diferencial < 0:
        st.info("Euríbor + diferencial negativo: podría dar cuotas menores; revisa si tu contrato tiene suelo.")

    st.divider()

    if st.button("Calcular", key="calcular_mixta"):
        n_fijo = int(years_fixed * 12)
        n_var = int((years_total - years_fixed) * 12)
        r_fijo = (tipo_fijo / 100) / 12
        r_var = ((euribor + diferencial) / 100) / 12

        if n_fijo + n_var <= 0:
            st.error("Plazo inválido.")
        else:
            # Cuota fase fija calculada a plazo completo (método clásico de mixtas comerciales)
            cuota_fija = principal / (n_fijo + n_var) if r_fijo == 0 else principal * (r_fijo * (1 + r_fijo) ** (n_fijo + n_var)) / ((1 + r_fijo) ** (n_fijo + n_var) - 1)

            pendiente = principal
            intereses_mixta = 0.0

            # Simula años fijos
            for _ in range(n_fijo):
                interes = pendiente * r_fijo
                amortizacion = cuota_fija - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            # Cuota variable con capital remanente
            if n_var > 0:
                cuota_variable = pendiente / n_var if r_var == 0 else pendiente * (r_var * (1 + r_var) ** n_var) / ((1 + r_var) ** n_var - 1)
            else:
                cuota_variable = 0.0

            # Simula años variables
            for _ in range(n_var):
                interes = pendiente * r_var
                amortizacion = cuota_variable - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            st.success("¡Cálculo realizado con éxito!")
            # Métricas principales
            c1, c2, c3 = st.columns(3)
            c1.metric("Cuota fija", f"{cuota_fija:,.2f} €")
            c2.metric("Cuota variable", f"{cuota_variable:,.2f} €")
            c3.metric("Intereses totales", f"{intereses_mixta:,.2f} €")

            st.divider()
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

            st.divider()
            st.write("### Evolución de capital pendiente e intereses")
            plot_evolucion_plotly(df_cuadro, "Evolución Hipoteca Mixta")
# =============================
# 2. PÁGINA HIPOTECA MIXTA (mejorada)
# =============================
elif pagina == "Hipoteca Mixta":
    st.title("Calculadora de Hipoteca Mixta")
    st.info("Simula una hipoteca con años a tipo fijo y años a tipo variable. Calcula cuotas, intereses y cuadro de amortización.")
    st.divider()

    years_fixed = st.number_input(
        "Años a tipo fijo:", min_value=1, max_value=40, value=10,
        help="Número de años iniciales con interés fijo."
    )
    years_total = st.number_input(
        "Años totales de la hipoteca:", min_value=years_fixed, max_value=40, value=20,
        help="Duración total de la hipoteca en años."
    )
    tipo_fijo = st.number_input(
        "Tipo de interés fijo (%):", min_value=-2.0, max_value=20.0, value=2.0, step=0.1,
        help="Interés aplicado durante los años fijos."
    )
    euribor = st.number_input(
        "Euribor estimado para los años variables (%):", min_value=-3.0, max_value=10.0, value=2.0, step=0.1,
        help="Estimación del Euríbor durante la fase variable."
    )
    diferencial = st.number_input(
        "Diferencial sobre euribor (%):", min_value=0.0, max_value=5.0, value=1.0, step=0.1,
        help="Porcentaje fijo que se suma al Euríbor en la fase variable."
    )
    principal = st.number_input(
        "Importe total (€):", min_value=1000.0, max_value=1_000_000.0, value=150000.0, step=1000.0,
        help="Cantidad total prestada por el banco."
    )

    # Validaciones y avisos
    if years_total < years_fixed:
        st.error("Los años totales no pueden ser menores que los años fijos.")
    if tipo_fijo < 0:
        st.warning("Tipo fijo negativo: escenario poco común, revisa el dato.")
    if euribor + diferencial < 0:
        st.info("Euríbor + diferencial negativo: podría dar cuotas menores; revisa si tu contrato tiene suelo.")

    st.divider()

    if st.button("Calcular", key="calcular_mixta"):
        n_fijo = int(years_fixed * 12)
        n_var = int((years_total - years_fixed) * 12)
        r_fijo = (tipo_fijo / 100) / 12
        r_var = ((euribor + diferencial) / 100) / 12

        if n_fijo + n_var <= 0:
            st.error("Plazo inválido.")
        else:
            # Cuota fase fija calculada a plazo completo (método clásico de mixtas comerciales)
            cuota_fija = principal / (n_fijo + n_var) if r_fijo == 0 else principal * (r_fijo * (1 + r_fijo) ** (n_fijo + n_var)) / ((1 + r_fijo) ** (n_fijo + n_var) - 1)

            pendiente = principal
            intereses_mixta = 0.0

            # Simula años fijos
            for _ in range(n_fijo):
                interes = pendiente * r_fijo
                amortizacion = cuota_fija - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            # Cuota variable con capital remanente
            if n_var > 0:
                cuota_variable = pendiente / n_var if r_var == 0 else pendiente * (r_var * (1 + r_var) ** n_var) / ((1 + r_var) ** n_var - 1)
            else:
                cuota_variable = 0.0

            # Simula años variables
            for _ in range(n_var):
                interes = pendiente * r_var
                amortizacion = cuota_variable - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            st.success("¡Cálculo realizado con éxito!")
            # Métricas principales
            c1, c2, c3 = st.columns(3)
            c1.metric("Cuota fija", f"{cuota_fija:,.2f} €")
            c2.metric("Cuota variable", f"{cuota_variable:,.2f} €")
            c3.metric("Intereses totales", f"{intereses_mixta:,.2f} €")

            st.divider()
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

            st.divider()
            st.write("### Evolución de capital pendiente e intereses")
            plot_evolucion_plotly(df_cuadro, "Evolución Hipoteca Mixta")
# =============================
# 2. PÁGINA HIPOTECA MIXTA (mejorada)
# =============================
elif pagina == "Hipoteca Mixta":
    st.title("Calculadora de Hipoteca Mixta")
    st.info("Simula una hipoteca con años a tipo fijo y años a tipo variable. Calcula cuotas, intereses y cuadro de amortización.")
    st.divider()

    years_fixed = st.number_input(
        "Años a tipo fijo:", min_value=1, max_value=40, value=10,
        help="Número de años iniciales con interés fijo."
    )
    years_total = st.number_input(
        "Años totales de la hipoteca:", min_value=years_fixed, max_value=40, value=20,
        help="Duración total de la hipoteca en años."
    )
    tipo_fijo = st.number_input(
        "Tipo de interés fijo (%):", min_value=-2.0, max_value=20.0, value=2.0, step=0.1,
        help="Interés aplicado durante los años fijos."
    )
    euribor = st.number_input(
        "Euribor estimado para los años variables (%):", min_value=-3.0, max_value=10.0, value=2.0, step=0.1,
        help="Estimación del Euríbor durante la fase variable."
    )
    diferencial = st.number_input(
        "Diferencial sobre euribor (%):", min_value=0.0, max_value=5.0, value=1.0, step=0.1,
        help="Porcentaje fijo que se suma al Euríbor en la fase variable."
    )
    principal = st.number_input(
        "Importe total (€):", min_value=1000.0, max_value=1_000_000.0, value=150000.0, step=1000.0,
        help="Cantidad total prestada por el banco."
    )

    # Validaciones y avisos
    if years_total < years_fixed:
        st.error("Los años totales no pueden ser menores que los años fijos.")
    if tipo_fijo < 0:
        st.warning("Tipo fijo negativo: escenario poco común, revisa el dato.")
    if euribor + diferencial < 0:
        st.info("Euríbor + diferencial negativo: podría dar cuotas menores; revisa si tu contrato tiene suelo.")

    st.divider()

    if st.button("Calcular", key="calcular_mixta"):
        n_fijo = int(years_fixed * 12)
        n_var = int((years_total - years_fixed) * 12)
        r_fijo = (tipo_fijo / 100) / 12
        r_var = ((euribor + diferencial) / 100) / 12

        if n_fijo + n_var <= 0:
            st.error("Plazo inválido.")
        else:
            # Cuota fase fija calculada a plazo completo (método clásico de mixtas comerciales)
            cuota_fija = principal / (n_fijo + n_var) if r_fijo == 0 else principal * (r_fijo * (1 + r_fijo) ** (n_fijo + n_var)) / ((1 + r_fijo) ** (n_fijo + n_var) - 1)

            pendiente = principal
            intereses_mixta = 0.0

            # Simula años fijos
            for _ in range(n_fijo):
                interes = pendiente * r_fijo
                amortizacion = cuota_fija - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            # Cuota variable con capital remanente
            if n_var > 0:
                cuota_variable = pendiente / n_var if r_var == 0 else pendiente * (r_var * (1 + r_var) ** n_var) / ((1 + r_var) ** n_var - 1)
            else:
                cuota_variable = 0.0

            # Simula años variables
            for _ in range(n_var):
                interes = pendiente * r_var
                amortizacion = cuota_variable - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            st.success("¡Cálculo realizado con éxito!")
            # Métricas principales
            c1, c2, c3 = st.columns(3)
            c1.metric("Cuota fija", f"{cuota_fija:,.2f} €")
            c2.metric("Cuota variable", f"{cuota_variable:,.2f} €")
            c3.metric("Intereses totales", f"{intereses_mixta:,.2f} €")

            st.divider()
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

            st.divider()
            st.write("### Evolución de capital pendiente e intereses")
            plot_evolucion_plotly(df_cuadro, "Evolución Hipoteca Mixta")
# =============================
# 2. PÁGINA HIPOTECA MIXTA (mejorada)
# =============================
elif pagina == "Hipoteca Mixta":
    st.title("Calculadora de Hipoteca Mixta")
    st.info("Simula una hipoteca con años a tipo fijo y años a tipo variable. Calcula cuotas, intereses y cuadro de amortización.")
    st.divider()

    years_fixed = st.number_input(
        "Años a tipo fijo:", min_value=1, max_value=40, value=10,
        help="Número de años iniciales con interés fijo."
    )
    years_total = st.number_input(
        "Años totales de la hipoteca:", min_value=years_fixed, max_value=40, value=20,
        help="Duración total de la hipoteca en años."
    )
    tipo_fijo = st.number_input(
        "Tipo de interés fijo (%):", min_value=-2.0, max_value=20.0, value=2.0, step=0.1,
        help="Interés aplicado durante los años fijos."
    )
    euribor = st.number_input(
        "Euribor estimado para los años variables (%):", min_value=-3.0, max_value=10.0, value=2.0, step=0.1,
        help="Estimación del Euríbor durante la fase variable."
    )
    diferencial = st.number_input(
        "Diferencial sobre euribor (%):", min_value=0.0, max_value=5.0, value=1.0, step=0.1,
        help="Porcentaje fijo que se suma al Euríbor en la fase variable."
    )
    principal = st.number_input(
        "Importe total (€):", min_value=1000.0, max_value=1_000_000.0, value=150000.0, step=1000.0,
        help="Cantidad total prestada por el banco."
    )

    # Validaciones y avisos
    if years_total < years_fixed:
        st.error("Los años totales no pueden ser menores que los años fijos.")
    if tipo_fijo < 0:
        st.warning("Tipo fijo negativo: escenario poco común, revisa el dato.")
    if euribor + diferencial < 0:
        st.info("Euríbor + diferencial negativo: podría dar cuotas menores; revisa si tu contrato tiene suelo.")

    st.divider()

    if st.button("Calcular", key="calcular_mixta"):
        n_fijo = int(years_fixed * 12)
        n_var = int((years_total - years_fixed) * 12)
        r_fijo = (tipo_fijo / 100) / 12
        r_var = ((euribor + diferencial) / 100) / 12

        if n_fijo + n_var <= 0:
            st.error("Plazo inválido.")
        else:
            # Cuota fase fija calculada a plazo completo (método clásico de mixtas comerciales)
            cuota_fija = principal / (n_fijo + n_var) if r_fijo == 0 else principal * (r_fijo * (1 + r_fijo) ** (n_fijo + n_var)) / ((1 + r_fijo) ** (n_fijo + n_var) - 1)

            pendiente = principal
            intereses_mixta = 0.0

            # Simula años fijos
            for _ in range(n_fijo):
                interes = pendiente * r_fijo
                amortizacion = cuota_fija - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            # Cuota variable con capital remanente
            if n_var > 0:
                cuota_variable = pendiente / n_var if r_var == 0 else pendiente * (r_var * (1 + r_var) ** n_var) / ((1 + r_var) ** n_var - 1)
            else:
                cuota_variable = 0.0

            # Simula años variables
            for _ in range(n_var):
                interes = pendiente * r_var
                amortizacion = cuota_variable - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            st.success("¡Cálculo realizado con éxito!")
            # Métricas principales
            c1, c2, c3 = st.columns(3)
            c1.metric("Cuota fija", f"{cuota_fija:,.2f} €")
            c2.metric("Cuota variable", f"{cuota_variable:,.2f} €")
            c3.metric("Intereses totales", f"{intereses_mixta:,.2f} €")

            st.divider()
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

            st.divider()
            st.write("### Evolución de capital pendiente e intereses")
            plot_evolucion_plotly(df_cuadro, "Evolución Hipoteca Mixta")
# =============================
# 2. PÁGINA HIPOTECA MIXTA (mejorada)
# =============================
elif pagina == "Hipoteca Mixta":
    st.title("Calculadora de Hipoteca Mixta")
    st.info("Simula una hipoteca con años a tipo fijo y años a tipo variable. Calcula cuotas, intereses y cuadro de amortización.")
    st.divider()

    years_fixed = st.number_input(
        "Años a tipo fijo:", min_value=1, max_value=40, value=10,
        help="Número de años iniciales con interés fijo."
    )
    years_total = st.number_input(
        "Años totales de la hipoteca:", min_value=years_fixed, max_value=40, value=20,
        help="Duración total de la hipoteca en años."
    )
    tipo_fijo = st.number_input(
        "Tipo de interés fijo (%):", min_value=-2.0, max_value=20.0, value=2.0, step=0.1,
        help="Interés aplicado durante los años fijos."
    )
    euribor = st.number_input(
        "Euribor estimado para los años variables (%):", min_value=-3.0, max_value=10.0, value=2.0, step=0.1,
        help="Estimación del Euríbor durante la fase variable."
    )
    diferencial = st.number_input(
        "Diferencial sobre euribor (%):", min_value=0.0, max_value=5.0, value=1.0, step=0.1,
        help="Porcentaje fijo que se suma al Euríbor en la fase variable."
    )
    principal = st.number_input(
        "Importe total (€):", min_value=1000.0, max_value=1_000_000.0, value=150000.0, step=1000.0,
        help="Cantidad total prestada por el banco."
    )

    # Validaciones y avisos
    if years_total < years_fixed:
        st.error("Los años totales no pueden ser menores que los años fijos.")
    if tipo_fijo < 0:
        st.warning("Tipo fijo negativo: escenario poco común, revisa el dato.")
    if euribor + diferencial < 0:
        st.info("Euríbor + diferencial negativo: podría dar cuotas menores; revisa si tu contrato tiene suelo.")

    st.divider()

    if st.button("Calcular", key="calcular_mixta"):
        n_fijo = int(years_fixed * 12)
        n_var = int((years_total - years_fixed) * 12)
        r_fijo = (tipo_fijo / 100) / 12
        r_var = ((euribor + diferencial) / 100) / 12

        if n_fijo + n_var <= 0:
            st.error("Plazo inválido.")
        else:
            # Cuota fase fija calculada a plazo completo (método clásico de mixtas comerciales)
            cuota_fija = principal / (n_fijo + n_var) if r_fijo == 0 else principal * (r_fijo * (1 + r_fijo) ** (n_fijo + n_var)) / ((1 + r_fijo) ** (n_fijo + n_var) - 1)

            pendiente = principal
            intereses_mixta = 0.0

            # Simula años fijos
            for _ in range(n_fijo):
                interes = pendiente * r_fijo
                amortizacion = cuota_fija - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            # Cuota variable con capital remanente
            if n_var > 0:
                cuota_variable = pendiente / n_var if r_var == 0 else pendiente * (r_var * (1 + r_var) ** n_var) / ((1 + r_var) ** n_var - 1)
            else:
                cuota_variable = 0.0

            # Simula años variables
            for _ in range(n_var):
                interes = pendiente * r_var
                amortizacion = cuota_variable - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            st.success("¡Cálculo realizado con éxito!")
            # Métricas principales
            c1, c2, c3 = st.columns(3)
            c1.metric("Cuota fija", f"{cuota_fija:,.2f} €")
            c2.metric("Cuota variable", f"{cuota_variable:,.2f} €")
            c3.metric("Intereses totales", f"{intereses_mixta:,.2f} €")

            st.divider()
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

            st.divider()
            st.write("### Evolución de capital pendiente e intereses")
            plot_evolucion_plotly(df_cuadro, "Evolución Hipoteca Mixta")
# =============================
# 2. PÁGINA HIPOTECA MIXTA (mejorada)
# =============================
elif pagina == "Hipoteca Mixta":
    st.title("Calculadora de Hipoteca Mixta")
    st.info("Simula una hipoteca con años a tipo fijo y años a tipo variable. Calcula cuotas, intereses y cuadro de amortización.")
    st.divider()

    years_fixed = st.number_input(
        "Años a tipo fijo:", min_value=1, max_value=40, value=10,
        help="Número de años iniciales con interés fijo."
    )
    years_total = st.number_input(
        "Años totales de la hipoteca:", min_value=years_fixed, max_value=40, value=20,
        help="Duración total de la hipoteca en años."
    )
    tipo_fijo = st.number_input(
        "Tipo de interés fijo (%):", min_value=-2.0, max_value=20.0, value=2.0, step=0.1,
        help="Interés aplicado durante los años fijos."
    )
    euribor = st.number_input(
        "Euribor estimado para los años variables (%):", min_value=-3.0, max_value=10.0, value=2.0, step=0.1,
        help="Estimación del Euríbor durante la fase variable."
    )
    diferencial = st.number_input(
        "Diferencial sobre euribor (%):", min_value=0.0, max_value=5.0, value=1.0, step=0.1,
        help="Porcentaje fijo que se suma al Euríbor en la fase variable."
    )
    principal = st.number_input(
        "Importe total (€):", min_value=1000.0, max_value=1_000_000.0, value=150000.0, step=1000.0,
        help="Cantidad total prestada por el banco."
    )

    # Validaciones y avisos
    if years_total < years_fixed:
        st.error("Los años totales no pueden ser menores que los años fijos.")
    if tipo_fijo < 0:
        st.warning("Tipo fijo negativo: escenario poco común, revisa el dato.")
    if euribor + diferencial < 0:
        st.info("Euríbor + diferencial negativo: podría dar cuotas menores; revisa si tu contrato tiene suelo.")

    st.divider()

    if st.button("Calcular", key="calcular_mixta"):
        n_fijo = int(years_fixed * 12)
        n_var = int((years_total - years_fixed) * 12)
        r_fijo = (tipo_fijo / 100) / 12
        r_var = ((euribor + diferencial) / 100) / 12

        if n_fijo + n_var <= 0:
            st.error("Plazo inválido.")
        else:
            # Cuota fase fija calculada a plazo completo (método clásico de mixtas comerciales)
            cuota_fija = principal / (n_fijo + n_var) if r_fijo == 0 else principal * (r_fijo * (1 + r_fijo) ** (n_fijo + n_var)) / ((1 + r_fijo) ** (n_fijo + n_var) - 1)

            pendiente = principal
            intereses_mixta = 0.0

            # Simula años fijos
            for _ in range(n_fijo):
                interes = pendiente * r_fijo
                amortizacion = cuota_fija - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            # Cuota variable con capital remanente
            if n_var > 0:
                cuota_variable = pendiente / n_var if r_var == 0 else pendiente * (r_var * (1 + r_var) ** n_var) / ((1 + r_var) ** n_var - 1)
            else:
                cuota_variable = 0.0

            # Simula años variables
            for _ in range(n_var):
                interes = pendiente * r_var
                amortizacion = cuota_variable - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            st.success("¡Cálculo realizado con éxito!")
            # Métricas principales
            c1, c2, c3 = st.columns(3)
            c1.metric("Cuota fija", f"{cuota_fija:,.2f} €")
            c2.metric("Cuota variable", f"{cuota_variable:,.2f} €")
            c3.metric("Intereses totales", f"{intereses_mixta:,.2f} €")

            st.divider()
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

            st.divider()
            st.write("### Evolución de capital pendiente e intereses")
            plot_evolucion_plotly(df_cuadro, "Evolución Hipoteca Mixta")
# =============================
# 2. PÁGINA HIPOTECA MIXTA (mejorada)
# =============================
elif pagina == "Hipoteca Mixta":
    st.title("Calculadora de Hipoteca Mixta")
    st.info("Simula una hipoteca con años a tipo fijo y años a tipo variable. Calcula cuotas, intereses y cuadro de amortización.")
    st.divider()

    years_fixed = st.number_input(
        "Años a tipo fijo:", min_value=1, max_value=40, value=10,
        help="Número de años iniciales con interés fijo."
    )
    years_total = st.number_input(
        "Años totales de la hipoteca:", min_value=years_fixed, max_value=40, value=20,
        help="Duración total de la hipoteca en años."
    )
    tipo_fijo = st.number_input(
        "Tipo de interés fijo (%):", min_value=-2.0, max_value=20.0, value=2.0, step=0.1,
        help="Interés aplicado durante los años fijos."
    )
    euribor = st.number_input(
        "Euribor estimado para los años variables (%):", min_value=-3.0, max_value=10.0, value=2.0, step=0.1,
        help="Estimación del Euríbor durante la fase variable."
    )
    diferencial = st.number_input(
        "Diferencial sobre euribor (%):", min_value=0.0, max_value=5.0, value=1.0, step=0.1,
        help="Porcentaje fijo que se suma al Euríbor en la fase variable."
    )
    principal = st.number_input(
        "Importe total (€):", min_value=1000.0, max_value=1_000_000.0, value=150000.0, step=1000.0,
        help="Cantidad total prestada por el banco."
    )

    # Validaciones y avisos
    if years_total < years_fixed:
        st.error("Los años totales no pueden ser menores que los años fijos.")
    if tipo_fijo < 0:
        st.warning("Tipo fijo negativo: escenario poco común, revisa el dato.")
    if euribor + diferencial < 0:
        st.info("Euríbor + diferencial negativo: podría dar cuotas menores; revisa si tu contrato tiene suelo.")

    st.divider()

    if st.button("Calcular", key="calcular_mixta"):
        n_fijo = int(years_fixed * 12)
        n_var = int((years_total - years_fixed) * 12)
        r_fijo = (tipo_fijo / 100) / 12
        r_var = ((euribor + diferencial) / 100) / 12

        if n_fijo + n_var <= 0:
            st.error("Plazo inválido.")
        else:
            # Cuota fase fija calculada a plazo completo (método clásico de mixtas comerciales)
            cuota_fija = principal / (n_fijo + n_var) if r_fijo == 0 else principal * (r_fijo * (1 + r_fijo) ** (n_fijo + n_var)) / ((1 + r_fijo) ** (n_fijo + n_var) - 1)

            pendiente = principal
            intereses_mixta = 0.0

            # Simula años fijos
            for _ in range(n_fijo):
                interes = pendiente * r_fijo
                amortizacion = cuota_fija - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            # Cuota variable con capital remanente
            if n_var > 0:
                cuota_variable = pendiente / n_var if r_var == 0 else pendiente * (r_var * (1 + r_var) ** n_var) / ((1 + r_var) ** n_var - 1)
            else:
                cuota_variable = 0.0

            # Simula años variables
            for _ in range(n_var):
                interes = pendiente * r_var
                amortizacion = cuota_variable - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            st.success("¡Cálculo realizado con éxito!")
            # Métricas principales
            c1, c2, c3 = st.columns(3)
            c1.metric("Cuota fija", f"{cuota_fija:,.2f} €")
            c2.metric("Cuota variable", f"{cuota_variable:,.2f} €")
            c3.metric("Intereses totales", f"{intereses_mixta:,.2f} €")

            st.divider()
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

            st.divider()
            st.write("### Evolución de capital pendiente e intereses")
            plot_evolucion_plotly(df_cuadro, "Evolución Hipoteca Mixta")
# =============================
# 2. PÁGINA HIPOTECA MIXTA (mejorada)
# =============================
elif pagina == "Hipoteca Mixta":
    st.title("Calculadora de Hipoteca Mixta")
    st.info("Simula una hipoteca con años a tipo fijo y años a tipo variable. Calcula cuotas, intereses y cuadro de amortización.")
    st.divider()

    years_fixed = st.number_input(
        "Años a tipo fijo:", min_value=1, max_value=40, value=10,
        help="Número de años iniciales con interés fijo."
    )
    years_total = st.number_input(
        "Años totales de la hipoteca:", min_value=years_fixed, max_value=40, value=20,
        help="Duración total de la hipoteca en años."
    )
    tipo_fijo = st.number_input(
        "Tipo de interés fijo (%):", min_value=-2.0, max_value=20.0, value=2.0, step=0.1,
        help="Interés aplicado durante los años fijos."
    )
    euribor = st.number_input(
        "Euribor estimado para los años variables (%):", min_value=-3.0, max_value=10.0, value=2.0, step=0.1,
        help="Estimación del Euríbor durante la fase variable."
    )
    diferencial = st.number_input(
        "Diferencial sobre euribor (%):", min_value=0.0, max_value=5.0, value=1.0, step=0.1,
        help="Porcentaje fijo que se suma al Euríbor en la fase variable."
    )
    principal = st.number_input(
        "Importe total (€):", min_value=1000.0, max_value=1_000_000.0, value=150000.0, step=1000.0,
        help="Cantidad total prestada por el banco."
    )

    # Validaciones y avisos
    if years_total < years_fixed:
        st.error("Los años totales no pueden ser menores que los años fijos.")
    if tipo_fijo < 0:
        st.warning("Tipo fijo negativo: escenario poco común, revisa el dato.")
    if euribor + diferencial < 0:
        st.info("Euríbor + diferencial negativo: podría dar cuotas menores; revisa si tu contrato tiene suelo.")

    st.divider()

    if st.button("Calcular", key="calcular_mixta"):
        n_fijo = int(years_fixed * 12)
        n_var = int((years_total - years_fixed) * 12)
        r_fijo = (tipo_fijo / 100) / 12
        r_var = ((euribor + diferencial) / 100) / 12

        if n_fijo + n_var <= 0:
            st.error("Plazo inválido.")
        else:
            # Cuota fase fija calculada a plazo completo (método clásico de mixtas comerciales)
            cuota_fija = principal / (n_fijo + n_var) if r_fijo == 0 else principal * (r_fijo * (1 + r_fijo) ** (n_fijo + n_var)) / ((1 + r_fijo) ** (n_fijo + n_var) - 1)

            pendiente = principal
            intereses_mixta = 0.0

            # Simula años fijos
            for _ in range(n_fijo):
                interes = pendiente * r_fijo
                amortizacion = cuota_fija - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            # Cuota variable con capital remanente
            if n_var > 0:
                cuota_variable = pendiente / n_var if r_var == 0 else pendiente * (r_var * (1 + r_var) ** n_var) / ((1 + r_var) ** n_var - 1)
            else:
                cuota_variable = 0.0

            # Simula años variables
            for _ in range(n_var):
                interes = pendiente * r_var
                amortizacion = cuota_variable - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            st.success("¡Cálculo realizado con éxito!")
            # Métricas principales
            c1, c2, c3 = st.columns(3)
            c1.metric("Cuota fija", f"{cuota_fija:,.2f} €")
            c2.metric("Cuota variable", f"{cuota_variable:,.2f} €")
            c3.metric("Intereses totales", f"{intereses_mixta:,.2f} €")

            st.divider()
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

            st.divider()
            st.write("### Evolución de capital pendiente e intereses")
            plot_evolucion_plotly(df_cuadro, "Evolución Hipoteca Mixta")
# =============================
# 2. PÁGINA HIPOTECA MIXTA (mejorada)
# =============================
elif pagina == "Hipoteca Mixta":
    st.title("Calculadora de Hipoteca Mixta")
    st.info("Simula una hipoteca con años a tipo fijo y años a tipo variable. Calcula cuotas, intereses y cuadro de amortización.")
    st.divider()

    years_fixed = st.number_input(
        "Años a tipo fijo:", min_value=1, max_value=40, value=10,
        help="Número de años iniciales con interés fijo."
    )
    years_total = st.number_input(
        "Años totales de la hipoteca:", min_value=years_fixed, max_value=40, value=20,
        help="Duración total de la hipoteca en años."
    )
    tipo_fijo = st.number_input(
        "Tipo de interés fijo (%):", min_value=-2.0, max_value=20.0, value=2.0, step=0.1,
        help="Interés aplicado durante los años fijos."
    )
    euribor = st.number_input(
        "Euribor estimado para los años variables (%):", min_value=-3.0, max_value=10.0, value=2.0, step=0.1,
        help="Estimación del Euríbor durante la fase variable."
    )
    diferencial = st.number_input(
        "Diferencial sobre euribor (%):", min_value=0.0, max_value=5.0, value=1.0, step=0.1,
        help="Porcentaje fijo que se suma al Euríbor en la fase variable."
    )
    principal = st.number_input(
        "Importe total (€):", min_value=1000.0, max_value=1_000_000.0, value=150000.0, step=1000.0,
        help="Cantidad total prestada por el banco."
    )

    # Validaciones y avisos
    if years_total < years_fixed:
        st.error("Los años totales no pueden ser menores que los años fijos.")
    if tipo_fijo < 0:
        st.warning("Tipo fijo negativo: escenario poco común, revisa el dato.")
    if euribor + diferencial < 0:
        st.info("Euríbor + diferencial negativo: podría dar cuotas menores; revisa si tu contrato tiene suelo.")

    st.divider()

    if st.button("Calcular", key="calcular_mixta"):
        n_fijo = int(years_fixed * 12)
        n_var = int((years_total - years_fixed) * 12)
        r_fijo = (tipo_fijo / 100) / 12
        r_var = ((euribor + diferencial) / 100) / 12

        if n_fijo + n_var <= 0:
            st.error("Plazo inválido.")
        else:
            # Cuota fase fija calculada a plazo completo (método clásico de mixtas comerciales)
            cuota_fija = principal / (n_fijo + n_var) if r_fijo == 0 else principal * (r_fijo * (1 + r_fijo) ** (n_fijo + n_var)) / ((1 + r_fijo) ** (n_fijo + n_var) - 1)

            pendiente = principal
            intereses_mixta = 0.0

            # Simula años fijos
            for _ in range(n_fijo):
                interes = pendiente * r_fijo
                amortizacion = cuota_fija - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            # Cuota variable con capital remanente
            if n_var > 0:
                cuota_variable = pendiente / n_var if r_var == 0 else pendiente * (r_var * (1 + r_var) ** n_var) / ((1 + r_var) ** n_var - 1)
            else:
                cuota_variable = 0.0

            # Simula años variables
            for _ in range(n_var):
                interes = pendiente * r_var
                amortizacion = cuota_variable - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            st.success("¡Cálculo realizado con éxito!")
            # Métricas principales
            c1, c2, c3 = st.columns(3)
            c1.metric("Cuota fija", f"{cuota_fija:,.2f} €")
            c2.metric("Cuota variable", f"{cuota_variable:,.2f} €")
            c3.metric("Intereses totales", f"{intereses_mixta:,.2f} €")

            st.divider()
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

            st.divider()
            st.write("### Evolución de capital pendiente e intereses")
            plot_evolucion_plotly(df_cuadro, "Evolución Hipoteca Mixta")
# =============================
# 2. PÁGINA HIPOTECA MIXTA (mejorada)
# =============================
elif pagina == "Hipoteca Mixta":
    st.title("Calculadora de Hipoteca Mixta")
    st.info("Simula una hipoteca con años a tipo fijo y años a tipo variable. Calcula cuotas, intereses y cuadro de amortización.")
    st.divider()

    years_fixed = st.number_input(
        "Años a tipo fijo:", min_value=1, max_value=40, value=10,
        help="Número de años iniciales con interés fijo."
    )
    years_total = st.number_input(
        "Años totales de la hipoteca:", min_value=years_fixed, max_value=40, value=20,
        help="Duración total de la hipoteca en años."
    )
    tipo_fijo = st.number_input(
        "Tipo de interés fijo (%):", min_value=-2.0, max_value=20.0, value=2.0, step=0.1,
        help="Interés aplicado durante los años fijos."
    )
    euribor = st.number_input(
        "Euribor estimado para los años variables (%):", min_value=-3.0, max_value=10.0, value=2.0, step=0.1,
        help="Estimación del Euríbor durante la fase variable."
    )
    diferencial = st.number_input(
        "Diferencial sobre euribor (%):", min_value=0.0, max_value=5.0, value=1.0, step=0.1,
        help="Porcentaje fijo que se suma al Euríbor en la fase variable."
    )
    principal = st.number_input(
        "Importe total (€):", min_value=1000.0, max_value=1_000_000.0, value=150000.0, step=1000.0,
        help="Cantidad total prestada por el banco."
    )

    # Validaciones y avisos
    if years_total < years_fixed:
        st.error("Los años totales no pueden ser menores que los años fijos.")
    if tipo_fijo < 0:
        st.warning("Tipo fijo negativo: escenario poco común, revisa el dato.")
    if euribor + diferencial < 0:
        st.info("Euríbor + diferencial negativo: podría dar cuotas menores; revisa si tu contrato tiene suelo.")

    st.divider()

    if st.button("Calcular", key="calcular_mixta"):
        n_fijo = int(years_fixed * 12)
        n_var = int((years_total - years_fixed) * 12)
        r_fijo = (tipo_fijo / 100) / 12
        r_var = ((euribor + diferencial) / 100) / 12

        if n_fijo + n_var <= 0:
            st.error("Plazo inválido.")
        else:
            # Cuota fase fija calculada a plazo completo (método clásico de mixtas comerciales)
            cuota_fija = principal / (n_fijo + n_var) if r_fijo == 0 else principal * (r_fijo * (1 + r_fijo) ** (n_fijo + n_var)) / ((1 + r_fijo) ** (n_fijo + n_var) - 1)

            pendiente = principal
            intereses_mixta = 0.0

            # Simula años fijos
            for _ in range(n_fijo):
                interes = pendiente * r_fijo
                amortizacion = cuota_fija - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            # Cuota variable con capital remanente
            if n_var > 0:
                cuota_variable = pendiente / n_var if r_var == 0 else pendiente * (r_var * (1 + r_var) ** n_var) / ((1 + r_var) ** n_var - 1)
            else:
                cuota_variable = 0.0

            # Simula años variables
            for _ in range(n_var):
                interes = pendiente * r_var
                amortizacion = cuota_variable - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            st.success("¡Cálculo realizado con éxito!")
            # Métricas principales
            c1, c2, c3 = st.columns(3)
            c1.metric("Cuota fija", f"{cuota_fija:,.2f} €")
            c2.metric("Cuota variable", f"{cuota_variable:,.2f} €")
            c3.metric("Intereses totales", f"{intereses_mixta:,.2f} €")

            st.divider()
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

            st.divider()
            st.write("### Evolución de capital pendiente e intereses")
            plot_evolucion_plotly(df_cuadro, "Evolución Hipoteca Mixta")
# =============================
# 2. PÁGINA HIPOTECA MIXTA (mejorada)
# =============================
elif pagina == "Hipoteca Mixta":
    st.title("Calculadora de Hipoteca Mixta")
    st.info("Simula una hipoteca con años a tipo fijo y años a tipo variable. Calcula cuotas, intereses y cuadro de amortización.")
    st.divider()

    years_fixed = st.number_input(
        "Años a tipo fijo:", min_value=1, max_value=40, value=10,
        help="Número de años iniciales con interés fijo."
    )
    years_total = st.number_input(
        "Años totales de la hipoteca:", min_value=years_fixed, max_value=40, value=20,
        help="Duración total de la hipoteca en años."
    )
    tipo_fijo = st.number_input(
        "Tipo de interés fijo (%):", min_value=-2.0, max_value=20.0, value=2.0, step=0.1,
        help="Interés aplicado durante los años fijos."
    )
    euribor = st.number_input(
        "Euribor estimado para los años variables (%):", min_value=-3.0, max_value=10.0, value=2.0, step=0.1,
        help="Estimación del Euríbor durante la fase variable."
    )
    diferencial = st.number_input(
        "Diferencial sobre euribor (%):", min_value=0.0, max_value=5.0, value=1.0, step=0.1,
        help="Porcentaje fijo que se suma al Euríbor en la fase variable."
    )
    principal = st.number_input(
        "Importe total (€):", min_value=1000.0, max_value=1_000_000.0, value=150000.0, step=1000.0,
        help="Cantidad total prestada por el banco."
    )

    # Validaciones y avisos
    if years_total < years_fixed:
        st.error("Los años totales no pueden ser menores que los años fijos.")
    if tipo_fijo < 0:
        st.warning("Tipo fijo negativo: escenario poco común, revisa el dato.")
    if euribor + diferencial < 0:
        st.info("Euríbor + diferencial negativo: podría dar cuotas menores; revisa si tu contrato tiene suelo.")

    st.divider()

    if st.button("Calcular", key="calcular_mixta"):
        n_fijo = int(years_fixed * 12)
        n_var = int((years_total - years_fixed) * 12)
        r_fijo = (tipo_fijo / 100) / 12
        r_var = ((euribor + diferencial) / 100) / 12

        if n_fijo + n_var <= 0:
            st.error("Plazo inválido.")
        else:
            # Cuota fase fija calculada a plazo completo (método clásico de mixtas comerciales)
            cuota_fija = principal / (n_fijo + n_var) if r_fijo == 0 else principal * (r_fijo * (1 + r_fijo) ** (n_fijo + n_var)) / ((1 + r_fijo) ** (n_fijo + n_var) - 1)

            pendiente = principal
            intereses_mixta = 0.0

            # Simula años fijos
            for _ in range(n_fijo):
                interes = pendiente * r_fijo
                amortizacion = cuota_fija - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            # Cuota variable con capital remanente
            if n_var > 0:
                cuota_variable = pendiente / n_var if r_var == 0 else pendiente * (r_var * (1 + r_var) ** n_var) / ((1 + r_var) ** n_var - 1)
            else:
                cuota_variable = 0.0

            # Simula años variables
            for _ in range(n_var):
                interes = pendiente * r_var
                amortizacion = cuota_variable - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            st.success("¡Cálculo realizado con éxito!")
            # Métricas principales
            c1, c2, c3 = st.columns(3)
            c1.metric("Cuota fija", f"{cuota_fija:,.2f} €")
            c2.metric("Cuota variable", f"{cuota_variable:,.2f} €")
            c3.metric("Intereses totales", f"{intereses_mixta:,.2f} €")

            st.divider()
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

            st.divider()
            st.write("### Evolución de capital pendiente e intereses")
            plot_evolucion_plotly(df_cuadro, "Evolución Hipoteca Mixta")
# =============================
# 2. PÁGINA HIPOTECA MIXTA (mejorada)
# =============================
elif pagina == "Hipoteca Mixta":
    st.title("Calculadora de Hipoteca Mixta")
    st.info("Simula una hipoteca con años a tipo fijo y años a tipo variable. Calcula cuotas, intereses y cuadro de amortización.")
    st.divider()

    years_fixed = st.number_input(
        "Años a tipo fijo:", min_value=1, max_value=40, value=10,
        help="Número de años iniciales con interés fijo."
    )
    years_total = st.number_input(
        "Años totales de la hipoteca:", min_value=years_fixed, max_value=40, value=20,
        help="Duración total de la hipoteca en años."
    )
    tipo_fijo = st.number_input(
        "Tipo de interés fijo (%):", min_value=-2.0, max_value=20.0, value=2.0, step=0.1,
        help="Interés aplicado durante los años fijos."
    )
    euribor = st.number_input(
        "Euribor estimado para los años variables (%):", min_value=-3.0, max_value=10.0, value=2.0, step=0.1,
        help="Estimación del Euríbor durante la fase variable."
    )
    diferencial = st.number_input(
        "Diferencial sobre euribor (%):", min_value=0.0, max_value=5.0, value=1.0, step=0.1,
        help="Porcentaje fijo que se suma al Euríbor en la fase variable."
    )
    principal = st.number_input(
        "Importe total (€):", min_value=1000.0, max_value=1_000_000.0, value=150000.0, step=1000.0,
        help="Cantidad total prestada por el banco."
    )

    # Validaciones y avisos
    if years_total < years_fixed:
        st.error("Los años totales no pueden ser menores que los años fijos.")
    if tipo_fijo < 0:
        st.warning("Tipo fijo negativo: escenario poco común, revisa el dato.")
    if euribor + diferencial < 0:
        st.info("Euríbor + diferencial negativo: podría dar cuotas menores; revisa si tu contrato tiene suelo.")

    st.divider()

    if st.button("Calcular", key="calcular_mixta"):
        n_fijo = int(years_fixed * 12)
        n_var = int((years_total - years_fixed) * 12)
        r_fijo = (tipo_fijo / 100) / 12
        r_var = ((euribor + diferencial) / 100) / 12

        if n_fijo + n_var <= 0:
            st.error("Plazo inválido.")
        else:
            # Cuota fase fija calculada a plazo completo (método clásico de mixtas comerciales)
            cuota_fija = principal / (n_fijo + n_var) if r_fijo == 0 else principal * (r_fijo * (1 + r_fijo) ** (n_fijo + n_var)) / ((1 + r_fijo) ** (n_fijo + n_var) - 1)

            pendiente = principal
            intereses_mixta = 0.0

            # Simula años fijos
            for _ in range(n_fijo):
                interes = pendiente * r_fijo
                amortizacion = cuota_fija - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            # Cuota variable con capital remanente
            if n_var > 0:
                cuota_variable = pendiente / n_var if r_var == 0 else pendiente * (r_var * (1 + r_var) ** n_var) / ((1 + r_var) ** n_var - 1)
            else:
                cuota_variable = 0.0

            # Simula años variables
            for _ in range(n_var):
                interes = pendiente * r_var
                amortizacion = cuota_variable - interes
                pendiente -= amortizacion
                intereses_mixta += interes

            st.success("¡Cálculo realizado con éxito!")
            # Métricas principales
            c1, c2, c3 = st.columns(3)
            c1.metric("Cuota fija", f"{cuota_fija:,.2f} €")
            c2.metric("Cuota variable", f"{cuota_variable:,.2f} €")
            c3.metric("Intereses totales", f"{intereses_mixta:,.2f} €")

            st.divider()
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

            st.divider()
            st.write("### Evolución de capital pendiente e intereses")
            plot_evolucion_plotly(df_cuadro, "Evolución Hipoteca Mixta")



# =============================
# 3. PÁGINA COMPARATIVA FIJA VS MIXTA
# =============================
elif pagina == "Comparativa Fija vs Mixta":
    st.title("Comparativa Hipoteca Fija vs Mixta")
    st.info("Compara intereses y evolución de dos hipotecas: una fija y una mixta.")
    st.divider()

    principal = st.number_input(
        "Importe total (€):",
        min_value=1000.0, max_value=1000000.0, value=150000.0, step=1000.0,
        help="Cantidad total prestada por el banco."
    )
    years_fija = st.number_input(
        "Años hipoteca fija:",
        min_value=1, max_value=40, value=20,
        help="Duración total de la hipoteca fija."
    )
    tipo_fijo = st.number_input(
        "Tipo interés fija (%):",
        min_value=0.0, max_value=20.0, value=3.0, step=0.1,
        help="Interés anual de la hipoteca fija."
    )
    years_fixed = st.number_input(
        "Años fijos (mixta):",
        min_value=1, max_value=40, value=10,
        help="Años iniciales a tipo fijo en la mixta."
    )
    years_total = st.number_input(
        "Años totales (mixta):",
        min_value=years_fixed, max_value=40, value=20,
        help="Duración total de la hipoteca mixta."
    )
    tipo_fijo_mixta = st.number_input(
        "Tipo fijo (mixta) (%):",
        min_value=0.0, max_value=20.0, value=2.0, step=0.1,
        help="Interés anual de la parte fija en la mixta."
    )
    euribor = st.number_input(
        "Euribor estimado (mixta) (%):",
        min_value=-2.0, max_value=10.0, value=2.0, step=0.1,
        help="Euríbor estimado para la parte variable."
    )
    diferencial = st.number_input(
        "Diferencial (mixta) (%):",
        min_value=0.0, max_value=5.0, value=1.0, step=0.1,
        help="Diferencial añadido al euríbor en la parte variable."
    )
    st.divider()

    if st.button("Comparar"):
        n_fija = int(years_fija * 12)
        r_fija = (tipo_fijo / 100) / 12
        cuota_fija = principal * (r_fija * (1 + r_fija) ** n_fija) / ((1 + r_fija) ** n_fija - 1)
        df_fija = cuadro_amortizacion_fija(principal, years_fija, r_fija, cuota_fija)
        intereses_fija = df_fija["Intereses pagados"].sum()

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

        st.success("¡Comparativa realizada!")
        st.write(f"**Intereses totales fija:** {intereses_fija:,.2f} €")
        st.write(f"**Intereses totales mixta:** {intereses_mixta:,.2f} €")

        st.divider()
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
    st.info("Simula cuánto te ahorras en intereses si haces una amortización anticipada en una hipoteca fija. Puedes elegir reducir plazo o cuota.")
    st.divider()

    years = st.number_input(
        "Años de la hipoteca:",
        min_value=1, max_value=40, value=20, key="aa_years",
        help="Plazo total de devolución del préstamo en años."
    )
    interest = st.number_input(
        "Tipo de interés anual (%):",
        min_value=0.0, max_value=20.0, value=3.0, step=0.1, key="aa_interest",
        help="Porcentaje fijo que aplica el banco cada año sobre el capital pendiente."
    )
    principal = st.number_input(
        "Importe total (€):",
        min_value=1000.0, max_value=1000000.0, value=150000.0, step=1000.0, key="aa_principal",
        help="Cantidad total que te presta el banco."
    )
    year_amort = st.number_input(
        "Año en que amortizas:",
        min_value=1, max_value=years, value=5,
        help="Año en el que realizarás la amortización anticipada."
    )
    importe_amort = st.number_input(
        "Importe a amortizar (€):",
        min_value=100.0, max_value=principal, value=10000.0, step=500.0,
        help="Cantidad que vas a amortizar anticipadamente."
    )
    tipo_amort = st.radio(
        "¿Qué quieres reducir?",
        ("Plazo", "Cuota"),
        help="Elige si prefieres reducir el plazo de la hipoteca o la cuota mensual."
    )
    st.divider()

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
            st.success(f"Nuevo plazo: {total_meses//12} años y {total_meses%12} meses")
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
            st.success(f"Nueva cuota: {nueva_cuota:,.2f} €")

        intereses_totales_con_amort = intereses_con_amort
        ahorro = intereses_totales_sin_amort - intereses_totales_con_amort

        st.write(f"**Intereses totales SIN amortizar:** {intereses_totales_sin_amort:,.2f} €")
        st.write(f"**Intereses totales CON amortización:** {intereses_totales_con_amort:,.2f} €")
        st.write(f"### ¡Ahorro en intereses! → {ahorro:,.2f} €")
        st.divider()

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
# =============================
# 5. PÁGINA COMPARADOR DE OFERTAS (AVANZADO)
# =============================
elif pagina == "Comparador de Ofertas":
    st.title("Comparador de Ofertas de Hipoteca")
    st.info("Compara ofertas teniendo en cuenta bonificaciones, comisión de apertura y amortizaciones parciales con su comisión.")

    # ---------- Helpers internos del comparador ----------
    def cuota_francesa(P, r, n):
        if n <= 0:
            return 0.0
        if r == 0:
            return P / n
        return P * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

    def simulate_offer(
        tipo, principal, years,
        # Fija
        tin_fija=None,
        # Mixta
        years_fixed=None, tin_fijo_mixta=None, euribor=None, diferencial=None,
        # Bonificaciones
        bonus_pp=0.0, bonus_cost_anual=0.0,
        # Comisiones
        com_apertura_pct=0.0, com_apertura_fija=0.0, com_amort_parcial_pct=0.0,
        # Amortizaciones parciales
        amortizaciones=None, # lista de dicts: {anio:int, importe:float, modo:str in {"Plazo","Cuota"}}
    ):
        """
        Devuelve: dict con métricas y un pequeño resumen.
        Simulación mes a mes con:
          - recalculo de cuota al pasar de fijo->variable (mixta)
          - amortizaciones parciales (reducir plazo o cuota)
          - comisiones (apertura y amortización)
          - costes anuales de bonificaciones hasta el último mes pagado
        """
        amortizaciones = amortizaciones or []
        # Normaliza y ordena eventos por mes
        events = []
        for ev in amortizaciones:
            mes = max(1, int(ev["anio"] * 12))
            events.append({"mes": mes, "importe": float(ev["importe"]), "modo": ev["modo"]})
        events.sort(key=lambda x: x["mes"])

        n_total = int(years * 12)

        # Construye el "rate schedule"
        schedule = []
        if tipo == "Fija":
            # TIN efectivo tras bonificación
            tin_eff = max(0.0, (tin_fija - bonus_pp)) / 100.0
            r_m = tin_eff / 12.0
            schedule = [(1, n_total, r_m)]
        else:
            # Mixta: reduce en p.p. tipo fijo y el diferencial de variable
            tin_fijo_eff = max(0.0, (tin_fijo_mixta - bonus_pp)) / 100.0
            diff_eff = max(0.0, (diferencial - bonus_pp)) / 100.0
            r_fijo_m = tin_fijo_eff / 12.0
            r_var_m = (max(-5.0, euribor) / 100.0 + diff_eff) / 12.0  # euríbor mínimo -5% por si acaso
            n_fijo = int(years_fixed * 12)
            n_var = n_total - n_fijo
            schedule = []
            if n_fijo > 0:
                schedule.append((1, n_fijo, r_fijo_m))
            if n_var > 0:
                schedule.append((n_fijo + 1, n_fijo + n_var, r_var_m))

        # Comisión de apertura
        com_apertura_eur = principal * (com_apertura_pct / 100.0) + com_apertura_fija

        # Simulación
        balance = principal
        intereses_tot = 0.0
        com_amort_parcial_tot = 0.0
        mes_actual = 1
        seg_idx = 0
        cuota_actual = 0.0
        meses_restantes = n_total
        meses_pagados = 0

        # Inicializa cuota para el primer segmento
        if schedule:
            r_seg = schedule[0][2]
            cuota_actual = cuota_francesa(balance, r_seg, meses_restantes)

        # Función para saber si cambia de segmento (entra variable) y recalcular cuota
        def maybe_recalc_by_segment(mes, balance, meses_restantes, cuota_actual):
            nonlocal seg_idx
            if seg_idx < len(schedule):
                start, end, r_seg = schedule[seg_idx]
                # Si estamos fuera del segmento actual, avanza
                while not (start <= mes <= end) and seg_idx + 1 < len(schedule):
                    seg_idx += 1
                    start, end, r_seg = schedule[seg_idx]
                # Si el mes es el inicio del segmento, recalcula cuota a ese r y plazo restante
                if mes == start:
                    cuota_nueva = cuota_francesa(balance, r_seg, meses_restantes)
                    return cuota_nueva, r_seg
                else:
                    return cuota_actual, r_seg
            return cuota_actual, 0.0

        # Función para aplicar amortización parcial en un mes
        def apply_amort_event_if_any(mes, balance, cuota_actual, meses_restantes, r_seg):
            nonlocal com_amort_parcial_tot
            # Busca eventos en este mes
            for ev in [e for e in events if e["mes"] == mes and balance > 0]:
                importe = min(ev["importe"], balance)
                if importe <= 0:
                    continue
                # Comisión por amortización
                com_amort_parcial_tot += importe * (com_amort_parcial_pct / 100.0)
                balance -= importe
                if balance < 0:
                    balance = 0.0
                # Si el modo es "Cuota", recalcula cuota para los meses restantes a r_seg
                if ev["modo"] == "Cuota":
                    cuota_nueva = cuota_francesa(balance, r_seg, meses_restantes)
                    return balance, cuota_nueva
                # Si es "Plazo", mantenemos cuota_actual (se acortará el plazo por agotarse antes)
            return balance, cuota_actual

        # Bucle de meses
        while balance > 1e-8 and meses_restantes > 0 and mes_actual <= n_total + 600:  # margen por si hay muchas reducciones de plazo
            cuota_actual, r_seg = maybe_recalc_by_segment(mes_actual, balance, meses_restantes, cuota_actual)

            # Amortización parcial en este mes (antes de calcular intereses)
            balance, cuota_actual = apply_amort_event_if_any(mes_actual, balance, cuota_actual, meses_restantes, r_seg)

            # Si llegó a cero tras amortización
            if balance <= 1e-8:
                break

            # Interés y capital de la cuota
            interes_mes = balance * r_seg
            capital_mes = max(0.0, cuota_actual - interes_mes)

            # Si la última cuota sobrepasa el balance, ajusta
            if capital_mes > balance:
                capital_mes = balance
                cuota_real = interes_mes + capital_mes
            else:
                cuota_real = cuota_actual

            intereses_tot += interes_mes
            balance -= capital_mes

            mes_actual += 1
            meses_restantes -= 1
            meses_pagados += 1

        # Coste anual de bonificaciones durante los años efectivamente pagados
        años_pagados = int(np.ceil(meses_pagados / 12.0))
        coste_bonis_total = años_pagados * bonus_cost_anual

        total_coste = intereses_tot + com_apertura_eur + com_amort_parcial_tot + coste_bonis_total

        # Cuota inicial (la del primer mes)
        cuota_inicial = cuota_actual
        if schedule:
            # Recalcula explícitamente la cuota del primer segmento y plazo completo
            r0 = schedule[0][2]
            cuota_inicial = cuota_francesa(principal, r0, n_total)

        return {
            "cuota_inicial": cuota_inicial,
            "intereses": intereses_tot,
            "coste_apertura": com_apertura_eur,
            "coste_amort_parcial": com_amort_parcial_tot,
            "coste_bonificaciones": coste_bonis_total,
            "total_coste": total_coste,
            "meses_pagados": meses_pagados
        }

    # ---------- UI del comparador ----------
    st.divider()
    num_ofertas = st.number_input("¿Cuántas ofertas quieres comparar?", min_value=2, max_value=6, value=2)

    ofertas_cfg = []
    for i in range(int(num_ofertas)):
        st.subheader(f"Oferta {i+1}")
        tipo = st.selectbox(f"Tipo de hipoteca {i+1}", ["Fija", "Mixta"], key=f"cmp_tipo_{i}")

        principal = st.number_input(
            f"Importe total {i+1} (€):", min_value=1000.0, max_value=1_000_000.0, value=150000.0, step=1000.0,
            key=f"cmp_principal_{i}", help="Capital solicitado."
        )
        years = st.number_input(
            f"Años {i+1}:", min_value=1, max_value=40, value=20, key=f"cmp_years_{i}",
            help="Plazo total en años."
        )

        # Bonificaciones por oferta
        with st.expander(f"Bonificaciones oferta {i+1}"):
            opciones = ["Seguro de vida", "Seguro de hogar", "Seguro de vivienda", "Nómina", "Gastos anuales", "Fondo", "Otro"]
            bonis = st.multiselect("Selecciona bonificaciones:", opciones, key=f"cmp_bonis_sel_{i}")
            bonus_pp_total = 0.0
            bonus_cost_anual = 0.0
            for b in bonis:
                nombre = st.text_input("Nombre", value=b if b != "Otro" else "", key=f"cmp_boni_nombre_{i}_{b}")
                coste = st.number_input(f"Sobrecoste anual de {nombre} (€):", min_value=0.0, value=0.0, step=50.0, key=f"cmp_boni_cost_{i}_{b}")
                bon_pp = st.number_input(f"Bonificación en tipo por {nombre} (p.p.):", min_value=0.0, max_value=3.0, value=0.10, step=0.01, key=f"cmp_boni_pp_{i}_{b}")
                bonus_pp_total += bon_pp
                bonus_cost_anual += coste

        # Comisiones de la oferta
        with st.expander(f"Comisiones oferta {i+1}"):
            com_apertura_pct = st.number_input("Comisión de apertura (% del capital):", min_value=0.0, max_value=5.0, value=0.0, step=0.05, key=f"cmp_apertura_pct_{i}")
            com_apertura_fija = st.number_input("Comisión de apertura fija (€):", min_value=0.0, max_value=10000.0, value=0.0, step=50.0, key=f"cmp_apertura_fix_{i}")
            com_amort_parcial_pct = st.number_input("Comisión amortización parcial (% del importe amortizado):", min_value=0.0, max_value=5.0, value=0.0, step=0.05, key=f"cmp_com_amort_{i}")

        # Amortizaciones parciales
        amortizaciones = []
        with st.expander(f"Amortizaciones parciales oferta {i+1} (opcional)"):
            n_amort = st.number_input("Número de amortizaciones parciales", min_value=0, max_value=12, value=0, key=f"cmp_n_amort_{i}")
            for j in range(int(n_amort)):
                colA, colB, colC = st.columns(3)
                with colA:
                    anio = st.number_input(f"Año amortización #{j+1}", min_value=1, max_value=years, value=min(5, years), key=f"cmp_amort_anio_{i}_{j}")
                with colB:
                    importe = st.number_input(f"Importe amortización #{j+1} (€)", min_value=0.0, max_value=principal, value=5000.0, step=500.0, key=f"cmp_amort_imp_{i}_{j}")
                with colC:
                    modo = st.selectbox(f"Modo #{j+1}", ["Plazo", "Cuota"], key=f"cmp_amort_modo_{i}_{j}")
                amortizaciones.append({"anio": anio, "importe": importe, "modo": modo})

        # Parámetros de tipo
        if tipo == "Fija":
            tin_fija = st.number_input(f"TIN fijo oferta {i+1} (%):", min_value=0.0, max_value=20.0, value=3.0, step=0.1, key=f"cmp_tin_fija_{i}")
            ofertas_cfg.append({
                "nombre": f"Oferta {i+1}", "tipo": tipo, "principal": principal, "years": years,
                "tin_fija": tin_fija, "bonus_pp": bonus_pp_total, "bonus_cost_anual": bonus_cost_anual,
                "com_apertura_pct": com_apertura_pct, "com_apertura_fija": com_apertura_fija,
                "com_amort_parcial_pct": com_amort_parcial_pct, "amortizaciones": amortizaciones
            })
        else:
            years_fixed = st.number_input(f"Años fijos oferta {i+1}:", min_value=1, max_value=years, value=min(10, years), key=f"cmp_years_fixed_{i}")
            tin_fijo_mixta = st.number_input(f"TIN fijo (fase fija) oferta {i+1} (%):", min_value=0.0, max_value=20.0, value=2.0, step=0.1, key=f"cmp_tin_fijo_m_{i}")
            euribor_ = st.number_input(f"Euríbor estimado fase variable oferta {i+1} (%):", min_value=-2.0, max_value=10.0, value=2.0, step=0.1, key=f"cmp_eur_{i}")
            diferencial_ = st.number_input(f"Diferencial oferta {i+1} (%):", min_value=0.0, max_value=5.0, value=1.0, step=0.1, key=f"cmp_diff_{i}")
            ofertas_cfg.append({
                "nombre": f"Oferta {i+1}", "tipo": tipo, "principal": principal, "years": years,
                "years_fixed": years_fixed, "tin_fijo_mixta": tin_fijo_mixta, "euribor": euribor_, "diferencial": diferencial_,
                "bonus_pp": bonus_pp_total, "bonus_cost_anual": bonus_cost_anual,
                "com_apertura_pct": com_apertura_pct, "com_apertura_fija": com_apertura_fija,
                "com_amort_parcial_pct": com_amort_parcial_pct, "amortizaciones": amortizaciones
            })

    st.divider()
    if st.button("Comparar ofertas (con costes y bonificaciones)"):
        resultados = []
        for cfg in ofertas_cfg:
            if cfg["tipo"] == "Fija":
                res = simulate_offer(
                    tipo="Fija",
                    principal=cfg["principal"], years=cfg["years"],
                    tin_fija=cfg["tin_fija"],
                    bonus_pp=cfg["bonus_pp"], bonus_cost_anual=cfg["bonus_cost_anual"],
                    com_apertura_pct=cfg["com_apertura_pct"], com_apertura_fija=cfg["com_apertura_fija"],
                    com_amort_parcial_pct=cfg["com_amort_parcial_pct"],
                    amortizaciones=cfg["amortizaciones"]
                )
            else:
                res = simulate_offer(
                    tipo="Mixta",
                    principal=cfg["principal"], years=cfg["years"],
                    years_fixed=cfg["years_fixed"], tin_fijo_mixta=cfg["tin_fijo_mixta"],
                    euribor=cfg["euribor"], diferencial=cfg["diferencial"],
                    bonus_pp=cfg["bonus_pp"], bonus_cost_anual=cfg["bonus_cost_anual"],
                    com_apertura_pct=cfg["com_apertura_pct"], com_apertura_fija=cfg["com_apertura_fija"],
                    com_amort_parcial_pct=cfg["com_amort_parcial_pct"],
                    amortizaciones=cfg["amortizaciones"]
                )

            resultados.append({
                "Oferta": cfg["nombre"],
                "Tipo": cfg["tipo"],
                "Cuota inicial (€)": res["cuota_inicial"],
                "Intereses totales (€)": res["intereses"],
                "Coste apertura (€)": res["coste_apertura"],
                "Coste amortizaciones (€)": res["coste_amort_parcial"],
                "Coste bonificaciones (€)": res["coste_bonificaciones"],
                "Coste total (€)": res["total_coste"],
                "Meses pagados": res["meses_pagados"]
            })

        df = pd.DataFrame(resultados)
        st.success("¡Comparativa completada!")
        st.write("### Resumen con costes incluidos")
        st.dataframe(df.style.format({
            "Cuota inicial (€)": "{:,.2f}",
            "Intereses totales (€)": "{:,.2f}",
            "Coste apertura (€)": "{:,.2f}",
            "Coste amortizaciones (€)": "{:,.2f}",
            "Coste bonificaciones (€)": "{:,.2f}",
            "Coste total (€)": "{:,.2f}"
        }), use_container_width=True)

        # Ranking por coste total
        df_sorted = df.sort_values("Coste total (€)")
        st.write("### Ranking por coste total (menor es mejor)")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_sorted["Oferta"], y=df_sorted["Coste total (€)"],
            marker_color=["#2ECC71" if i == 0 else "#3498DB" for i in range(len(df_sorted))]
        ))
        fig.update_layout(
            xaxis_title="Oferta",
            yaxis_title="Coste total (€)",
            hovermode="x",
            title="Coste total incluyendo intereses + apertura + amortizaciones + bonificaciones"
        )
        st.plotly_chart(fig, use_container_width=True)



# =============================
# 6. PÁGINA BONIFICACIONES
# =============================
elif pagina == "Bonificaciones":
    st.title("¿Compensa aceptar bonificaciones en tu hipoteca fija?")
    st.info("Analiza si contratar productos vinculados (seguros, nómina, fondos...) realmente te ahorra dinero en intereses o te sale más caro.")
    st.divider()

    years = st.number_input(
        "Años de la hipoteca:",
        min_value=1, max_value=40, value=20, key="boni_years",
        help="Plazo total de devolución del préstamo en años."
    )
    interest = st.number_input(
        "Tipo de interés SIN bonificaciones (%):",
        min_value=0.0, max_value=20.0, value=3.0, step=0.1, key="boni_interest",
        help="Porcentaje fijo que aplica el banco cada año sobre el capital pendiente, sin bonificaciones."
    )
    principal = st.number_input(
        "Importe total (€):",
        min_value=1000.0, max_value=1000000.0, value=150000.0, step=1000.0, key="boni_principal",
        help="Cantidad total que te presta el banco."
    )

    opciones = ["Seguro de vida", "Seguro de hogar", "Seguro de vivienda", "Nómina", "Gastos anuales", "Fondo", "Otro"]
    bonis = st.multiselect(
        "Selecciona las bonificaciones que quieres analizar:",
        opciones,
        help="Elige todos los productos que te exige el banco para bonificar el tipo de interés."
    )

    bonificaciones = []
    for b in bonis:
        st.subheader(f"{b}")
        if b == "Otro":
            nombre = st.text_input("Nombre de la bonificación", key=f"boni_nombre_{b}", help="Introduce el nombre del producto o gasto bonificado.")
        else:
            nombre = b
        sobrecoste = st.number_input(
            f"Sobrecoste anual de {nombre} (€):",
            min_value=0.0, value=0.0, step=50.0, key=f"boni_sc_{b}",
            help="Coste anual extra por contratar este producto."
        )
        bonifica = st.number_input(
            f"Bonificación en el tipo de interés de {nombre} (%):",
            min_value=0.0, max_value=2.0, value=0.1, step=0.01, key=f"boni_b_{b}",
            help="Cuánto baja el tipo de interés por este producto."
        )
        bonificaciones.append({
            "nombre": nombre,
            "sobrecoste": sobrecoste,
            "bonifica": bonifica
        })

    st.divider()

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

        st.success("¡Cálculo realizado!")
        st.write(f"**Intereses totales SIN bonificaciones:** {sum(intereses_anuales_sin):,.2f} €")
        st.write(f"**Intereses totales CON bonificaciones:** {sum(intereses_anuales_con):,.2f} €")
        st.write(f"**Sobrecoste anual total por bonificaciones:** {total_sobrecoste_anual:,.2f} €")

        st.divider()
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
    st.info("Compara el coste y el ahorro de cambiar tu hipoteca fija a otra entidad, incluyendo los gastos de subrogación.")
    st.divider()

    # --- Tu hipoteca actual
    st.header("Tu hipoteca actual")
    importe_inicial = st.number_input(
        "Importe inicial de la hipoteca (€):",
        min_value=1000.0, max_value=1_000_000.0, value=150000.0, step=1000.0, key="sub_imp_ini",
        help="Capital inicial prestado por el banco."
    )
    años_totales = st.number_input(
        "Años totales de la hipoteca:",
        min_value=1, max_value=40, value=20, key="sub_anios_tot",
        help="Plazo total desde el inicio."
    )
    tipo_actual = st.number_input(
        "Tipo de interés actual (%):",
        min_value=0.0, max_value=20.0, value=3.0, step=0.1, key="sub_tin_act",
        help="TIN actual de tu hipoteca."
    )
    año_actual = st.number_input(
        "Año en el que estás:",
        min_value=1, max_value=años_totales, value=7, key="sub_anio_act",
        help="Año transcurrido desde el inicio."
    )

    # Cálculo de capital pendiente hoy
    n_total = int(años_totales * 12)
    n_pasados = int((año_actual - 1) * 12)
    r_actual = (tipo_actual / 100) / 12
    cuota_actual = (importe_inicial / n_total) if r_actual == 0 else (
        importe_inicial * (r_actual * (1 + r_actual) ** n_total) / ((1 + r_actual) ** n_total - 1)
    )
    pendiente_hoy = importe_inicial
    for _ in range(n_pasados):
        interes_mes = pendiente_hoy * r_actual
        capital_mes = cuota_actual - interes_mes
        pendiente_hoy -= capital_mes
        if pendiente_hoy < 0:
            pendiente_hoy = 0.0

    st.write(f"**Capital pendiente estimado:** {pendiente_hoy:,.2f} €")
    st.divider()

    # --- Hipoteca alternativa
    st.header("Hipoteca alternativa (tras subrogación)")
    tipo_nuevo = st.number_input(
        "Tipo de interés alternativo (%):",
        min_value=0.0, max_value=20.0, value=2.0, step=0.1, key="sub_tin_new",
        help="TIN de la nueva hipoteca."
    )
    años_restantes = st.number_input(
        "Plazo restante (años):",
        min_value=1, max_value=40, value=max(1, años_totales - año_actual + 1), key="sub_anios_rest",
        help="Años que te quedarían por pagar tras subrogar."
    )
    gastos_subrogacion = st.number_input(
        "Coste de subrogación (€):",
        min_value=0.0, max_value=20000.0, value=1500.0, step=100.0, key="sub_gastos",
        help="Notaría, gestoría, tasación, etc."
    )

    st.divider()

    # Botón con key única
    if st.button("Comparar escenarios", key="sub_btn_compare"):
        # Validaciones rápidas
        if años_restantes <= 0 or pendiente_hoy <= 0:
            st.warning("Revisa los datos: plazo restante debe ser > 0 y el capital pendiente también.")
        else:
            with st.spinner("Calculando…"):
                n_restantes = int(años_restantes * 12)

                # Escenario 1: te quedas como estás
                intereses_restantes = 0.0
                cap_pend = pendiente_hoy
                for _ in range(n_restantes):
                    interes_mes = cap_pend * r_actual
                    capital_mes = cuota_actual - interes_mes
                    intereses_restantes += interes_mes
                    cap_pend -= capital_mes
                    if cap_pend < 0:
                        cap_pend = 0.0
                total_restante = intereses_restantes + pendiente_hoy

                # Escenario 2: subrogas
                r_nuevo = (tipo_nuevo / 100) / 12
                cuota_nueva = (pendiente_hoy / n_restantes) if r_nuevo == 0 else (
                    pendiente_hoy * (r_nuevo * (1 + r_nuevo) ** n_restantes) / ((1 + r_nuevo) ** n_restantes - 1)
                )
                intereses_nuevos = 0.0
                cap_pend = pendiente_hoy
                for _ in range(n_restantes):
                    interes_mes = cap_pend * r_nuevo
                    capital_mes = cuota_nueva - interes_mes
                    intereses_nuevos += interes_mes
                    cap_pend -= capital_mes
                    if cap_pend < 0:
                        cap_pend = 0.0
                total_nuevo = intereses_nuevos + pendiente_hoy + gastos_subrogacion

                ahorro_total = total_restante - total_nuevo

            st.success("¡Comparativa realizada!")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Escenario 1: No subrogas**")
                st.write(f"- Cuota mensual: {cuota_actual:,.2f} €")
                st.write(f"- Intereses por pagar: {intereses_restantes:,.2f} €")
                st.write(f"- Total a pagar (incl. capital): {total_restante:,.2f} €")
            with col2:
                st.write("**Escenario 2: Subrogas**")
                st.write(f"- Nueva cuota mensual: {cuota_nueva:,.2f} €")
                st.write(f"- Intereses por pagar: {intereses_nuevos:,.2f} €")
                st.write(f"- Total a pagar (capital + intereses + gastos): {total_nuevo:,.2f} €")

            st.write(f"### Ahorro total con la subrogación: {ahorro_total:,.2f} €")
            st.divider()

            # Grafico
            fig = go.Figure()



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
