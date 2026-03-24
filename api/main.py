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

# --- LOS IMPORTS PESADOS NO VAN AQUÍ ---

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    engine = None

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- MODELO (Integridad CO) ---
class MencionInteligencia(Base):
    __tablename__ = "inteligencia_electoral"
    id = Column(Integer, primary_key=True, index=True)
    texto_original = Column(String, nullable=False)
    hash_texto = Column(String(64), unique=True, index=True)
    sentimiento_ia = Column(String(50), index=True)
    entidades_json = Column(JSON, nullable=True)
    fuente_nombre = Column(String(100), index=True)
    url_origen = Column(String, nullable=True)
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)

class IngestaDatosRequest(BaseModel):
    texto: str
    fuente_nombre: str = "RSS"
    url_origen: Optional[HttpUrl] = None

class AnalisisResponse(BaseModel):
    id_registro: int
    clasificacion: str
    status: str

# --- GESTOR DE IA (CON CARGA INTERNA) ---
class MLManager:
    def __init__(self):
        self.analyzer = None
        self.nlp = None

    def load_model(self):
        # CARGA BAJO DEMANDA: Solo se importa cuando se necesita
        if self.analyzer is None:
            from pysentimiento import create_analyzer # Import interno
            self.analyzer = create_analyzer(task="sentiment", lang="es")
        if self.nlp is None:
            import spacy # Import interno
            self.nlp = spacy.load("es_core_news_sm")

    def predict_all(self, text: str):
        self.load_model()
        sent = self.analyzer.predict(text)
        doc = self.nlp(text)
        entidades = {
            "personas": list(set([ent.text for ent in doc.ents if ent.label_ == "PER"])),
            "lugares": list(set([ent.text for ent in doc.ents if ent.label_ == "LOC"]))
        }
        return {"sentimiento": sent.output, "probas": sent.probas, "entidades": entidades}

ml_manager = MLManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    if engine:
        Base.metadata.create_all(bind=engine)
    yield 

app = FastAPI(title="Monitor Integridad CO", lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "online", "message": "Motor de Integridad Activo"}

@app.post("/api/v1/ml/analizar", response_model=AnalisisResponse)
async def analizar(request: IngestaDatosRequest, db: Session = Depends(get_db)):
    res = ml_manager.predict_all(request.texto)
    texto_hash = hashlib.sha256(request.texto.encode('utf-8')).hexdigest()
    
    nuevo = MencionInteligencia(
        texto_original=request.texto,
        hash_texto=texto_hash,
        sentimiento_ia=res["sentimiento"],
        entidades_json=res["entidades"],
        fuente_nombre=request.fuente_nombre,
        url_origen=str(request.url_origen) if request.url_origen else None
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"id_registro": nuevo.id, "clasificacion": nuevo.sentimiento_ia, "status": "Éxito"}