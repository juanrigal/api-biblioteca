from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

libros = []
siguiente_id = 1


class LibroEntrada(BaseModel):
    titulo: str
    autor: str
    anio: int
    disponible: bool = True


class Libro(LibroEntrada):
    id: int


def buscar_libro(id: int):
    for libro in libros:
        if libro["id"] == id:
            return libro
    raise HTTPException(status_code=404, detail="Libro no encontrado")


@app.get("/")
def raiz():
    return {"mensaje": "API de la biblioteca"}


@app.get("/libros", response_model=list[Libro])
def listar_libros():
    return libros


@app.post("/libros", status_code=201, response_model=Libro)
def crear_libro(libro: LibroEntrada):
    global siguiente_id
    nuevo = {"id": siguiente_id, **libro.model_dump()}
    libros.append(nuevo)
    siguiente_id += 1
    return nuevo


@app.get("/libros/{id}", response_model=Libro)
def obtener_libro(id: int):
    return buscar_libro(id)


@app.delete("/libros/{id}", status_code=204)
def borrar_libro(id: int):
    libro = buscar_libro(id)
    libros.remove(libro)