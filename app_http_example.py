import streamlit as st
import pandas as pd
from http_client import (
    get_agentes_http, 
    get_agente_http, 
    add_agente_http, 
    update_agente_http, 
    delete_agente_http
)

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Gestión de Agentes (HTTP)",
    page_icon="👮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("Sistema de Gestión de Agentes (HTTP)")
st.write("Este es un ejemplo de cómo usar llamadas HTTP a la API para gestionar agentes")

# Verificar conexión con la API
try:
    agentes = get_agentes_http()
    if agentes:
        st.success("✅ Conexión con la API establecida correctamente")
    else:
        st.warning("⚠️ No se pudieron obtener datos de la API. Asegúrate de que la API esté en ejecución.")
except Exception as e:
    st.error(f"❌ Error al conectar con la API: {str(e)}")
    st.info("Asegúrate de ejecutar primero el servidor API con 'python run_api.py'")
    agentes = []

# Crear pestañas para las diferentes funcionalidades
tab_listar, tab_editar, tab_agregar = st.tabs(["Listado de Agentes", "Editar Agente", "Añadir Agente"])

with tab_listar:
    st.subheader("Listado de Agentes (vía HTTP)")
    
    # Botón para actualizar datos
    if st.button("🔄 Actualizar Datos", key="refresh_http"):
        st.cache_data.clear()
        agentes = get_agentes_http()
        st.success("Datos actualizados correctamente")
    
    # Convertir a DataFrame para mostrar
    if agentes:
        df = pd.DataFrame(agentes)
        
        # Convertir valores booleanos a texto para mejor visualización
        df["activo"] = df["activo"].map({1: "Sí", 0: "No"})
        df["monitor"] = df["monitor"].map({1: "Sí", 0: "No"})
        
        # Mostrar tabla
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No hay agentes disponibles o no se pudo conectar con la API")

with tab_editar:
    st.subheader("Editar Agente (vía HTTP)")
    
    if not agentes:
        st.warning("No se pudieron cargar los agentes. Verifica la conexión con la API.")
    else:
        # Selector de agente
        agentes_opciones = [f"{agente['nip']} - {agente['nombre_completo']}" for agente in agentes]
        agente_seleccionado = st.selectbox("Seleccionar Agente", [""] + agentes_opciones)
        
        if agente_seleccionado:
            # Obtener NIP del agente seleccionado
            nip_seleccionado = agente_seleccionado.split(" - ")[0]
            
            # Obtener datos del agente desde la API
            agente_data = get_agente_http(nip_seleccionado)
            
            if agente_data:
                with st.form("editar_agente_http_form"):
                    st.write(f"Editando Agente: {nip_seleccionado}")
                    
                    # Campos del formulario
                    nip = st.text_input("NIP", agente_data["nip"], disabled=True)
                    nombre = st.text_input("Nombre", agente_data["nombre"])
                    apellido1 = st.text_input("Apellido 1", agente_data["apellido1"])
                    apellido2 = st.text_input("Apellido 2", agente_data["apellido2"] if agente_data["apellido2"] else "")
                    
                    # Crear dos columnas para los campos adicionales
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        seccion = st.selectbox(
                            "Sección", 
                            ["", "Seguridad", "Atestados"], 
                            index=0 if not agente_data["seccion"] else 
                                  (1 if agente_data["seccion"] == "Seguridad" else 2)
                        )
                        activo = st.checkbox("Activo", bool(agente_data["activo"]))
                    
                    with col2:
                        grupo = st.selectbox(
                            "Grupo", 
                            ["", "G-1", "G-2"], 
                            index=0 if not agente_data["grupo"] else 
                                  (1 if agente_data["grupo"] == "G-1" else 2)
                        )
                        monitor = st.checkbox("Monitor", bool(agente_data["monitor"]))
                    
                    # Botones de acción
                    col_guardar, col_eliminar = st.columns(2)
                    
                    with col_guardar:
                        guardar = st.form_submit_button("Guardar Cambios")
                    
                    with col_eliminar:
                        eliminar = st.form_submit_button("Eliminar Agente", type="secondary")
                    
                    # Procesar acciones
                    if guardar:
                        # Actualizar agente mediante la API
                        success, result = update_agente_http(
                            nip, nombre, apellido1, apellido2, 
                            seccion, grupo, activo, monitor
                        )
                        
                        if success:
                            st.success(f"Agente {nip} actualizado correctamente")
                            st.cache_data.clear()  # Limpiar caché para actualizar datos
                        else:
                            st.error(f"Error al actualizar agente: {result}")
                    
                    if eliminar:
                        # Eliminar agente mediante la API
                        success, result = delete_agente_http(nip)
                        
                        if success:
                            st.success(f"Agente {nip} eliminado correctamente")
                            st.cache_data.clear()  # Limpiar caché para actualizar datos
                        else:
                            st.error(f"Error al eliminar agente: {result}")
            else:
                st.error("No se pudo obtener la información del agente desde la API")
        else:
            st.info("Selecciona un agente para editar sus datos")

with tab_agregar:
    st.subheader("Añadir Nuevo Agente (vía HTTP)")
    
    with st.form("agregar_agente_http_form"):
        # Campos del formulario
        nip = st.text_input("NIP", key="nuevo_nip_http")
        nombre = st.text_input("Nombre", key="nuevo_nombre_http")
        apellido1 = st.text_input("Apellido 1", key="nuevo_apellido1_http")
        apellido2 = st.text_input("Apellido 2", "", key="nuevo_apellido2_http")
        
        # Crear dos columnas para los campos adicionales
        col1, col2 = st.columns(2)
        
        with col1:
            seccion = st.selectbox("Sección", ["", "Seguridad", "Atestados"], key="nuevo_seccion_http")
            activo = st.checkbox("Activo", True, key="nuevo_activo_http")
        
        with col2:
            grupo = st.selectbox("Grupo", ["", "G-1", "G-2"], key="nuevo_grupo_http")
            monitor = st.checkbox("Monitor", False, key="nuevo_monitor_http")
        
        # Botón de guardar
        guardar = st.form_submit_button("Guardar Nuevo Agente")
        
        # Procesar formulario
        if guardar:
            # Validar campos obligatorios
            if not nip or not nombre or not apellido1:
                st.error("Los campos NIP, Nombre y Apellido 1 son obligatorios")
            else:
                # Añadir nuevo agente mediante la API
                success, result = add_agente_http(
                    nip, nombre, apellido1, apellido2, 
                    seccion, grupo, activo, monitor
                )
                
                if success:
                    st.success(f"Agente {nip} añadido correctamente")
                    st.cache_data.clear()  # Limpiar caché para actualizar datos
                else:
                    st.error(f"Error al añadir agente: {result}")

# Información adicional
st.divider()
st.subheader("Información sobre la API")
st.markdown("""
Esta aplicación se comunica con una API REST que proporciona acceso a la base de datos SQLite.

### Endpoints disponibles:

- **GET /agentes**: Obtiene todos los agentes
- **GET /agentes/{nip}**: Obtiene un agente específico por su NIP
- **POST /agentes**: Crea un nuevo agente
- **PUT /agentes/{nip}**: Actualiza un agente existente
- **DELETE /agentes/{nip}**: Elimina un agente

### Documentación completa:

La documentación interactiva de la API está disponible en [http://localhost:8000/docs](http://localhost:8000/docs) cuando el servidor API está en ejecución.
""")

# Instrucciones para ejecutar la API
st.info("Para ejecutar la API, abre una terminal y ejecuta: `python run_api.py`")
