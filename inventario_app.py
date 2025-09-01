# Sistema Avanzado de Gestión de Inventario
# Proyecto personalizado para NEOS Pizza
# Usa POO + Colecciones (diccionario) + SQLite
# Autor: Estefania Karen Alvarado Santi

from dataclasses import dataclass
from typing import Dict, List
import sqlite3
import sys

DB_PATH = "inventario.db"  # Se crea automáticamente en la carpeta del proyecto

# ------------------ Clase Producto ------------------
@dataclass
class Producto:
    id: int
    nombre: str
    cantidad: int
    precio: float

    def get_id(self): return self.id
    def set_id(self, nuevo_id: int): self.id = nuevo_id

    def get_nombre(self): return self.nombre
    def set_nombre(self, nuevo_nombre: str): self.nombre = nuevo_nombre

    def get_cantidad(self): return self.cantidad
    def set_cantidad(self, nueva_cantidad: int): self.cantidad = nueva_cantidad

    def get_precio(self): return self.precio
    def set_precio(self, nuevo_precio: float): self.precio = nuevo_precio


# ------------------ Clase Inventario ------------------
class Inventario:
    """
    Maneja los productos en un diccionario {id: Producto}
    y los sincroniza con la base de datos SQLite.
    """
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._crear_tabla_si_no_existe()
        self.productos: Dict[int, Producto] = {}
        self._cargar_desde_bd()

    def _crear_tabla_si_no_existe(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                cantidad INTEGER NOT NULL CHECK (cantidad >= 0),
                precio REAL NOT NULL CHECK (precio >= 0)
            );
        """)
        self.conn.commit()

    def _cargar_desde_bd(self):
        self.productos.clear()
        cur = self.conn.execute("SELECT id, nombre, cantidad, precio FROM productos ORDER BY id;")
        for row in cur.fetchall():
            p = Producto(id=row[0], nombre=row[1], cantidad=row[2], precio=row[3])
            self.productos[p.id] = p

    def _existe_id(self, id_: int) -> bool:
        return id_ in self.productos

    # ---------------- CRUD ----------------
    def agregar_producto(self, producto: Producto) -> bool:
        if self._existe_id(producto.id):
            return False
        try:
            self.conn.execute(
                "INSERT INTO productos (id, nombre, cantidad, precio) VALUES (?, ?, ?, ?);",
                (producto.id, producto.nombre, producto.cantidad, producto.precio),
            )
            self.conn.commit()
            self.productos[producto.id] = producto
            return True
        except sqlite3.IntegrityError:
            return False

    def eliminar_producto(self, id_: int) -> bool:
        if not self._existe_id(id_):
            return False
        self.conn.execute("DELETE FROM productos WHERE id = ?;", (id_,))
        self.conn.commit()
        self.productos.pop(id_, None)
        return True

    def actualizar_cantidad(self, id_: int, nueva_cantidad: int) -> bool:
        if not self._existe_id(id_):
            return False
        self.conn.execute("UPDATE productos SET cantidad = ? WHERE id = ?;", (nueva_cantidad, id_))
        self.conn.commit()
        self.productos[id_].set_cantidad(nueva_cantidad)
        return True

    def actualizar_precio(self, id_: int, nuevo_precio: float) -> bool:
        if not self._existe_id(id_):
            return False
        self.conn.execute("UPDATE productos SET precio = ? WHERE id = ?;", (nuevo_precio, id_))
        self.conn.commit()
        self.productos[id_].set_precio(nuevo_precio)
        return True

    def buscar_por_nombre(self, nombre: str) -> List[Producto]:
        nombre_norm = nombre.strip().lower()
        return [p for p in self.productos.values() if nombre_norm in p.nombre.lower()]

    def listar_todos(self) -> List[Producto]:
        return list(self.productos.values())

    def cerrar(self):
        self.conn.close()


# ------------------ Productos iniciales NEOS Pizza ------------------
def cargar_ejemplo_neos(inventario: Inventario):
    if inventario.listar_todos():
        return
    ejemplos = [
        Producto(id=101, nombre="Harina 1kg", cantidad=20, precio=2.50),
        Producto(id=102, nombre="Queso Mozzarella 1kg", cantidad=15, precio=6.00),
        Producto(id=103, nombre="Salsa de Tomate 500g", cantidad=30, precio=1.80),
        Producto(id=104, nombre="Orégano 50g", cantidad=40, precio=0.50),
        Producto(id=105, nombre="Caja para Pizza (mediana)", cantidad=200, precio=0.30),
        Producto(id=106, nombre="Aceite 1L", cantidad=10, precio=3.20),
        Producto(id=107, nombre="Bebida 1.5L", cantidad=50, precio=1.50),
        Producto(id=108, nombre="Pepperoni 500g", cantidad=12, precio=4.00),
    ]
    for p in ejemplos:
        inventario.agregar_producto(p)
    print("✔ Inventario inicial de NEOS Pizza cargado con productos de ejemplo.\n")


# ------------------ Interfaz Usuario (Consola) ------------------
def pedir_int(mensaje: str) -> int:
    while True:
        try:
            return int(input(mensaje))
        except ValueError:
            print("Debe ser un número entero.")

def pedir_float(mensaje: str) -> float:
    while True:
        try:
            return float(input(mensaje))
        except ValueError:
            print("Debe ser un número decimal (usa punto).")

def imprimir_producto(p: Producto):
    print(f"ID: {p.id} | Nombre: {p.nombre} | Cantidad: {p.cantidad} | Precio: ${p.precio:.2f}")

def menu():
    print("\n=== INVENTARIO NEOS PIZZA ===")
    print("1) Añadir producto")
    print("2) Eliminar producto por ID")
    print("3) Actualizar cantidad")
    print("4) Actualizar precio")
    print("5) Buscar por nombre")
    print("6) Mostrar todos")
    print("0) Salir")

def main():
    inventario = Inventario(DB_PATH)
    cargar_ejemplo_neos(inventario)
    try:
        while True:
            menu()
            opcion = input("Selecciona una opción: ").strip()

            if opcion == "1":
                print("\n[AÑADIR PRODUCTO]")
                id_ = pedir_int("ID: ")
                nombre = input("Nombre: ").strip()
                cantidad = pedir_int("Cantidad: ")
                precio = pedir_float("Precio: ")
                nuevo = Producto(id=id_, nombre=nombre, cantidad=cantidad, precio=precio)
                if inventario.agregar_producto(nuevo):
                    print("✔ Producto agregado.")
                else:
                    print("✖ No se pudo agregar (ID duplicado).")

            elif opcion == "2":
                id_ = pedir_int("ID a eliminar: ")
                if inventario.eliminar_producto(id_):
                    print("✔ Producto eliminado.")
                else:
                    print("✖ ID no encontrado.")

            elif opcion == "3":
                id_ = pedir_int("ID: ")
                nueva_cantidad = pedir_int("Nueva cantidad: ")
                if inventario.actualizar_cantidad(id_, nueva_cantidad):
                    print("✔ Cantidad actualizada.")
                else:
                    print("✖ ID no encontrado.")

            elif opcion == "4":
                id_ = pedir_int("ID: ")
                nuevo_precio = pedir_float("Nuevo precio: ")
                if inventario.actualizar_precio(id_, nuevo_precio):
                    print("✔ Precio actualizado.")
                else:
                    print("✖ ID no encontrado.")

            elif opcion == "5":
                nombre = input("Buscar nombre: ")
                resultados = inventario.buscar_por_nombre(nombre)
                if resultados:
                    for p in resultados:
                        imprimir_producto(p)
                else:
                    print("No se encontraron productos.")

            elif opcion == "6":
                productos = inventario.listar_todos()
                if productos:
                    for p in productos:
                        imprimir_producto(p)
                else:
                    print("Inventario vacío.")

            elif opcion == "0":
                print("Saliendo...")
                break
            else:
                print("Opción inválida.")
    finally:
        inventario.cerrar()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPrograma interrumpido.")
        sys.exit(0)