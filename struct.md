
**Motor de Datos (Data Engine) de grado empresarial**. 


---

## 🧭 Guideline: Arquitectura de la API "Data Engine"

El objetivo ahora es que tu API sea la "fuente de la verdad". Cualquier persona (o tú mismo en el futuro, si decides hacer un frontend en React o Vue) podrá conectarse a ella para extraer tanto datos crudos como análisis procesados por Machine Learning.

### 1. Reestructuración Modular (FastAPI Routers)
Vamos a abandonar el archivo `main.py` gigante. FastAPI brilla cuando divides tu aplicación en "mini-APIs" usando `APIRouter`. 
* **Ruta `/api/v1/raw`**: Para servir los datos limpios y en bruto desde Supabase (con paginación y filtros).
* **Ruta `/api/v1/ml`**: endpoints exclusivos para interactuar con los modelos de inteligencia artificial.
* **Ruta `/api/v1/insights`**: Para entregar métricas pre-calculadas (tendencias, agrupaciones, promedios).
* **Ruta `/api/v1/admin`**: Para disparar los scrapers y tareas de mantenimiento.

### 2. Gestión Eficiente de Modelos ML (Lifespan Events)
El mayor error al usar Machine Learning en APIs es cargar el modelo en cada petición o cargarlo globalmente de forma ineficiente (lo que nos causaba el *Out of Memory* en Render).
* **La solución:** Usaremos la característica de `lifespan` de FastAPI. Esto nos permite cargar el modelo pesado de `pysentimiento` **exactamente una vez** cuando el servidor arranca, mantenerlo en la memoria caché de la aplicación, y cerrarlo limpiamente cuando el servidor se apaga.

### 3. El Contrato de Datos (Pydantic Mágico)
Vamos a exprimir Pydantic al máximo. No devolveremos simples diccionarios, sino "Schemas" estrictos.
* Si alguien pide información de un candidato, Pydantic validará automáticamente los tipos de datos, formateará las fechas en ISO 8601 y generará la documentación interactiva (Swagger UI) sin que escribamos código extra.

### 4. Asincronismo Real y Tareas de Fondo
FastAPI está construido sobre Starlette y `asyncio`.
* Convertiremos nuestras consultas a Supabase para que no bloqueen el servidor.
* Usaremos `BackgroundTasks` de FastAPI de forma nativa para que, si llamas a un endpoint para actualizar los datos (`POST /admin/scraper`), la API te responda "Aceptado" en 10 milisegundos, mientras el scraper y el modelo de ML trabajan silenciosamente en segundo plano.

### 5. Inferencia ML "On-the-Fly"
Aparte de guardar noticias, la API ofrecerá un servicio puro de Machine Learning.
* Crearemos un endpoint `POST /api/v1/ml/analizar-texto` donde tú le envías un texto cualquiera en el body del JSON, y la API usa el modelo cargado en el *lifespan* para devolverte el sentimiento y la probabilidad exacta en tiempo real.

---

## 🗺️ Mapa de Endpoints Proyectado

Para que tengas una visión clara de lo que vamos a construir, así se verá tu documentación Swagger:

* `GET /raw/menciones` (Lista paginada de la base de datos).
* `GET /insights/tendencia/{candidato}` (Agrupación SQL por fechas).
* `POST /ml/analizar` (Inferencia en vivo pasando texto por el modelo).
* `POST /admin/sync-fuentes` (Dispara el scraper en background).

---

Este es un backend robusto, escalable y profesional.

¿Quieres que empecemos por crear la estructura de carpetas y el archivo `main.py` usando la arquitectura de **Routers y Lifespan** para gestionar el modelo de ML correctamente?