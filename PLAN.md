# Plan de refactorización — Tienda "La Esquina"

Estado de partida (rama `refactorizacion`, commit `eec738a`):

* `pytest`: 20/20 pruebas pasan.
* `ruff check src`: 13 errores (ya se aplicaron las correcciones automáticas de `--fix`).

Los problemas están ordenados **de mayor a menor impacto** en la calidad del código
(riesgo de errores, dificultad para entenderlo y mantenerlo, errores de ruff que
resuelve). Al final hay un orden de ejecución sugerido, porque algunos cambios
facilitan los siguientes.

## Reglas que aplican a todo el plan

* No se modifican `tests/`, `pyproject.toml` ni `datos_ejemplo.json`.
* `agregarProducto` y `buscarProducto` conservan su nombre exacto.
* El comportamiento observable no cambia: textos y orden del menú, formato y claves
  del JSON, mensajes de `ultimo_error` y resultados de los reportes.
* Las pruebas usan directamente `gestor.INVENTARIO`, `gestor.VENTAS`,
  `gestor.reiniciar_sistema()`, `gestor.registrar_venta()`, `gestor.cotizar()`,
  `gestor.actualizar_stock()`, `gestor.eliminar_producto()`, `almacen.guardar_datos()`,
  `almacen.cargar_datos()` y las funciones públicas de `reportes`: esos nombres y
  sus firmas se conservan.
* Una refactorización a la vez. Después de cada una: `pytest` y `ruff check src`, y un commit.

---

## 1. `registrar_venta` es una función gigante con validaciones anidadas

**Archivo:** `src/gestor.py` · **Ruff:** C901 (complejidad 12 > 10), SIM102 ×3, SIM108

**Problema.** Una sola función de ~75 líneas hace siete cosas: valida los datos, calcula
el subtotal, aplica el descuento por volumen, aplica el extra VIP, calcula el IVA y el
total, descuenta el stock y genera el folio, arma el registro de la venta y construye
el ticket en texto. La validación usa una "pirámide" de cuatro `if` anidados con sus
`else` al final, lo que obliga a leer de afuera hacia adentro para saber qué error
corresponde a qué condición. La regla VIP tiene otros cuatro `if` anidados. Las
variables se llaman `temp2`, `aux`, `desc` y `t`, lo que no ayuda a entender qué
representan. Es la función más importante del sistema y la más difícil de modificar
sin romper algo.

**Refactorización sugerida.** Dividirla en funciones pequeñas con una sola responsabilidad:

* `_validar_venta(codigo, cantidad) -> bool`: cláusulas de guarda planas (`if ...: return`),
  **en el mismo orden actual**: código vacío → producto no existe → cantidad inválida →
  stock insuficiente, con los mismos mensajes en `ultimo_error`.
* `_es_cliente_vip(cliente) -> bool`: `cliente` no vacío y que empiece con `"VIP"`
  (puede usarse `cliente.startswith("VIP")`, que equivale a `len >= 3 and [0:3] == "VIP"`).
* Las funciones de cálculo del punto 2 (descuento e importes).
* `_armar_ticket(venta) -> str`: construye el texto del ticket idéntico al actual
  (incluida la línea de descuento solo si es mayor que 0).
* `registrar_venta` queda como coordinadora: validar → calcular → descontar stock →
  folio → registro → ticket → agregar a `VENTAS`.

**Cuidado.** Conservar exactamente las mismas operaciones de punto flotante
(`aux * 0.10`, `desc + aux * 0.02`, `base * 0.16`, `round(..., 2)`); reordenarlas
puede cambiar centavos en los totales. El descuento VIP se suma sobre el **subtotal**
(`aux * 0.02`) y la condición usa el subtotal **ya con descuento** (`aux - desc > 200`).

---

## 2. Cálculo de precios duplicado entre `registrar_venta` y `cotizar`

**Archivo:** `src/gestor.py` · **Ruff:** contribuye a resolver SIM108

**Problema.** La regla de descuentos por volumen (10% si es de $1000 o más, 5% si es de
$500 o más) y el cálculo del IVA están copiados en las dos funciones, y además están
escritos de forma distinta (`if/else` anidado en una, sin `else` en la otra). Si mañana
cambia un porcentaje, hay que acordarse de cambiarlo en dos lugares; si se olvida uno,
la cotización y la venta dan totales distintos sin que nadie lo note. Existe una
prueba (`test_cotizar_coincide_con_el_total_de_la_venta`) precisamente porque este
riesgo es real.

**Refactorización sugerida.** Extraer funciones compartidas:

* `calcular_descuento_volumen(subtotal: float) -> float`
* `calcular_total(base: float) -> float` (o una que devuelva impuesto y total)

`cotizar` y `registrar_venta` las usan. **`cotizar` no debe empezar a aplicar el
descuento VIP ni a validar stock**, porque hoy no lo hace (eso sería un cambio de
comportamiento). También se conserva que `cotizar` con código vacío reporte
`"producto no existe"` (y no `"codigo vacio"` como `registrar_venta`).

---

## 3. `menu()` es una función gigante que mezcla todo

**Archivo:** `src/main.py` · **Ruff:** C901 (complejidad 17 > 10)

**Problema.** `menu()` carga los datos, imprime las opciones, lee la opción y contiene
la lógica de las 8 opciones en una sola cadena de `if/elif` de ~60 líneas. Para agregar
o cambiar una opción hay que tocar esa función enorme. Los nombres `c`, `n`, `p`, `s`,
`cant`, `cli`, `v`, `t` obligan a leer el contexto para entender cada línea.

**Refactorización sugerida.**

* Una función por opción: `_opcion_agregar_producto()`, `_opcion_registrar_venta()`,
  `_opcion_cotizar()`, `_opcion_reporte_inventario()`, etc.
* `_mostrar_menu()` con los textos de las opciones (idénticos y en el mismo orden).
* `_cargar_datos_iniciales()` para la bienvenida y la carga del archivo.
* Un diccionario `{"1": _opcion_agregar_producto, ...}` para despachar la opción; la
  opción `"8"` (guardar y salir) y la de "Opcion no valida." se manejan aparte.
* Nombres descriptivos (`codigo`, `nombre`, `precio`, `cantidad`, `cliente`, `venta`).

**Cuidado.** El orden de las preguntas (`input`) y todos los `print` deben quedar
exactamente iguales, incluida la línea vacía antes de cada menú.

---

## 4. Números mágicos dispersos

**Archivos:** `src/gestor.py`, `src/reportes.py` · **Ruff:** no lo detecta

**Problema.** Las reglas del negocio están escritas como números sueltos: `0.16` (IVA),
`1000`/`0.10` y `500`/`0.05` (descuentos por volumen), `200`/`0.02` y `"VIP"` (clientes
VIP) y `5` (stock mínimo, repetido en dos funciones de `reportes.py`). Quien lee el
código tiene que adivinar qué significa cada número, y cambiar una regla requiere
buscarlo en varios lugares.

**Refactorización sugerida.** Constantes con nombre al inicio de cada módulo:
`TASA_IVA = 0.16`, `MONTO_DESCUENTO_ALTO = 1000`, `TASA_DESCUENTO_ALTO = 0.10`,
`MONTO_DESCUENTO_MEDIO = 500`, `TASA_DESCUENTO_MEDIO = 0.05`, `PREFIJO_VIP = "VIP"`,
`MONTO_MINIMO_VIP = 200`, `TASA_DESCUENTO_VIP = 0.02`, `STOCK_MINIMO = 5`.
Los valores no cambian, solo se les da nombre.

---

## 5. Lógica duplicada y algoritmo innecesario en `reportes.py`

**Archivo:** `src/reportes.py` · **Ruff:** no lo detecta

**Problema.**

* `resumen_ventas` vuelve a sumar los totales con su propio ciclo en lugar de usar
  `total_vendido()`.
* `reporte_inventario` repite la condición de stock bajo (`< 5`) en lugar de reutilizar
  el mismo criterio que `productos_stock_bajo`.
* `mas_vendidos` implementa un ordenamiento de burbuja a mano (con su propio TODO
  pidiendo cambiarlo) y acumula las unidades con un `if/else` que `dict.get` resuelve
  en una línea.
* `hacer_cosa` es un nombre que no dice nada: en realidad da formato de dinero.

**Refactorización sugerida.**

* `hacer_cosa` → `formatear_dinero(valor: float) -> str`.
* Extraer `_tiene_stock_bajo(producto) -> bool` y usarla en ambos reportes.
* `resumen_ventas` usa `total_vendido()` para la línea del total.
* `mas_vendidos` usa `sorted(..., key=lambda par: par[1], reverse=True)[:n]`.

**Cuidado.** El ordenamiento de burbuja actual es estable (solo intercambia si es
estrictamente menor), y `sorted(..., reverse=True)` también lo es, así que los
empates se resuelven igual. `total_vendido()` redondea a 2 decimales y
`formatear_dinero` vuelve a redondear: el texto resultante es el mismo.

---

## 6. Los reportes mezclan cálculo con salida a pantalla

**Archivos:** `src/reportes.py`, `src/main.py` · **Ruff:** no lo detecta

**Problema.** `reporte_inventario` y `resumen_ventas` arman el texto, lo **imprimen** y
además lo regresan. Una función de reportes no debería decidir cómo se muestra el
resultado: eso impide reutilizarla (por ejemplo, para guardar el reporte en un
archivo) sin que se imprima en consola, y hace que las pruebas impriman basura.

**Refactorización sugerida.** Que ambas funciones solo regresen el texto, y que
`main.py` haga el `print(...)`. La salida en pantalla queda idéntica (el mismo
`print(texto)` ahora se hace desde el menú). Las pruebas solo revisan el texto
regresado, así que siguen pasando.

---

## 7. Código muerto

**Archivos:** `src/gestor.py`, `src/reportes.py` · **Ruff:** N802 y SIM115 de `reporteViejoCSV`

**Problema.** Hay código que nadie usa y que confunde a quien lo lee:
`calcular_descuento_viejo` (fórmula de 2023, "por si acaso"), la función comentada
`exportar_txt`, `reporteViejoCSV` ("ya no se usa") y la variable `MODO_DEBUG`.
Además, `reporteViejoCSV` genera dos de los errores de ruff. El historial de git ya
conserva ese código si algún día se necesita.

**Refactorización sugerida.** Eliminarlos. Antes, confirmar con una búsqueda que
nada en `src/` ni en `tests/` los usa (hoy ninguno lo hace).

---

## 8. Archivos abiertos sin `with`

**Archivo:** `src/almacen.py` · **Ruff:** SIM115 ×2

**Problema.** `guardar_datos` y `cargar_datos` usan `open()` + `close()` manual. Si
`json.dump` falla a la mitad, el archivo queda abierto. `cargar_datos` además tiene
que acordarse de cerrar el archivo en dos caminos distintos (error y éxito).

**Refactorización sugerida.** Usar `with open(...) as archivo:`. En `cargar_datos`,
leer el JSON dentro del `with` y conservar el mismo manejo de error
(`"archivo corrupto"` → `False`). Construir el diccionario de `guardar_datos` en una
sola expresión literal con las mismas claves (`inventario`, `ventas`, `contador`) y el
mismo `indent=2, ensure_ascii=False`.

**Cuidado.** `cargar_datos` debe seguir **vaciando y volviendo a llenar** el mismo
diccionario `INVENTARIO` y la misma lista `VENTAS` (no reasignarlos), porque los otros
módulos y las pruebas guardan referencias a esos objetos.

---

## 9. Nombres poco descriptivos o fuera de snake_case

**Archivos:** todos · **Ruff:** N802 (`hayArchivo`), N816 (`contadorVentas`), SIM103

**Problema.** Conviven estilos (`hayArchivo` y `guardar_datos` en el mismo módulo) y
hay nombres que no dicen nada: `x`, `d`, `f`, `t`, `aux`, `temp`, `temp2`, `k`.
`hayArchivo` además envuelve `os.path.exists` en un `if/else` que regresa `True`/`False`.

**Refactorización sugerida.**

* `hayArchivo` → `hay_archivo` con `return os.path.exists(ruta)` (y actualizar `main.py`).
* `contadorVentas` → `contador_ventas` (actualizar `gestor.py` y `almacen.py`; la clave
  `"contador"` del JSON **no** cambia).
* Variables locales con nombres descriptivos (`producto`, `venta`, `subtotal`,
  `descuento`, `datos`, `archivo`, `resultados`...).
* `agregarProducto` y `buscarProducto` **no se renombran**.

---

## 10. Faltan type hints y documentación uniforme

**Archivos:** todos · **Ruff:** no lo detecta

**Problema.** Ninguna función declara los tipos de sus parámetros ni de su valor de
retorno, así que hay que leer el cuerpo para saber si `registrar_venta` regresa un
`dict` o `None`, o si `precio` es `int` o `float`. Algunas funciones se documentan
con docstring y otras con un comentario (`agregarProducto`, `buscarProducto`,
`hayArchivo`, `pedir_numero`).

**Refactorización sugerida.** Agregar type hints a las funciones públicas
(`def registrar_venta(codigo: str, cantidad: int, cliente: str = "") -> dict | None:`,
`def mas_vendidos(n: int = 3) -> list[tuple[str, int]]:`, etc.) y convertir los
comentarios descriptivos en docstrings.

---

## 11. Estado global (alcance limitado)

**Archivos:** `src/gestor.py`, `src/almacen.py`, `src/reportes.py`

**Problema.** Todo el sistema depende de variables globales de módulo (`INVENTARIO`,
`VENTAS`, `contadorVentas`, `ultimo_error`) que se modifican con `global` desde varias
funciones y desde otro módulo (`almacen`). Esto acopla los módulos y hace que el
estado de una prueba pueda contaminar la siguiente (por eso existe el fixture
`sistema_limpio`).

**Refactorización sugerida (opcional).** Eliminarlo por completo no es posible sin
romper las pruebas, que usan `gestor.INVENTARIO` y `gestor.VENTAS` directamente. Se
puede reducir el acoplamiento sin cambiar esa interfaz: que `almacen` no escriba
directamente en las variables de `gestor`, sino que llame a funciones de `gestor`
como `exportar_estado() -> dict` y `restaurar_estado(datos)`. Es el cambio con más
riesgo y menos beneficio dentro de las reglas del reto, por eso va al final.

---

## Fuera de alcance (anotado, no se cambia)

* `ARCHIVO = "datos_ejemplo.json"` es relativo al directorio desde donde se ejecuta.
  Ejecutando desde la raíz, la opción 8 sobrescribiría `datos_ejemplo.json`. Cambiar la
  ruta alteraría qué archivo se carga, es decir, el comportamiento observable, así que
  no se modifica. Ejecutar siempre con `cd src && python main.py`.
* `cotizar` no aplica el descuento VIP: puede ser un error de negocio, pero corregirlo
  cambia resultados. Se conserva tal cual.

## Orden de ejecución sugerido

El impacto decide la prioridad, pero algunos cambios preparan el terreno para otros:

| Paso | Refactorización | Puntos del plan | Errores de ruff que resuelve |
|------|-----------------|-----------------|------------------------------|
| 1 | Eliminar código muerto | 7 | N802 (`reporteViejoCSV`), SIM115 (reportes) |
| 2 | Constantes para los números mágicos | 4 | — |
| 3 | Extraer el cálculo de precios compartido | 2 | SIM108 |
| 4 | Dividir `registrar_venta` | 1 | C901, SIM102 ×3 |
| 5 | Dividir `menu()` | 3 | C901 |
| 6 | Simplificar `reportes.py` y separar la salida a pantalla | 5, 6 | — |
| 7 | `with` en `almacen.py` | 8 | SIM115 ×2 |
| 8 | Nombres en snake_case y descriptivos | 9 | N802, N816, SIM103 |
| 9 | Type hints y docstrings | 10 | — |
| 10 | (Opcional) Reducir el estado global | 11 | — |

Al terminar el paso 8, `ruff check src` debe reportar **0 errores**, y `pytest` debe
pasar 20/20 después de cada paso.
