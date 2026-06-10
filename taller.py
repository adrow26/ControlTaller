import flet as ft
import os
import sqlite3

DB_NAME = "taller.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY, usuario TEXT UNIQUE, password TEXT)''')
    # Usuario por defecto si no existe
    c.execute("INSERT OR IGNORE INTO usuarios (usuario, password) VALUES (?, ?)", ("admin", "1234"))
    conn.commit()
    conn.close()

def verificar_login(usuario, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE usuario=? AND password=?", (usuario, password))
    user = c.fetchone()
    conn.close()
    return user is not None

def main(page: ft.Page):
    init_db()  # Crea la BD al iniciar
    
    page.title = "Login - Control Taller"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = "#1a1a1a"

    def login_click(e):
        if verificar_login(user_field.value, pass_field.value):
            page.clean()
            page.add(ft.Text("App Taller lista ✅", size=30))
        else:
            error_text.value = "Usuario o contraseña incorrectos"
        page.update()

    user_field = ft.TextField(label="Usuario", width=300)
    pass_field = ft.TextField(label="Contraseña", password=True, width=300)
    error_text = ft.Text(color="red")
    login_btn = ft.ElevatedButton("Entrar", on_click=login_click, width=300)

    page.add(
        ft.Column([
            ft.Text("Control Taller", size=40, weight="bold"),
            user_field,
            pass_field,
            login_btn,
            error_text
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

ft.app(target=main, port=int(os.getenv("PORT", 8080)), host="0.0.0.0", view=None)
