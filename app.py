import streamlit as st
import pandas as pd
import problema

st.set_page_config(page_title="Asignacion Quirurgica", layout="wide")

# --- CSS Personalizado (Sin emojis, minimalista, estetico) ---
st.markdown("""
<style>
    .stApp {
        background-color: #FAFAFA;
        color: #2D3748;
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, h4 {
        color: #1A365D;
        font-weight: 600;
    }
    .stButton>button {
        background-color: #2B6CB0;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
        transition: background-color 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #2C5282;
        color: white;
    }
    .stButton>button:focus {
        box-shadow: none;
    }
    .card {
        background-color: white;
        padding: 2rem;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        margin-bottom: 1.5rem;
        border: 1px solid #E2E8F0;
    }
    .quirofano-card {
        background-color: #F7FAFC;
        padding: 1rem;
        border-radius: 6px;
        border-left: 4px solid #3182CE;
        margin-bottom: 1rem;
    }
    .cirugia-item {
        background-color: white;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        border: 1px solid #E2E8F0;
        margin-top: 0.5rem;
        display: flex;
        justify-content: space-between;
    }
</style>
""", unsafe_allow_html=True)

st.title("Optimizacion de Asignacion de Quirofanos")
st.markdown("Sistema para la programacion optima de cirugias considerando recursos, prioridades y bioseguridad.")

# --- INICIALIZACION DE ESTADO ---
if "cirugias" not in st.session_state:
    st.session_state.cirugias = []
if "cirujanos_counts" not in st.session_state:
    st.session_state.cirujanos_counts = {
        "Cirugia General": 0,
        "Cirugia Vascular": 0,
        "Cirugia Oncologica": 0,
        "Neurocirugia": 0
    }
if "recursos_soporte" not in st.session_state:
    st.session_state.recursos_soporte = {
        "anestesistas_g2": 6,
        "circulantes": 7,
        "instrumentistas": 8,
        "camas_preanest": 4
    }

ESPECIALIDADES = ["Cirugia General", "Cirugia Vascular", "Cirugia Oncologica", "Neurocirugia"]

# --- TABS PARA SEPARAR SECCIONES ---
tab_datos, tab_resultados = st.tabs(["Configuracion de Datos", "Optimizacion y Resultados"])

with tab_datos:
    st.header("Configuracion de Recursos y Demanda")
    
    col_personal, col_cirugias = st.columns([1, 2])
    
    with col_personal:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Personal Medico")
        
        st.markdown("**Cirujanos por Especialidad (Max 10 en total)**")
        for esp in ESPECIALIDADES:
            st.session_state.cirujanos_counts[esp] = st.number_input(
                esp, min_value=0, max_value=10, value=st.session_state.cirujanos_counts[esp], step=1
            )
        
        current_total_cirujanos = sum(st.session_state.cirujanos_counts.values())
        if current_total_cirujanos > 10:
            st.error(f"Limite excedido. Tienes {current_total_cirujanos} cirujanos (Maximo 10).")
        
        st.markdown("---")
        st.markdown("**Personal de Soporte**")
        st.session_state.recursos_soporte["anestesistas_g2"] = st.number_input("Anestesistas", 0, 20, st.session_state.recursos_soporte["anestesistas_g2"])
        st.session_state.recursos_soporte["circulantes"] = st.number_input("Circulantes", 0, 20, st.session_state.recursos_soporte["circulantes"])
        st.session_state.recursos_soporte["instrumentistas"] = st.number_input("Instrumentistas", 0, 20, st.session_state.recursos_soporte["instrumentistas"])
        st.session_state.recursos_soporte["camas_preanest"] = st.number_input("Camas de Preanestesia", 0, 20, st.session_state.recursos_soporte["camas_preanest"])
        st.markdown("</div>", unsafe_allow_html=True)

    with col_cirugias:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Demanda de Cirugias (Max 20)")
        
        with st.expander("Formulario para Nueva Cirugia", expanded=True):
            with st.form("form_add_cirugia"):
                c1, c2 = st.columns(2)
                with c1:
                    nombre_c = st.text_input("Nombre de la Cirugia")
                    especialidad_c = st.selectbox("Especialidad", ESPECIALIDADES)
                    contaminada_c = st.checkbox("Paciente Contaminado")
                with c2:
                    bloques_op_c = st.number_input("Duracion Operacion (bloques 30 min)", min_value=1, max_value=24, value=2)
                    bloques_limp_c = st.number_input("Duracion Limpieza (bloques 30 min)", min_value=1, max_value=10, value=1)
                    prioridad_c = st.select_slider("Prioridad Medica", options=[2, 3, 5, 7, 11], value=5)
                
                submitted = st.form_submit_button("Agregar Cirugia")
                if submitted:
                    if len(st.session_state.cirugias) >= 20:
                        st.error("Se ha alcanzado el limite de 20 cirugias.")
                    elif not nombre_c:
                        st.error("Debe ingresar un nombre para la cirugia.")
                    else:
                        new_id = max([c[0] for c in st.session_state.cirugias] + [0]) + 1
                        st.session_state.cirugias.append(
                            (new_id, nombre_c, bloques_op_c, bloques_limp_c, 1 if contaminada_c else 0, prioridad_c, especialidad_c)
                        )
                        st.success("Cirugia agregada exitosamente.")
                        st.rerun()
        
        if st.session_state.cirugias:
            df_cirugias = pd.DataFrame(st.session_state.cirugias, columns=["ID", "Nombre", "Blq. Operacion", "Blq. Limpieza", "Contaminada", "Prioridad", "Especialidad"])
            df_cirugias["Contaminada"] = df_cirugias["Contaminada"].map({1: "Si", 0: "No"})
            st.dataframe(df_cirugias, use_container_width=True, hide_index=True)
            
            if st.button("Limpiar Registro de Cirugias"):
                st.session_state.cirugias = []
                st.rerun()
        else:
            st.info("No hay cirugias registradas en el sistema.")
        st.markdown("</div>", unsafe_allow_html=True)


with tab_resultados:
    st.header("Ejecucion del Modelo y Planificacion")
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Parametros de Ejecucion")
    
    col_params, col_actions = st.columns([1, 1])
    
    with col_params:
        tiempo_limite_dict = {
            "30 segundos": 30,
            "1 minuto": 60,
            "2 minutos": 120,
            "5 minutos": 300
        }
        tiempo_seleccionado = st.selectbox("Tiempo limite de resolucion", list(tiempo_limite_dict.keys()), index=1)
        segundos_limite = tiempo_limite_dict[tiempo_seleccionado]
        
    with col_actions:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Prueba de Modelo (Datos por Defecto)", use_container_width=True):
            with st.spinner("Ejecutando modelo con datos precargados..."):
                cirugias_raw, cirujanos_raw, soporte = problema.obtener_datos_por_defecto()
                res = problema.optimizar_asignacion_quirofanos(
                    cirugias_raw, cirujanos_raw, soporte, max_seconds=60
                )
                st.session_state.last_result = res
                st.session_state.last_cirugias_input = cirugias_raw
                
        if st.button("Ejecutar Modelo con Datos Personalizados", type="primary", use_container_width=True):
            if len(st.session_state.cirugias) == 0:
                st.warning("Debes registrar cirugias en la pestaña de Configuracion.")
            elif current_total_cirujanos > 10:
                st.error("Corrige el limite de cirujanos antes de ejecutar.")
            else:
                with st.spinner(f"Optimizando asignaciones (Maximo {segundos_limite} seg)..."):
                    cirujanos_custom = []
                    c_idx = 1
                    for esp, count in st.session_state.cirujanos_counts.items():
                        for _ in range(count):
                            cirujanos_custom.append((f"C{c_idx}", f"Cirujano {c_idx} ({esp[:3]})", esp))
                            c_idx += 1
                    
                    res = problema.optimizar_asignacion_quirofanos(
                        st.session_state.cirugias, 
                        cirujanos_custom, 
                        st.session_state.recursos_soporte,
                        max_seconds=segundos_limite
                    )
                    st.session_state.last_result = res
                    st.session_state.last_cirugias_input = st.session_state.cirugias
    st.markdown("</div>", unsafe_allow_html=True)
    
    if "last_result" in st.session_state:
        res = st.session_state.last_result
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Resultados de Asignacion")
        
        status_color = "#38A169" if res["status"] in ["OPTIMAL", "FEASIBLE"] else "#E53E3E"
        st.markdown(f"**Estado del Modelo:** <span style='color:{status_color}; font-weight:bold;'>{res['status']}</span>", unsafe_allow_html=True)
        
        if res["status"] in ["OPTIMAL", "FEASIBLE"]:
            c1, c2 = st.columns(2)
            c1.metric("Valor Objetivo Alcanzado", f"{res['objetivo']:.1f}")
            c2.metric("Cirugias Planificadas", f"{len(res['programadas'])}")
            
            def slot_to_time(slot):
                mins = (slot - 1) * 30
                return f"{8 + mins // 60:02d}:{mins % 60:02d}"
                
            st.markdown("---")
            st.markdown("### Resumen Global de Demanda")
            
            input_data = st.session_state.get("last_cirugias_input", [])
            if input_data:
                df_input = pd.DataFrame(input_data, columns=["ID", "Nombre", "Blq. Operacion", "Blq. Limpieza", "Contaminada", "Prioridad", "Especialidad"])
                asignadas = { p["id"]: p for p in res["programadas"] }
                
                def get_q(cid): return f"Q{asignadas[cid]['quirofano']}" if cid in asignadas else "No Asignada"
                
                def get_horario(cid):
                    if cid in asignadas:
                        h_ini = slot_to_time(asignadas[cid]["inicio"])
                        h_fin = slot_to_time(asignadas[cid]["fin_limpieza"])
                        return f"{h_ini} - {h_fin}"
                    return "—"
                    
                df_input["Asignada a"] = df_input["ID"].apply(get_q)
                df_input["Horario"] = df_input["ID"].apply(get_horario)
                df_input["Contaminada"] = df_input["Contaminada"].map({1: "Sí", 0: "No"})
                
                st.dataframe(df_input, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("### Detalle por Quirofano")
            
            df_res = pd.DataFrame(res["programadas"])
            
            if df_res.empty:
                st.info("No se programó ninguna cirugía con la configuración actual.")
            else:
                # Agrupar por quirofano para mostrar de forma organizada
                quirofanos_usados = sorted(df_res["quirofano"].unique())
                
                for q in quirofanos_usados:
                    st.markdown(f"<div class='quirofano-card'><h4>Quirofano {q}</h4>", unsafe_allow_html=True)
                    cirugias_q = df_res[df_res["quirofano"] == q].sort_values(by="inicio")
                    
                    for _, row in cirugias_q.iterrows():
                        hora_inicio = slot_to_time(row["inicio"])
                        hora_fin = slot_to_time(row["fin_limpieza"])
                        contam_badge = "<span style='color: #E53E3E; font-weight: bold;'>[Contaminada: Si]</span>" if row["contaminada"] else "<span style='color: #38A169; font-weight: bold;'>[Contaminada: No]</span>"
                        
                        st.markdown(f"""
                        <div class='cirugia-item'>
                            <div>
                                <strong>{hora_inicio} - {hora_fin}</strong> | {row['nombre']} {contam_badge}
                            </div>
                            <div style='color: #718096; font-size: 0.9em;'>
                                {row['cirujano_nombre']} | {row['especialidad']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
        else:
            st.error("El modelo no logro encontrar una solucion con los recursos proporcionados.")
        st.markdown("</div>", unsafe_allow_html=True)
