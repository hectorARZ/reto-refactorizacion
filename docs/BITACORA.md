# Bitácora de refactorización

**Nombre:**
**Matrícula:**
**Fecha:** 2026-10-08

Registra aquí **cada refactorización** que realices con Claude Code. Copia el
prompt tal cual lo escribiste (o un resumen fiel si fue una conversación larga),
describe el cambio que se aplicó al código y justifica por qué mejora la calidad.
Después de cada cambio ejecuta `pytest` y anota el resultado.

## Preparación: análisis del proyecto y armado del plan

Prompts previos a las refactorizaciones, usados para entender el código y construir
`PLAN.md`. Los prompts se copian tal cual se escribieron.

| #  | Prompt usado | Resultado | Verificación |
|----|--------------|-----------|--------------|
| P1 | "Inicializa un repositorio git de este proyecto, realiza un commit estado inicial con todo el proyecto y muestrame el log" | Repositorio inicializado en la rama `main`. Commit `Estado inicial` con 16 archivos (927 líneas). `.venv/`, cachés y `.DS_Store` quedaron excluidos por el `.gitignore`. | `git log` muestra el commit; árbol de trabajo limpio. |
| P2 | "Necesito un mapa del proyecto: que hace cada archivo, explicación de las funciones, el flujo del proyecto, solamente eso un análisis no modifiques nada aun" | Mapa de archivos, explicación de cada función, diagrama del flujo del menú y lista de observaciones. Se detectó que los comandos de `CLAUDE.md` (`pip install -e .`, `python -m src.main`) no funcionaban, que la ruta del archivo de datos es relativa al directorio de ejecución, y se identificaron código duplicado, código muerto y números mágicos. | `pytest`: 20 passed. `ruff check src`: 20 errores. `python -m src.main` falla con `ModuleNotFoundError: No module named 'gestor'`. Sin cambios en los archivos (`git status` limpio). |
| P3 | "corre de nuevo el ruff y muestrame la salida para tener una vision de los problemas que hay en el codigo, ademas<br><br>Los comandos de tu `CLAUDE.md` no funcionan tal cual. Probé `python -m src.main` y falla con `ModuleNotFoundError: gestor`. La forma correcta es la del README: `cd src && python main.py`. Además, `pyproject.toml` no tiene sección `[project]`, así que es probable que `pip install -e .` tampoco funcione. Lo correcto es `pip install -r requirements.txt`.<br><br>corrigue eso" | Salida completa de `ruff check src` clasificada por tipo de error. En `CLAUDE.md` se cambiaron solo los comandos: Instalar → `pip install -r requirements.txt`; Ejecutar → `cd src && python main.py`. | `ruff check src`: 20 errores (C901 ×2, SIM102 ×3, SIM115 ×3, N802 ×2, N816, SIM103, SIM108, UP009 ×4, UP015, I001, F401); 7 corregibles con `--fix`. |
| P4 | "Ahora, en estos momentos si corremos el comando ruff check src --fix, afectara en algo cuando empezemos las refactorizaciones de los problemas criticos?" | Se revisó con `ruff check src --diff` (sin aplicar cambios) qué haría `--fix`: quitar las declaraciones `# -*- coding: utf-8 -*-`, quitar el modo `"r"` en `open`, quitar el `import os` sin usar en `reportes.py` y ordenar los imports de `main.py`. Conclusión: no toca lógica ni se cruza con los errores que requieren refactorización; conviene hacerlo antes, en un commit aparte, y sin `--unsafe-fixes`. | `ruff --diff`: "Would fix 7 errors". Ningún archivo modificado. |
| P5 | "inicialmente corramos ruff check src --fix, verifica al final todo de nuevo" | Se aplicaron las 7 correcciones automáticas en `src/`. Se hizo commit por separado (`Corregir comandos de instalación y ejecución en CLAUDE.md` y `Aplicar correcciones automáticas de ruff (--fix)`). No cuenta como refactorización significativa (cambio cosmético). | `ruff check src --fix`: "Found 20 errors (7 fixed, 13 remaining)". `pytest`: 20 passed in 0.18s. `tests/`, `pyproject.toml` y `datos_ejemplo.json` sin cambios. |
| P6 | "Crea un plan para la refactorización del codigo, donde ordenes los problemas de mayor a menor impacto en el codigo, y guardalo en PLAN.md<br>dando una explicacion del problema y la sugerencia de refactorizacion a realizar" | `PLAN.md` con 11 problemas ordenados por impacto (problema, refactorización sugerida, errores de ruff que resuelve y precauciones para no cambiar el comportamiento), una sección de cosas fuera de alcance y un orden de ejecución sugerido que cubre los 13 errores de ruff restantes. | Documento; no modifica código. Se verificó que los nombres a renombrar (`contadorVentas`, `hayArchivo`, `hacer_cosa`, `reporteViejoCSV`) no se usan en `tests/`. |

## Refactorizaciones

| #  | Prompt usado | Cambio realizado | Justificación | Tests OK |
|----|--------------|------------------|---------------|----------|
| 1  | "Implementa el punto 1 del `PLAN.md`." | En `src/gestor.py` se dividió `registrar_venta` (~75 líneas) en funciones con una sola responsabilidad: `_validar_venta` (cláusulas de guarda planas, mismo orden y mismos mensajes en `ultimo_error`), `_calcular_descuento_volumen` (10% desde $1000, 5% desde $500), `_es_cliente_vip` (`startswith("VIP")`), `_calcular_descuento` (volumen + 2% VIP si la compra ya con descuento pasa de $200) y `_armar_ticket`. `registrar_venta` quedó como coordinadora (~30 líneas) y arma el registro como diccionario literal. Variables renombradas: `temp2` → `producto`, `aux` → `subtotal`, `desc` → `descuento`, `t` → `lineas`. `cotizar` no se tocó (le corresponde al punto 2). | La función más importante del sistema hacía siete cosas y tenía dos "pirámides" de `if` anidados (validación y regla VIP), lo que la hacía difícil de leer y riesgosa de modificar. Ahora cada regla de negocio está en una función con nombre propio que se puede leer, probar y reutilizar por separado (`_calcular_descuento_volumen` servirá para eliminar la duplicación con `cotizar` en el punto 2). Se conservaron exactamente las operaciones de punto flotante y los tipos (un descuento de `0` sigue siendo entero en el JSON). | Sí. `pytest`: 20 passed in 0.12s. `ruff check src`: de 13 a 8 errores (se resolvieron C901 de `registrar_venta`, SIM102 ×3 y SIM108; los 8 restantes corresponden a otros puntos del plan). Prueba de equivalencia adicional: 10,000 ventas aleatorias comparando la versión anterior (commit `eec738a`) contra la nueva → totales, tipos, tickets, mensajes de error, stock y folios idénticos (1,499 ventas exitosas y el resto rechazadas con el mismo error). Nota: la primera corrida de esa comparación falló por un error en el script de comparación (generaba productos distintos para cada versión), no en el código refactorizado; se corrigió el script y pasó. |
| 2  |              |                  |               |          |
| 3  |              |                  |               |          |
| 4  |              |                  |               |          |
| 5  |              |                  |               |          |

> Agrega más filas si realizas más de 5 refactorizaciones.

## Reflexión final (10-15 líneas)

Responde: ¿Qué tan útil fue Claude Code para detectar y corregir los problemas?
¿Qué propuso la IA que tú no habías notado? ¿En qué casos tuviste que corregir
o rechazar sus sugerencias? ¿Qué aprendiste sobre refactorizar con apoyo de IA?

*(Escribe aquí tu reflexión)*
