"""
Módulo para implementar búsqueda AJAX en Streamlit
"""

import streamlit as st
import pandas as pd
import time

def setup_ajax_search():
    """
    Configura el CSS y JavaScript necesario para la búsqueda AJAX
    """
    # Añadir CSS personalizado para mejorar la experiencia de usuario
    st.markdown("""
    <style>
        .search-container {
            position: relative;
            margin-bottom: 10px;
        }
        .search-input {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ccc;
            border-radius: 4px;
            transition: border-color 0.3s;
        }
        .search-input:focus {
            border-color: #4CAF50;
            outline: none;
        }
        .search-icon {
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            color: #888;
        }
        .search-results {
            margin-top: 5px;
            padding: 5px;
            border-radius: 4px;
            background-color: #f9f9f9;
        }
        .highlight {
            background-color: #ffff99;
            padding: 0 2px;
            border-radius: 2px;
        }
        .ajax-status {
            font-size: 0.8em;
            color: #888;
            margin-top: 2px;
        }
    </style>
    """, unsafe_allow_html=True)

def create_ajax_search(df, search_columns, placeholder="Buscar...", key_prefix="ajax_search"):
    """
    Crea un campo de búsqueda con comportamiento AJAX
    
    Args:
        df: DataFrame con los datos
        search_columns: Lista de columnas donde buscar
        placeholder: Texto de placeholder para el campo de búsqueda
        key_prefix: Prefijo para las claves de estado de sesión
        
    Returns:
        DataFrame filtrado según la búsqueda
    """
    # Configurar estado de sesión
    if f'{key_prefix}_original_df' not in st.session_state:
        st.session_state[f'{key_prefix}_original_df'] = df.copy()
    
    if f'{key_prefix}_filtered_df' not in st.session_state:
        st.session_state[f'{key_prefix}_filtered_df'] = df.copy()
    
    if f'{key_prefix}_query' not in st.session_state:
        st.session_state[f'{key_prefix}_query'] = ""
    
    if f'{key_prefix}_last_update' not in st.session_state:
        st.session_state[f'{key_prefix}_last_update'] = time.time()
    
    # Función de callback para actualizar resultados
    def update_search_results():
        query = st.session_state[f'{key_prefix}_query'].lower()
        if not query:
            st.session_state[f'{key_prefix}_filtered_df'] = st.session_state[f'{key_prefix}_original_df'].copy()
        else:
            # Crear máscara combinando todas las columnas de búsqueda
            mask = pd.Series(False, index=st.session_state[f'{key_prefix}_original_df'].index)
            for col in search_columns:
                if col in st.session_state[f'{key_prefix}_original_df'].columns:
                    # Convertir columna a string para buscar
                    col_str = st.session_state[f'{key_prefix}_original_df'][col].astype(str).str.lower()
                    mask = mask | col_str.str.contains(query, na=False)
            
            # Aplicar filtro
            st.session_state[f'{key_prefix}_filtered_df'] = st.session_state[f'{key_prefix}_original_df'][mask].copy()
        
        # Actualizar timestamp
        st.session_state[f'{key_prefix}_last_update'] = time.time()
    
    # Campo de búsqueda con estilo AJAX
    st.text_input(
        placeholder,
        key=f'{key_prefix}_query',
        on_change=update_search_results,
        help="Escribe para filtrar resultados en tiempo real"
    )
    
    # Mostrar indicador de búsqueda activa
    if st.session_state[f'{key_prefix}_query']:
        st.caption(f"🔍 Buscando: '{st.session_state[f'{key_prefix}_query']}'")
        
        # Mostrar tiempo de respuesta
        response_time = round((time.time() - st.session_state[f'{key_prefix}_last_update']) * 1000)
        st.caption(f"⚡ Tiempo de respuesta: {response_time}ms")
    
    # Devolver DataFrame filtrado
    return st.session_state[f'{key_prefix}_filtered_df']

def highlight_search_results(df, text_columns, search_query, key_prefix="ajax_search"):
    """
    Resalta los términos de búsqueda en el DataFrame
    
    Args:
        df: DataFrame filtrado
        text_columns: Columnas de texto donde resaltar
        search_query: Término de búsqueda
        key_prefix: Prefijo para las claves de estado de sesión
        
    Returns:
        DataFrame con los términos resaltados
    """
    if not st.session_state.get(f'{key_prefix}_query'):
        return df
    
    # Crear copia para no modificar el original
    highlighted_df = df.copy()
    
    # Función para resaltar texto
    def highlight_text(text):
        if not isinstance(text, str):
            return text
        
        query = st.session_state[f'{key_prefix}_query'].lower()
        if query in text.lower():
            # Encontrar todas las ocurrencias sin distinguir mayúsculas/minúsculas
            start = 0
            result = ""
            text_lower = text.lower()
            
            while start < len(text):
                pos = text_lower.find(query, start)
                if pos == -1:
                    result += text[start:]
                    break
                
                # Añadir texto antes de la coincidencia
                result += text[start:pos]
                
                # Añadir texto resaltado
                result += f"<span class='highlight'>{text[pos:pos+len(query)]}</span>"
                
                # Actualizar posición
                start = pos + len(query)
            
            return result
        return text
    
    # Aplicar resaltado a columnas de texto
    for col in text_columns:
        if col in highlighted_df.columns:
            highlighted_df[col] = highlighted_df[col].apply(highlight_text)
    
    return highlighted_df
