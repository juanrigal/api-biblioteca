# API de la Biblioteca

API REST con FastAPI para gestionar los libros de una biblioteca: crear, listar, actualizar, borrar, filtrar, paginar y buscar.
Los datos se guardan en `datos/libros.json` y sobreviven al reinicio del servidor.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate   # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Cómo correr

```bash
uvicorn main:app --reload
```

La documentación interactiva queda en http://127.0.0.1:8000/docs

## Endpoints

- `GET /` · `GET /libros` · `GET /libros/buscar?texto=...` · `GET /libros/estadisticas`
- `POST /libros` · `GET/PUT/PATCH/DELETE /libros/{id}`
- `POST /libros/{id}/prestar` · `POST /libros/{id}/devolver`