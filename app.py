"""
app.py

Interfaz visual (Streamlit) del simulador de logística de emergencia.

Requerimientos:
    pip install streamlit plotly
    streamlit run app.py

Requiere en el mismo directorio: datos_recuperacion.py,
depositos_cercanos.py, motor.py, logo.png, fondo.png
"""

import base64

import streamlit as st
import plotly.graph_objects as go

from datos_recuperacion import NODOS, NOMBRES, COORDS
from motor import construir_escenario, resolver_optimo, resolver_heuristico

st.set_page_config(page_title="Q-SOS", page_icon="logo.png", layout="wide")


def _fondo_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


_fondo_b64 = _fondo_base64("fondo.png")
st.markdown(
    f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(10,14,39,0.78), rgba(10,14,39,0.78)),
                           url("data:image/png;base64,{_fondo_b64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    [data-testid="stHeader"] {{
        background: rgba(0,0,0,0);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    st.image("logo.png", width=90)
with col_titulo:
    st.markdown("## Q-SOS")
    st.caption("Simulador de respuesta a sismos — logística de emergencia, Junín, Perú")

nombres_ordenados = sorted(NOMBRES.values())
id_por_nombre = {v: k for k, v in NOMBRES.items()}

col_izq, col_der = st.columns([1, 2])

with col_izq:
    idx_default = nombres_ordenados.index("Chongos Bajo")
    nombre_destino = st.selectbox("Epicentro (destino)", nombres_ordenados, index=idx_default)
    destino = id_por_nombre[nombre_destino]
    n_dep = st.slider("Depósitos candidatos a considerar", 3, 10, 6)
    metodo = st.radio(
        "Método de resolución",
        ["Óptimo exacto (programación dinámica)", "Heurístico cuántico-híbrido (simulated annealing local)"],
    )
    calcular = st.button("Calcular envío", type="primary", use_container_width=True)
    comparar = st.button("Comparar ambos métodos", use_container_width=True)

    if calcular or comparar:
        escenario = construir_escenario(destino, n_depositos=n_dep)
        st.session_state["escenario"] = escenario
        if comparar:
            st.session_state["resultado_optimo"] = resolver_optimo(escenario)
            st.session_state["resultado_heuristico"] = resolver_heuristico(escenario)
            st.session_state["modo"] = "comparar"
        elif metodo.startswith("Óptimo"):
            st.session_state["resultado_optimo"] = resolver_optimo(escenario)
            st.session_state["resultado_heuristico"] = None
            st.session_state["modo"] = "optimo"
        else:
            st.session_state["resultado_heuristico"] = resolver_heuristico(escenario)
            st.session_state["resultado_optimo"] = None
            st.session_state["modo"] = "heuristico"

    if "escenario" in st.session_state and st.session_state["escenario"]["destino"] == destino:
        esc = st.session_state["escenario"]
        st.divider()

        def _mostrar(res, titulo):
            st.markdown(f"**{titulo}**")
            if res is None:
                st.error("No se encontró una asignación factible con esta flota candidata.")
                return
            c1, c2 = st.columns(2)
            c1.metric("Distancia total", f"{res['distancia_total']} km")
            c2.metric("Capacidad cubierta", f"{res['capacidad_cubierta']} / {esc['demanda_total']}")
            for (dep, t), cant in res["asignacion"].items():
                st.write(f"{NOMBRES[dep]} envía {cant}x {t} ({esc['distancia'][dep]} km)")

        if st.session_state.get("modo") == "comparar":
            c_izq, c_der = st.columns(2)
            with c_izq:
                _mostrar(st.session_state["resultado_optimo"], "Óptimo exacto (DP)")
            with c_der:
                _mostrar(st.session_state["resultado_heuristico"], "Heurístico cuántico-híbrido")
        elif st.session_state.get("modo") == "optimo":
            _mostrar(st.session_state["resultado_optimo"], "Óptimo exacto (DP)")
        elif st.session_state.get("modo") == "heuristico":
            _mostrar(st.session_state["resultado_heuristico"], "Heurístico cuántico-híbrido")

with col_der:
    fig = go.Figure()

    fig.add_trace(go.Scattermapbox(
        lat=[n[4] for n in NODOS], lon=[n[5] for n in NODOS],
        mode="markers", marker=dict(size=7, color="#5B6B8C"),
        text=[n[1] for n in NODOS], hoverinfo="text", name="Localidades",
    ))

    tiene_escenario = "escenario" in st.session_state and st.session_state["escenario"]["destino"] == destino
    color_por_metodo = {"optimo": "#5BC9CC", "heuristico": "#F2A623"}

    if tiene_escenario:
        esc = st.session_state["escenario"]
        dlat, dlon = COORDS[esc["destino"]]

        resultados_a_dibujar = []
        if st.session_state.get("modo") == "comparar":
            resultados_a_dibujar = [
                (st.session_state["resultado_optimo"], "optimo"),
                (st.session_state["resultado_heuristico"], "heuristico"),
            ]
        elif st.session_state.get("modo") == "optimo":
            resultados_a_dibujar = [(st.session_state["resultado_optimo"], "optimo")]
        elif st.session_state.get("modo") == "heuristico":
            resultados_a_dibujar = [(st.session_state["resultado_heuristico"], "heuristico")]

        for res, metodo_id in resultados_a_dibujar:
            if res is None:
                continue
            color = color_por_metodo[metodo_id]
            for (dep, t), cant in res["asignacion"].items():
                plat, plon = COORDS[dep]
                fig.add_trace(go.Scattermapbox(
                    lat=[plat, dlat], lon=[plon, dlon], mode="lines",
                    line=dict(width=1 + 2 * cant, color=color), showlegend=False,
                ))
                fig.add_trace(go.Scattermapbox(
                    lat=[plat], lon=[plon], mode="markers",
                    marker=dict(size=13, color=color),
                    text=[f"{NOMBRES[dep]} · {cant}x {t}"], hoverinfo="text", showlegend=False,
                ))

        fig.add_trace(go.Scattermapbox(
            lat=[dlat], lon=[dlon], mode="markers",
            marker=dict(size=17, color="#E24B4A"),
            text=[f"{NOMBRES[esc['destino']]} (epicentro)"], hoverinfo="text", name="Epicentro",
        ))
    else:
        dlat, dlon = COORDS[destino]
        fig.add_trace(go.Scattermapbox(
            lat=[dlat], lon=[dlon], mode="markers",
            marker=dict(size=17, color="#E24B4A"),
            text=[f"{NOMBRES[destino]} (epicentro)"], hoverinfo="text", name="Epicentro",
        ))

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox=dict(center=dict(lat=-12.0, lon=-75.25), zoom=9.3),
        margin=dict(l=0, r=0, t=0, b=0), height=650,
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    if tiene_escenario and st.session_state.get("modo") == "comparar":
        st.caption("Turquesa = óptimo exacto (DP) · Ámbar = heurístico cuántico-híbrido")

st.markdown(
    """
    <div style="text-align:center; margin-top:2.5rem; padding-top:1rem;
                border-top:1px solid rgba(255,255,255,0.15);">
        <span style="font-size:13px; color:rgba(255,255,255,0.7);">Developer by:</span><br>
        <span style="font-size:30px; font-weight:700; color:#5BC9CC;">Quantum Cooking</span>
    </div>
    """,
    unsafe_allow_html=True,
)
