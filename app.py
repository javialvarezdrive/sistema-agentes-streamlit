import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import os
from datetime import datetime, timedelta
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Gestión de Agentes",
    page_icon="👮",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.streamlit.io/community',
        'Report a bug': "https://github.com/streamlit/streamlit/issues",
        'About': "# Sistema de Gestión de Agentes\nAplicación para visualizar y analizar datos de actividades y agentes."
    }
)

# Conectar a SQLite
@st.cache_resource
def init_connection():
    return sqlite3.connect('sistema_agentes.db', check_same_thread=False)

conn = init_connection()

# Función para obtener la conexión a la base de datos
def get_db_connection():
    return sqlite3.connect('sistema_agentes.db', check_same_thread=False)

# Funciones para obtener datos
@st.cache_data(ttl=300)
def get_actividades():
    return pd.read_sql_query("SELECT * FROM actividades", conn)

@st.cache_data(ttl=300)
def get_agentes():
    conn = get_db_connection()
    query = """
    SELECT 
        nip, 
        nombre, 
        apellido1, 
        apellido2, 
        nombre || ' ' || apellido1 || CASE WHEN apellido2 IS NOT NULL THEN ' ' || apellido2 ELSE '' END as nombre_completo,
        seccion,
        grupo,
        activo,
        monitor
    FROM agentes
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=300)
def get_agentes_actividades():
    return pd.read_sql_query("SELECT * FROM agentes_actividades", conn)

@st.cache_data(ttl=300)
def get_cursos():
    return pd.read_sql_query("SELECT * FROM cursos", conn)

@st.cache_data(ttl=300)
def get_monitores():
    return pd.read_sql_query("SELECT * FROM monitores", conn)

@st.cache_data(ttl=300)
def get_turnos():
    return pd.read_sql_query("SELECT * FROM turno", conn)

@st.cache_data(ttl=300)
def get_vista_actividades_con_agentes():
    return pd.read_sql_query("SELECT * FROM vista_actividades_con_agentes", conn)

# Función para actualizar un agente
def update_agente(nip, nombre, apellido1, apellido2, seccion, grupo, activo, monitor):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE agentes 
        SET nombre = ?, apellido1 = ?, apellido2 = ?, seccion = ?, grupo = ?, activo = ?, monitor = ?
        WHERE nip = ?
        """,
        (nombre, apellido1, apellido2, seccion, grupo, activo, monitor, nip)
    )
    conn.commit()
    conn.close()

# Función para añadir un nuevo agente
def add_agente(nip, nombre, apellido1, apellido2, seccion, grupo, activo, monitor):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO agentes (nip, nombre, apellido1, apellido2, seccion, grupo, activo, monitor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (nip, nombre, apellido1, apellido2, seccion, grupo, activo, monitor)
        )
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

# Función para eliminar un agente
def delete_agente(nip):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM agentes WHERE nip = ?", (nip,))
    conn.commit()
    conn.close()

# Verificar si la base de datos existe
if not os.path.exists('sistema_agentes.db'):
    st.warning("La base de datos no existe. Ejecutando script de creación...")
    try:
        import create_sqlite_db
        create_sqlite_db.create_database()
        st.success("Base de datos creada con éxito. Recarga la página para ver los datos.")
        st.stop()
    except Exception as e:
        st.error(f"Error al crear la base de datos: {e}")
        st.stop()

# Obtener datos
try:
    actividades = get_actividades()
    agentes = get_agentes()
    agentes_actividades = get_agentes_actividades()
    cursos = get_cursos()
    monitores = get_monitores()
    turnos = get_turnos()
    
    # Intentar obtener la vista consolidada
    try:
        vista_actividades = get_vista_actividades_con_agentes()
        df_analisis = vista_actividades
    except Exception as e:
        st.warning(f"No se pudo cargar la vista consolidada: {e}")
        # Crear un dataframe de análisis manualmente
        df_actividades = actividades.merge(cursos, left_on='curso_id', right_on='id', suffixes=('', '_curso'))
        df_actividades = df_actividades.merge(turnos, left_on='turno_id', right_on='id', suffixes=('', '_turno'))
        
        # Contar agentes por actividad
        agentes_por_actividad = agentes_actividades.groupby('actividad_id').size().reset_index(name='total_agentes')
        df_analisis = df_actividades.merge(agentes_por_actividad, left_on='id', right_on='actividad_id', how='left')
        df_analisis['total_agentes'] = df_analisis['total_agentes'].fillna(0)
        
        # Añadir información de asistencia
        asistencia = agentes_actividades.groupby('actividad_id').agg(
            asistencia_confirmada=('asistencia', lambda x: (x == True).sum()),
            asistencia_pendiente=('asistencia', lambda x: x.isna().sum())
        ).reset_index()
        
        df_analisis = df_analisis.merge(asistencia, left_on='id', right_on='actividad_id', how='left')
        df_analisis['asistencia_confirmada'] = df_analisis['asistencia_confirmada'].fillna(0)
        df_analisis['asistencia_pendiente'] = df_analisis['asistencia_pendiente'].fillna(0)
        
        # Calcular porcentaje de asistencia
        df_analisis['asistencia_porcentaje'] = df_analisis.apply(
            lambda row: (row['asistencia_confirmada'] / row['total_agentes'] * 100) if row['total_agentes'] > 0 else 0, 
            axis=1
        )
        
        # Añadir campos temporales
        df_analisis['fecha'] = pd.to_datetime(df_analisis['fecha'])
        df_analisis['dia_semana'] = df_analisis['fecha'].dt.day_name()
        df_analisis['mes'] = df_analisis['fecha'].dt.month_name()
        df_analisis['anio'] = df_analisis['fecha'].dt.year
        df_analisis['semana_del_anio'] = df_analisis['fecha'].dt.isocalendar().week
        
        # Determinar estado
        hoy = datetime.now().date()
        df_analisis['estado'] = df_analisis['fecha'].apply(
            lambda x: 'Completada' if x.date() < hoy else ('En curso' if x.date() == hoy else 'Pendiente')
        )
    
    # Procesar los datos si están vacíos
    if actividades.empty or agentes.empty:
        st.error("No se pudieron cargar los datos. Verifica la base de datos SQLite.")
        st.stop()
        
    # Título de la aplicación
    st.title("Sistema de Gestión de Agentes")
    
    # Sidebar para filtros
    st.sidebar.header("Filtros")
    
    # Selector de vista
    vista_seleccionada = st.sidebar.radio("Seleccionar Vista", ["Actividades", "Gestión de Agentes"])
    
    if vista_seleccionada == "Actividades":
        # Filtro de fecha
        min_date = pd.to_datetime(actividades['fecha']).min() if not actividades.empty else datetime.now().date()
        max_date = pd.to_datetime(actividades['fecha']).max() if not actividades.empty else datetime.now().date()
        
        date_range = st.sidebar.date_input(
            "Rango de fechas",
            value=(
                min_date.date() if isinstance(min_date, pd.Timestamp) else min_date,
                max_date.date() if isinstance(max_date, pd.Timestamp) else max_date
            ),
            min_value=min_date.date() if isinstance(min_date, pd.Timestamp) else min_date,
            max_value=max_date.date() if isinstance(max_date, pd.Timestamp) else max_date
        )
        
        # Convertir a lista si es una tupla
        if isinstance(date_range, tuple):
            start_date, end_date = date_range
        else:
            start_date = end_date = date_range
        
        # Filtro de curso
        if 'nombre' in cursos.columns:
            curso_options = ['Todos'] + cursos['nombre'].tolist()
            curso_filtro = st.sidebar.selectbox("Curso", curso_options)
        else:
            curso_filtro = 'Todos'
        
        # Filtro de turno
        if 'nombre' in turnos.columns:
            turno_options = ['Todos'] + turnos['nombre'].tolist()
            turno_filtro = st.sidebar.selectbox("Turno", turno_options)
        else:
            turno_filtro = 'Todos'
        
        # Filtro de estado
        estado_options = ['Todos', 'Pendiente', 'En curso', 'Completada']
        estado_filtro = st.sidebar.selectbox("Estado", estado_options)
        
        # Aplicar filtros al dataframe de análisis
        df_filtrado = df_analisis.copy()
        
        # Filtro de fecha
        if 'fecha' in df_filtrado.columns:
            if isinstance(df_filtrado['fecha'].iloc[0], str):
                df_filtrado['fecha'] = pd.to_datetime(df_filtrado['fecha'])
            
            df_filtrado = df_filtrado[
                (df_filtrado['fecha'].dt.date >= start_date) & 
                (df_filtrado['fecha'].dt.date <= end_date)
            ]
        
        # Filtro de curso
        if curso_filtro != 'Todos':
            if 'curso_nombre' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['curso_nombre'] == curso_filtro]
            elif 'nombre_curso' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['nombre_curso'] == curso_filtro]
        
        # Filtro de turno
        if turno_filtro != 'Todos':
            if 'turno_nombre' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['turno_nombre'] == turno_filtro]
            elif 'nombre_turno' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['nombre_turno'] == turno_filtro]
        
        # Filtro de estado
        if estado_filtro != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['estado'] == estado_filtro]
        
        # Dashboard principal
        st.header("Dashboard de Actividades")
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Actividades", len(df_filtrado))
        
        with col2:
            total_agentes_asignados = df_filtrado['total_agentes'].sum()
            st.metric("Total Agentes Asignados", int(total_agentes_asignados))
        
        with col3:
            asistencia_confirmada = df_filtrado['asistencia_confirmada'].sum()
            st.metric("Asistencia Confirmada", int(asistencia_confirmada))
        
        with col4:
            if total_agentes_asignados > 0:
                porcentaje_asistencia = (asistencia_confirmada / total_agentes_asignados) * 100
            else:
                porcentaje_asistencia = 0
            st.metric("Porcentaje Asistencia", f"{porcentaje_asistencia:.2f}%")
        
        # Gráficos
        st.subheader("Análisis de Actividades")
        
        tab1, tab2, tab3 = st.tabs(["Actividades por Curso", "Asistencia por Día", "Distribución de Estados"])
        
        with tab1:
            # Actividades por curso
            if 'curso_nombre' in df_filtrado.columns:
                curso_col = 'curso_nombre'
            elif 'nombre_curso' in df_filtrado.columns:
                curso_col = 'nombre_curso'
            else:
                curso_col = None
                
            if curso_col:
                actividades_por_curso = df_filtrado.groupby(curso_col).size().reset_index(name='count')
                fig = px.bar(
                    actividades_por_curso, 
                    x=curso_col, 
                    y='count',
                    title='Actividades por Curso',
                    labels={'count': 'Número de Actividades', curso_col: 'Curso'},
                    color='count',
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            # Asistencia por día de la semana
            if 'dia_semana' in df_filtrado.columns:
                asistencia_por_dia = df_filtrado.groupby('dia_semana').agg({
                    'total_agentes': 'sum',
                    'asistencia_confirmada': 'sum'
                }).reset_index()
                
                asistencia_por_dia['porcentaje'] = (asistencia_por_dia['asistencia_confirmada'] / asistencia_por_dia['total_agentes'] * 100).fillna(0)
                
                # Ordenar días de la semana
                dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                dias_orden_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                
                # Mapear días en inglés a español si es necesario
                if asistencia_por_dia['dia_semana'].iloc[0] in dias_orden:
                    asistencia_por_dia['dia_semana'] = pd.Categorical(
                        asistencia_por_dia['dia_semana'], 
                        categories=dias_orden, 
                        ordered=True
                    )
                else:
                    asistencia_por_dia['dia_semana'] = pd.Categorical(
                        asistencia_por_dia['dia_semana'], 
                        categories=dias_orden_es, 
                        ordered=True
                    )
                    
                asistencia_por_dia = asistencia_por_dia.sort_values('dia_semana')
                
                fig = px.line(
                    asistencia_por_dia,
                    x='dia_semana',
                    y='porcentaje',
                    title='Porcentaje de Asistencia por Día de la Semana',
                    labels={'porcentaje': 'Porcentaje de Asistencia', 'dia_semana': 'Día de la Semana'},
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            # Distribución de estados
            estados_count = df_filtrado['estado'].value_counts().reset_index()
            estados_count.columns = ['Estado', 'Cantidad']
            
            fig = px.pie(
                estados_count,
                values='Cantidad',
                names='Estado',
                title='Distribución de Estados de Actividades',
                color='Estado',
                color_discrete_map={
                    'Pendiente': 'royalblue',
                    'En curso': 'gold',
                    'Completada': 'green'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Tabla de actividades
        st.subheader("Listado de Actividades")
        
        # Seleccionar columnas relevantes para mostrar
        columnas_mostrar = [
            'fecha', 
            'curso_nombre' if 'curso_nombre' in df_filtrado.columns else 'nombre_curso',
            'turno_nombre' if 'turno_nombre' in df_filtrado.columns else 'nombre_turno',
            'monitor_nombre' if 'monitor_nombre' in df_filtrado.columns else 'monitor_nip',
            'total_agentes',
            'asistencia_confirmada',
            'asistencia_pendiente',
            'asistencia_porcentaje',
            'estado'
        ]
        
        # Filtrar solo las columnas que existen
        columnas_mostrar = [col for col in columnas_mostrar if col in df_filtrado.columns]
        
        # Mostrar tabla
        st.dataframe(
            df_filtrado[columnas_mostrar].sort_values('fecha', ascending=False),
            use_container_width=True,
            hide_index=True
        )
        
    elif vista_seleccionada == "Gestión de Agentes":
        # Sección de gestión de agentes
        st.header("Gestión de Agentes")
        
        # Obtener datos de agentes
        agentes_df = get_agentes()
        
        # Crear pestañas para las diferentes funcionalidades
        tab_listar, tab_editar, tab_agregar = st.tabs(["Listado de Agentes", "Editar Agente", "Añadir Agente"])
        
        with tab_listar:
            # Mostrar tabla de agentes
            st.subheader("Listado Completo de Agentes")
            
            # Opciones de filtrado
            col1, col2, col3 = st.columns(3)
            with col1:
                filtro_seccion = st.selectbox("Filtrar por Sección", ["Todas", "Seguridad", "Atestados"])
            with col2:
                filtro_grupo = st.selectbox("Filtrar por Grupo", ["Todos", "G-1", "G-2"])
            with col3:
                filtro_activo = st.selectbox("Filtrar por Estado", ["Todos", "Activos", "Inactivos"])
            
            # Aplicar filtros
            agentes_filtrados = agentes_df.copy()
            
            if filtro_seccion != "Todas":
                agentes_filtrados = agentes_filtrados[agentes_filtrados["seccion"] == filtro_seccion]
            
            if filtro_grupo != "Todos":
                agentes_filtrados = agentes_filtrados[agentes_filtrados["grupo"] == filtro_grupo]
            
            if filtro_activo == "Activos":
                agentes_filtrados = agentes_filtrados[agentes_filtrados["activo"] == 1]
            elif filtro_activo == "Inactivos":
                agentes_filtrados = agentes_filtrados[agentes_filtrados["activo"] == 0]
            
            # Convertir valores booleanos a texto para mejor visualización
            agentes_display = agentes_filtrados.copy()
            agentes_display["activo"] = agentes_display["activo"].map({1: "Sí", 0: "No"})
            agentes_display["monitor"] = agentes_display["monitor"].map({1: "Sí", 0: "No"})
            
            # Renombrar columnas para mostrar
            agentes_display.columns = ["NIP", "Nombre", "Apellido 1", "Apellido 2", "Nombre Completo", "Sección", "Grupo", "Activo", "Monitor"]
            
            # Mostrar dataframe con datos filtrados
            st.dataframe(agentes_display, use_container_width=True, height=400)
            
            # Botón para actualizar datos
            if st.button("Actualizar Datos", key="actualizar_listado"):
                st.rerun()
        
        with tab_editar:
            st.subheader("Editar Agente Existente")
            
            # Selector de agente a editar
            agentes_opciones = [f"{nip} - {nombre}" for nip, nombre in zip(agentes_df["nip"], agentes_df["nombre_completo"])]
            agente_seleccionado = st.selectbox("Seleccionar Agente a Editar", [""] + agentes_opciones)
            
            if agente_seleccionado:
                # Obtener NIP del agente seleccionado
                nip_seleccionado = agente_seleccionado.split(" - ")[0]
                
                # Obtener datos del agente
                agente_data = agentes_df[agentes_df["nip"] == nip_seleccionado].iloc[0]
                
                # Formulario de edición
                with st.form("editar_agente_form"):
                    st.write(f"Editando Agente: {nip_seleccionado}")
                    
                    # Campos del formulario
                    nip = st.text_input("NIP", agente_data["nip"], disabled=True)
                    nombre = st.text_input("Nombre", agente_data["nombre"])
                    apellido1 = st.text_input("Apellido 1", agente_data["apellido1"])
                    apellido2 = st.text_input("Apellido 2", agente_data["apellido2"] if pd.notna(agente_data["apellido2"]) else "")
                    
                    # Crear dos columnas para los campos adicionales
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        seccion = st.selectbox(
                            "Sección", 
                            ["", "Seguridad", "Atestados"], 
                            index=0 if pd.isna(agente_data["seccion"]) else 
                                  (1 if agente_data["seccion"] == "Seguridad" else 2)
                        )
                        activo = st.checkbox("Activo", bool(agente_data["activo"]))
                    
                    with col2:
                        grupo = st.selectbox(
                            "Grupo", 
                            ["", "G-1", "G-2"], 
                            index=0 if pd.isna(agente_data["grupo"]) else 
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
                        # Convertir valores booleanos a enteros para SQLite
                        activo_int = 1 if activo else 0
                        monitor_int = 1 if monitor else 0
                        
                        # Actualizar agente
                        update_agente(nip, nombre, apellido1, apellido2, seccion, grupo, activo_int, monitor_int)
                        st.success(f"Agente {nip} actualizado correctamente")
                        st.rerun()
                    
                    if eliminar:
                        # Eliminar agente
                        delete_agente(nip)
                        st.success(f"Agente {nip} eliminado correctamente")
                        st.rerun()
            else:
                st.info("Selecciona un agente para editar sus datos")
        
        with tab_agregar:
            st.subheader("Añadir Nuevo Agente")
            
            # Formulario para añadir nuevo agente
            with st.form("agregar_agente_form"):
                # Campos del formulario
                nip = st.text_input("NIP", key="nuevo_nip")
                nombre = st.text_input("Nombre", key="nuevo_nombre")
                apellido1 = st.text_input("Apellido 1", key="nuevo_apellido1")
                apellido2 = st.text_input("Apellido 2", "", key="nuevo_apellido2")
                
                # Crear dos columnas para los campos adicionales
                col1, col2 = st.columns(2)
                
                with col1:
                    seccion = st.selectbox("Sección", ["", "Seguridad", "Atestados"], key="nuevo_seccion")
                    activo = st.checkbox("Activo", True, key="nuevo_activo")
                
                with col2:
                    grupo = st.selectbox("Grupo", ["", "G-1", "G-2"], key="nuevo_grupo")
                    monitor = st.checkbox("Monitor", False, key="nuevo_monitor")
                
                # Botón de guardar
                guardar = st.form_submit_button("Guardar Nuevo Agente")
                
                # Procesar formulario
                if guardar:
                    # Validar campos obligatorios
                    if not nip or not nombre or not apellido1:
                        st.error("Los campos NIP, Nombre y Apellido 1 son obligatorios")
                    else:
                        # Convertir valores booleanos a enteros para SQLite
                        activo_int = 1 if activo else 0
                        monitor_int = 1 if monitor else 0
                        
                        # Añadir nuevo agente
                        success = add_agente(nip, nombre, apellido1, apellido2, seccion, grupo, activo_int, monitor_int)
                        
                        if success:
                            st.success(f"Agente {nip} añadido correctamente")
                            # Limpiar formulario y cambiar a la pestaña de listado
                            st.rerun()
                        else:
                            st.error(f"Error al añadir agente. El NIP {nip} ya existe")
    
except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
    st.exception(e)
