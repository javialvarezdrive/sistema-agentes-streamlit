import requests
import json
import streamlit as st

# URL base de la API
API_BASE_URL = "http://localhost:8000"

# Función para manejar errores de la API
def handle_api_error(response):
    try:
        error_data = response.json()
        error_message = error_data.get("detail", "Error desconocido")
    except:
        error_message = f"Error: {response.status_code} - {response.text}"
    
    return error_message

# Funciones para interactuar con la API

@st.cache_data(ttl=60)  # Caché de 60 segundos
def get_agentes_http():
    """Obtiene la lista de agentes desde la API"""
    try:
        response = requests.get(f"{API_BASE_URL}/agentes")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(handle_api_error(response))
            return []
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return []

def get_agente_http(nip):
    """Obtiene un agente específico por su NIP"""
    try:
        response = requests.get(f"{API_BASE_URL}/agentes/{nip}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(handle_api_error(response))
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

def add_agente_http(nip, nombre, apellido1, apellido2, seccion, grupo, activo, monitor):
    """Añade un nuevo agente a través de la API"""
    try:
        data = {
            "nip": nip,
            "nombre": nombre,
            "apellido1": apellido1,
            "apellido2": apellido2,
            "seccion": seccion,
            "grupo": grupo,
            "activo": bool(activo),
            "monitor": bool(monitor)
        }
        
        response = requests.post(
            f"{API_BASE_URL}/agentes",
            json=data
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, handle_api_error(response)
    except Exception as e:
        return False, f"Error de conexión: {str(e)}"

def update_agente_http(nip, nombre=None, apellido1=None, apellido2=None, seccion=None, grupo=None, activo=None, monitor=None):
    """Actualiza un agente existente a través de la API"""
    try:
        # Crear un diccionario con los campos que no son None
        data = {}
        if nombre is not None:
            data["nombre"] = nombre
        if apellido1 is not None:
            data["apellido1"] = apellido1
        if apellido2 is not None:
            data["apellido2"] = apellido2
        if seccion is not None:
            data["seccion"] = seccion
        if grupo is not None:
            data["grupo"] = grupo
        if activo is not None:
            data["activo"] = bool(activo)
        if monitor is not None:
            data["monitor"] = bool(monitor)
        
        response = requests.put(
            f"{API_BASE_URL}/agentes/{nip}",
            json=data
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, handle_api_error(response)
    except Exception as e:
        return False, f"Error de conexión: {str(e)}"

def delete_agente_http(nip):
    """Elimina un agente a través de la API"""
    try:
        response = requests.delete(f"{API_BASE_URL}/agentes/{nip}")
        if response.status_code == 200:
            return True, "Agente eliminado correctamente"
        else:
            return False, handle_api_error(response)
    except Exception as e:
        return False, f"Error de conexión: {str(e)}"

@st.cache_data(ttl=60)  # Caché de 60 segundos
def get_actividades_http():
    """Obtiene la lista de actividades desde la API"""
    try:
        response = requests.get(f"{API_BASE_URL}/actividades")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(handle_api_error(response))
            return []
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return []

@st.cache_data(ttl=60)  # Caché de 60 segundos
def get_agentes_actividad_http(actividad_id):
    """Obtiene los agentes asignados a una actividad específica"""
    try:
        response = requests.get(f"{API_BASE_URL}/actividades/{actividad_id}/agentes")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(handle_api_error(response))
            return []
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return []
