"""Punto de entrada del gestor de tienda (menu interactivo en consola)."""

import almacen
import gestor
import reportes

ARCHIVO = "datos_ejemplo.json"


def pedir_numero(mensaje):
    # pide un numero al usuario hasta que escriba algo valido
    while True:
        temp2 = input(mensaje)
        try:
            return float(temp2)
        except ValueError:
            print("Eso no es un numero, intenta de nuevo.")


OPCIONES_MENU = (
    "1) Agregar producto",
    "2) Registrar venta",
    "3) Cotizar",
    "4) Reporte de inventario",
    "5) Resumen de ventas",
    "6) Mas vendidos",
    "7) Alertas de stock bajo",
    "8) Guardar y salir",
)
OPCION_SALIR = "8"


def _imprimir_error():
    """Muestra el motivo de la ultima operacion fallida."""
    print("Error:", gestor.ultimo_error)


def _cargar_datos_iniciales():
    """Da la bienvenida y carga los datos guardados, si existen."""
    print("Bienvenido al gestor de la tienda La Esquina")
    if almacen.hayArchivo(ARCHIVO):
        almacen.cargar_datos(ARCHIVO)
        print("Datos cargados de", ARCHIVO)


def _mostrar_menu():
    """Imprime las opciones del menu, precedidas de una linea vacia."""
    print("")
    for opcion in OPCIONES_MENU:
        print(opcion)


def _opcion_agregar_producto():
    codigo = input("Codigo: ")
    nombre = input("Nombre: ")
    precio = pedir_numero("Precio: ")
    stock = int(pedir_numero("Stock inicial: "))
    if gestor.agregarProducto(codigo, nombre, precio, stock):
        print("Producto agregado.")
    else:
        _imprimir_error()


def _opcion_registrar_venta():
    codigo = input("Codigo del producto: ")
    cantidad = int(pedir_numero("Cantidad: "))
    cliente = input("Codigo de cliente (enter si no tiene): ")
    venta = gestor.registrar_venta(codigo, cantidad, cliente)
    if venta is not None:
        print(venta["ticket"])
    else:
        _imprimir_error()


def _opcion_cotizar():
    codigo = input("Codigo del producto: ")
    cantidad = int(pedir_numero("Cantidad: "))
    total = gestor.cotizar(codigo, cantidad)
    if total is not None:
        print("Total estimado (con IVA): $" + str(total))
    else:
        _imprimir_error()


def _opcion_reporte_inventario():
    reportes.reporte_inventario()


def _opcion_resumen_ventas():
    reportes.resumen_ventas()


def _opcion_mas_vendidos():
    for codigo, unidades in reportes.mas_vendidos():
        print(codigo, "->", unidades, "unidades")


def _opcion_stock_bajo():
    bajos = reportes.productos_stock_bajo()
    if not bajos:
        print("No hay productos con stock bajo.")
        return
    for producto in bajos:
        print("OJO:", producto["nombre"], "solo tiene", producto["stock"], "unidades")


def _guardar_y_salir():
    almacen.guardar_datos(ARCHIVO)
    print("Datos guardados. Hasta luego.")


ACCIONES = {
    "1": _opcion_agregar_producto,
    "2": _opcion_registrar_venta,
    "3": _opcion_cotizar,
    "4": _opcion_reporte_inventario,
    "5": _opcion_resumen_ventas,
    "6": _opcion_mas_vendidos,
    "7": _opcion_stock_bajo,
}


def menu():
    """Ciclo principal: muestra el menu y ejecuta la opcion elegida."""
    _cargar_datos_iniciales()
    while True:
        _mostrar_menu()
        opcion = input("Opcion: ")
        if opcion == OPCION_SALIR:
            _guardar_y_salir()
            break
        accion = ACCIONES.get(opcion)
        if accion is None:
            print("Opcion no valida.")
        else:
            accion()


if __name__ == "__main__":
    menu()
