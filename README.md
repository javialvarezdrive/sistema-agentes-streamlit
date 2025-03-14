# Sistema de Gestión de Agentes - Aplicación Streamlit

Esta aplicación Streamlit proporciona un dashboard interactivo para visualizar y analizar datos del Sistema de Gestión de Agentes, utilizando una base de datos SQLite local.

## Características

- **Dashboard de Actividades**: Visualiza métricas clave como total de actividades, agentes asignados y porcentajes de asistencia
- **Gráficos Interactivos**: Analiza actividades por curso, asistencia por día de la semana y distribución de estados
- **Filtros Dinámicos**: Filtra los datos por fecha, curso, turno y estado
- **Tablas de Datos**: Visualiza listados detallados de actividades y agentes
- **Gestión de Agentes**: Interfaz para añadir, editar y eliminar agentes
- **API REST**: Acceso a los datos mediante una API REST con FastAPI

## Configuración

1. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

2. Inicializa la base de datos SQLite (solo la primera vez):
   ```
   python create_sqlite_db.py
   ```

3. Ejecuta la aplicación Streamlit:
   ```
   streamlit run app.py
   ```

4. (Opcional) Ejecuta la API REST:
   ```
   python run_api.py
   ```

## Estructura de Datos

La aplicación utiliza las siguientes tablas de la base de datos SQLite:

- `actividades`: Registro de actividades programadas
- `agentes`: Información de los agentes
- `agentes_actividades`: Relación muchos a muchos entre agentes y actividades
- `cursos`: Catálogo de cursos disponibles
- `monitores`: Información de los monitores
- `turno`: Definición de turnos (mañana, tarde, etc.)

## API REST

La aplicación incluye una API REST desarrollada con FastAPI que proporciona acceso a los datos:

- **GET /agentes**: Obtiene todos los agentes
- **GET /agentes/{nip}**: Obtiene un agente específico
- **POST /agentes**: Crea un nuevo agente
- **PUT /agentes/{nip}**: Actualiza un agente existente
- **DELETE /agentes/{nip}**: Elimina un agente
- **GET /actividades**: Obtiene todas las actividades
- **GET /actividades/{id}/agentes**: Obtiene los agentes asignados a una actividad

La documentación interactiva de la API está disponible en http://localhost:8000/docs cuando el servidor está en ejecución.

## Despliegue

La aplicación está preparada para ser desplegada en Render. Consulta el archivo `deploy_guide.md` para obtener instrucciones detalladas sobre cómo desplegar la aplicación.

## Requisitos del Sistema

- Python 3.7+
- SQLite 3
- Streamlit 1.32.0+
- FastAPI 0.110.0+ (para la API REST)
