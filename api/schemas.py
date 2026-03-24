from pydantic import BaseModel, Field
from typing import Dict

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

class AnalisisResponse(BaseModel):
    texto_original: str
    clasificacion: str = Field(description="POSITIVO, NEGATIVO o NEUTRAL")
    probabilidades: Dict[str, float] = Field(description="Nivel de confianza de la IA para cada clase")