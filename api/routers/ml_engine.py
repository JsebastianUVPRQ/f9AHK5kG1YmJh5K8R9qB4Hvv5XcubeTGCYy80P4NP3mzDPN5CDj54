from fastapi import APIRouter, HTTPException
from api.schemas import AnalisisRequest, AnalisisResponse
from api.core.ml_manager import ml_manager

router = APIRouter(
    prefix="/api/v1/ml",
    tags=["🧠 Machine Learning"]
)

@router.post("/analizar", response_model=AnalisisResponse)
async def analizar_texto(request: AnalisisRequest):
    """
    **Inferencia en Tiempo Real:**
    Envía cualquier texto y el modelo de Hugging Face determinará si el tono 
    político es Positivo, Negativo o Neutral, devolviendo la probabilidad matemática de cada uno.
    """
    try:
        resultado = ml_manager.predict(request.texto)
        
        return AnalisisResponse(
            texto_original=request.texto,
            clasificacion=resultado["clasificacion"],
            probabilidades=resultado["probas"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el motor de IA: {str(e)}")