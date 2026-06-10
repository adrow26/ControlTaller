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
def insertar_cliente(nombre, telefono, direccion):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO clientes (nombre, telefono, direccion) VALUES (?,?,?)",
                   (nombre, telefono, direccion))
    conn.commit()
    conn.close()

def cargar_clientes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, telefono, direccion FROM clientes ORDER BY id DESC")
    datos = cursor.fetchall()
    conn.close()
    return datos
    
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
            ft.ElevatedButton("🚗 Clientes", width=300, on_click=lambda e: mostrar_clientes(page)),
            ft.ElevatedButton("🔧 Vehículos", width=300, on_click=lambda e: print("Abrir Vehículos")), 
            ft.ElevatedButton("📋 Órdenes de Trabajo", width=300, on_click=lambda e: print("Abrir Órdenes")),
            ft.ElevatedButton("🚪 Cerrar sesión", width=300, color="red", on_click=cerrar_sesion)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
    )
def mostrar_clientes(page):
    # Inputs del formulario
    nombre_input = ft.TextField(label="Nombre", width=300)
    tel_input = ft.TextField(label="Teléfono", width=200)
    dir_input = ft.TextField(label="Dirección", width=400)

    # Tabla
    tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Nombre")),
            ft.DataColumn(ft.Text("Teléfono")),
            ft.DataColumn(ft.Text("Dirección")),
        ],
        rows=[]
    )

    def guardar_cliente(e):
        if nombre_input.value == "" or tel_input.value == "":
            page.snack_bar = ft.SnackBar(ft.Text("Nombre y Teléfono son obligatorios"))
            page.snack_bar.open = True
        else:
            insertar_cliente(nombre_input.value, tel_input.value, dir_input.value)
            nombre_input.value = ""
            tel_input.value = ""
            dir_input.value = ""
            cargar_tabla()
            page.snack_bar = ft.SnackBar(ft.Text("Cliente guardado"))
            page.snack_bar.open = True
        page.update()

    def cargar_tabla():
        tabla.rows.clear()
        clientes = cargar_clientes()
        for c in clientes:
            tabla.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(c[0]))),
                    ft.DataCell(ft.Text(c[1])),
                    ft.DataCell(ft.Text(c[2])),
                    ft.DataCell(ft.Text(c[3])),
                ])
            )
        page.update()

    # Botón guardar
    btn_guardar = ft.ElevatedButton("Guardar", on_click=guardar_cliente)

    page.clean()
    page.add(
        ft.Column([
            ft.Text("Gestión de Clientes", size=30, weight="bold"),
            nombre_input,
            tel_input,
            dir_input,
            btn_guardar,
            ft.Divider(),
            ft.Text("Clientes registrados", size=20),
            tabla,
            ft.ElevatedButton("⬅ Volver al menú", on_click=lambda e: mostrar_app(page))
        ], scroll=ft.ScrollMode.AUTO)
    )
    cargar_tabla()
def main(page: ft.Page):
    page.title = "Control Taller"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = "#1a1a1a"
    
    crear_tablas_taller()
    mostrar_login(page)

ft.app(target=main, port=int(os.getenv("PORT", 8080)), host="0.0.0.0", view=None)
