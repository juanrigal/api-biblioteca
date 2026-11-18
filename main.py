from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field   

app = FastAPI()

libros = []
siguiente_id = 1

class LibroEntrada(BaseModel):
    titulo: str = Field(min_length=3, max_length=100)
    autor: str = Field(min_length=3, max_length=60)
    anio: int = Field(ge=1000, le=2100) 
    disponible: bool = True



class LibroEntrada(BaseModel):
    titulo: str
    autor: str
    anio: int
    disponible: bool = True

class LibroParcial(BaseModel):
    titulo: str | None = Field(default=None, min_length=3, max_length=100)
    autor: str | None = Field(default=None, min_length=3, max_length=60)
    anio: int | None = Field(default=None, ge=1000, le=2100)
    disponible: bool | None = None

class Libro(LibroEntrada):
    id: int


def buscar_libro(id: int):
    for libro in libros:
        if libro["id"] == id:
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


@app.get("/")
def raiz():
    return {"mensaje": "API de la biblioteca"}


@app.get("/libros", response_model=list[Libro])
def listar_libros(
    autor: str | None = None,
    disponible: bool | None = None,
    desde: int = Query(default=0, ge=0),
    limite: int = Query(default=100, ge=0),
):
    resultado = libros
    if autor is not None:
        resultado = [
            libro for libro in resultado
            if libro["autor"].lower() == autor.lower()
        ]
    if disponible is not None:
        resultado = [
            libro for libro in resultado
            if libro["disponible"] == disponible
        ]
    return resultado[desde:desde + limite]


@app.post("/libros", status_code=201, response_model=Libro)
def crear_libro(libro: LibroEntrada):
    global siguiente_id
    if existe_duplicado(libro.titulo, libro.autor):
        raise HTTPException(status_code=409, detail="El libro ya existe")
    nuevo = {"id": siguiente_id, **libro.model_dump()}
    libros.append(nuevo)
    siguiente_id += 1
    return nuevo


@app.get("/libros/{id}", response_model=Libro)
def obtener_libro(id: int):
    return buscar_libro(id)

@app.put("/libros/{id}", responde_model=Libro)
def reemplazar_libro(id: int, datos: LibroEntrada):
    libro = buscar_libro(id)
    libro.update(datos.model_dump())
    return libro

@app.patch("/libros/{id}", response_model=Libro)
def actualizar_libro(id: int, datos: LibroParcial):
    libro = buscar_libro(id)
    cambios = datos.model_dump(exclude_unset=True)
    if None in cambios.values():
        raise HTTPException(status_code=422, detail="Los campos no pueden ser null")
    libro.update(cambios)
    return libro


@app.delete("/libros/{id}", status_code=204)
def borrar_libro(id: int):
    libro = buscar_libro(id)
    libros.remove(libro)