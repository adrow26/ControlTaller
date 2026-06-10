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
    # Usuario admin por defecto
    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, password) VALUES (?, ?)", ("admin", "1234"))
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
            mensaje.value = "✅ Login correcto"
            mensaje.color = "green"
            page.update()
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
                ft.ElevatedButton("Entrar", on_click=iniciar_sesion),
                ft.ElevatedButton("Registrar", on_click=registrar)
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
            ft.ElevatedButton("🚗 Clientes", width=300, on_click=lambda e: print("Abrir Clientes")),
            ft.ElevatedButton("🔧 Vehículos", width=300, on_click=lambda e: print("Abrir Vehículos")), 
            ft.ElevatedButton("📋 Órdenes de Trabajo", width=300, on_click=lambda e: print("Abrir Órdenes")),
            ft.ElevatedButton("🚪 Cerrar sesión", width=300, color="red", on_click=cerrar_sesion)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
    )

def main(page: ft.Page):
    page.title = "Control Taller"
    page.window_width = 400
    page.window_height = 600
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    conectar_db()
    mostrar_login(page)

ft.app(target=main)
