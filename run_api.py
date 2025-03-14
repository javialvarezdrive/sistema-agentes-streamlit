import uvicorn

if __name__ == "__main__":
    print("Iniciando API del Sistema de Agentes en http://localhost:8000")
    print("Documentación de la API disponible en http://localhost:8000/docs")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
