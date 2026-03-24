import os
import hashlib
import feedparser
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from dotenv import load_dotenv

from pysentimiento import create_analyzer
import spacy

# ==========================================
# 1. CONFIGURACIÓN DE BASE DE DATOS
# ==========================================
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    print(f"🚨 ERROR FATAL BD: Verifica tu .env. Detalles: {e}")
    engine = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 2. MODELOS SQL (La Estructura Avanzada)
# ==========================================
class MencionInteligencia(Base):
    __tablename__ = "inteligencia_electoral"

    id = Column(Integer, primary_key=True, index=True)
    texto_original = Column(String, nullable=False)
    hash_texto = Column(String(64), unique=True, index=True)

    sentimiento_ia = Column(String(50), index=True)
    prob_positiva = Column(Float)
    prob_negativa = Column(Float)
    
    candidato_principal = Column(String(100), index=True, nullable=True)
    tema_principal = Column(String(100), index=True, nullable=True)
    entidades_json = Column(JSON, nullable=True)

    fuente_tipo = Column(String(50), index=True)
    fuente_nombre = Column(String(100), index=True)
    url_origen = Column(String, nullable=True)
    
    ubicacion_geo = Column(String(100), index=True, nullable=True)
    metricas_impacto = Column(JSON, nullable=True)
    
    fecha_publicacion = Column(DateTime, nullable=True)
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)

# ==========================================
# 3. ESQUEMAS PYDANTIC (Contratos)
# ==========================================
class IngestaDatosRequest(BaseModel):
    texto: str = Field(..., min_length=5, description="El texto capturado.")
    candidato_principal: Optional[str] = Field(default=None)
    fuente_tipo: str = Field(default="API_MANUAL")
    fuente_nombre: str = Field(default="Usuario")
    url_origen: Optional[HttpUrl] = None
    ubicacion_geo: Optional[str] = None
    metricas_impacto: Optional[Dict[str, Any]] = None

class AnalisisResponse(BaseModel):
    id_registro: int
    clasificacion: str
    probabilidades: Dict[str, float]
    status: str

# ==========================================
# 4. EL CEREBRO DE IA (ML Manager)
# ==========================================
class MLManager:
    def __init__(self):
        self.analyzer = None
        self.nlp = None

    def load_model(self):
        if self.analyzer is None:
            print("⏳ Cargando modelo NLP 'pysentimiento'...")
            self.analyzer = create_analyzer(task="sentiment", lang="es")
            print("✅ Modelo de Sentimiento cargado.")
            
        if self.nlp is None:
            print("⏳ Cargando modelo NER 'spaCy'...")
            try:
                self.nlp = spacy.load("es_core_news_sm")
                print("✅ Modelo de Entidades cargado.")
            except OSError:
                print("🚨 ERROR: Modelo spaCy no encontrado.")

    def predict_sentiment(self, text: str):
        self.load_model()
        if self.analyzer is None:
            raise RuntimeError("Modelo no cargado.")
        resultado = self.analyzer.predict(text)
        return {"clasificacion": resultado.output, "probas": resultado.probas}

    def extract_entities(self, text: str):
        self.load_model()
        if self.nlp is None:
            return {"personas": [], "organizaciones": [], "lugares": []}
        doc = self.nlp(text)
        return {
            "personas": list(set([ent.text for ent in doc.ents if ent.label_ == "PER"])),
            "organizaciones": list(set([ent.text for ent in doc.ents if ent.label_ == "ORG"])),
            "lugares": list(set([ent.text for ent in doc.ents if ent.label_ == "LOC"]))
        }


ml_manager = MLManager()

# ==========================================
# 5. WORKER EN SEGUNDO PLANO (Scraper Actualizado)
# ==========================================
def extraer_y_analizar_noticias():
    """Descarga el RSS, analiza con IA (Sentimiento + NER) y guarda en Supabase."""
    print("🕵️‍♂️ [Scraper] Iniciando extracción de noticias en segundo plano...")
    url_rss = "https://news.google.com/rss/search?q=elecciones+colombia+2026&hl=es-419&gl=CO&ceid=CO:es-419"
    
    db = SessionLocal()
    try:
        feed = feedparser.parse(url_rss)
        nuevos_registros = 0
        
        for entrada in feed.entries[:10]: # Subí el límite a 10
            titulo = entrada.title
            texto_hash = hashlib.sha256(titulo.encode('utf-8')).hexdigest()
            
            # Evitar duplicados con el hash
            existe = db.query(MencionInteligencia).filter_by(hash_texto=texto_hash).first()
            if existe:
                continue
                
            # Pasar por IA Completa (Sentimiento + Entidades)
            sentimiento = ml_manager.predict_sentiment(titulo)
            entidades = ml_manager.extract_entities(titulo)
            
            # Guardar en BD con la nueva estructura
            nueva_noticia = MencionInteligencia(
                texto_original=titulo,
                hash_texto=texto_hash,
                sentimiento_ia=sentimiento["clasificacion"],
                prob_positiva=sentimiento["probas"].get("POS", 0.0),
                prob_negativa=sentimiento["probas"].get("NEG", 0.0),
                entidades_json=entidades,
                fuente_tipo="RSS",
                fuente_nombre="Google News",
                url_origen=entrada.link
            )
            db.add(nueva_noticia)
            nuevos_registros += 1
            
        if nuevos_registros > 0:
            db.commit()
            print(f"✅ [Scraper] Éxito: {nuevos_registros} nuevos nodos de inteligencia creados.")
        else:
            print("📭 [Scraper] No hay noticias nuevas.")
            
    except Exception as e:
        db.rollback()
        print(f"🚨 [Scraper] Error: {str(e)}")
    finally:
        db.close()

# ==========================================
# 6. CONFIGURACIÓN DE FASTAPI Y LIFESPAN
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Arrancando API Data Engine...")
    if engine:
        Base.metadata.create_all(bind=engine)
        print("🗄️ Base de datos conectada y sincronizada.")
    # ml_manager.load_model()
    yield 
    print("🛑 Apagando API... Limpiando memoria.")

app = FastAPI(
    title="Colombia Elects API",
    version="2.0.0",
    lifespan=lifespan
)

# ==========================================
# 7. ENDPOINTS
# ==========================================
@app.get("/", tags=["⚙️ Sistema"])
async def root():
    return {"status": "online", "docs_url": "/docs"}

@app.post("/api/v1/admin/sync-fuentes", tags=["⚙️ Sistema"])
async def sincronizar_fuentes(background_tasks: BackgroundTasks):
    """Dispara el web scraper en segundo plano usando IA."""
    background_tasks.add_task(extraer_y_analizar_noticias)
    return {"status": "aceptado", "mensaje": "Extracción y análisis iniciados en segundo plano."}

@app.post("/api/v1/ml/analizar", response_model=AnalisisResponse, tags=["🧠 Ingesta Manual"])
async def analizar_texto(request: IngestaDatosRequest, db: Session = Depends(get_db)):
    """Inferencia, NER y Almacenamiento manual."""
    try:
        texto_hash = hashlib.sha256(request.texto.encode('utf-8')).hexdigest()
        
        existe = db.query(MencionInteligencia).filter_by(hash_texto=texto_hash).first()
        if existe:
            return AnalisisResponse(
                id_registro=existe.id,
                clasificacion=existe.sentimiento_ia,
                probabilidades={"POS": existe.prob_positiva, "NEG": existe.prob_negativa},
                status="El texto ya existía."
            )

        sentimiento = ml_manager.predict_sentiment(request.texto)
        entidades = ml_manager.extract_entities(request.texto)
        
        ubicacion_final = request.ubicacion_geo or (entidades["lugares"][0] if entidades["lugares"] else None)

        nuevo_registro = MencionInteligencia(
            texto_original=request.texto,
            hash_texto=texto_hash,
            sentimiento_ia=sentimiento["clasificacion"],
            prob_positiva=sentimiento["probas"].get("POS", 0.0),
            prob_negativa=sentimiento["probas"].get("NEG", 0.0),
            candidato_principal=request.candidato_principal,
            entidades_json=entidades,
            fuente_tipo=request.fuente_tipo,
            fuente_nombre=request.fuente_nombre,
            url_origen=str(request.url_origen) if request.url_origen else None,
            ubicacion_geo=ubicacion_final,
            metricas_impacto=request.metricas_impacto
        )
        
        db.add(nuevo_registro)
        db.commit()
        db.refresh(nuevo_registro)
        
        return AnalisisResponse(
            id_registro=nuevo_registro.id,
            clasificacion=sentimiento["clasificacion"],
            probabilidades=sentimiento["probas"],
            status="Nodo creado exitosamente."
        )
    except Exception as e:
        db.rollback() 
        raise HTTPException(status_code=500, detail=str(e))