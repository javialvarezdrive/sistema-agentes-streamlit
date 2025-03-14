from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os
from typing import List, Optional

# Crear la aplicación FastAPI
app = FastAPI(title="API Sistema de Agentes")

# Configurar CORS para permitir solicitudes desde Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas las origenes en desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ruta a la base de datos
DATABASE_PATH = "sistema_agentes.db"

# Función para obtener conexión a la base de datos
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Modelos Pydantic
class Agente(BaseModel):
    nip: str
    nombre: str
    apellido1: str
    apellido2: Optional[str] = None
    seccion: Optional[str] = None
    grupo: Optional[str] = None
    activo: bool = True
    monitor: bool = False

class AgenteUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido1: Optional[str] = None
    apellido2: Optional[str] = None
    seccion: Optional[str] = None
    grupo: Optional[str] = None
    activo: Optional[bool] = None
    monitor: Optional[bool] = None

# Endpoints de la API
@app.get("/")
async def root():
    return {"message": "API Sistema de Agentes"}

# Obtener todos los agentes
@app.get("/agentes", response_model=List[dict])
async def get_agentes(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            nip, 
            nombre, 
            apellido1, 
            apellido2, 
            nombre || ' ' || apellido1 || COALESCE(' ' || apellido2, '') as nombre_completo,
            seccion, 
            grupo, 
            activo, 
            monitor 
        FROM agentes
        ORDER BY apellido1, nombre
    """)
    agentes = [dict(row) for row in cursor.fetchall()]
    return agentes

# Obtener un agente por NIP
@app.get("/agentes/{nip}", response_model=dict)
async def get_agente(nip: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            nip, 
            nombre, 
            apellido1, 
            apellido2, 
            nombre || ' ' || apellido1 || COALESCE(' ' || apellido2, '') as nombre_completo,
            seccion, 
            grupo, 
            activo, 
            monitor 
        FROM agentes
        WHERE nip = ?
    """, (nip,))
    agente = cursor.fetchone()
    if agente is None:
        raise HTTPException(status_code=404, detail=f"Agente con NIP {nip} no encontrado")
    return dict(agente)

# Crear un nuevo agente
@app.post("/agentes", response_model=dict)
async def create_agente(agente: Agente, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    # Verificar si el agente ya existe
    cursor.execute("SELECT nip FROM agentes WHERE nip = ?", (agente.nip,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail=f"El agente con NIP {agente.nip} ya existe")
    
    # Convertir booleanos a enteros para SQLite
    activo_int = 1 if agente.activo else 0
    monitor_int = 1 if agente.monitor else 0
    
    try:
        cursor.execute("""
            INSERT INTO agentes (nip, nombre, apellido1, apellido2, seccion, grupo, activo, monitor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            agente.nip, 
            agente.nombre, 
            agente.apellido1, 
            agente.apellido2, 
            agente.seccion, 
            agente.grupo, 
            activo_int, 
            monitor_int
        ))
        db.commit()
        
        # Obtener el agente recién creado
        cursor.execute("""
            SELECT 
                nip, 
                nombre, 
                apellido1, 
                apellido2, 
                nombre || ' ' || apellido1 || COALESCE(' ' || apellido2, '') as nombre_completo,
                seccion, 
                grupo, 
                activo, 
                monitor 
            FROM agentes
            WHERE nip = ?
        """, (agente.nip,))
        return dict(cursor.fetchone())
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear agente: {str(e)}")

# Actualizar un agente existente
@app.put("/agentes/{nip}", response_model=dict)
async def update_agente(nip: str, agente_update: AgenteUpdate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    # Verificar si el agente existe
    cursor.execute("SELECT nip FROM agentes WHERE nip = ?", (nip,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"Agente con NIP {nip} no encontrado")
    
    # Construir la consulta de actualización dinámicamente
    update_fields = []
    params = []
    
    if agente_update.nombre is not None:
        update_fields.append("nombre = ?")
        params.append(agente_update.nombre)
    
    if agente_update.apellido1 is not None:
        update_fields.append("apellido1 = ?")
        params.append(agente_update.apellido1)
    
    if agente_update.apellido2 is not None:
        update_fields.append("apellido2 = ?")
        params.append(agente_update.apellido2)
    
    if agente_update.seccion is not None:
        update_fields.append("seccion = ?")
        params.append(agente_update.seccion)
    
    if agente_update.grupo is not None:
        update_fields.append("grupo = ?")
        params.append(agente_update.grupo)
    
    if agente_update.activo is not None:
        update_fields.append("activo = ?")
        params.append(1 if agente_update.activo else 0)
    
    if agente_update.monitor is not None:
        update_fields.append("monitor = ?")
        params.append(1 if agente_update.monitor else 0)
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
    
    query = f"UPDATE agentes SET {', '.join(update_fields)} WHERE nip = ?"
    params.append(nip)
    
    try:
        cursor.execute(query, params)
        db.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"No se pudo actualizar el agente con NIP {nip}")
        
        # Obtener el agente actualizado
        cursor.execute("""
            SELECT 
                nip, 
                nombre, 
                apellido1, 
                apellido2, 
                nombre || ' ' || apellido1 || COALESCE(' ' || apellido2, '') as nombre_completo,
                seccion, 
                grupo, 
                activo, 
                monitor 
            FROM agentes
            WHERE nip = ?
        """, (nip,))
        return dict(cursor.fetchone())
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar agente: {str(e)}")

# Eliminar un agente
@app.delete("/agentes/{nip}")
async def delete_agente(nip: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    # Verificar si el agente existe
    cursor.execute("SELECT nip FROM agentes WHERE nip = ?", (nip,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"Agente con NIP {nip} no encontrado")
    
    try:
        cursor.execute("DELETE FROM agentes WHERE nip = ?", (nip,))
        db.commit()
        return {"message": f"Agente con NIP {nip} eliminado correctamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar agente: {str(e)}")

# Endpoint para obtener actividades
@app.get("/actividades", response_model=List[dict])
async def get_actividades(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            a.id,
            a.fecha,
            a.hora_inicio,
            a.hora_fin,
            c.nombre as curso,
            a.turno,
            a.estado,
            a.observaciones
        FROM actividades a
        LEFT JOIN cursos c ON a.id_curso = c.id
        ORDER BY a.fecha DESC, a.hora_inicio
    """)
    actividades = [dict(row) for row in cursor.fetchall()]
    return actividades

# Endpoint para obtener agentes asignados a una actividad
@app.get("/actividades/{actividad_id}/agentes", response_model=List[dict])
async def get_agentes_actividad(actividad_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            a.nip,
            a.nombre,
            a.apellido1,
            a.apellido2,
            a.nombre || ' ' || a.apellido1 || COALESCE(' ' || a.apellido2, '') as nombre_completo,
            aa.asistencia
        FROM agentes_actividades aa
        JOIN agentes a ON aa.id_agente = a.nip
        WHERE aa.id_actividad = ?
        ORDER BY a.apellido1, a.nombre
    """, (actividad_id,))
    agentes = [dict(row) for row in cursor.fetchall()]
    return agentes

# Ejecutar la aplicación con uvicorn si se ejecuta directamente
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
