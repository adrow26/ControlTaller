import flet as ft
import os

def main(page: ft.Page):
    page.title = "Control Taller"
    page.add(ft.Text("App Taller lista ✅", size=30))

if __name__ == "__main__":
ft.app(target=main, port=8080, host="0.0.0.0")
