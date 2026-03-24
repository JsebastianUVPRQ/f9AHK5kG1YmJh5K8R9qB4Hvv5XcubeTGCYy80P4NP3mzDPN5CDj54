from pysentimiento import create_analyzer
import spacy

class MLManager:
    def __init__(self):
        self.analyzer = None
        self.nlp = None

    def load_model(self):
        """Carga los modelos en memoria caché."""
        # 1. Modelo de Sentimiento
        if self.analyzer is None:
            print("⏳ Cargando modelo NLP 'pysentimiento'...")
            self.analyzer = create_analyzer(task="sentiment", lang="es")
            print("✅ Modelo de Sentimiento cargado.")
            
        # 2. Modelo de Entidades (NER)
        if self.nlp is None:
            print("⏳ Cargando modelo NER 'spaCy'...")
            try:
                self.nlp = spacy.load("es_core_news_sm")
                print("✅ Modelo de Entidades cargado.")
            except OSError:
                print("🚨 ERROR: Modelo spaCy no encontrado. Ejecuta: python -m spacy download es_core_news_sm")

    def predict_sentiment(self, text: str):
        """Ejecuta la inferencia de sentimiento."""
        if self.analyzer is None:
            raise RuntimeError("El modelo de sentimiento no está cargado.")
        resultado = self.analyzer.predict(text)
        return {
            "clasificacion": resultado.output,
            "probas": resultado.probas
        }

    def extract_entities(self, text: str):
        """Extrae Personas, Organizaciones y Lugares del texto."""
        if self.nlp is None:
            return {"personas": [], "organizaciones": [], "lugares": []}
        
        doc = self.nlp(text)
        
        entidades = {
            "personas": [ent.text for ent in doc.ents if ent.label_ == "PER"],
            "organizaciones": [ent.text for ent in doc.ents if ent.label_ == "ORG"],
            "lugares": [ent.text for ent in doc.ents if ent.label_ == "LOC"]
        }
        
        # Eliminamos duplicados dentro de la misma categoría
        for key in entidades:
            entidades[key] = list(set(entidades[key]))
            
        return entidades

ml_manager = MLManager()