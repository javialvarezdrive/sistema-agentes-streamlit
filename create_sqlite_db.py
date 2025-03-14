import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta
import random

# Crear la base de datos SQLite
def create_database():
    # Verificar si la base de datos ya existe
    db_path = 'sistema_agentes.db'
    if os.path.exists(db_path):
        print(f"La base de datos {db_path} ya existe. Se usará la existente.")
        return
    
    # Crear conexión a la base de datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Crear tablas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS turno (
        id INTEGER PRIMARY KEY,
        nombre TEXT NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cursos (
        id INTEGER PRIMARY KEY,
        nombre TEXT NOT NULL,
        descripcion TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS monitores (
        nip TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        apellido1 TEXT NOT NULL,
        apellido2 TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS actividades (
        id INTEGER PRIMARY KEY,
        fecha TEXT NOT NULL,
        turno_id INTEGER NOT NULL,
        monitor_nip TEXT,
        curso_id INTEGER NOT NULL,
        notas TEXT,
        FOREIGN KEY (turno_id) REFERENCES turno(id),
        FOREIGN KEY (monitor_nip) REFERENCES monitores(nip),
        FOREIGN KEY (curso_id) REFERENCES cursos(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agentes (
        nip TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        apellido1 TEXT NOT NULL,
        apellido2 TEXT,
        email TEXT,
        telefono TEXT,
        seccion TEXT,
        grupo TEXT,
        activo BOOLEAN DEFAULT 1,
        monitor BOOLEAN DEFAULT 0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agentes_actividades (
        agente_nip TEXT,
        actividad_id INTEGER,
        asistencia BOOLEAN,
        PRIMARY KEY (agente_nip, actividad_id),
        FOREIGN KEY (agente_nip) REFERENCES agentes(nip),
        FOREIGN KEY (actividad_id) REFERENCES actividades(id)
    )
    ''')
    
    # Insertar datos de ejemplo
    # Turnos
    turnos = [
        (1, 'Mañana'),
        (2, 'Tarde'),
        (3, 'Noche')
    ]
    cursor.executemany('INSERT INTO turno (id, nombre) VALUES (?, ?)', turnos)
    
    # Cursos
    cursos = [
        (1, 'Defensa Personal', 'Técnicas básicas de defensa personal'),
        (2, 'Tiro', 'Práctica de tiro con armas reglamentarias'),
        (3, 'Primeros Auxilios', 'Atención básica de emergencias médicas'),
        (4, 'Legislación', 'Actualización en normativa legal'),
        (5, 'Procedimientos', 'Protocolos de actuación policial')
    ]
    cursor.executemany('INSERT INTO cursos (id, nombre, descripcion) VALUES (?, ?, ?)', cursos)
    
    # Monitores
    monitores = [
        ('M001', 'Juan', 'García', 'López'),
        ('M002', 'María', 'Fernández', 'Martínez'),
        ('M003', 'Carlos', 'Rodríguez', 'Sánchez'),
        ('M004', 'Laura', 'González', 'Pérez'),
        ('M005', 'Antonio', 'Martínez', None)
    ]
    cursor.executemany('INSERT INTO monitores (nip, nombre, apellido1, apellido2) VALUES (?, ?, ?, ?)', monitores)
    
    # Agentes
    agentes = [
        ('A001', 'Pedro', 'López', 'García', 'pedro@ejemplo.com', '600111222', 'A1', 'G1', 1, 0),
        ('A002', 'Ana', 'Martínez', 'Rodríguez', 'ana@ejemplo.com', '600222333', 'A2', 'G2', 1, 0),
        ('A003', 'Miguel', 'Sánchez', 'Fernández', 'miguel@ejemplo.com', '600333444', 'A3', 'G3', 1, 0),
        ('A004', 'Lucía', 'Pérez', 'González', 'lucia@ejemplo.com', '600444555', 'A4', 'G4', 1, 0),
        ('A005', 'David', 'García', 'Martínez', 'david@ejemplo.com', '600555666', 'A5', 'G5', 1, 0),
        ('A006', 'Elena', 'Rodríguez', 'López', 'elena@ejemplo.com', '600666777', 'A6', 'G6', 1, 0),
        ('A007', 'Javier', 'González', 'Sánchez', 'javier@ejemplo.com', '600777888', 'A7', 'G7', 1, 0),
        ('A008', 'Carmen', 'Fernández', 'Pérez', 'carmen@ejemplo.com', '600888999', 'A8', 'G8', 1, 0),
        ('A009', 'Alberto', 'Martínez', 'García', 'alberto@ejemplo.com', '600999000', 'A9', 'G9', 1, 0),
        ('A010', 'Silvia', 'López', 'Rodríguez', 'silvia@ejemplo.com', '601000111', 'A10', 'G10', 1, 0),
        ('A011', 'Roberto', 'Sánchez', 'González', 'roberto@ejemplo.com', '601111222', 'A11', 'G11', 1, 0),
        ('A012', 'Natalia', 'Pérez', 'Fernández', 'natalia@ejemplo.com', '601222333', 'A12', 'G12', 1, 0),
        ('A013', 'Francisco', 'García', 'Martínez', 'francisco@ejemplo.com', '601333444', 'A13', 'G13', 1, 0),
        ('A014', 'Isabel', 'Rodríguez', 'López', 'isabel@ejemplo.com', '601444555', 'A14', 'G14', 1, 0),
        ('A015', 'Alejandro', 'González', 'Sánchez', 'alejandro@ejemplo.com', '601555666', 'A15', 'G15', 1, 0)
    ]
    cursor.executemany('INSERT INTO agentes (nip, nombre, apellido1, apellido2, email, telefono, seccion, grupo, activo, monitor) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', agentes)
    
    # Actividades
    # Generar fechas para los últimos 30 días y próximos 30 días
    hoy = datetime.now().date()
    fechas = [(hoy - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30, 0, -1)]
    fechas += [hoy.strftime('%Y-%m-%d')]
    fechas += [(hoy + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 31)]
    
    actividades = []
    for i, fecha in enumerate(fechas, 1):
        # Seleccionar curso, turno y monitor aleatorios
        curso_id = random.randint(1, 5)
        turno_id = random.randint(1, 3)
        monitor_nip = f'M00{random.randint(1, 5)}'
        
        # Añadir notas aleatorias para algunas actividades
        notas = None
        if random.random() > 0.7:
            notas_opciones = [
                "Traer equipo completo",
                "Sesión teórico-práctica",
                "Evaluación final del módulo",
                "Clase de repaso",
                "Sesión especial con invitados"
            ]
            notas = random.choice(notas_opciones)
        
        actividades.append((i, fecha, turno_id, monitor_nip, curso_id, notas))
    
    cursor.executemany('INSERT INTO actividades (id, fecha, turno_id, monitor_nip, curso_id, notas) VALUES (?, ?, ?, ?, ?, ?)', actividades)
    
    # Asignaciones de agentes a actividades
    asignaciones = []
    for actividad_id in range(1, len(fechas) + 1):
        # Asignar entre 5 y 12 agentes a cada actividad
        num_agentes = random.randint(5, 12)
        agentes_seleccionados = random.sample(range(1, 16), num_agentes)
        
        for agente_num in agentes_seleccionados:
            agente_nip = f'A{agente_num:03d}'
            
            # Para actividades pasadas, establecer asistencia
            fecha_actividad = datetime.strptime(fechas[actividad_id - 1], '%Y-%m-%d').date()
            if fecha_actividad < hoy:
                asistencia = random.random() > 0.2  # 80% de probabilidad de asistencia
            else:
                asistencia = None  # Actividades futuras o del día actual no tienen asistencia registrada
            
            asignaciones.append((agente_nip, actividad_id, asistencia))
    
    cursor.executemany('INSERT INTO agentes_actividades (agente_nip, actividad_id, asistencia) VALUES (?, ?, ?)', asignaciones)
    
    # Crear vista para facilitar consultas
    cursor.execute('''
    CREATE VIEW IF NOT EXISTS vista_actividades_con_agentes AS
    SELECT 
        a.id as actividad_id,
        a.fecha,
        t.nombre as turno_nombre,
        c.nombre as curso_nombre,
        COALESCE(m.nombre || ' ' || m.apellido1 || CASE WHEN m.apellido2 IS NOT NULL THEN ' ' || m.apellido2 ELSE '' END, 'Sin monitor') as monitor_nombre,
        COUNT(aa.agente_nip) as total_agentes,
        SUM(CASE WHEN aa.asistencia = 1 THEN 1 ELSE 0 END) as asistencia_confirmada,
        SUM(CASE WHEN aa.asistencia IS NULL THEN 1 ELSE 0 END) as asistencia_pendiente,
        CASE 
            WHEN COUNT(aa.agente_nip) > 0 THEN 
                ROUND((SUM(CASE WHEN aa.asistencia = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(aa.agente_nip)), 2)
            ELSE 0
        END as asistencia_porcentaje,
        strftime('%w', a.fecha) as dia_semana_num,
        CASE strftime('%w', a.fecha)
            WHEN '0' THEN 'Domingo'
            WHEN '1' THEN 'Lunes'
            WHEN '2' THEN 'Martes'
            WHEN '3' THEN 'Miércoles'
            WHEN '4' THEN 'Jueves'
            WHEN '5' THEN 'Viernes'
            WHEN '6' THEN 'Sábado'
        END as dia_semana,
        strftime('%m', a.fecha) as mes_num,
        CASE strftime('%m', a.fecha)
            WHEN '01' THEN 'Enero'
            WHEN '02' THEN 'Febrero'
            WHEN '03' THEN 'Marzo'
            WHEN '04' THEN 'Abril'
            WHEN '05' THEN 'Mayo'
            WHEN '06' THEN 'Junio'
            WHEN '07' THEN 'Julio'
            WHEN '08' THEN 'Agosto'
            WHEN '09' THEN 'Septiembre'
            WHEN '10' THEN 'Octubre'
            WHEN '11' THEN 'Noviembre'
            WHEN '12' THEN 'Diciembre'
        END as mes,
        strftime('%Y', a.fecha) as anio,
        strftime('%W', a.fecha) as semana_del_anio,
        CASE 
            WHEN date(a.fecha) < date('now') THEN 'Completada'
            WHEN date(a.fecha) = date('now') THEN 'En curso'
            ELSE 'Pendiente'
        END as estado
    FROM 
        actividades a
    LEFT JOIN 
        turno t ON a.turno_id = t.id
    LEFT JOIN 
        cursos c ON a.curso_id = c.id
    LEFT JOIN 
        monitores m ON a.monitor_nip = m.nip
    LEFT JOIN 
        agentes_actividades aa ON a.id = aa.actividad_id
    GROUP BY 
        a.id, a.fecha, t.nombre, c.nombre, monitor_nombre
    ORDER BY 
        a.fecha DESC
    ''')
    
    # Guardar cambios y cerrar conexión
    conn.commit()
    conn.close()
    
    print(f"Base de datos {db_path} creada con éxito con datos de ejemplo.")

if __name__ == "__main__":
    create_database()
