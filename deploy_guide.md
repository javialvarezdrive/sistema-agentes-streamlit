# Guía de Despliegue en Render

Esta guía te ayudará a desplegar tu aplicación Sistema de Gestión de Agentes en Render.com.

## Requisitos Previos

1. Una cuenta en [Render](https://render.com/)
2. Tu código subido a un repositorio Git (GitHub, GitLab, etc.)

## Pasos para el Despliegue

### 1. Preparar tu Repositorio

Asegúrate de que tu repositorio contenga los siguientes archivos:

- `requirements.txt`: Con todas las dependencias
- `render.yaml`: Configuración para Render (ya creado)
- `Procfile`: Instrucciones de inicio (ya creado)

### 2. Modificar el Cliente HTTP

Antes de desplegar, debes modificar el archivo `http_client.py` para que use la URL de la API en producción:

```python
import os

# URL base de la API
API_BASE_URL = os.environ.get("API_URL", "http://localhost:8000")
```

### 3. Configurar la Base de Datos para Producción

Para un entorno de producción, deberías considerar:

1. **Usar una base de datos PostgreSQL** en lugar de SQLite:
   - Render ofrece bases de datos PostgreSQL gestionadas
   - Modifica tu código para usar PostgreSQL en producción

2. **O persistir los datos de SQLite**:
   - Configura un volumen persistente en Render
   - Cambia la ruta de la base de datos a usar ese volumen

### 4. Desplegar en Render

1. Inicia sesión en [Render Dashboard](https://dashboard.render.com/)

2. Haz clic en "New" y selecciona "Blueprint"

3. Conecta tu repositorio Git

4. Render detectará automáticamente el archivo `render.yaml` y configurará los servicios

5. Revisa la configuración y haz clic en "Apply"

6. Render comenzará a construir y desplegar tus servicios

### 5. Variables de Entorno

Asegúrate de configurar estas variables de entorno en Render:

- `API_URL`: URL de tu servicio API (se configura automáticamente con `render.yaml`)
- `DATABASE_URL`: Si usas PostgreSQL

### 6. Verificar el Despliegue

Una vez completado el despliegue:

1. Visita la URL de tu aplicación Streamlit
2. Verifica que la conexión con la API funcione correctamente
3. Prueba todas las funcionalidades

## Solución de Problemas

Si encuentras problemas durante el despliegue:

1. Revisa los logs en el dashboard de Render
2. Verifica que todas las dependencias estén en `requirements.txt`
3. Asegúrate de que la aplicación funcione correctamente en local

## Consideraciones Adicionales

### Seguridad

Para un entorno de producción, considera implementar:

1. Autenticación para proteger tu API
2. HTTPS (proporcionado automáticamente por Render)
3. Validación de datos más estricta

### Escalabilidad

Render permite escalar fácilmente:

1. Aumenta los recursos de tus servicios según sea necesario
2. Configura auto-scaling para manejar picos de tráfico

### Costos

Render ofrece:
- Un nivel gratuito con limitaciones
- Planes de pago para más recursos y funcionalidades

Revisa la [página de precios](https://render.com/pricing) para más detalles.
