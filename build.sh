#!/usr/bin/env bash
# Salir si hay un error
set -o errexit

# 1. Instalar dependencias optimizadas
pip install -r requirements.txt

# 2. Descargar el modelo de lenguaje de spaCy
python -m spacy download es_core_news_sm