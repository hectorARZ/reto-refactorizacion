"""Modulo principal del gestor de inventario y ventas de "La Esquina".

Aqui vive casi toda la logica del negocio. Historicamente este archivo
lo fueron parchando varias personas, asi que hay de todo un poco.
"""

from datetime import datetime

# ---------------------------------------------------------------
# Estado global de la aplicacion (inventario, ventas y contadores)
# ---------------------------------------------------------------
INVENTARIO = {}
VENTAS = []
contadorVentas = 0
ultimo_error = ""
MODO_DEBUG = False


def reiniciar_sistema():
    """Borra todo el estado del sistema (inventario, ventas y folios)."""
    global contadorVentas, ultimo_error
    INVENTARIO.clear()
    VENTAS.clear()
    contadorVentas = 0
    ultimo_error = ""


def agregarProducto(codigo, nombre, precio, stock):
    # valida los datos y da de alta un producto en el inventario
    global ultimo_error
    if codigo is None or codigo == "":
        ultimo_error = "codigo vacio"
        return False
    if codigo in INVENTARIO:
        ultimo_error = "el producto ya existe"
        return False
    if precio <= 0:
        ultimo_error = "precio invalido"
        return False
    if stock < 0:
        ultimo_error = "stock invalido"
        return False
    x = {}
    x["codigo"] = codigo
    x["nombre"] = nombre
    x["precio"] = precio
    x["stock"] = stock
    INVENTARIO[codigo] = x
    return True


def eliminar_producto(codigo):
    """Quita un producto del inventario. Regresa False si no existe."""
    global ultimo_error
    if codigo in INVENTARIO:
        del INVENTARIO[codigo]
        return True
    ultimo_error = "producto no existe"
    return False


def actualizar_stock(codigo, cantidad):
    """Suma unidades al stock (o resta si la cantidad es negativa)."""
    global ultimo_error
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return False
    aux = INVENTARIO[codigo]["stock"] + cantidad
    if aux < 0:
        ultimo_error = "el stock no puede quedar negativo"
        return False
    INVENTARIO[codigo]["stock"] = aux
    return True


def buscarProducto(texto):
    # busca productos cuyo nombre contenga el texto (sin importar mayusculas)
    temp2 = []
    for k in INVENTARIO:
        if texto.lower() in INVENTARIO[k]["nombre"].lower():
            temp2.append(INVENTARIO[k])
    return temp2


def _validar_venta(codigo, cantidad):
    """Revisa que la venta se pueda hacer; si no, deja el motivo en ultimo_error."""
    global ultimo_error
    if codigo is None or codigo == "":
        ultimo_error = "codigo vacio"
        return False
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return False
    if cantidad is None or cantidad <= 0:
        ultimo_error = "cantidad invalida"
        return False
    if INVENTARIO[codigo]["stock"] < cantidad:
        ultimo_error = "stock insuficiente"
        return False
    return True


def _calcular_descuento_volumen(subtotal):
    """Descuento por volumen de compra: 10% desde $1000, 5% desde $500."""
    if subtotal >= 1000:
        return subtotal * 0.10
    if subtotal >= 500:
        return subtotal * 0.05
    return 0


def _es_cliente_vip(cliente):
    """Los clientes cuyo codigo empieza con VIP tienen un descuento extra."""
    return bool(cliente) and cliente.startswith("VIP")


def _calcular_descuento(subtotal, cliente):
    """Descuento total: por volumen, mas 2% del subtotal para clientes VIP
    cuya compra (ya con el descuento por volumen) pase de $200."""
    descuento = _calcular_descuento_volumen(subtotal)
    if _es_cliente_vip(cliente) and subtotal - descuento > 200:
        descuento = descuento + subtotal * 0.02
    return descuento


def _calcular_impuesto_y_total(base):
    """Calcula el IVA (16%) sobre la base y el total redondeado a 2 decimales."""
    impuesto = base * 0.16
    total = round(base + impuesto, 2)
    return impuesto, total


def _armar_ticket(venta):
    """Arma el ticket de la venta en texto plano."""
    lineas = [
        "TIENDA LA ESQUINA",
        "----------------------------",
        "Folio: " + str(venta["folio"]),
        venta["nombre"] + " x" + str(venta["cantidad"]),
        "Subtotal: $" + str(venta["subtotal"]),
    ]
    if venta["descuento"] > 0:
        lineas.append("Descuento: -$" + str(venta["descuento"]))
    lineas.append("IVA: $" + str(venta["impuesto"]))
    lineas.append("TOTAL: $" + str(venta["total"]))
    return "".join(linea + "\n" for linea in lineas)


def registrar_venta(codigo, cantidad, cliente=""):
    """Registra una venta: valida, calcula importes, descuenta el stock,
    asigna el folio, arma el ticket y guarda el registro en VENTAS.

    Si algo falla regresa None y deja el motivo en ultimo_error.
    """
    global contadorVentas
    if not _validar_venta(codigo, cantidad):
        return None
    producto = INVENTARIO[codigo]
    subtotal = producto["precio"] * cantidad
    descuento = _calcular_descuento(subtotal, cliente)
    impuesto, total = _calcular_impuesto_y_total(subtotal - descuento)

    producto["stock"] = producto["stock"] - cantidad
    contadorVentas = contadorVentas + 1
    venta = {
        "folio": contadorVentas,
        "codigo": codigo,
        "nombre": producto["nombre"],
        "cantidad": cantidad,
        "subtotal": round(subtotal, 2),
        "descuento": round(descuento, 2),
        "impuesto": round(impuesto, 2),
        "total": total,
        "cliente": cliente,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    venta["ticket"] = _armar_ticket(venta)
    VENTAS.append(venta)
    return venta


def cotizar(codigo, cantidad):
    """Calcula cuanto costaria una compra sin registrar la venta.

    Aplica el descuento por volumen y el IVA, pero no el descuento VIP
    ni revisa el stock.
    """
    global ultimo_error
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return None
    if cantidad is None or cantidad <= 0:
        ultimo_error = "cantidad invalida"
        return None
    subtotal = INVENTARIO[codigo]["precio"] * cantidad
    descuento = _calcular_descuento_volumen(subtotal)
    _, total = _calcular_impuesto_y_total(subtotal - descuento)
    return total


def calcular_descuento_viejo(monto):
    # NOTA: esta era la formula de descuentos que se uso hasta 2023,
    # ya nadie la llama pero la dejamos por si acaso
    if monto > 800:
        return monto * 0.08
    return 0


# def exportar_txt(ruta):
#     f = open(ruta, "w")
#     for k in INVENTARIO:
#         f.write(k + " - " + str(INVENTARIO[k]["stock"]) + "\n")
#     f.close()
#     return True
