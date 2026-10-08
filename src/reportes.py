"""Reportes de la tienda: inventario, ventas y mas vendidos."""

import gestor

# Un producto tiene stock bajo si le quedan menos unidades que este minimo
STOCK_MINIMO = 5


def formatear_dinero(valor):
    """Da formato de dinero a un numero: signo de pesos y 2 decimales."""
    return "$" + str(round(valor, 2))


def _tiene_stock_bajo(producto):
    """Indica si al producto le quedan menos unidades que STOCK_MINIMO."""
    return producto["stock"] < STOCK_MINIMO


def productos_stock_bajo():
    """Regresa la lista de productos con stock por debajo del minimo."""
    return [p for p in gestor.INVENTARIO.values() if _tiene_stock_bajo(p)]


def _linea_inventario(producto):
    """Arma la linea del reporte de inventario para un producto."""
    linea = (
        producto["codigo"] + " | " + producto["nombre"] + " | "
        + formatear_dinero(producto["precio"]) + " | stock: " + str(producto["stock"])
    )
    if _tiene_stock_bajo(producto):
        linea = linea + "  <-- STOCK BAJO"
    return linea


def reporte_inventario():
    """Arma el reporte del inventario, lo imprime y lo regresa como texto."""
    texto = "===== INVENTARIO =====\n"
    valor_total = 0
    for producto in gestor.INVENTARIO.values():
        texto = texto + _linea_inventario(producto) + "\n"
        valor_total = valor_total + producto["precio"] * producto["stock"]
    texto = texto + "Valor total del inventario: "
    texto = texto + formatear_dinero(valor_total) + "\n"
    print(texto)
    return texto


def total_vendido():
    """Suma el total (con IVA) de todas las ventas registradas."""
    total = 0
    for venta in gestor.VENTAS:
        total = total + venta["total"]
    return round(total, 2)


def mas_vendidos(n=3):
    """Regresa los n productos mas vendidos como lista de (codigo, unidades).

    Los empates conservan el orden en que se vendio cada producto por primera vez.
    """
    unidades = {}
    for venta in gestor.VENTAS:
        codigo = venta["codigo"]
        unidades[codigo] = unidades.get(codigo, 0) + venta["cantidad"]
    ranking = sorted(unidades.items(), key=lambda par: par[1], reverse=True)
    return ranking[:n]


def resumen_ventas():
    """Arma el resumen de ventas del dia, lo imprime y lo regresa."""
    texto = "===== RESUMEN DE VENTAS =====\n"
    for venta in gestor.VENTAS:
        texto = texto + "Folio " + str(venta["folio"]) + ": " + venta["nombre"]
        texto = texto + " x" + str(venta["cantidad"]) + " = "
        texto = texto + formatear_dinero(venta["total"]) + "\n"
    texto = texto + "Numero de ventas: " + str(len(gestor.VENTAS)) + "\n"
    texto = texto + "Total del dia: " + formatear_dinero(total_vendido()) + "\n"
    print(texto)
    return texto


def reporteViejoCSV(ruta):
    # version vieja del reporte que pedia contabilidad, ya no se usa
    # desde que cambiaron de sistema, pero por si las dudas aqui sigue
    f = open(ruta, "w", encoding="utf-8")
    f.write("codigo,nombre,stock\n")
    for k in gestor.INVENTARIO:
        p = gestor.INVENTARIO[k]
        f.write(p["codigo"] + "," + p["nombre"] + "," + str(p["stock"]) + "\n")
    f.close()
    return ruta
