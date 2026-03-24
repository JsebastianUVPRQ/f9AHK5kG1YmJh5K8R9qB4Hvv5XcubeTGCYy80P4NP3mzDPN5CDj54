from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.database import engine, Base

# Importaremos los routers más adelante, por ahora los comentamos
# from api.routers import data_raw, ml_engine, insights, admin

# 1. GESTIÓN DEL CICLO DE VIDA (Lifespan)
# Aquí cargaremos el modelo de IA una sola vez al arrancar, ahorrando RAM en Render.
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Iniciando Motor de Datos...")
    # Asegurar que las tablas existan en Supabase
    Base.metadata.create_all(bind=engine)
    
    # TODO: Inicializar el modelo de pysentimiento aquí
    print("🧠 (Placeholder) Modelo de IA cargado en memoria caché.")
    
    yield # Aquí la API está "Live" y recibiendo peticiones
    
    print("🛑 Apagando Motor de Datos... Limpiando memoria.")
    # TODO: Descargar el modelo de IA de la memoria
    
# 2. METADATOS PARA SWAGGER UI (La "Interfaz Gráfica" de tu API)
tags_metadata = [
    {
        "name": "🧠 Machine Learning",
        "description": "Endpoints para inferencia en tiempo real usando modelos NLP basados en Transformers.",
    },
    {
        "name": "🗄️ Datos Crudos",
        "description": "Acceso directo a la base de datos de menciones electorales (Paginado y filtrado).",
    },
    {
        "name": "📊 Insights",
        "description": "Métricas calculadas, tendencias y agrupaciones estadísticas.",
    },
    {
        "name": "⚙️ Administración",
        "description": "Controladores del sistema, disparadores del Scraper y tareas en segundo plano.",
    }
]

# 3. INSTANCIA PRINCIPAL DE LA API
app = FastAPI(
    title="Colombia Elects API - Data Engine",
    description="""
    **Motor de Inteligencia de Datos** para el monitoreo de elecciones en Colombia (2026).
    
    Esta API proporciona acceso a:
    * 🗞️ Extracción automatizada de noticias y redes sociales.
    * 🤖 Análisis de sentimiento impulsado por NLP (Hugging Face).
    * 📈 Series de tiempo y métricas de reputación digital.
    """,
    version="1.0.0",
    contact={
        "name": "Monitor Electoral OS",
        "url": "https://github.com/TU_USUARIO/colombia_elecciones_tracker",
    },
    license_info={
        "name": "AGPL-3.0",                     # identificador SPDX
        "url": "https://www.gnu.org/licenses/agpl-3.0.html",
    },
    openapi_tags=tags_metadata,
    lifespan=lifespan
)

# 4. REGISTRO DE ROUTERS (Los conectaremos en los próximos pasos)
# app.include_router(ml_engine.router)
# app.include_router(data_raw.router)
# app.include_router(insights.router)
# app.include_router(admin.router)

# 5. ENDPOINT RAÍZ (Healthcheck de ultra-baja latencia para Render)
@app.get("/", tags=["⚙️ Administración"])
async def root():
    """
    **Healthcheck Endpoint:**
    Verifica que el servidor esté online y aceptando conexiones.
    Útil para los balanceadores de carga de AWS/Render.
    """
    return {
        "status": "online", 
        "engine": "FastAPI v1.0",
        "docs_url": "/docs"
    }