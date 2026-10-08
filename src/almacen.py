"""Persistencia del gestor: carga y guardado de datos en JSON."""

import json
import os

import gestor


def guardar_datos(ruta):
    """Guarda el inventario, las ventas y el folio actual en un JSON."""
    datos = {
        "inventario": gestor.INVENTARIO,
        "ventas": gestor.VENTAS,
        "contador": gestor.contadorVentas,
    }
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=2, ensure_ascii=False)
    return True


def cargar_datos(ruta):
    """Lee el archivo JSON y deja los datos en el estado global.

    Regresa False si el archivo no existe o esta corrupto. Vacia y vuelve a
    llenar los mismos INVENTARIO y VENTAS (no los reemplaza), porque otros
    modulos guardan referencias a esos objetos.
    """
    if not os.path.exists(ruta):
        gestor.ultimo_error = "el archivo no existe"
        return False
    with open(ruta, encoding="utf-8") as archivo:
        try:
            datos = json.load(archivo)
        except Exception:
            gestor.ultimo_error = "archivo corrupto"
            return False
    gestor.INVENTARIO.clear()
    for codigo in datos["inventario"]:
        gestor.INVENTARIO[codigo] = datos["inventario"][codigo]
    gestor.VENTAS.clear()
    gestor.VENTAS.extend(datos["ventas"])
    gestor.contadorVentas = datos.get("contador", 0)
    return True


def hayArchivo(ruta):
    # checa si ya existe el archivo de datos
    if os.path.exists(ruta):
        return True
    else:
        return False
