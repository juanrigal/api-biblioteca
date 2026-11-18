import json
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

app = FastAPI()

# La ruta se calcula desde la ubicación de main.py, no desde donde se ejecute.
CARPETA_DATOS = Path(__file__).parent / "datos"
ARCHIVO = CARPETA_DATOS / "libros.json"


# ---------------------------------------------------------------- modelos


class LibroEntrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    titulo: str = Field(min_length=3, max_length=100)
    autor: str = Field(min_length=3, max_length=60)
    anio: int = Field(ge=1000, le=2100)
    disponible: bool = True


class LibroParcial(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    titulo: str | None = Field(default=None, min_length=3, max_length=100)
    autor: str | None = Field(default=None, min_length=3, max_length=60)
    anio: int | None = Field(default=None, ge=1000, le=2100)
    disponible: bool | None = None


class Libro(LibroEntrada):
    id: int


# ------------------------------------------------------------ persistencia


def guardar():
    """Guarda la lista en disco: escribe un temporal y lo reemplaza."""
    CARPETA_DATOS.mkdir(exist_ok=True)
    temporal = ARCHIVO.with_name("libros.json.tmp")
    with open(temporal, "w", encoding="utf-8") as f:
        json.dump(libros, f, ensure_ascii=False, indent=2)
    temporal.replace(ARCHIVO)


def cargar():
    """Lee el archivo y valida cada libro; ante cualquier problema, lista vacía."""
    try:
        with open(ARCHIVO, encoding="utf-8") as f:
            datos = json.load(f)
        if not isinstance(datos, list):
            logger.warning("El archivo no contiene una lista, se arranca vacío")
            return []
        validos = [Libro.model_validate(d).model_dump() for d in datos]
    except FileNotFoundError:
        logger.info("No hay archivo de datos, se arranca vacío")
        return []
    except (OSError, ValueError):
        logger.warning("Archivo de datos dañado, se arranca vacío")
        return []
    return sorted(validos, key=lambda libro: libro["id"])


libros = cargar()
siguiente_id = max((libro["id"] for libro in libros), default=0) + 1


# ---------------------------------------------------------------- ayudas


def buscar_libro(libro_id: int):
    for libro in libros:
        if libro["id"] == libro_id:
            return libro
    raise HTTPException(status_code=404, detail="Libro no encontrado")


def existe_duplicado(titulo: str, autor: str) -> bool:
    for libro in libros:
        if (
            libro["titulo"].lower() == titulo.lower()
            and libro["autor"].lower() == autor.lower()
        ):
            return True
    return False


# ------------------------------------------------------------- endpoints
# Las rutas fijas (/libros/buscar, /libros/estadisticas) van ANTES de
# /libros/{libro_id}; si no, FastAPI intenta convertir "buscar" a entero.


@app.get("/")
def raiz():
    """Mensaje de bienvenida de la API."""
    return {"mensaje": "API de la biblioteca"}


@app.get("/libros", response_model=list[Libro])
def listar_libros(
    autor: str | None = None,
    disponible: bool | None = None,
    desde: int = Query(default=0, ge=0),
    limite: int = Query(default=100, ge=0),
):
    """Lista libros con filtros por autor y disponibilidad, y paginación."""
    resultado = libros
    if autor is not None:
        resultado = [
            libro for libro in resultado if libro["autor"].lower() == autor.lower()
        ]
    if disponible is not None:
        resultado = [libro for libro in resultado if libro["disponible"] == disponible]
    return resultado[desde : desde + limite]


@app.get("/libros/buscar", response_model=list[Libro])
def buscar_libros(texto: str):
    """Busca libros cuyo título o autor contenga el texto."""
    texto = texto.lower()
    return [
        libro
        for libro in libros
        if texto in libro["titulo"].lower() or texto in libro["autor"].lower()
    ]


@app.get("/libros/estadisticas")
def estadisticas():
    """Devuelve el total de libros, los disponibles y los prestados."""
    total = len(libros)
    disponibles = sum(1 for libro in libros if libro["disponible"])
    return {
        "total": total,
        "disponibles": disponibles,
        "prestados": total - disponibles,
    }


@app.post("/libros", status_code=201, response_model=Libro)
def crear_libro(libro: LibroEntrada):
    """Crea un libro nuevo; 409 si ya existe el mismo título y autor."""
    global siguiente_id
    if existe_duplicado(libro.titulo, libro.autor):
        raise HTTPException(status_code=409, detail="El libro ya existe")
    nuevo = {"id": siguiente_id, **libro.model_dump()}
    libros.append(nuevo)
    siguiente_id += 1
    guardar()
    logger.info("Libro creado con id %s", nuevo["id"])
    return nuevo


@app.get("/libros/{libro_id}", response_model=Libro)
def obtener_libro(libro_id: int):
    """Devuelve un libro por su id."""
    return buscar_libro(libro_id)


@app.put("/libros/{libro_id}", response_model=Libro)
def reemplazar_libro(libro_id: int, datos: LibroEntrada):
    """Reemplaza todos los campos de un libro."""
    libro = buscar_libro(libro_id)
    libro.update(datos.model_dump())
    guardar()
    logger.info("Libro reemplazado con id %s", libro_id)
    return libro


@app.patch("/libros/{libro_id}", response_model=Libro)
def actualizar_libro(libro_id: int, datos: LibroParcial):
    """Actualiza solo los campos enviados de un libro."""
    libro = buscar_libro(libro_id)
    cambios = datos.model_dump(exclude_unset=True)
    if any(valor is None for valor in cambios.values()):
        raise HTTPException(status_code=422, detail="Los campos no pueden ser null")
    libro.update(cambios)
    guardar()
    logger.info("Libro actualizado con id %s", libro_id)
    return libro


@app.delete("/libros/{libro_id}", status_code=204)
def borrar_libro(libro_id: int):
    """Borra un libro por su id."""
    libro = buscar_libro(libro_id)
    libros.remove(libro)
    guardar()
    logger.info("Libro borrado con id %s", libro_id)


@app.post("/libros/{libro_id}/prestar", response_model=Libro)
def prestar_libro(libro_id: int):
    """Marca un libro como prestado; 409 si ya lo estaba."""
    libro = buscar_libro(libro_id)
    if not libro["disponible"]:
        raise HTTPException(status_code=409, detail="El libro ya está prestado")
    libro["disponible"] = False
    guardar()
    return libro


@app.post("/libros/{libro_id}/devolver", response_model=Libro)
def devolver_libro(libro_id: int):
    """Marca un libro como disponible; 409 si ya lo estaba."""
    libro = buscar_libro(libro_id)
    if libro["disponible"]:
        raise HTTPException(status_code=409, detail="El libro ya está disponible")
    libro["disponible"] = True
    guardar()
    return libro