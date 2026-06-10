import flet as ft
import os

def main(page: ft.Page):
    page.title = "Login - Control Taller"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = "#1a1a1a"

    def login_click(e):
        usuario = user_field.value
        password = pass_field.value
        
        # Aquí pones tu validación real después
        if usuario == "admin" and password == "1234":
            page.clean()
            page.add(ft.Text("App Taller lista ✅", size=30))
            page.update()
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
