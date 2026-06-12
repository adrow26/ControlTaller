import flet as ft
import datetime
import json
import os
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

ARCHIVO_DATOS = "datos_taller.json"

def main(page: ft.Page):
    page.title = "Control Taller"
    page.window.width = 450
    page.scroll = ft.ScrollMode.AUTO
    
    # FilePicker obligatorio para descargar PDF en web/Railway
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    # Cargar datos
    ordenes = []
    if os.path.exists(ARCHIVO_DATOS):
        try:
            with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
                data = json.load(f)
                ordenes = data.get("ordenes", [])
        except:
            ordenes = []

    def guardar_datos():
        with open(ARCHIVO_DATOS, "w", encoding="utf-8") as f:
            json.dump({"ordenes": ordenes}, f, ensure_ascii=False, indent=2)

    # Campos formulario
    txt_cliente = ft.TextField(label="Cliente", width=400)
    txt_equipo = ft.TextField(label="Equipo", width=400)
    txt_falla = ft.TextField(label="Falla reportada", multiline=True, min_lines=3, width=400)
    txt_trabajo = ft.TextField(label="Trabajo realizado", multiline=True, min_lines=3, width=400)
    txt_repuesto = ft.TextField(label="Repuesto", width=200)
    txt_costo = ft.TextField(label="Costo repuesto Bs", width=180, keyboard_type=ft.KeyboardType.NUMBER)
    txt_total = ft.TextField(label="Total Bs", width=180, keyboard_type=ft.KeyboardType.NUMBER)

    # Tabla con expand=True para que no se bloquee después de 4 filas
    tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Cliente")),
            ft.DataColumn(ft.Text("Equipo")),
            ft.DataColumn(ft.Text("Repuesto")),
            ft.DataColumn(ft.Text("Costo")),
            ft.DataColumn(ft.Text("Total")),
        ],
        rows=[]
    )

    lista_tabla = ft.ListView(expand=True, spacing=5)
    lista_tabla.controls.append(tabla)

    def refrescar_tabla():
        tabla.rows.clear()
        for t in ordenes:
            costo = float(t.get("costo_repuesto", 0))  # Fix ValueError
            total = float(t["total"])
            tabla.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(t["cliente"])),
                    ft.DataCell(ft.Text(t["equipo"])),
                    ft.DataCell(ft.Text(t.get("repuesto", "-"))),
                    ft.DataCell(ft.Text(f"Bs {costo:.2f}")),
                    ft.DataCell(ft.Text(f"Bs {total:.2f}")),
                ])
            )
        page.update()

    def agregar_orden(e):
        if not all([txt_cliente.value, txt_equipo.value, txt_falla.value, txt_trabajo.value, txt_total.value]):
            page.snack_bar = ft.SnackBar(ft.Text("Completa todos los campos obligatorios"))
            page.snack_bar.open = True
            page.update()
            return

        try:
            costo_val = float(txt_costo.value or 0)
            total_val = float(txt_total.value)
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("Costo y Total deben ser números"))
            page.snack_bar.open = True
            page.update()
            return

        orden = {
            "id": len(ordenes) + 1,
            "fecha": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
            "cliente": txt_cliente.value,
            "equipo": txt_equipo.value,
            "falla": txt_falla.value,
            "trabajo": txt_trabajo.value,
            "repuesto": txt_repuesto.value,
            "costo_repuesto": costo_val,
            "total": total_val
        }
        ordenes.append(orden)
        guardar_datos()
        
        # Limpiar campos
        for campo in [txt_cliente, txt_equipo, txt_falla, txt_trabajo, txt_repuesto, txt_costo, txt_total]:
            campo.value = ""
        
        refrescar_tabla()
        page.snack_bar = ft.SnackBar(ft.Text("Orden guardada"))
        page.snack_bar.open = True
        page.update()

    def generar_pdf(path):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        
        data = [["ID", "Fecha", "Cliente", "Equipo", "Total Bs"]]
        total_general = 0
        for o in ordenes:
            data.append([str(o["id"]), o["fecha"], o["cliente"], o["equipo"], f"{o['total']:.2f}"])
            total_general += o["total"]
        data.append(["", "", "TOTAL GENERAL", f"{total_general:.2f}"])
        
        table = Table(data, colWidths=[40, 90, 120, 120, 80])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.grey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("GRID", (0,0), (-1,-1), 1, colors.black),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold")
        ]))
        
        doc.build([Paragraph("Reporte de Órdenes - Taller", styles["Title"]), table])
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        with open(path, "wb") as f:
            f.write(pdf_bytes)

    def save_file_result(e: ft.FilePickerResultEvent):
        if e.path:
            generar_pdf(e.path)
            page.snack_bar = ft.SnackBar(ft.Text(f"PDF guardado correctamente"))
            page.snack_bar.open = True
            page.update()

    file_picker.on_result = save_file_result

    def exportar_pdf(e):
        if not ordenes:
            page.snack_bar = ft.SnackBar(ft.Text("No hay órdenes para exportar"))
            page.snack_bar.open = True
            page.update()
            return
        fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        file_picker.save_file(
            file_name=f"reporte_taller_{fecha}.pdf",
            file_type=ft.FilePickerFileType.PDF
        )

    # Layout principal
    page.add(
        ft.Column([
            ft.Text("Sistema Control Taller", size=24, weight=ft.FontWeight.BOLD),
            txt_cliente,
            txt_equipo,
            txt_falla,
            txt_trabajo,
            ft.Row([txt_repuesto, txt_costo, txt_total]),
            ft.Row([
                ft.ElevatedButton("Guardar Orden", on_click=agregar_orden),
                ft.ElevatedButton("Exportar PDF", on_click=exportar_pdf, icon="picture_as_pdf")
            ]),
            ft.Divider(),
            ft.Text("Órdenes registradas:", weight=ft.FontWeight.BOLD),
            ft.Container(content=lista_tabla, expand=True)
        ], expand=True, scroll=ft.ScrollMode.AUTO)
    )
    
    refrescar_tabla()

# Fix para Railway: usar puerto de variable de entorno y host 0.0.0.0
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8501))
    ft.app(target=main, view=ft.WEB_BROWSER, port=port, host="0.0.0.0")
