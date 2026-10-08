# Gestor de inventario y ventas — Tienda "La Esquina"

## Comandos

* Instalar: `pip install -r requirements.txt`  (Python 3.10+)
* Ejecutar: `cd src && python main.py`
* Pruebas: `pytest`
* Linter: `ruff check src`

## Estructura

* `src/gestor.py`: productos y ventas.
* `src/almacen.py`: persistencia JSON.
* `src/reportes.py`: reportes e indicadores.
* `src/main.py`: menú de consola.

## Objetivo de la refactorización

* Nombres en snake_case, excepto `agregarProducto` y `buscarProducto`.
* Funciones cortas, con una sola responsabilidad.
* Añadir type hints a las funciones públicas cuando corresponda.
* Eliminar código duplicado.

## Ojo

* `tests/` y `pyproject.toml` NO se modifican.
* `agregarProducto` y `buscarProducto` conservan su nombre exacto (los usan los tests),
  aunque no sigan snake_case.
* El comportamiento observable debe ser idéntico: textos y orden del menú,
  formato y claves del JSON, y resultados de los reportes.
* No modificar ni borrar `datos_ejemplo.json`.

## Al terminar cada refactorización

* Ejecutar `pytest` y `ruff check src`.
* Si alguno falla, corregirlo antes de seguir. Si no se puede sin romper una regla
  de "Ojo", detenerse y avisar.
* Una refactorización a la vez; resumir qué cambió.