import flet as ft
import os

async def main(page: ft.Page):
    page.title = "Control Taller"
    page.add(ft.Text("App Taller lista ✅", size=30))

app = ft.app_async(
    target=main,
    port=int(os.environ["PORT"]),
    host="0.0.0.0"
)
