from pydantic import BaseModel, Field, HttpUrl
from typing import Dict, List, Optional, Any
from datetime import datetime
class AnalisisRequest(BaseModel):
    texto: str = Field(..., min_length=5, description="El texto en español a analizar.")
    
    # Esto aparecerá pre-llenado en la documentación interactiva (Swagger UI)
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "texto": "Las propuestas de este candidato para 2026 me parecen excelentes y muy viables."
                }
            ]
        }
    }

class IngestaDatosRequest(BaseModel):
    texto: str = Field(..., min_length=5, description="El texto capturado.")
    candidato_principal: Optional[str] = Field(default=None, description="Candidato detectado a priori.")
    fuente_tipo: str = Field(default="API_MANUAL", description="Categoría de la fuente (Noticias, Redes, etc.)")
    fuente_nombre: str = Field(default="Usuario", description="Nombre del medio o usuario.")
    url_origen: Optional[HttpUrl] = None
    ubicacion_geo: Optional[str] = None
    metricas_impacto: Optional[Dict[str, Any]] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "texto": "Las políticas de seguridad en Cali deben mejorar urgentemente.",
                    "candidato_principal": "Candidato X",
                    "fuente_tipo": "Twitter",
                    "fuente_nombre": "@ciudadano_cali",
                    "ubicacion_geo": "Cali, Valle del Cauca",
                    "metricas_impacto": {"likes": 250, "retweets": 45}
                }
            ]
        }
    }


class AnalisisResponse(BaseModel):
    id_registro: int
    clasificacion: str
    probabilidades: Dict[str, float]
    status: str = "Datos procesados e indexados correctamente."