import flet as ft
import sqlite3
import os

DB_NAME = "taller.db"

def conectar_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

def crear_tablas_taller():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabla usuarios - déjala, es para el login
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Tabla mecánicos - NUEVA
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mecanicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT
        )
    ''')

    # Tabla trabajos - NUEVA 
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trabajos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE DEFAULT CURRENT_DATE,
            mecanico_id INTEGER,
            cliente TEXT,
            vehiculo TEXT,
            descripcion TEXT,
            costo_mano_obra REAL,
            costo_repuestos REAL,
            total REAL,
            estado TEXT DEFAULT 'Pendiente',
            FOREIGN KEY (mecanico_id) REFERENCES mecanicos(id)
        )
    ''')
    
    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, password) VALUES (?, ?)", ("admin", "1234"))
    conn.commit()
    conn.close()

def insertar_mecanico(nombre, telefono):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO mecanicos (nombre, telefono) VALUES (?,?)", (nombre, telefono))
    conn.commit()
    conn.close()

def obtener_mecanicos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM mecanicos ORDER BY nombre")
    resultado = cursor.fetchall()
    conn.close()
    return resultado

def insertar_trabajo(descripcion, mecanico_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO trabajos (descripcion, mecanico_id) VALUES (?,?)", (descripcion, mecanico_id))
    conn.commit()
    conn.close()

def obtener_trabajos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT t.id, t.descripcion, m.nombre FROM trabajos t LEFT JOIN mecanicos m ON t.mecanico_id = m.id ORDER BY t.id DESC")
    resultado = cursor.fetchall()
    conn.close()
    return resultado
    
def insertar_cliente(nombre, telefono, direccion):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO clientes (nombre, telefono, direccion) VALUES (?,?,?)",
                   (nombre, telefono, direccion))
    conn.commit()
    conn.close()

def verificar_usuario(usuario, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND password=?", (usuario, password))
    resultado = cursor.fetchone()
    conn.close()
    return resultado is not None

def crear_usuario(usuario, password):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (usuario, password) VALUES (?, ?)", (usuario, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def mostrar_login(page):
    usuario_input = ft.TextField(label="Usuario", width=300)
    password_input = ft.TextField(label="Contraseña", password=True, width=300)
    mensaje = ft.Text("", color="red")

    def iniciar_sesion(e):
        if verificar_usuario(usuario_input.value, password_input.value):
            mostrar_app(page)
        else:
            mensaje.value = "❌ Usuario o contraseña incorrectos"
            mensaje.color = "red"
            page.update()

    def registrar(e):
        if usuario_input.value == "" or password_input.value == "":
            mensaje.value = "⚠️ Completa usuario y contraseña"
            mensaje.color = "orange"
        elif crear_usuario(usuario_input.value, password_input.value):
            mensaje.value = "✅ Usuario creado. Ya puedes iniciar sesión"
            mensaje.color = "green"
        else:
            mensaje.value = "❌ Ese usuario ya existe"
            mensaje.color = "red"
        page.update()

    page.clean()
    page.add(
        ft.Column([
            ft.Text("Control Taller", size=40, weight="bold"),
            ft.Text("Inicia sesión", size=20),
            usuario_input,
            password_input,
            ft.Row([
                ft.ElevatedButton("Entrar", on_click=iniciar_sesion, width=145),
                ft.ElevatedButton("Registrar", on_click=registrar, width=145)
            ], alignment=ft.MainAxisAlignment.CENTER),
            mensaje
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
    )

def mostrar_app(page):
    def cerrar_sesion(e):
        mostrar_login(page)

    page.clean()
    page.add(
        ft.Column([
            ft.Text("Control Taller", size=35, weight="bold"),
            ft.Text("¿Qué hacemos hoy?", size=16, color="grey"),
            ft.ElevatedButton("Órdenes de Trabajo", width=300, on_click=lambda e: mostrar_trabajos(page)),
            ft.ElevatedButton("Vehículos", width=300, on_click=lambda e: mostrar_aviso(page, "Módulo en construcción 🚧")),
            ft.ElevatedButton("Cerrar sesión", icon=ft.icons.LOGOUT, color="red", width=300, on_click=lambda e: cerrar_sesion(page)),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
    )

def mostrar_mecanicos(page):
    nombre_input = ft.TextField(label="Nombre del mecánico", width=300)
    telefono_input = ft.TextField(label="Teléfono", width=300)

    def cargar_tabla():
        mecanicos = obtener_mecanicos()
        rows = [ft.DataRow(cells=[
            ft.DataCell(ft.Text(str(m[0]))),
            ft.DataCell(ft.Text(m[1])),
            ft.DataCell(ft.Text(m[2] or ""))
        ]) for m in mecanicos]
        return ft.DataTable(columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Nombre")),
            ft.DataColumn(ft.Text("Teléfono"))
        ], rows=rows)

    tabla = cargar_tabla()

    def agregar_mecanico(e):
        if nombre_input.value:
            insertar_mecanico(nombre_input.value, telefono_input.value)
            nombre_input.value = ""
            telefono_input.value = ""
            tabla.rows = cargar_tabla().rows
            page.update()

    page.clean()
    page.add(
        ft.Column([
            ft.Text("Gestión de Mecánicos", size=24, weight="bold"),
            nombre_input,
            telefono_input,
            ft.ElevatedButton("Guardar Mecánico", on_click=agregar_mecanico),
            ft.Divider(),
            ft.Text("Mecánicos registrados", size=20),
            tabla,
            ft.ElevatedButton("← Volver al menú", on_click=lambda e: mostrar_app(page))
        ], scroll=ft.ScrollMode.AUTO)
    )
    page.update()

def mostrar_trabajos(page):
    mecanicos = obtener_mecanicos()
if not mecanicos:
    page.clean()
    page.add(ft.Text("Primero registra al menos 1 mecánico"), ft.ElevatedButton("Volver", on_click=lambda e: mostrar_app(page)))
    page.update()
return
    
    desc_input = ft.TextField(label="Descripción del trabajo", width=300)
    mecanico_dropdown = ft.Dropdown(
        label="Mecánico",
        options=[ft.dropdown.Option(str(m[0]), m[1]) for m in obtener_mecanicos()],
        width=300
    )

    def cargar_tabla_trabajos():
        trabajos = obtener_trabajos()
        rows = [ft.DataRow(cells=[
            ft.DataCell(ft.Text(str(t[0]))),
            ft.DataCell(ft.Text(t[1])),
            ft.DataCell(ft.Text(t[2] or "Sin asignar"))
        ]) for t in trabajos]
        return ft.DataTable(columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Descripción")),
            ft.DataColumn(ft.Text("Mecánico"))
        ], rows=rows)

    tabla_trabajos = cargar_tabla_trabajos()

    def agregar_trabajo(e):
        if desc_input.value and mecanico_dropdown.value:
            insertar_trabajo(desc_input.value, int(mecanico_dropdown.value))
            desc_input.value = ""
            mecanico_dropdown.value = None
            mecanico_dropdown.options = [ft.dropdown.Option(str(m[0]), m[1]) for m in obtener_mecanicos()]
            tabla_trabajos.rows = cargar_tabla_trabajos().rows
            page.update()

    page.clean()
    page.add(
        ft.Column([
            ft.Text("Gestión de Trabajos", size=24, weight="bold"),
            desc_input,
            mecanico_dropdown,
            ft.ElevatedButton("Guardar Trabajo", on_click=agregar_trabajo),
            ft.Divider(),
            ft.Text("Trabajos registrados", size=20),
            tabla_trabajos,
            ft.ElevatedButton("← Volver al menú", on_click=lambda e: mostrar_app(page))
        ], scroll=ft.ScrollMode.AUTO)
    )
    page.update() 
def mostrar_aviso(page, mensaje):
    page.snack_bar = ft.SnackBar(ft.Text(mensaje), open=True)
    page.update()
    
def main(page: ft.Page):
    page.title = "Control Taller"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = "#1a1a1a"
    
    crear_tablas_taller()
    mostrar_login(page)

ft.app(target=main, port=int(os.getenv("PORT", 8080)), host="0.0.0.0", view=None)
