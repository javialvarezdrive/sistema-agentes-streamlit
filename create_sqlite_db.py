import sqlite3
import os

def create_database():
    # Verificar si la base de datos ya existe
    if os.path.exists('sistema_agentes.db'):
        print("La base de datos ya existe. No se creará una nueva.")
        return
    
    # Crear una nueva base de datos
    conn = sqlite3.connect('sistema_agentes.db')
    cursor = conn.cursor()
    
    # Crear tablas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cursos (
        id INTEGER PRIMARY KEY,
        nombre TEXT NOT NULL,
        descripcion TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS turnos (
        id INTEGER PRIMARY KEY,
        nombre TEXT NOT NULL,
        hora_inicio TEXT,
        hora_fin TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agentes (
        nip TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        apellido1 TEXT NOT NULL,
        apellido2 TEXT,
        seccion TEXT,
        grupo TEXT,
        es_monitor INTEGER DEFAULT 0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS actividades (
        id INTEGER PRIMARY KEY,
        fecha TEXT NOT NULL,
        turno_id INTEGER,
        monitor_nip TEXT,
        curso_id INTEGER,
        notas TEXT,
        FOREIGN KEY (turno_id) REFERENCES turnos (id),
        FOREIGN KEY (monitor_nip) REFERENCES agentes (nip),
        FOREIGN KEY (curso_id) REFERENCES cursos (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agentes_actividades (
        agente_nip TEXT,
        actividad_id INTEGER,
        asistencia INTEGER DEFAULT 0,
        PRIMARY KEY (agente_nip, actividad_id),
        FOREIGN KEY (agente_nip) REFERENCES agentes (nip),
        FOREIGN KEY (actividad_id) REFERENCES actividades (id)
    )
    ''')
    
    # Insertar datos iniciales
    # Turnos
    turnos = [
        (1, 'Mañana', '08:00', '14:00'),
        (2, 'Tarde', '14:00', '20:00'),
        (3, 'Noche', '20:00', '08:00')
    ]
    cursor.executemany('INSERT INTO turnos (id, nombre, hora_inicio, hora_fin) VALUES (?, ?, ?, ?)', turnos)
    
    # Cursos
    cursos = [
        (1, 'Formación Básica', 'Curso básico para agentes nuevos'),
        (2, 'Actualización', 'Curso de actualización anual'),
        (3, 'Especialización', 'Curso de especialización en áreas específicas')
    ]
    cursor.executemany('INSERT INTO cursos (id, nombre, descripcion) VALUES (?, ?, ?)', cursos)
    
    # Confirmar cambios y cerrar conexión
    conn.commit()
    conn.close()
    
    print("Base de datos creada exitosamente con datos iniciales.")

if __name__ == "__main__":
    create_database()
