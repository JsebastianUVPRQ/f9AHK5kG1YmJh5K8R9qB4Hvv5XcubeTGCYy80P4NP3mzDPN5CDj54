import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Manejo seguro y optimizado para el Pooler de Supabase (Plan Nano)
try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,          # Conexiones base que FastAPI mantendrá abiertas
        max_overflow=20,       # Conexiones extra permitidas si hay un pico de tráfico (Total: 30)
        pool_recycle=1800,     # Reciclar conexiones cada 30 min para evitar que Supabase las mate por inactividad
        pool_pre_ping=True     # El "escudo": verifica que la conexión esté viva antes de enviar el query
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    print("🚨 ERROR FATAL: No se pudo conectar a la base de datos. Revisa tu .env")
    engine = None

def get_db():
    """Dependencia de FastAPI para inyectar la base de datos en los endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()