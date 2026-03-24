import feedparser
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict
from contextlib import asynccontextmanager
from pysentimiento import create_analyzer
from sqlalchemy.orm import Session
import hashlib


# Importaciones de tu base de datos local
from database import engine, get_db, SessionLocal
import models

# ==========================================
# 1. EL CEREBRO DE IA (ML Manager)
# ==========================================
class MLManager:
    def __init__(self):
        self.analyzer = None

    def load_model(self):
        """Carga el modelo de Transformers en memoria caché."""
        if self.analyzer is None:
            print("⏳ Cargando modelo NLP 'pysentimiento' (esto toma unos segundos)...")
            self.analyzer = create_analyzer(task="sentiment", lang="es")
            print("✅ Modelo NLP cargado y listo para inferencia.")

    def predict(self, text: str):
        """Ejecuta la inferencia en vivo."""
        if self.analyzer is None:
            raise RuntimeError("El modelo NLP no está cargado en memoria.")
        
        resultado = self.analyzer.predict(text)
        return {
            "clasificacion": resultado.output,
            "probas": resultado.probas
        }

ml_manager = MLManager()

# ==========================================
# 2. LOS CONTRATOS DE DATOS (Schemas Pydantic)
# ==========================================
class AnalisisRequest(BaseModel):
    texto: str = Field(..., min_length=5, description="El texto en español a analizar.")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{"texto": "Las propuestas de este candidato son excelentes para el país."}]
        }
    }

class AnalisisResponse(BaseModel):
    texto_original: str
    clasificacion: str = Field(description="POSITIVO, NEGATIVO o NEUTRAL")
    probabilidades: Dict[str, float]

# ==========================================
# 3. WORKER EN SEGUNDO PLANO (El Scraper)
# ==========================================
def extraer_y_analizar_noticias():
    """Descarga el RSS, analiza con IA y guarda en Supabase sin bloquear la API."""
    print("🕵️‍♂️ [Scraper] Iniciando extracción de noticias en segundo plano...")
    url_rss = "https://news.google.com/rss/search?q=elecciones+colombia+2026&hl=es-419&gl=CO&ceid=CO:es-419"
    
    db = SessionLocal()
    try:
        feed = feedparser.parse(url_rss)
        nuevos_registros = 0
        
        for entrada in feed.entries[:5]: # Límite de 5 para pruebas
            titulo = entrada.title
            
            # Evitar duplicados
            existe = db.query(models.AnalisisSentimiento).filter_by(texto_original=titulo).first()
            if existe:
                continue
                
            # Pasar por IA
            resultado_ia = ml_manager.predict(titulo)
            
            # Guardar en BD
            nueva_noticia = models.AnalisisSentimiento(
                texto_original=titulo,
                clasificacion=resultado_ia["clasificacion"],
                prob_positiva=resultado_ia["probas"].get("POS", 0.0),
                prob_negativa=resultado_ia["probas"].get("NEG", 0.0),
                prob_neutral=resultado_ia["probas"].get("NEU", 0.0)
            )
            db.add(nueva_noticia)
            nuevos_registros += 1
            
        if nuevos_registros > 0:
            db.commit()
            print(f"✅ [Scraper] Éxito: {nuevos_registros} nuevas noticias analizadas y guardadas.")
        else:
            print("📭 [Scraper] No hay noticias nuevas en este momento.")
            
    except Exception as e:
        db.rollback()
        print(f"🚨 [Scraper] Error: {str(e)}")
    finally:
        db.close()

# ==========================================
# 4. CICLO DE VIDA Y CONFIGURACIÓN FASTAPI
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Arrancando API Data Engine...")
    # Sincronizar tablas en Supabase
    if engine:
        models.Base.metadata.create_all(bind=engine)
        print("🗄️ Base de datos conectada y sincronizada.")
    
    # Cargar IA
    ml_manager.load_model()
    yield 
    print("🛑 Apagando API... Limpiando memoria.")

tags_metadata = [
    {"name": "🧠 Machine Learning", "description": "Inferencia en tiempo real y almacenamiento."},
    {"name": "⚙️ Sistema", "description": "Controladores, healthchecks y tareas de fondo."}
]

app = FastAPI(
    title="Colombia Elects API - Data Engine",
    description="Motor backend de NLP para clasificar sentimientos políticos.",
    version="2.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan
)

# ==========================================
# 5. ENDPOINTS (Rutas de la API)
# ==========================================
@app.get("/", tags=["⚙️ Sistema"])
async def root():
    return {"status": "online", "docs_url": "/docs"}

@app.post("/api/v1/ml/analizar", response_model=AnalisisResponse, tags=["🧠 Machine Learning"])
async def analizar_texto(request: AnalisisRequest, db: Session = Depends(get_db)):
    """Analiza un texto manual y lo guarda en Supabase."""
    try:
        resultado = ml_manager.predict(request.texto)
        
        nuevo_analisis = models.AnalisisSentimiento(
            texto_original=request.texto,
            clasificacion=resultado["clasificacion"],
            prob_positiva=resultado["probas"].get("POS", 0.0),
            prob_negativa=resultado["probas"].get("NEG", 0.0),
            prob_neutral=resultado["probas"].get("NEU", 0.0)
        )
        db.add(nuevo_analisis)
        db.commit()
        
        return AnalisisResponse(
            texto_original=request.texto,
            clasificacion=resultado["clasificacion"],
            probabilidades=resultado["probas"]
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/admin/sync-fuentes", tags=["⚙️ Sistema"])
async def sincronizar_fuentes(background_tasks: BackgroundTasks):
    """Dispara el web scraper en segundo plano."""
    background_tasks.add_task(extraer_y_analizar_noticias)
    return {
        "status": "aceptado",
        "mensaje": "El motor de extracción ha comenzado a buscar noticias en segundo plano."
    }


@app.post("/api/v1/ml/analizar", response_model=AnalisisResponse, tags=["🧠 Machine Learning"])
async def analizar_texto(request: IngestaDatosRequest, db: Session = Depends(get_db)):
    """
    **Inferencia, NER y Almacenamiento:**
    Analiza un texto, extrae entidades clave (Lugares, Personas) y guarda el nodo de inteligencia en Supabase.
    """
    try:
        # 1. Generar huella digital (Hash) para evitar duplicados exactos en BD
        texto_hash = hashlib.sha256(request.texto.encode('utf-8')).hexdigest()
        
        # 2. Ejecutar inferencia de Sentimiento
        sentimiento = ml_manager.predict_sentiment(request.texto)
        
        # 3. Extraer Entidades con spaCy
        entidades_extraidas = ml_manager.extract_entities(request.texto)
        
        # Opcional: Si el usuario no envió una ubicación, intentamos inferirla de las entidades
        ubicacion_final = request.ubicacion_geo
        if not ubicacion_final and entidades_extraidas["lugares"]:
            ubicacion_final = entidades_extraidas["lugares"][0] # Tomamos el primer lugar detectado

        # 4. Construir el objeto para la Base de Datos (MencionInteligencia)
        nuevo_registro = models.MencionInteligencia(
            texto_original=request.texto,
            hash_texto=texto_hash,
            sentimiento_ia=sentimiento["clasificacion"],
            prob_positiva=sentimiento["probas"].get("POS", 0.0),
            prob_negativa=sentimiento["probas"].get("NEG", 0.0),
            candidato_principal=request.candidato_principal,
            entidades_json=entidades_extraidas, # ¡Aquí se guarda la magia de Palantir!
            fuente_tipo=request.fuente_tipo,
            fuente_nombre=request.fuente_nombre,
            url_origen=str(request.url_origen) if request.url_origen else None,
            ubicacion_geo=ubicacion_final,
            metricas_impacto=request.metricas_impacto
        )
        
        db.add(nuevo_registro)
        db.commit()
        db.refresh(nuevo_registro)
        
        # 5. Responder al usuario
        return AnalisisResponse(
            id_registro=nuevo_registro.id,
            clasificacion=sentimiento["clasificacion"],
            probabilidades=sentimiento["probas"],
            status="Nodo de inteligencia creado y enlazado correctamente."
        )
        
    except Exception as e:
        db.rollback() 
        raise HTTPException(status_code=500, detail=f"Error en el motor de IA/DB: {str(e)}")