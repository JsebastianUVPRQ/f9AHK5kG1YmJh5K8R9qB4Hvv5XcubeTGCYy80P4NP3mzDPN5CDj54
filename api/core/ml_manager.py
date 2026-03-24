from pysentimiento import create_analyzer

class MLManager:
    def __init__(self):
        self.analyzer = None

    def load_model(self):
        """Carga el modelo de Transformers en memoria."""
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

# Instancia global que importaremos en nuestra API
ml_manager = MLManager()