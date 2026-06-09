import flet as ft
import os
from datetime import datetime, timedelta
from fpdf import FPDF
import matplotlib.pyplot as plt
from collections import defaultdict
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, select
from sqlalchemy.orm import declarative_base, sessionmaker

# === BASE DE DATOS POSTGRESQL ===
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///taller.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Trabajo(Base):
    __tablename__ = "trabajos"
    id = Column(Integer, primary_key=True)
    fecha = Column(Date, nullable=False)
    mecanico = Column(String, nullable=False)
    cliente = Column(String)
    trabajo = Column(String, nullable=False)
    repuestos = Column(String)
    precio = Column(Float, nullable=False)

class Mecanico(Base):
    __tablename__ = "mecanicos"
    id = Column(Integer, primary_key=True)
    nombre = Column(String, unique=True, nullable=False)

Base.metadata.create_all(engine)

CARPETA_REPORTES = "reportes"
if not os.path.exists(CARPETA_REPORTES):
    os.makedirs(CARPETA_REPORTES)

def limpiar_texto(texto):
    if not texto:
        return ""
    texto = str(texto)
    reemplazos = {"á":"a","é":"e","í":"i","ó":"o","ú":"u","Á":"A","É":"E","Í":"I","Ó":"O","Ú":"U","ñ":"n","Ñ":"N","•":"-","–":"-"}
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    return texto

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "REPORTE TALLER DE MOTOS", 0, 1, "C")
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Pagina {self.page_no()}", 0, 0, "C")

def generar_pdf(reporte_texto, fecha, total, subtipo="diario"):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    for linea in reporte_texto.split("\n"):
        linea = limpiar_texto(linea)
        if "TOTAL GENERAL" in linea or "RESUMEN" in linea:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, linea, 0, 1)
            pdf.set_font("Arial", size=11)
        elif linea.startswith("MECANICO") or linea.startswith("==="):
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, linea, 0, 1)
            pdf.set_font("Arial", size=11)
        else:
            pdf.cell(0, 6, linea, 0, 1)
    nombre_archivo = f"{CARPETA_REPORTES}/reporte_{subtipo}_{fecha}.pdf"
    pdf.output(nombre_archivo)
    return nombre_archivo

def generar_grafico_barras(datos_mecanicos, fecha):
    mecanicos = list(datos_mecanicos.keys())
    totales = list(datos_mecanicos.values())
    plt.figure(figsize=(8, 5))
    plt.bar(mecanicos, totales, color='skyblue')
    plt.xlabel('Mecanico')
    plt.ylabel('Total $')
    plt.title(f'Ganancias por Mecanico - {fecha}')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    img_path = f"{CARPETA_REPORTES}/grafico_{fecha}.png"
    plt.savefig(img_path)
    plt.close()
    return img_path

def main(page: ft.Page):
    page.title = "Control Taller Motos"
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    session = Session()
    mecanicos = [m.nombre for m in session.query(Mecanico).all()]
    if not mecanicos:
        for m in ["Mecanico 1", "Mecanico 2", "Mecanico 3", "Mecanico 4"]:
            session.add(Mecanico(nombre=m))
        session.commit()
        mecanicos = [m.nombre for m in session.query(Mecanico).all()]

    dropdown_mec = ft.Dropdown(label="Mecanico *", options=[ft.dropdown.Option(m) for m in mecanicos], width=300)
    txt_cliente = ft.TextField(label="Moto/Cliente", width=300)
    txt_trabajo = ft.TextField(label="Trabajo realizado *", multiline=True, width=300)
    txt_repuestos = ft.TextField(label="Repuestos usados", multiline=True, width=300)
    txt_precio = ft.TextField(label="Precio *", width=300, keyboard_type=ft.KeyboardType.NUMBER)
    txt_fecha = ft.Text("Fecha: no seleccionada", size=12, weight=ft.FontWeight.BOLD)

    def fecha_seleccionada(e):
        txt_fecha.value = f"Fecha: {date_picker.value.strftime('%d/%m/%Y')}"
        page.update()

    date_picker = ft.DatePicker(first_date=datetime(2024,1,1), on_change=fecha_seleccionada)
    page.overlay.append(date_picker)

    def abrir_taller(e):
        date_picker.value = datetime.now()
        txt_fecha.value = f"Fecha: {datetime.now().strftime('%d/%m/%Y')}"
        date_picker.open = True
        page.update()

    btn_abrir_taller = ft.ElevatedButton("Abrir taller - Fecha de hoy", on_click=abrir_taller, color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_700)
    lista_trabajos = ft.Column(spacing=10)

    def actualizar_lista(filtro_cliente="", filtro_fecha="", filtro_mec=""):
        lista_trabajos.controls.clear()
        query = session.query(Trabajo)
        if filtro_cliente:
            query = query.filter(Trabajo.cliente.ilike(f"%{filtro_cliente}%"))
        if filtro_fecha:
            query = query.filter(Trabajo.fecha == datetime.strptime(filtro_fecha, "%Y-%m-%d").date())
        if filtro_mec:
            query = query.filter(Trabajo.mecanico == filtro_mec)

        trabajos_filtrados = query.order_by(Trabajo.id.desc()).limit(50).all()

        for t in trabajos_filtrados:
            lista_trabajos.controls.append(
                ft.Card(content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"{t.fecha} - {t.mecanico}", weight=ft.FontWeight.BOLD),
                        ft.Text(f"Moto: {t.cliente or '-'}"),
                        ft.Text(f"Trabajo: {t.trabajo}"),
                        ft.Text(f"Repuestos: {t.repuestos or '-'}"),
                        ft.Text(f"Precio: ${t.precio}", color=ft.Colors.GREEN_700, size=16)
                    ]), padding=10
                ))
            )
        page.update()

    txt_buscar_cliente = ft.TextField(label="Buscar cliente", width=200, on_change=lambda e: actualizar_lista(txt_buscar_cliente.value, txt_buscar_fecha.value, dropdown_buscar_mec.value))
    txt_buscar_fecha = ft.TextField(label="Buscar fecha YYYY-MM-DD", width=200, on_change=lambda e: actualizar_lista(txt_buscar_cliente.value, txt_buscar_fecha.value, dropdown_buscar_mec.value))
    dropdown_buscar_mec = ft.Dropdown(label="Buscar mecanico", width=200, options=[ft.dropdown.Option("")]+[ft.dropdown.Option(m) for m in mecanicos], on_change=lambda e: actualizar_lista(txt_buscar_cliente.value, txt_buscar_fecha.value, dropdown_buscar_mec.value))

    def agregar_trabajo(e):
        if not date_picker.value or not dropdown_mec.value or not txt_trabajo.value or not txt_precio.value:
            page.snack_bar = ft.SnackBar(ft.Text("Completa todos los campos obligatorios *"))
            page.snack_bar.open = True
            page.update()
            return

        nuevo = Trabajo(
            fecha=date_picker.value.date(),
            mecanico=dropdown_mec.value,
            cliente=txt_cliente.value,
            trabajo=txt_trabajo.value,
            repuestos=txt_repuestos.value,
            precio=float(txt_precio.value)
        )
        session.add(nuevo)
        session.commit()

        txt_cliente.value = ""
        txt_trabajo.value = ""
        txt_repuestos.value = ""
        txt_precio.value = ""
        txt_fecha.value = "Fecha: no seleccionada"
        date_picker.value = None

        actualizar_lista()
        page.snack_bar = ft.SnackBar(ft.Text("Trabajo guardado OK"))
        page.snack_bar.open = True
        page.update()

    def cerrar_taller(e):
        fecha_hoy = datetime.now().date()
        trabajos_hoy = session.query(Trabajo).filter(Trabajo.fecha == fecha_hoy).all()

        if not trabajos_hoy:
            page.snack_bar = ft.SnackBar(ft.Text("No hay trabajos registrados hoy"))
            page.snack_bar.open = True
            page.update()
            return

        reporte = f"REPORTE DIARIO - {fecha_hoy}\n" + "="*50 + "\n\n"
        total_general = 0
        datos_grafico = defaultdict(float)

        for mec in mecanicos:
            trabajos_mec = [t for t in trabajos_hoy if t.mecanico == mec]
            if trabajos_mec:
                reporte += f"MECANICO: {mec}\n" + "-"*30 + "\n"
                total_mec = 0
                for t in trabajos_mec:
                    reporte += f"- {t.trabajo} - ${t.precio}\n"
                    if t.repuestos:
                        reporte += f" Repuestos: {t.repuestos}\n"
                    total_mec += float(t.precio)
                reporte += f"TOTAL {mec}: ${total_mec}\n\n"
                total_general += total_mec
                datos_grafico[mec] = total_mec

        reporte += "="*50 + f"\nTOTAL GENERAL DEL DIA: ${total_general}\n"
        archivo_pdf = generar_pdf(reporte, str(fecha_hoy), total_general, "diario")
        img_grafico = generar_grafico_barras(datos_grafico, str(fecha_hoy))

        dlg = ft.AlertDialog(
            title=ft.Text("Reporte generado OK"),
            content=ft.Text(f"PDF: {archivo_pdf}\nGrafico: {img_grafico}\n\nTotal del dia: ${total_general}"),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: cerrar_dialogo())]
        )
        def cerrar_dialogo():
            dlg.open = False
            page.update()
        page.dialog = dlg
        dlg.open = True
        page.update()

    btn_guardar = ft.ElevatedButton("Guardar trabajo", on_click=agregar_trabajo)
    btn_cerrar = ft.ElevatedButton("Cerrar taller - Generar PDF", on_click=cerrar_taller, bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)

    tab_trabajos = ft.Column([
        ft.Text("Registrar nuevo trabajo", size=20, weight=ft.FontWeight.BOLD),
        btn_abrir_taller, txt_fecha, dropdown_mec, txt_cliente, txt_trabajo, txt_repuestos, txt_precio,
        btn_guardar, btn_cerrar,
        ft.Divider(),
        ft.Text("Buscar trabajos", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([txt_buscar_cliente, txt_buscar_fecha, dropdown_buscar_mec]),
        ft.Divider(),
        ft.Text("Ultimos trabajos", size=16, weight=ft.FontWeight.BOLD),
        lista_trabajos
    ], scroll=ft.ScrollMode.AUTO)

    txt_nuevo_mec = ft.TextField(label="Nombre nuevo mecanico", width=250)
    lista_mec_ui = ft.Column()

    def actualizar_lista_mec():
        lista_mec_ui.controls.clear()
        for m in session.query(Mecanico).all():
            lista_mec_ui.controls.append(
                ft.Row([ft.Text(m.nombre, expand=True), ft.IconButton(ft.Icons.DELETE, on_click=lambda e, id=m.id: eliminar_mec(id))])
            )
        page.update()

    def agregar_mec(e):
        if txt_nuevo_mec.value:
            if not session.query(Mecanico).filter_by(nombre=txt_nuevo_mec.value).first():
                session.add(Mecanico(nombre=txt_nuevo_mec.value))
                session.commit()
                mecanicos.append(txt_nuevo_mec.value)
                dropdown_mec.options.append(ft.dropdown.Option(txt_nuevo_mec.value))
                dropdown_buscar_mec.options.append(ft.dropdown.Option(txt_nuevo_mec.value))
                txt_nuevo_mec.value = ""
                actualizar_lista_mec()
                page.update()

    def eliminar_mec(id):
        mec = session.get(Mecanico, id)
        if mec:
            session.delete(mec)
            session.commit()
            actualizar_lista_mec()
            dropdown_mec.options = [ft.dropdown.Option(m.nombre) for m in session.query(Mecanico).all()]
            dropdown_buscar_mec.options = [ft.dropdown.Option("")] + [ft.dropdown.Option(m.nombre) for m in session.query(Mecanico).all()]
            page.update()

    btn_add_mec = ft.ElevatedButton("Agregar mecanico", on_click=agregar_mec)
    tab_mecanicos = ft.Column([ft.Text("Gestionar Mecanicos", size=20, weight=ft.FontWeight.BOLD), ft.Row([txt_nuevo_mec, btn_add_mec]), ft.Divider(), ft.Text("Lista actual:", size=16), lista_mec_ui], scroll=ft.ScrollMode.AUTO)
    actualizar_lista_mec()

    dropdown_periodo = ft.Dropdown(label="Periodo", width=200, options=[ft.dropdown.Option("Semanal"), ft.dropdown.Option("Mensual")], value="Semanal")

    def generar_informe_periodo(e):
        periodo = dropdown_periodo.value
        hoy = datetime.now().date()

        if periodo == "Semanal":
            inicio = hoy - timedelta(days=7)
            fecha_str = f"{inicio.strftime('%Y%m%d')}_al_{hoy.strftime('%Y%m%d')}"
            trabajos_periodo = session.query(Trabajo).filter(Trabajo.fecha >= inicio).all()
            titulo = f"REPORTE SEMANAL {inicio.strftime('%d/%m')} al {hoy.strftime('%d/%m/%Y')}"
        else:
            inicio = hoy.replace(day=1)
            fecha_str = hoy.strftime('%Y%m')
            trabajos_periodo = session.query(Trabajo).filter(Trabajo.fecha >= inicio).all()
            titulo = f"REPORTE MENSUAL {hoy.strftime('%B %Y')}"

        if not trabajos_periodo:
            page.snack_bar = ft.SnackBar(ft.Text("No hay trabajos en ese periodo"))
            page.snack_bar.open = True
            page.update()
            return

        reporte = f"{titulo}\n" + "="*50 + "\n\n"
        total_general = 0
        datos_grafico = defaultdict(float)

        for mec in mecanicos:
            trabajos_mec = [t for t in trabajos_periodo if t.mecanico == mec]
            if trabajos_mec:
                reporte += f"MECANICO: {mec}\n" + "-"*30 + "\n"
                total_mec = 0
                for t in trabajos_mec:
                    reporte += f"- {t.fecha} {t.trabajo} - ${t.precio}\n"
                    total_mec += float(t.precio)
                reporte += f"TOTAL {mec}: ${total_mec}\n\n"
                total_general += total_mec
                datos_grafico[mec] = total_mec

        reporte += "="*50 + f"\nTOTAL GENERAL DEL PERIODO: ${total_general}\n"
        archivo_pdf = generar_pdf(reporte, fecha_str, total_general, periodo.lower())
        img_grafico = generar_grafico_barras(datos_grafico, fecha_str)

        dlg = ft.AlertDialog(
            title=ft.Text(f"Reporte {periodo} generado OK"),
            content=ft.Text(f"PDF: {archivo_pdf}\nGrafico: {img_grafico}\n\nTotal: ${total_general}"),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: cerrar_dialogo())]
        )
        def cerrar_dialogo():
            dlg.open = False
            page.update()
        page.dialog = dlg
        dlg.open = True
        page.update()

    btn_generar_periodo = ft.ElevatedButton("Generar informe", on_click=generar_informe_periodo)

    def ver_informes(e):
        lista_informes.controls.clear()
        archivos = [f for f in os.listdir(CARPETA_REPORTES) if f.endswith(".pdf")]
        archivos.sort(reverse=True)
        if not archivos:
            lista_informes.controls.append(ft.Text("No hay informes guardados"))
        else:
            for archivo in archivos[:30]:
                lista_informes.controls.append(
                    ft.Card(content=ft.Container(
                        content=ft.Row([
                            ft.Text(archivo, expand=True),
                            ft.TextButton("Abrir", on_click=lambda e, a=archivo: os.startfile(os.path.join(CARPETA_REPORTES, a)))
                        ]), padding=10
                    ))
                )
        page.update()

    btn_ver = ft.ElevatedButton("Ver informes", on_click=ver_informes)
    lista_informes = ft.Column()
    tab_informes = ft.Column([ft.Text("Informes Periodo", size=20, weight=ft.FontWeight.BOLD), ft.Row([dropdown_periodo, btn_generar_periodo]), ft.Divider(), ft.Text("Todos los informes guardados", size=16, weight=ft.FontWeight.BOLD), btn_ver, lista_informes], scroll=ft.ScrollMode.AUTO)

    tabs = ft.Tabs(selected_index=0, tabs=[
        ft.Tab(tab_content=ft.Text("Trabajos"), content=tab_trabajos),
        ft.Tab(tab_content=ft.Text("Mecanicos"), content=tab_mecanicos),
        ft.Tab(tab_content=ft.Text("Informes"), content=tab_informes),
    ])

    page.add(tabs)
    actualizar_lista()
    page.on_close = lambda e: session.close()

ft.app(target=main, view=ft.WEB_BROWSER, port=8000, host="0.0.0.0")