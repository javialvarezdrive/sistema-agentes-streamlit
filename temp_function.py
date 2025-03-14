# Función para añadir una nueva actividad
def add_actividad(fecha, turno_id, monitor_nip, curso_id, notas=None):
    """Añade una nueva actividad y devuelve su ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO actividades (fecha, turno_id, monitor_nip, curso_id, notas) VALUES (?, ?, ?, ?, ?)",
            (fecha, turno_id, monitor_nip, curso_id, notas)
        )
        actividad_id = cursor.lastrowid
        conn.commit()
        return True, actividad_id
    except Exception as e:
        st.error(f"Error al añadir actividad: {e}")
        return False, None
    finally:
        conn.close()
