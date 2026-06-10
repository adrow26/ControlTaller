import flet as ft
import os

def main(page: ft.Page):
    page.title = "Control Taller"
    page.add(ft.Text("App Taller lista ✅", size=30))

ft.app(target=main, port=int(os.getenv("PORT", 8080)), host="0.0.0.0", view=None)
