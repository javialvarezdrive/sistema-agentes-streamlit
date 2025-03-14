from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import pandas as pd
from datetime import datetime

app = FastAPI(title="API Sistema de Gestión de Agentes")

# Función para obtener la conexión a la base de datos
def get_db_connection():
    conn = sqlite3.connect('sistema_agentes.db')
    conn.row_factory = sqlite3.Row
    return conn

# Rutas de la API
@app.get("/")
async def root():
    return {"message": "API del Sistema de Gestión de Agentes"}

@app.get("/actividades")
async def get_actividades():
    """Obtiene todas las actividades ordenadas por fecha en orden cronológico ascendente"""
    conn = get_db_connection()
    query = """
    SELECT 
        a.id, 
        a.fecha, 
        t.nombre as turno, 
        c.nombre as curso,
        a.monitor_nip,
        (SELECT nombre || ' ' || apellido1 FROM agentes WHERE nip = a.monitor_nip) as monitor_nombre,
        a.notas
    FROM actividades a
    JOIN turnos t ON a.turno_id = t.id
    JOIN cursos c ON a.curso_id = c.id
    ORDER BY a.fecha ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.to_dict(orient="records")

@app.get("/agentes")
async def get_agentes():
    """Obtiene todos los agentes"""
    conn = get_db_connection()
    query = """
    SELECT 
        a.nip, 
        a.nombre, 
        a.apellido1, 
        a.apellido2,
        a.seccion,
        a.grupo,
        a.nombre || ' ' || a.apellido1 || CASE WHEN a.apellido2 IS NOT NULL THEN ' ' || a.apellido2 ELSE '' END as nombre_completo
    FROM agentes a
    ORDER BY a.seccion, a.grupo, a.apellido1, a.nombre
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.to_dict(orient="records")

@app.get("/agentes_por_actividad/{actividad_id}")
async def get_agentes_por_actividad(actividad_id: int):
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
    return df.to_dict(orient="records")

# Modelo para la asistencia
class AsistenciaUpdate(BaseModel):
    agente_nip: str
    actividad_id: int
    asistencia: int

@app.post("/actualizar_asistencia")
async def actualizar_asistencia(data: AsistenciaUpdate):
    """Actualiza la asistencia de un agente a una actividad"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE agentes_actividades SET asistencia = ? WHERE agente_nip = ? AND actividad_id = ?",
            (data.asistencia, data.agente_nip, data.actividad_id)
        )
        conn.commit()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar asistencia: {str(e)}")
    finally:
        conn.close()
