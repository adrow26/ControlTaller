import flet as ft

async def main(page: ft.Page):
    page.title = "Control Taller"
    page.add(ft.Text("App Taller lista ✅", size=30))

app = ft.app_async(target=main)
