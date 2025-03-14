import requests
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener la URL de la API desde las variables de entorno o usar un valor predeterminado
API_URL = os.getenv('API_URL', 'http://localhost:8000')

def get_actividades():
    """Obtiene todas las actividades desde la API"""
    try:
        response = requests.get(f"{API_URL}/actividades")
        response.raise_for_status()  # Lanzar excepción si hay error HTTP
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener actividades: {e}")
        return []

def get_agentes():
    """Obtiene todos los agentes desde la API"""
    try:
        response = requests.get(f"{API_URL}/agentes")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener agentes: {e}")
        return []

def get_agentes_por_actividad(actividad_id):
    """Obtiene los agentes asignados a una actividad específica"""
    try:
        response = requests.get(f"{API_URL}/agentes_por_actividad/{actividad_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener agentes por actividad: {e}")
        return []

def actualizar_asistencia(agente_nip, actividad_id, asistencia):
    """Actualiza la asistencia de un agente a una actividad"""
    try:
        data = {
            "agente_nip": agente_nip,
            "actividad_id": actividad_id,
            "asistencia": asistencia
        }
        response = requests.post(f"{API_URL}/actualizar_asistencia", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al actualizar asistencia: {e}")
        return {"success": False}
