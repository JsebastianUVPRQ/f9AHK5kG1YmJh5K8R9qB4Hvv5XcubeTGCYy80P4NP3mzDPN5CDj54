from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

# Importamos la conexión a DB y los modelos
from database import get_db
import models

# Importamos el esquema que acabamos de crear (ajusta la ruta si estás en un solo archivo)
# from api.schemas import MencionLectura 

router = APIRouter(
    prefix="/api/v1/raw",
    tags=["🗄️ Datos Crudos"]
)

@router.get("/menciones", response_model=List[MencionLectura])
def obtener_menciones_crudas(
    skip: int = Query(0, description="Registros a omitir (Paginación)"),
    limit: int = Query(50, le=1000, description="Límite de registros por página (Máx 1000)"),
    candidato: Optional[str] = Query(None, description="Filtrar por nombre exacto del candidato"),
    db: Session = Depends(get_db)
):
    """
    **Extracción de Nodos de Inteligencia:**
    Devuelve los registros en bruto almacenados en la base de datos.
    Soporta paginación nativa y filtrado por candidato para evitar la sobrecarga de la red.
    """
    try:
        query = db.query(models.MencionInteligencia)
        
        # Aplicar filtro si el usuario lo solicita
        if candidato:
            query = query.filter(models.MencionInteligencia.candidato_principal == candidato)
            
        # Ejecutar consulta con paginación
        resultados = query.order_by(models.MencionInteligencia.fecha_ingesta.desc()).offset(skip).limit(limit).all()
        return resultados
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar la base de datos: {str(e)}")