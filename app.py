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
    conn = sqlite3.connect('sistema_agentes.db')
    conn.row_factory = sqlite3.Row
    return conn

# Función auxiliar para filtrar agentes por búsqueda
def filtrar_agentes_por_busqueda(df, busqueda):
    if not busqueda:
        return df
    
    busqueda_lower = busqueda.lower()
    mask = (
        df["nip"].str.lower().str.contains(busqueda_lower) | 
        df["nombre_completo"].str.lower().str.contains(busqueda_lower)
    )
    return df[mask]

# Función para actualizar la búsqueda de agentes (callback)
def actualizar_busqueda_agentes():
    # Esta función se llama cuando cambia el texto de búsqueda
    st.session_state.agentes_filtrados_busqueda = filtrar_agentes_por_busqueda(
        st.session_state.agentes_df_original, 
        st.session_state.texto_busqueda_agentes
    )

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
        grupo
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
    conn = get_db_connection()
    query = "SELECT * FROM cursos ORDER BY nombre"
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Error al obtener cursos: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

@st.cache_data(ttl=300)
def get_monitores():
    conn = get_db_connection()
    query = """
    SELECT 
        nip, 
        nombre, 
        apellido1, 
        apellido2, 
        nombre || ' ' || apellido1 || CASE WHEN apellido2 IS NOT NULL THEN ' ' || apellido2 ELSE '' END as nombre_completo
    FROM monitores
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=300)
def get_turnos():
    return pd.read_sql_query("SELECT * FROM turno", conn)

@st.cache_data(ttl=300)
def get_vista_actividades_con_agentes():
    return pd.read_sql_query("SELECT * FROM vista_actividades_con_agentes", conn)

# Función para obtener detalles de una actividad específica
def get_actividad_detalle(actividad_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT a.id, a.fecha, a.turno_id, a.monitor_nip, a.curso_id, a.notas,
           t.nombre as turno_nombre, c.nombre as curso_nombre,
           m.nombre || ' ' || m.apellido1 || CASE WHEN m.apellido2 IS NOT NULL THEN ' ' || m.apellido2 ELSE '' END as monitor_nombre
    FROM actividades a
    JOIN turno t ON a.turno_id = t.id
    JOIN cursos c ON a.curso_id = c.id
    LEFT JOIN monitores m ON a.monitor_nip = m.nip
    WHERE a.id = ?
    """
    
    try:
        cursor.execute(query, (actividad_id,))
        row = cursor.fetchone()
        
        if row:
            # Convertir a diccionario
            columns = [col[0] for col in cursor.description]
            actividad = dict(zip(columns, row))
            return actividad
        else:
            return None
    except Exception as e:
        st.error(f"Error al obtener detalles de la actividad: {e}")
        return None
    finally:
        conn.close()

# Función para obtener actividades con detalles adicionales
@st.cache_data(ttl=300)
def get_actividades_detalle():
    conn = get_db_connection()
    query = """
    SELECT 
        a.id,
        a.fecha,
        a.turno_id,
        t.nombre as turno_nombre,
        a.monitor_nip,
        m.nombre || ' ' || m.apellido1 || CASE WHEN m.apellido2 IS NOT NULL THEN ' ' || m.apellido2 ELSE '' END as monitor_nombre,
        a.curso_id,
        c.nombre as curso_nombre,
        a.notas,
        (SELECT COUNT(*) FROM agentes_actividades aa WHERE aa.actividad_id = a.id) as total_agentes
    FROM actividades a
    JOIN turno t ON a.turno_id = t.id
    JOIN cursos c ON a.curso_id = c.id
    LEFT JOIN monitores m ON a.monitor_nip = m.nip
    ORDER BY a.fecha DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Función para añadir un nuevo curso
def add_curso(nombre, descripcion=""):
    """Añade un nuevo curso con descripción opcional"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO cursos (nombre, descripcion) VALUES (?, ?)", (nombre, descripcion))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error al añadir curso: {e}")
        return False
    finally:
        conn.close()

# Función para añadir una nueva actividad
def add_actividad(fecha, turno_id, monitor_nip, curso_id, notas=None):
    """Añade una nueva actividad y devuelve su ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        st.write(f"Debug - Intentando insertar: fecha={fecha}, turno_id={turno_id}, monitor_nip={monitor_nip}, curso_id={curso_id}, notas={notas}")
        cursor.execute(
            "INSERT INTO actividades (fecha, turno_id, monitor_nip, curso_id, notas) VALUES (?, ?, ?, ?, ?)",
            (fecha, turno_id, monitor_nip, curso_id, notas)
        )
        actividad_id = cursor.lastrowid
        st.write(f"Debug - ID generado: {actividad_id}")
        conn.commit()
        st.write("Debug - Commit realizado")
        return True, actividad_id
    except Exception as e:
        st.error(f"Error al añadir actividad: {e}")
        st.write(f"Debug - Excepción detallada: {type(e).__name__}: {str(e)}")
        return False, None
    finally:
        conn.close()

# Función para obtener los agentes asignados a una actividad
@st.cache_data(ttl=300)
def get_agentes_por_actividad(actividad_id):
    """Obtiene los agentes asignados a una actividad específica"""
    conn = get_db_connection()
    query = """
    SELECT 
        a.nip, 
        a.nombre, 
        a.apellido1, 
        a.apellido2,
        a.seccion,
        a.grupo,
        a.nombre || ' ' || a.apellido1 || CASE WHEN a.apellido2 IS NOT NULL THEN ' ' || a.apellido2 ELSE '' END as nombre_completo,
        aa.asistencia
    FROM agentes a
    JOIN agentes_actividades aa ON a.nip = aa.agente_nip
    WHERE aa.actividad_id = ?
    ORDER BY a.seccion, a.grupo, a.apellido1, a.nombre
    """
    df = pd.read_sql_query(query, conn, params=(actividad_id,))
    conn.close()
    return df

# Función para asignar un agente a una actividad
def asignar_agente_actividad(agente_nip, actividad_id, asistencia=None):
    """Asigna un agente a una actividad"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Verificar si ya existe la asignación
        cursor.execute(
            "SELECT COUNT(*) FROM agentes_actividades WHERE actividad_id = ? AND agente_nip = ?",
            (actividad_id, agente_nip)
        )
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Insertar nueva asignación
            cursor.execute(
                "INSERT INTO agentes_actividades (actividad_id, agente_nip, asistencia) VALUES (?, ?, ?)",
                (actividad_id, agente_nip, asistencia if asistencia is not None else 0)
            )
            conn.commit()
            return True
        else:
            return False  # Ya existe la asignación
    except Exception as e:
        st.error(f"Error al asignar agente a actividad: {e}")
        return False
    finally:
        conn.close()

# Función para eliminar un agente de una actividad
def desasignar_agente_actividad(agente_nip, actividad_id):
    """Elimina un agente de una actividad"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM agentes_actividades WHERE actividad_id = ? AND agente_nip = ?",
            (actividad_id, agente_nip)
        )
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error al eliminar agente de actividad: {e}")
        return False
    finally:
        conn.close()

# Función para actualizar la asistencia de un agente a una actividad
def actualizar_asistencia_agente(actividad_id, agente_nip, asistencia):
    """Actualiza el estado de asistencia de un agente a una actividad"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE agentes_actividades SET asistencia = ? WHERE actividad_id = ? AND agente_nip = ?",
            (asistencia, actividad_id, agente_nip)
        )
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error al actualizar asistencia: {e}")
        return False
    finally:
        conn.close()

# Función para eliminar una actividad
def delete_actividad(actividad_id):
    """Elimina una actividad y todas sus asignaciones de agentes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Primero eliminamos todas las asignaciones de agentes a esta actividad
        cursor.execute(
            "DELETE FROM agentes_actividades WHERE actividad_id = ?",
            (actividad_id,)
        )
        
        # Luego eliminamos la actividad
        cursor.execute(
            "DELETE FROM actividades WHERE id = ?",
            (actividad_id,)
        )
        
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error al eliminar la actividad: {e}")
        return False
    finally:
        conn.close()

# Función para actualizar una actividad
def update_actividad(actividad_id, fecha, turno_id, monitor_nip, curso_id, notas=None):
    """Actualiza los datos de una actividad existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE actividades 
            SET fecha = ?, turno_id = ?, monitor_nip = ?, curso_id = ?, notas = ?
            WHERE id = ?
            """,
            (fecha, turno_id, monitor_nip, curso_id, notas, actividad_id)
        )
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error al actualizar actividad: {e}")
        return False
    finally:
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
    vista_seleccionada = st.sidebar.radio("Seleccionar Vista", ["Actividades", "Gestión de Agentes", "Gestión de Monitores", "Cursos"])
    
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
            'id',
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
        df_filtrado['fecha'] = df_filtrado['fecha'].apply(lambda x: x.strftime('%d/%m/%Y') if isinstance(x, pd.Timestamp) else x)
        st.dataframe(
            df_filtrado[columnas_mostrar].sort_values('fecha', ascending=False),
            use_container_width=True,
            hide_index=False
        )
        
    elif vista_seleccionada == "Gestión de Agentes":
        # Sección de gestión de agentes
        st.header("Gestión de Agentes")
        
        # Obtener datos de agentes
        agentes_df = get_agentes()
        
        # Inicializar estados de sesión si no existen
        if 'agentes_df_original' not in st.session_state:
            st.session_state.agentes_df_original = agentes_df.copy()
        
        if 'agentes_filtrados_busqueda' not in st.session_state:
            st.session_state.agentes_filtrados_busqueda = agentes_df.copy()
        
        if 'texto_busqueda_agentes' not in st.session_state:
            st.session_state.texto_busqueda_agentes = ""
        
        # Función para actualizar la búsqueda de agentes (callback)
        def actualizar_busqueda_agentes():
            busqueda = st.session_state.texto_busqueda_agentes.lower()
            if busqueda:
                # Filtrar por NIP o nombre
                st.session_state.agentes_filtrados_busqueda = st.session_state.agentes_df_original[
                    st.session_state.agentes_df_original["nip"].str.lower().str.contains(busqueda) | 
                    st.session_state.agentes_df_original["nombre_completo"].str.lower().str.contains(busqueda)
                ]
            else:
                # Si no hay búsqueda, mostrar todos
                st.session_state.agentes_filtrados_busqueda = st.session_state.agentes_df_original.copy()
        
        # Opciones de filtrado
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filtro_seccion = st.selectbox("Filtrar por Sección", ["Todas", "Seguridad", "Atestados"])
        with col2:
            filtro_grupo = st.selectbox("Filtrar por Grupo", ["Todos", "G-1", "G-2"])
        with col3:
            # Buscador con comportamiento AJAX
            st.text_input(
                "Buscar por NIP o Nombre", 
                key="texto_busqueda_agentes",
                on_change=actualizar_busqueda_agentes,
                help="Escribe para filtrar agentes en tiempo real"
            )
            
            # Añadir indicador visual de búsqueda activa
            if st.session_state.texto_busqueda_agentes:
                st.caption(f"🔍 Buscando: '{st.session_state.texto_busqueda_agentes}'")
        
        # Aplicar filtros de sección y grupo a los resultados ya filtrados por búsqueda
        agentes_filtrados = st.session_state.agentes_filtrados_busqueda.copy()
        
        if filtro_seccion != "Todas":
            agentes_filtrados = agentes_filtrados[agentes_filtrados["seccion"] == filtro_seccion]
        
        if filtro_grupo != "Todos":
            agentes_filtrados = agentes_filtrados[agentes_filtrados["grupo"] == filtro_grupo]
        
        # Mostrar contador de resultados con estilo mejorado
        if len(agentes_filtrados) == 0:
            st.warning(f"No se encontraron agentes con los criterios de búsqueda")
        elif len(agentes_filtrados) < len(agentes_df):
            st.success(f"Mostrando {len(agentes_filtrados)} de {len(agentes_df)} agentes")
        else:
            st.info(f"Mostrando todos los agentes ({len(agentes_filtrados)})")
        
        # Renombrar columnas para mostrar
        agentes_display = agentes_filtrados.copy()
        agentes_display.columns = ["NIP", "Nombre", "Apellido 1", "Apellido 2", "Nombre Completo", "Sección", "Grupo"]
        
        # Mostrar dataframe con datos filtrados
        st.dataframe(agentes_display, use_container_width=True, height=400)
        
        # Botón para limpiar filtros
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Limpiar Filtros", key="limpiar_filtros_agentes"):
                st.session_state.texto_busqueda_agentes = ""
                st.session_state.agentes_filtrados_busqueda = st.session_state.agentes_df_original.copy()
                st.rerun()
        
        # Crear pestañas para las diferentes funcionalidades
        tab_listar, tab_editar, tab_agregar = st.tabs(["Listado de Agentes", "Editar Agente", "Añadir Agente"])
        
        with tab_listar:
            # Mostrar tabla de agentes
            st.subheader("Listado Completo de Agentes")
            
            # Mostrar dataframe con datos filtrados
            st.dataframe(agentes_display, use_container_width=True, height=400)
            
            # Botón para limpiar filtros
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("Limpiar Filtros", key="limpiar_filtros_agentes"):
                    st.session_state.texto_busqueda_agentes = ""
                    st.session_state.agentes_filtrados_busqueda = st.session_state.agentes_df_original.copy()
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
                    
                    with col2:
                        grupo = st.selectbox(
                            "Grupo", 
                            ["", "G-1", "G-2"], 
                            index=0 if pd.isna(agente_data["grupo"]) else 
                                  (1 if agente_data["grupo"] == "G-1" else 2)
                        )
                    
                    # Botones de acción
                    col_guardar, col_eliminar = st.columns(2)
                    
                    with col_guardar:
                        guardar = st.form_submit_button("Guardar Cambios")
                    
                    with col_eliminar:
                        eliminar = st.form_submit_button("Eliminar Agente", type="secondary")
                    
                    # Procesar acciones
                    if guardar:
                        # Actualizar agente
                        update_agente(nip, nombre, apellido1, apellido2, seccion, grupo)
                        st.success(f"Agente {nip} actualizado correctamente")
                        # Usar session state para indicar que se debe recargar la página
                        st.session_state['agente_actualizado'] = True
                        st.rerun()
                    
                    if eliminar:
                        # Eliminar agente
                        delete_agente(nip)
                        st.success(f"Agente {nip} eliminado correctamente")
                        # Usar session state para indicar que se debe recargar la página
                        st.session_state['agente_eliminado'] = True
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
                
                with col2:
                    grupo = st.selectbox("Grupo", ["", "G-1", "G-2"], key="nuevo_grupo")
                
                # Botón de guardar
                guardar = st.form_submit_button("Guardar Nuevo Agente")
                
                # Procesar formulario
                if guardar:
                    # Validar campos obligatorios
                    if not nip or not nombre or not apellido1:
                        st.error("Los campos NIP, Nombre y Apellido 1 son obligatorios")
                    else:
                        # Añadir nuevo agente
                        success = add_agente(nip, nombre, apellido1, apellido2, seccion, grupo)
                        
                        if success:
                            st.success(f"Agente {nip} añadido correctamente")
                            # Usar session state para indicar que se debe recargar la página
                            st.session_state['agente_agregado'] = True
                            st.rerun()
                        else:
                            st.error(f"Error al añadir agente. El NIP {nip} ya existe")
    
    elif vista_seleccionada == "Gestión de Monitores":
        # Sección de gestión de monitores
        st.header("Gestión de Monitores")
        
        # Obtener datos de monitores y agentes
        monitores_df = get_monitores()
        agentes_df = get_agentes()
        
        # Crear pestañas para las diferentes funcionalidades
        tab_listar, tab_agregar = st.tabs(["Listado de Monitores", "Añadir Monitor"])
        
        with tab_listar:
            # Mostrar tabla de monitores
            st.subheader("Listado Completo de Monitores")
            
            if not monitores_df.empty:
                # Renombrar columnas para mostrar
                monitores_display = monitores_df.copy()
                monitores_display.columns = ["NIP", "Nombre", "Apellido 1", "Apellido 2", "Nombre Completo"]
                
                # Mostrar dataframe con datos
                st.dataframe(monitores_display, use_container_width=True, height=300)
                
                # Sección para eliminar monitores
                st.subheader("Eliminar Monitor")
                
                # Selector de monitor a eliminar
                monitores_opciones = [f"{nip} - {nombre}" for nip, nombre in zip(monitores_df["nip"], monitores_df["nombre_completo"])]
                monitor_seleccionado = st.selectbox("Seleccionar Monitor a Eliminar", [""] + monitores_opciones, key="eliminar_monitor")
                
                if monitor_seleccionado:
                    # Obtener NIP del monitor seleccionado
                    nip_seleccionado = monitor_seleccionado.split(" - ")[0]
                    
                    # Botón para eliminar
                    if st.button("Eliminar Monitor", type="primary", key="btn_eliminar_monitor"):
                        delete_monitor(nip_seleccionado)
                        st.success(f"Monitor {nip_seleccionado} eliminado correctamente")
                        st.cache_data.clear()  # Limpiar caché para actualizar datos
                        st.rerun()
            else:
                st.info("No hay monitores registrados en el sistema")
            
            # Botón para actualizar datos
            if st.button("Actualizar Datos", key="actualizar_monitores"):
                st.cache_data.clear()  # Limpiar caché para actualizar datos
                st.rerun()
        
        with tab_agregar:
            st.subheader("Añadir Nuevo Monitor")
            
            # Buscador de agentes con comportamiento AJAX
            st.write("Buscar agente para añadir como monitor:")
            
            # Campo de búsqueda con actualización en tiempo real
            busqueda = st.text_input(
                "Buscar por NIP o Nombre", 
                key="buscar_agente_monitor"
            )
            
            # Filtrar agentes según la búsqueda en tiempo real usando la función auxiliar
            agentes_filtrados = filtrar_agentes_por_busqueda(agentes_df, busqueda)
            
            # Excluir agentes que ya son monitores
            monitores_nips = monitores_df["nip"].tolist() if not monitores_df.empty else []
            if monitores_nips:
                agentes_filtrados = agentes_filtrados[~agentes_filtrados["nip"].isin(monitores_nips)]
            
            # Mostrar resultados incluso si la búsqueda está vacía, pero limitar a 20 registros
            if busqueda == "":
                st.write("Ingresa un término de búsqueda para filtrar agentes")
                # Si no hay búsqueda, mostrar solo los primeros 20 agentes disponibles
                if not agentes_filtrados.empty:
                    agentes_filtrados = agentes_filtrados.head(20)
            
            if not agentes_filtrados.empty:
                # Mostrar resultados de la búsqueda
                st.write(f"Resultados ({len(agentes_filtrados)} agentes):")
                
                # Renombrar columnas para mostrar
                agentes_display = agentes_filtrados.copy()
                columnas_mostrar = ["nip", "nombre_completo", "seccion", "grupo"]
                nombres_columnas = ["NIP", "Nombre", "Sección", "Grupo"]
                
                st.dataframe(
                    agentes_display[columnas_mostrar].rename(columns=dict(zip(columnas_mostrar, nombres_columnas))),
                    use_container_width=True,
                    height=200
                )
                
                # Selector de agente para añadir como monitor
                agentes_opciones = [
                    f"{nip} - {nombre}" 
                    for nip, nombre in zip(
                        agentes_filtrados["nip"], 
                        agentes_filtrados["nombre_completo"]
                    )
                ]
                
                agente_seleccionado = st.selectbox(
                    "Seleccionar Agente para añadir como Monitor", 
                    [""] + agentes_opciones,
                    key="agente_a_monitor"
                )
                
                if agente_seleccionado:
                    # Obtener NIP del agente seleccionado
                    nip_seleccionado = agente_seleccionado.split(" - ")[0]
                    
                    # Obtener datos del agente
                    agente_data = agentes_filtrados[agentes_filtrados["nip"] == nip_seleccionado].iloc[0]
                    
                    # Mostrar formulario para confirmar
                    with st.form("agregar_monitor_form"):
                        st.write(f"Añadir como Monitor: {agente_data['nombre_completo']}")
                        
                        # Campos del formulario (precargados con datos del agente)
                        nip = st.text_input("NIP", agente_data["nip"], disabled=True)
                        nombre = st.text_input("Nombre", agente_data["nombre"])
                        apellido1 = st.text_input("Apellido 1", agente_data["apellido1"])
                        apellido2 = st.text_input("Apellido 2", agente_data["apellido2"] if pd.notna(agente_data["apellido2"]) else "")
                        
                        # Botón de guardar
                        guardar = st.form_submit_button("Guardar como Monitor")
                        
                        # Procesar formulario
                        if guardar:
                            # Añadir como monitor
                            success = add_monitor(nip, nombre, apellido1, apellido2)
                            
                            if success:
                                st.success(f"Agente {nip} añadido como monitor correctamente")
                                st.cache_data.clear()  # Limpiar caché para actualizar datos
                                st.rerun()
                            else:
                                st.error(f"Error al añadir monitor. El NIP {nip} ya existe como monitor")
            elif busqueda != "":
                st.info("No se encontraron agentes con ese criterio de búsqueda")
    
    elif vista_seleccionada == "Cursos":
        # Sección de gestión de cursos y actividades
        st.header("Gestión de Cursos y Actividades")
        
        # Obtener datos necesarios
        actividades_df = get_actividades_detalle()
        cursos_df = get_cursos()
        turnos_df = get_turnos()
        monitores_df = get_monitores()
        agentes_df = get_agentes()
        
        # Crear pestañas para las diferentes funcionalidades
        # Inicializar la variable de sesión para controlar la pestaña activa si no existe
        if 'mostrar_tab_listado' not in st.session_state:
            st.session_state['mostrar_tab_listado'] = False
            
        # Crear las pestañas sin el parámetro index
        tab_listar, tab_crear, tab_editar, tab_asignar, tab_cursos = st.tabs([
            "Listado de Actividades", 
            "Crear Actividad", 
            "Editar Actividad",
            "Asignar Agentes",
            "Gestionar Cursos"
        ])
        
        # Resetear la variable de sesión después de usarla
        if st.session_state.get('mostrar_tab_listado', False):
            st.session_state['mostrar_tab_listado'] = False
            # Mostrar un mensaje en la pestaña de listado
            with tab_listar:
                st.success("¡Roger 10-4! Actividad creada correctamente.")
        
        with tab_listar:
            st.subheader("Listado de Actividades")
            
            # Filtros para el listado
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Filtro por fecha
                min_date = pd.to_datetime(actividades_df['fecha']).min() if not actividades_df.empty else datetime.now().date()
                max_date = pd.to_datetime(actividades_df['fecha']).max() if not actividades_df.empty else datetime.now().date()
                fecha_filtro = st.date_input(
                    "Filtrar por Fecha",
                    value=(datetime.now().date() - timedelta(days=7), datetime.now().date() + timedelta(days=30)),
                    min_value=min_date.date(),
                    max_value=max_date.date() + timedelta(days=365)
                )
            
            with col2:
                # Filtro por curso
                cursos_opciones = ["Todos"] + cursos_df["nombre"].tolist()
                curso_filtro = st.selectbox("Filtrar por Curso", cursos_opciones)
            
            with col3:
                # Filtro por turno
                turnos_opciones = ["Todos"] + turnos_df["nombre"].tolist()
                turno_filtro = st.selectbox("Filtrar por Turno", turnos_opciones)
            
            # Aplicar filtros
            actividades_filtradas = actividades_df.copy()
            
            # Filtro de fecha
            if isinstance(fecha_filtro, tuple) and len(fecha_filtro) == 2:
                fecha_inicio, fecha_fin = fecha_filtro
                actividades_filtradas = actividades_filtradas[
                    (pd.to_datetime(actividades_filtradas["fecha"]).dt.date >= fecha_inicio) &
                    (pd.to_datetime(actividades_filtradas["fecha"]).dt.date <= fecha_fin)
                ]
            
            # Filtro de curso
            if curso_filtro != "Todos":
                actividades_filtradas = actividades_filtradas[actividades_filtradas["curso_nombre"] == curso_filtro]
            
            # Filtro de turno
            if turno_filtro != "Todos":
                actividades_filtradas = actividades_filtradas[actividades_filtradas["turno_nombre"] == turno_filtro]
            
            # Mostrar tabla de actividades
            if not actividades_filtradas.empty:
                # Convertir fecha a formato legible
                actividades_display = actividades_filtradas.copy()
                actividades_display['fecha'] = pd.to_datetime(actividades_display['fecha']).dt.strftime('%Y-%m-%d')
                
                # Mostrar tabla
                st.dataframe(
                    actividades_display,
                    use_container_width=True
                )
            else:
                st.info("No hay actividades que coincidan con los filtros seleccionados")
            
            # Botón para actualizar datos
            if st.button("Actualizar Datos", key="actualizar_actividades"):
                st.cache_data.clear()  # Limpiar caché para actualizar datos
                st.rerun()
        
        with tab_crear:
            st.subheader("Crear Nueva Actividad")
            
            with st.form("crear_actividad_form"):
                # Campos del formulario
                fecha = st.date_input(
                    "Fecha", 
                    value=datetime.now().date()
                )
                
                # Seleccionar curso
                curso_id = st.selectbox(
                    "Curso", 
                    options=[int(id) for id in cursos_df["id"].tolist()],
                    format_func=lambda x: cursos_df.loc[cursos_df["id"] == x, "nombre"].iloc[0]
                )
                
                # Seleccionar turno
                turno_id = st.selectbox(
                    "Turno", 
                    options=[int(id) for id in turnos_df["id"].tolist()],
                    format_func=lambda x: turnos_df.loc[turnos_df["id"] == x, "nombre"].iloc[0]
                )
                
                # Seleccionar monitor
                if not monitores_df.empty:
                    monitores_opciones = [""] + monitores_df["nip"].tolist()
                    monitor_nip = st.selectbox(
                        "Monitor", 
                        options=[str(nip) for nip in monitores_df["nip"].tolist()],
                        format_func=lambda x: "" if x == "" else f"{x} - {monitores_df.loc[monitores_df['nip'] == x, 'nombre_completo'].iloc[0]}"
                    )
                else:
                    st.warning("No hay monitores registrados. Añade monitores primero.")
                    monitor_nip = ""
                
                # Notas
                notas = st.text_area("Notas (opcional)", height=100)
                
                # Botón de guardar
                guardar = st.form_submit_button("Guardar Actividad")
                
                # Procesar formulario
                if guardar:
                    # Validar campos obligatorios
                    if not fecha or not curso_id or not turno_id:
                        st.error("Los campos Fecha, Curso y Turno son obligatorios")
                    else:
                        # Si no se seleccionó un monitor, usar None
                        monitor_final = monitor_nip if monitor_nip else None
                        
                        # Debug - Mostrar valores antes de enviar
                        st.write("Debug - Valores a enviar:")
                        st.write(f"Fecha: {fecha} ({type(fecha)})")
                        st.write(f"Fecha formateada: {fecha.strftime('%Y-%m-%d')}")
                        st.write(f"Turno ID: {turno_id} ({type(turno_id)})")
                        st.write(f"Monitor NIP: {monitor_final} ({type(monitor_final)})")
                        st.write(f"Curso ID: {curso_id} ({type(curso_id)})")
                        st.write(f"Notas: {notas} ({type(notas)})")
                        
                        # Añadir nueva actividad
                        success, actividad_id = add_actividad(
                            fecha.strftime('%Y-%m-%d'), 
                            turno_id, 
                            monitor_final, 
                            curso_id, 
                            notas if notas else None
                        )
                        
                        if success:
                            st.success(f"¡Roger 10-4! Actividad creada correctamente con ID: {actividad_id}")
                            # Solo activar la variable de sesión para redirigir al listado
                            st.session_state['actividad_creada'] = True
                            st.session_state['actividad_id'] = actividad_id
                            st.session_state['mostrar_tab_listado'] = True
                            # Limpiar caché para actualizar los datos
                            st.cache_data.clear()
                            # Recargar la página para mostrar los cambios
                            st.rerun()
                        else:
                            st.error("Error al crear la actividad")
        
        with tab_editar:
            st.subheader("Editar Actividad Existente")
            
            # Selector de actividad a editar
            if not actividades_df.empty:
                # Preparar opciones para el selector
                actividades_ordenadas = actividades_df.sort_values(by="fecha", ascending=True)
                actividades_opciones = [
                    f"{id} - {curso} ({fecha})" 
                    for id, curso, fecha in zip(
                        actividades_ordenadas["id"], 
                        actividades_ordenadas["curso_nombre"], 
                        pd.to_datetime(actividades_ordenadas["fecha"]).dt.strftime('%d/%m/%Y')
                    )
                ]
                
                actividad_seleccionada = st.selectbox(
                    "Seleccionar Actividad a Editar", 
                    [""] + actividades_opciones,
                    key="editar_actividad_selector"
                )
                
                if actividad_seleccionada:
                    # Obtener ID de la actividad seleccionada
                    actividad_id = int(actividad_seleccionada.split(" - ")[0])
                    
                    # Obtener datos de la actividad
                    actividad_data = get_actividad_detalle(actividad_id)
                    
                    if actividad_data is not None:
                        with st.form("editar_actividad_form"):
                            st.write(f"Editando Actividad: {actividad_id} - {actividad_data['curso_nombre']} ({actividad_data['fecha']})")
                            
                            # Campos del formulario
                            fecha = st.date_input(
                                "Fecha", 
                                value=pd.to_datetime(actividad_data["fecha"]).date()
                            )
                            
                            # Convertir curso_id a tipo int para evitar problemas con numpy.int64
                            curso_id_actual = int(actividad_data["curso_id"])
                            
                            # Convertir los IDs a tipos nativos de Python
                            cursos_opciones = [int(id) for id in cursos_df["id"].tolist()]
                            
                            # Seleccionar curso
                            curso_id = st.selectbox(
                                "Curso", 
                                options=cursos_opciones,
                                format_func=lambda x: cursos_df.loc[cursos_df["id"] == x, "nombre"].iloc[0],
                                index=cursos_opciones.index(curso_id_actual)
                            )
                            
                            # Convertir turno_id a tipo int para evitar problemas con numpy.int64
                            turno_id_actual = int(actividad_data["turno_id"])
                            
                            # Convertir los IDs a tipos nativos de Python
                            turnos_opciones = [int(id) for id in turnos_df["id"].tolist()]
                            
                            # Seleccionar turno
                            turno_id = st.selectbox(
                                "Turno", 
                                options=turnos_opciones,
                                format_func=lambda x: turnos_df.loc[turnos_df["id"] == x, "nombre"].iloc[0],
                                index=turnos_opciones.index(turno_id_actual)
                            )
                            
                            # Convertir monitor_nip a tipo str para evitar problemas
                            monitor_nip_actual = str(actividad_data["monitor_nip"])
                            
                            # Seleccionar monitor
                            if not monitores_df.empty:
                                monitores_opciones = [""] + monitores_df["nip"].tolist()
                                
                                # Determinar el índice del monitor actual
                                if pd.notna(actividad_data["monitor_nip"]) and actividad_data["monitor_nip"] in monitores_opciones:
                                    monitor_index = monitores_opciones.index(actividad_data["monitor_nip"])
                                else:
                                    monitor_index = 0
                                
                                monitor_nip = st.selectbox(
                                    "Monitor", 
                                    options=[str(nip) for nip in monitores_df["nip"].tolist()],
                                    format_func=lambda x: "" if x == "" else f"{x} - {monitores_df.loc[monitores_df['nip'] == x, 'nombre_completo'].iloc[0]}",
                                    index=monitor_index
                                )
                            else:
                                st.warning("No hay monitores registrados. Añade monitores primero.")
                                monitor_nip = ""
                            
                            # Notas
                            notas = st.text_area(
                                "Notas (opcional)", 
                                value=actividad_data["notas"] if pd.notna(actividad_data["notas"]) else "",
                                height=100
                            )
                            
                            # Botones de acción
                            col_guardar, col_eliminar = st.columns(2)
                            
                            with col_guardar:
                                guardar = st.form_submit_button("Guardar Cambios")
                            
                            with col_eliminar:
                                eliminar = st.form_submit_button("Eliminar Actividad", type="secondary")
                            
                            # Procesar acciones
                            if guardar:
                                # Validar campos obligatorios
                                if not fecha or not curso_id or not turno_id:
                                    st.error("Los campos Fecha, Curso y Turno son obligatorios")
                                else:
                                    # Si no se seleccionó un monitor, usar None
                                    monitor_final = monitor_nip if monitor_nip else None
                                    
                                    # Actualizar actividad
                                    success = update_actividad(
                                        actividad_id,
                                        fecha.strftime('%Y-%m-%d'), 
                                        turno_id, 
                                        monitor_final, 
                                        curso_id, 
                                        notas if notas else None
                                    )
                                    
                                    if success:
                                        st.success(f"Actividad {actividad_id} actualizada correctamente")
                                        st.session_state['actividad_actualizada'] = True
                                        st.rerun()
                                    else:
                                        st.error(f"Error al actualizar la actividad {actividad_id}")
                            if eliminar:
                                # Eliminar actividad
                                success = delete_actividad(actividad_id)
                                
                                if success:
                                    st.success(f"Actividad {actividad_id} eliminada correctamente")
                                    st.session_state['actividad_eliminada'] = True
                                    st.rerun()
                                else:
                                    st.error(f"Error al eliminar la actividad {actividad_id}")
                    else:
                        st.error(f"No se pudo obtener la información de la actividad {actividad_id}")
                else:
                    st.info("Selecciona una actividad para editar sus datos")
            else:
                st.info("No hay actividades registradas en el sistema")
        
        with tab_asignar:
            st.subheader("Asignar Agentes a Actividades")
            
            # Selector de actividad
            if not actividades_df.empty:
                # Preparar opciones para el selector
                actividades_ordenadas = actividades_df.sort_values(by="fecha", ascending=True)
                actividades_opciones = [
                    f"{id} - {curso} ({fecha})" 
                    for id, curso, fecha in zip(
                        actividades_ordenadas["id"], 
                        actividades_ordenadas["curso_nombre"], 
                        pd.to_datetime(actividades_ordenadas["fecha"]).dt.strftime('%d/%m/%Y')
                    )
                ]
                
                actividad_seleccionada = st.selectbox(
                    "Seleccionar Actividad", 
                    [""] + actividades_opciones,
                    key="asignar_actividad_selector"
                )
                
                if actividad_seleccionada:
                    # Obtener ID de la actividad seleccionada
                    actividad_id = int(actividad_seleccionada.split(" - ")[0])
                    
                    # Obtener datos de la actividad
                    actividad_data = get_actividad_detalle(actividad_id)
                    
                    if actividad_data is not None:
                        # Mostrar información de la actividad
                        st.write(f"**Actividad seleccionada:** {actividad_id} - {actividad_data['curso_nombre']} ({actividad_data['fecha']})")
                        
                        # Sección de agentes asignados
                        st.subheader("Agentes Asignados")
                        
                        # Obtener agentes asignados a la actividad
                        agentes_asignados = get_agentes_por_actividad(actividad_id)
                        
                        if not agentes_asignados.empty:
                            # Mostrar tabla de agentes asignados con opción para confirmar asistencia
                            st.write("Agentes asignados a esta actividad:")
                            
                            # Crear una copia del DataFrame para mostrar
                            agentes_display = agentes_asignados.copy()
                            
                            # Renombrar columnas para mostrar
                            agentes_display.columns = ["NIP", "Nombre", "Apellido 1", "Apellido 2", "Nombre Completo", "Sección", "Grupo", "Asistencia"]
                            
                            # Convertir asistencia a texto
                            agentes_display["Asistencia"] = agentes_display["Asistencia"].apply(
                                lambda x: "✅ Confirmada" if x == 1 else "❌ No confirmada" if x == 0 else "❓ Pendiente"
                            )
                            
                            # Mostrar tabla
                            st.dataframe(agentes_display, use_container_width=True)
                            
                            # Sección para confirmar asistencia
                            with st.form(key=f"confirmar_asistencia_form_{actividad_id}"):
                                st.subheader("Confirmar Asistencia")
                                
                                # Selector de agente
                                agente_nip = st.selectbox(
                                    "Seleccionar Agente", 
                                    options=agentes_asignados["nip"].tolist(),
                                    format_func=lambda x: f"{x} - {agentes_asignados.loc[agentes_asignados['nip'] == x, 'nombre_completo'].iloc[0]}"
                                )
                                
                                # Selector de asistencia
                                asistencia = st.radio(
                                    "Asistencia", 
                                    options=[("Confirmada", 1), ("No confirmada", 0), ("Pendiente", None)],
                                    format_func=lambda x: x[0],
                                    index=0
                                )
                                
                                # Botón para confirmar
                                confirmar = st.form_submit_button("Guardar Asistencia")
                                
                                if confirmar:
                                    # Actualizar asistencia del agente
                                    success = actualizar_asistencia_agente(actividad_id, agente_nip, asistencia[1])
                                    
                                    if success:
                                        st.success(f"Asistencia actualizada para el agente {agente_nip}")
                                        # Limpiar caché para actualizar datos
                                        st.cache_data.clear()
                                        st.rerun()
                                    else:
                                        st.error("Error al actualizar la asistencia")
                        
                            # Botón para quitar agente
                            with st.form(key=f"quitar_agente_form_{actividad_id}"):
                                st.subheader("Quitar Agente")
                                
                                # Selector de agente
                                agente_quitar = st.selectbox(
                                    "Seleccionar Agente a Quitar", 
                                    options=agentes_asignados["nip"].tolist(),
                                    format_func=lambda x: f"{x} - {agentes_asignados.loc[agentes_asignados['nip'] == x, 'nombre_completo'].iloc[0]}",
                                    key=f"quitar_agente_{actividad_id}"
                                )
                                
                                # Botón para quitar
                                quitar = st.form_submit_button("Quitar Agente")
                                
                                if quitar:
                                    # Desasignar agente de la actividad
                                    success = desasignar_agente_actividad(agente_quitar, actividad_id)
                                    
                                    if success:
                                        st.success(f"Agente {agente_quitar} quitado de la actividad")
                                        # Limpiar caché para actualizar datos
                                        st.cache_data.clear()
                                        st.rerun()
                                    else:
                                        st.error("Error al quitar el agente")
                        
                        # Sección para añadir agentes
                        with st.form(key=f"anadir_agente_form_{actividad_id}"):
                            st.subheader("Añadir Agente")
                            
                            # Obtener todos los agentes
                            todos_agentes = get_agentes()
                            
                            # Filtrar agentes que no están asignados a esta actividad
                            if not agentes_asignados.empty:
                                agentes_no_asignados = todos_agentes[~todos_agentes["nip"].isin(agentes_asignados["nip"])]
                            else:
                                agentes_no_asignados = todos_agentes
                            
                            if not agentes_no_asignados.empty:
                                # Selector de agente
                                agente_anadir = st.selectbox(
                                    "Seleccionar Agente a Añadir", 
                                    options=agentes_no_asignados["nip"].tolist(),
                                    format_func=lambda x: f"{x} - {agentes_no_asignados.loc[agentes_no_asignados['nip'] == x, 'nombre_completo'].iloc[0]}",
                                    key=f"anadir_agente_{actividad_id}"
                                )
                                
                                # Botón para añadir
                                anadir = st.form_submit_button("Añadir Agente")
                                
                                if anadir:
                                    # Asignar agente a la actividad
                                    success = asignar_agente_actividad(agente_anadir, actividad_id)
                                    
                                    if success:
                                        st.success(f"Agente {agente_anadir} añadido a la actividad")
                                        # Limpiar caché para actualizar datos
                                        st.cache_data.clear()
                                        st.rerun()
                                    else:
                                        st.error("Error al añadir el agente")
                            else:
                                st.info("No hay agentes disponibles para añadir a esta actividad")
                    else:
                        st.error(f"No se pudo obtener la información de la actividad {actividad_id}")
                else:
                    st.info("Selecciona una actividad para gestionar sus agentes")
            else:
                st.info("No hay actividades registradas en el sistema")
        
        with tab_cursos:
            st.subheader("Gestión de Cursos")
            
            # Obtener lista de cursos
            cursos_df = get_cursos()
            
            # Mostrar lista de cursos actuales
            st.subheader("Cursos Disponibles")
            
            if not cursos_df.empty:
                # Mostrar tabla de cursos con IDs
                st.dataframe(
                    cursos_df,
                    use_container_width=True
                )
                
                # Sección para añadir nuevo curso
                st.subheader("Añadir Nuevo Curso")
                
                # Formulario para añadir curso
                with st.form("añadir_curso_form"):
                    nombre_curso = st.text_input("Nombre del Curso", key="nombre_nuevo_curso")
                    descripcion_curso = st.text_area("Descripción del Curso", key="descripcion_nuevo_curso")
                    
                    # Botón para añadir
                    submit_curso = st.form_submit_button("Añadir Curso")
                    
                    if submit_curso and nombre_curso:
                        # Verificar que el nombre no esté vacío
                        if nombre_curso.strip():
                            # Añadir curso
                            success = add_curso(nombre_curso, descripcion_curso)
                            
                            if success:
                                st.success(f"Curso '{nombre_curso}' añadido correctamente")
                                # Limpiar caché para actualizar lista de cursos
                                st.cache_data.clear()
                                # Recargar página
                                st.rerun()
                            else:
                                st.error("Error al añadir el curso")
                        else:
                            st.error("El nombre del curso no puede estar vacío")
            else:
                st.info("No hay cursos disponibles")
                
                # Formulario para añadir el primer curso
                with st.form("añadir_primer_curso_form"):
                    nombre_curso = st.text_input("Nombre del Curso", key="nombre_primer_curso")
                    descripcion_curso = st.text_area("Descripción del Curso", key="descripcion_primer_curso")
                    
                    # Botón para añadir
                    submit_curso = st.form_submit_button("Añadir Curso")
                    
                    if submit_curso and nombre_curso:
                        # Verificar que el nombre no esté vacío
                        if nombre_curso.strip():
                            # Añadir curso
                            success = add_curso(nombre_curso, descripcion_curso)
                            
                            if success:
                                st.success(f"Curso '{nombre_curso}' añadido correctamente")
                                # Limpiar caché para actualizar lista de cursos
                                st.cache_data.clear()
                                # Recargar página
                                st.rerun()
                            else:
                                st.error("Error al añadir el curso")
                        else:
                            st.error("El nombre del curso no puede estar vacío")
    
except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
    st.exception(e)
