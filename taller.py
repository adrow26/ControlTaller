import flet as ft
import os

def main(page: ft.Page):
    page.title = "Control Taller"
    page.add(ft.Text("App Taller lista ✅", size=30))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    ft.app(target=main, port=port, host="0.0.0.0")
