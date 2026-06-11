import flet as ft
import sqlite3
import os
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

DB_NAME = "taller.db"

def conectar_db():
    conn = sqlite3.connect(DB_NAME)
    return conn

def crear_tablas_taller():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mecanicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            especialidad TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            direccion TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trabajos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE DEFAULT CURRENT_DATE,
            mecanico_id INTEGER,
            orden_trabajo TEXT NOT NULL,
            repuestos_cambiados TEXT,
            costo_repuesto REAL DEFAULT 0,
            costo_trabajo REAL DEFAULT 0,
            total REAL DEFAULT 0,
            estado TEXT DEFAULT 'Pendiente',
            FOREIGN KEY (mecanico_id) REFERENCES mecanicos(id)
        )
    ''')

    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, password) VALUES (?,?)", ("admin", "1234"))
    conn.commit()
    conn.close()

def insertar_mecanico(nombre, telefono, especialidad):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO mecanicos (nombre, telefono, especialidad) VALUES (?,?,?)", (nombre, telefono, especialidad))
    conn.commit()
    conn.close()

def obtener_mecanicos():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, telefono, especialidad FROM mecanicos ORDER BY nombre")
    resultado = cursor.fetchall()
    conn.close()
    return resultado

def insertar_trabajo(mecanico_id, orden_trabajo, repuestos, costo_rep, costo_trab):
    total = float(costo_rep or 0) + float(costo_trab or 0)
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO trabajos (mecanico_id, orden_trabajo, repuestos_cambiados, costo_repuesto, costo_trabajo, total) VALUES (?,?,?,?,?,?)",
                   (mecanico_id, orden_trabajo, repuestos, costo_rep, costo_trab, total))
    conn.commit()
    conn.close()

def obtener_trabajos(filtro_fecha=None, mecanico_id=None):
    conn = conectar_db()
    cursor = conn.cursor()

    query = "SELECT t.id, t.fecha, m.nombre, t.orden_trabajo, t.repuestos_cambiados, t.costo_repuesto, t.costo_trabajo, t.total, t.estado FROM trabajos t LEFT JOIN mecanicos m ON t.mecanico_id = m.id WHERE 1=1"

    params = []
    if filtro_fecha:
        query += f" AND t.fecha {filtro_fecha}"
    if mecanico_id:
        query += " AND t.mecanico_id =?"
        params.append(mecanico_id)

    query += " ORDER BY t.fecha DESC, t.id DESC"
    cursor.execute(query, params)
    resultado = cursor.fetchall()
    conn.close()
    return resultado

def reporte_ganancias(tipo, mecanico_id=None):
    conn = conectar_db()
    cursor = conn.cursor()

    if tipo == "dia":
        filtro = "= date('now')"
    elif tipo == "semana":
        filtro = ">= date('now', '-7 days')"
    elif tipo == "mes":
        filtro = ">= date('now', 'start of month')"
    else:
        filtro = ""

    query = f'''
        SELECT m.nombre, COUNT(t.id) as total_trabajos, SUM(t.total) as ganancia
        FROM trabajos t
        JOIN mecanicos m ON t.mecanico_id = m.id
        WHERE t.fecha {filtro}
    '''

    params = []
    if mecanico_id:
        query += " AND m.id =?"
        params.append(mecanico_id)

    query += " GROUP BY m.id, m.nombre ORDER BY ganancia DESC"

    cursor.execute(query, params)
    resultado = cursor.fetchall()
    conn.close()
    return resultado

def generar_pdf_reporte(datos, tipo, mecanico_nombre):
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"reporte_{tipo}_{fecha}.pdf"
    ruta = os.path.join(os.getcwd(), nombre_archivo)

    c = canvas.Canvas(ruta, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 18)
    c.drawString(2*cm, height-2*cm, "Reporte de Ganancias - Control Taller")

    c.setFont("Helvetica", 12)
    c.drawString(2*cm, height-3*cm, f"Período: {tipo.capitalize()}")
    c.drawString(2*cm, height-3.7*cm, f"Mecánico: {mecanico_nombre}")
    c.drawString(2*cm, height-4.4*cm, f"Fecha emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    y = height - 6*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Mecánico")
    c.drawString(8*cm, y, "Trabajos")
    c.drawString(12*cm, y, "Ganancia Total")

    c.line(2*cm, y-0.3*cm, 18*cm, y-0.3*cm)
    y -= 1*cm

    c.setFont("Helvetica", 11)
    total_general = 0
    for d in datos:
        c.drawString(2*cm, y, str(d[0]))
        c.drawString(8*cm, y, str(d[1]))
        c.drawString(12*cm, y, f"Bs {d[2]:.2f}")
        total_general += d[2]
        y -= 0.8*cm
        if y < 3*cm:
            c.showPage()
            y = height - 2*cm

    c.line(2*cm, y, 18*cm, y)
    y -= 0.8*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(8*cm, y, "TOTAL:")
    c.drawString(12*cm, y, f"Bs {total_general:.2f}")

    c.save()
    return nombre_archivo

def verificar_usuario(usuario, password):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND password=?", (usuario, password))
    resultado = cursor.fetchone()
    conn.close()
    return resultado is not None

def crear_usuario(usuario, password):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (usuario, password) VALUES (?,?)", (usuario, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def mostrar_aviso(page, mensaje):
    page.snack_bar = ft.SnackBar(ft.Text(mensaje), open=True)
    page.update()

def mostrar_login(page):
    usuario_input = ft.TextField(label="Usuario", width=300)
    password_input = ft.TextField(label="Contraseña", password=True, width=300)
    mensaje = ft.Text("", color="red")

    def iniciar_sesion(e):
        if verificar_usuario(usuario_input.value, password_input.value):
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
                ft.ElevatedButton("Entrar", on_click=iniciar_sesion, width=145),
                ft.ElevatedButton("Registrar", on_click=registrar, width=145)
            ], alignment=ft.MainAxisAlignment.CENTER),
            mensaje
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
    )

def mostrar_app(page):
    page.clean()
    page.add(
        ft.Column([
            ft.Text("Control Taller", size=35, weight="bold"),
            ft.Text("¿Qué hacemos hoy?", size=16, color="grey"),
            ft.ElevatedButton("Mecánicos", width=300, icon=ft.icons.BUILD, on_click=lambda e: mostrar_mecanicos(page)),
            ft.ElevatedButton("Órdenes de Trabajo", width=300, icon=ft.icons.DESCRIPTION, on_click=lambda e: mostrar_trabajos(page)),
            ft.ElevatedButton("Reportes", width=300, icon=ft.icons.ANALYTICS, on_click=lambda e: mostrar_reportes(page)),
            ft.ElevatedButton("Cerrar sesión", icon=ft.icons.LOGOUT, color="red", width=300, on_click=lambda e: mostrar_login(page)),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
    )

def cargar_tabla_mecanicos():
    mecanicos = obtener_mecanicos()
    rows = [ft.DataRow(cells=[
        ft.DataCell(ft.Text(str(m[0]))),
        ft.DataCell(ft.Text(m[1])),
        ft.DataCell(ft.Text(m[2] or "")),
        ft.DataCell(ft.Text(m[3] or ""))
    ]) for m in mecanicos]
    return ft.DataTable(columns=[
        ft.DataColumn(ft.Text("ID")),
        ft.DataColumn(ft.Text("Nombre")),
        ft.DataColumn(ft.Text("Teléfono")),
        ft.DataColumn(ft.Text("Especialidad"))
    ], rows=rows, column_spacing=20)

def mostrar_mecanicos(page):
    nombre_input = ft.TextField(label="Nombre del mecánico", width=300)
    telefono_input = ft.TextField(label="Teléfono", width=300)
    especialidad_input = ft.TextField(label="Especialidad", width=300)
    tabla = cargar_tabla_mecanicos()

    def guardar_mecanico(e):
        if not nombre_input.value:
            mostrar_aviso(page, "El nombre es obligatorio")
            return

        insertar_mecanico(nombre_input.value, telefono_input.value, especialidad_input.value)
        mostrar_aviso(page, f"Mecánico {nombre_input.value} guardado ✅")
        nombre_input.value = ""
        telefono_input.value = ""
        especialidad_input.value = ""
        tabla.rows = cargar_tabla_mecanicos().rows
        page.update()

    page.clean()
    page.add(
        ft.Column([
            ft.Text("Gestión de Mecánicos", size=24, weight="bold"),
            nombre_input,
            telefono_input,
            especialidad_input,
            ft.ElevatedButton("Guardar Mecánico", icon=ft.icons.SAVE, on_click=guardar_mecanico),
            ft.Divider(),
            ft.Text("Mecánicos registrados", size=20),
            tabla,
            ft.ElevatedButton("← Volver al menú", on_click=lambda e: mostrar_app(page))
        ], scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
    )
    page.update()

def cargar_tabla_trabajos():
    trabajos = obtener_trabajos()
    rows = [ft.DataRow(cells=[
        ft.DataCell(ft.Text(t[1])),
        ft.DataCell(ft.Text(t[2] or "Sin asignar")),
        ft.DataCell(ft.Text(t[3])),
        ft.DataCell(ft.Text(t[4] or "-")),
        ft.DataCell(ft.Text(f"Bs {t[5]:.2f}")),
        ft.DataCell(ft.Text(f"Bs {t[6]:.2f}")),
        ft.DataCell(ft.Text(f"Bs {t[7]:.2f}", weight="bold")),
        ft.DataCell(ft.Text(t[8]))
    ]) for t in trabajos]
    return ft.DataTable(columns=[
        ft.DataColumn(ft.Text("Fecha")),
        ft.DataColumn(ft.Text("Mecánico")),
        ft.DataColumn(ft.Text("Orden")),
        ft.DataColumn(ft.Text("Repuestos")),
        ft.DataColumn(ft.Text("Costo Rep")),
        ft.DataColumn(ft.Text("Costo Trab")),
        ft.DataColumn(ft.Text("Total")),
        ft.DataColumn(ft.Text("Estado"))
    ], rows=rows, column_spacing=10)

def mostrar_trabajos(page):
    mecanicos = obtener_mecanicos()
    if not mecanicos:
        page.clean()
        page.add(ft.Text("Primero registra al menos 1 mecánico"), ft.ElevatedButton("Volver", on_click=lambda e: mostrar_app(page)))
        page.update()
        return

    mecanico_dropdown = ft.Dropdown(
        label="Mecánico",
        options=[ft.dropdown.Option(str(m[0]), m[1]) for m in mecanicos],
        width=300
    )
    orden_input = ft.TextField(label="Orden de Trabajo N°", width=300)
    repuestos_input = ft.TextField(label="Repuestos cambiados", width=300, multiline=True, min_lines=2)
    costo_rep_input = ft.TextField(label="Costo del repuesto Bs", width=145, keyboard_type=ft.KeyboardType.NUMBER)
    costo_trab_input = ft.TextField(label="Costo del trabajo Bs", width=145, keyboard_type=ft.KeyboardType.NUMBER)
    total_text = ft.Text("Total: Bs 0.00", size=18, weight="bold", color="green")

    def calcular_total(e):
        try:
            rep = float(costo_rep_input.value or 0)
            trab = float(costo_trab_input.value or 0)
            total_text.value = f"Total: Bs {rep + trab:.2f}"
        except:
            total_text.value = "Total: Bs 0.00"
        page.update()

    costo_rep_input.on_change = calcular_total
    costo_trab_input.on_change = calcular_total

    tabla = cargar_tabla_trabajos()

    def guardar_trabajo(e):
        if not mecanico_dropdown.value or not orden_input.value:
            mostrar_aviso(page, "Selecciona mecánico y número de orden")
            return

        insertar_trabajo(
            int(mecanico_dropdown.value),
            orden_input.value,
            repuestos_input.value,
            costo_rep_input.value,
            costo_trab_input.value
        )
        mostrar_aviso(page, f"Orden {orden_input.value} guardada ✅")

        orden_input.value = ""
        repuestos_input.value = ""
        costo_rep_input.value = ""
        costo_trab_input.value = ""
        total_text.value = "Total: Bs 0.00"
        tabla.rows = cargar_tabla_trabajos().rows
        page.update()

    page.clean()
    page.add(
        ft.Column([
            ft.Text("Nueva Orden de Trabajo", size=24, weight="bold"),
            mecanico_dropdown,
            orden_input,
            repuestos_input,
            ft.Row([costo_rep_input, costo_trab_input], alignment=ft.MainAxisAlignment.CENTER),
            total_text,
            ft.ElevatedButton("Guardar Orden", icon=ft.icons.SAVE, on_click=guardar_trabajo),
            ft.Divider(),
            ft.Text("Historial de Órdenes", size=20),
            ft.Container(tabla, expand=True),
            ft.ElevatedButton("← Volver al menú", on_click=lambda e: mostrar_app(page))
        ], scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
    )
    page.update()

def mostrar_reportes(page):
    mecanicos = obtener_mecanicos()
    filtro_mecanico = ft.Dropdown(
        label="Filtrar por Mecánico",
        options=[ft.dropdown.Option("", "Todos")] + [ft.dropdown.Option(str(m[0]), m[1]) for m in mecanicos],
        value="",
        width=300
    )

    datos_actuales = []
    tipo_actual = "dia"
    mecanico_nombre_actual = "Todos"

    tabla_reporte = ft.DataTable(columns=[
        ft.DataColumn(ft.Text("Mecánico")),
        ft.DataColumn(ft.Text("Trabajos")),
        ft.DataColumn(ft.Text("Ganancia Total"))
    ], rows=[])

    def cargar_reporte(tipo):
        nonlocal datos_actuales, tipo_actual, mecanico_nombre_actual
        tipo_actual = tipo
        mec_id = filtro_mecanico.value if filtro_mecanico.value else None
        mecanico_nombre_actual = filtro_mecanico.options[[o.key for o in filtro_mecanico.options].index(mec_id if mec_id else "")].text

        datos_actuales = reporte_ganancias(tipo, mec_id)
        rows = [ft.DataRow(cells=[
            ft.DataCell(ft.Text(d[0])),
            ft.DataCell(ft.Text(str(d[1]))),
            ft.DataCell(ft.Text(f"Bs {d[2]:.2f}", weight="bold", color="green"))
        ]) for d in datos_actuales]
        tabla_reporte.rows = rows
        page.update()

    def exportar_pdf(e):
        if not datos_actuales:
            mostrar_aviso(page, "No hay datos para exportar")
            return

        archivo = generar_pdf_reporte(datos_actuales, tipo_actual, mecanico_nombre_actual)
        mostrar_aviso(page, f"PDF generado: {archivo}")

    filtro_mecanico.on_change = lambda e: cargar_reporte(tipo_actual)

    page.clean()
    page.add(
        ft.Column([
            ft.Text("Reportes de Ganancias", size=24, weight="bold"),
            ft.Text("Ganancia por mecánico", size=16, color="grey"),
            filtro_mecanico,
            ft.Row([
                ft.ElevatedButton("Hoy", on_click=lambda e: cargar_reporte("dia")),
                ft.ElevatedButton("Semana", on_click=lambda e: cargar_reporte("semana")),
                ft.ElevatedButton("Mes", on_click=lambda e: cargar_reporte("mes"))
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ft.ElevatedButton("📄 Exportar PDF", icon=ft.icons.DOWNLOAD, color="blue", on_click=exportar_pdf),
            ft.Divider(),
            ft.Container(tabla_reporte, expand=True),
            ft.ElevatedButton("← Volver al menú", on_click=lambda e: mostrar_app(page))
        ], scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
    )

    cargar_reporte("dia")
    page.update()

def main(page: ft.Page):
    page.title = "Control Taller"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = "#1a1a1a"
    page.window_width = 450

    crear_tablas_taller()
    mostrar_login(page)

ft.app(target=main, port=int(os.getenv("PORT", 8080)), host="0.0.0.0", view=None)
