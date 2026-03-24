from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime
from database import Base

class MencionInteligencia(Base):
    __tablename__ = "inteligencia_electoral"

    # ==========================================
    # 1. CORE: El dato en bruto y su huella
    # ==========================================
    id = Column(Integer, primary_key=True, index=True)
    texto_original = Column(String, nullable=False)
    hash_texto = Column(String(64), unique=True, index=True) # Para evitar duplicados exactos

    # ==========================================
    # 2. INFERENCIA IA: Lo que dice nuestro modelo
    # ==========================================
    sentimiento_ia = Column(String(50), index=True)
    prob_positiva = Column(Float)
    prob_negativa = Column(Float)
    
    # ==========================================
    # 3. ENTIDADES: ¿De quién y de qué se habla?
    # ==========================================
    candidato_principal = Column(String(100), index=True, nullable=True)
    tema_principal = Column(String(100), index=True, nullable=True) # Ej: Economía, Seguridad, Escándalo
    entidades_json = Column(JSON, nullable=True) # {"personas": [], "organizaciones": [], "lugares": []}

    # ==========================================
    # 4. PROVENANCE: Trazabilidad del dato (Origen)
    # ==========================================
    fuente_tipo = Column(String(50), index=True) # Ej: Noticias, Twitter, Reddit, YouTube
    fuente_nombre = Column(String(100), index=True) # Ej: El Tiempo, @UsuarioX
    url_origen = Column(String, nullable=True)
    
    # ==========================================
    # 5. CONTEXTO GEO-TEMPORAL Y MÉTRICAS
    # ==========================================
    ubicacion_geo = Column(String(100), index=True, nullable=True) # Ej: Cali, Bogotá, Antioquia
    metricas_impacto = Column(JSON, nullable=True) # {"vistas": 5000, "likes": 120, "retweets": 45}
    
    fecha_publicacion = Column(DateTime, nullable=True) # Cuándo se publicó en internet
    fecha_ingesta = Column(DateTime, default=datetime.utcnow) # Cuándo lo vio nuestra API