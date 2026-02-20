import customtkinter as ctk
from tkinter import ttk
import sqlite3
from datetime import datetime
from tkinter import messagebox
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

# =========================
# CONFIGURACIÓN VISUAL
# =========================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# =========================
# BASE DE DATOS
# =========================

conn = sqlite3.connect("finanzas.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS movimientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT,
    monto REAL,
    fecha TEXT
)
""")
conn.commit()

# =========================
# FUNCIONES SISTEMA
# =========================

def calcular_balance():
    cursor.execute("""
    SELECT 
        SUM(CASE WHEN tipo='Ingreso' THEN monto ELSE 0 END),
        SUM(CASE WHEN tipo='Gasto' THEN monto ELSE 0 END)
    FROM movimientos
    """)
    ingresos, gastos = cursor.fetchone()
    ingresos = ingresos or 0
    gastos = gastos or 0
    return ingresos - gastos


def registrar(tipo):
    try:
        monto = float(entry_monto.get())
        if monto <= 0:
            return
    except:
        return

    if tipo == "Gasto" and monto > calcular_balance():
        messagebox.showwarning("Fondos insuficientes", "No tienes suficiente dinero.")
        return

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

    cursor.execute(
        "INSERT INTO movimientos (tipo, monto, fecha) VALUES (?, ?, ?)",
        (tipo, monto, fecha)
    )
    conn.commit()

    entry_monto.delete(0, "end")
    actualizar_tabla()
    actualizar_balance()


def actualizar_tabla():
    for fila in tree.get_children():
        tree.delete(fila)

    cursor.execute("SELECT * FROM movimientos ORDER BY id DESC")

    for row in cursor.fetchall():
        tree.insert("", "end", values=row)


def actualizar_balance():
    balance = calcular_balance()
    label_balance.configure(text=f"${balance:,.2f}")

# =========================
# GENERAR FACTURA PDF
# =========================

def generar_factura():
    seleccionados = tree.selection()

    if not seleccionados:
        messagebox.showwarning("Aviso", "Selecciona uno o más movimientos.")
        return

    datos_factura = []
    total = 0

    for item in seleccionados:
        valores = tree.item(item)["values"]
        id_mov, tipo, monto, fecha = valores
        total += float(monto)

        datos_factura.append([
            id_mov,
            tipo,
            fecha,
            f"${float(monto):,.2f}"
        ])

    nombre_archivo = f"Factura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(nombre_archivo)
    elementos = []
    estilos = getSampleStyleSheet()

    elementos.append(Paragraph("<b>FINANZAS PRO</b>", estilos["Title"]))
    elementos.append(Spacer(1, 0.3 * inch))

    encabezado = [["ID", "Tipo", "Fecha", "Monto"]]
    tabla_data = encabezado + datos_factura

    tabla = Table(tabla_data, colWidths=[50, 100, 120, 100])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ALIGN', (3, 1), (3, -1), 'RIGHT')
    ]))

    elementos.append(tabla)
    elementos.append(Spacer(1, 0.3 * inch))

    elementos.append(Paragraph(
        f"<b>Total: ${total:,.2f}</b>",
        estilos["Heading2"]
    ))

    doc.build(elementos)

    messagebox.showinfo("Factura generada",
                        f"Factura creada:\n{nombre_archivo}")
    
# =========================
# LOGIN
# =========================

def verificar_login():
    usuario = entry_usuario.get()
    contraseña = entry_contraseña.get()

    if usuario == "camilo" and contraseña == "1234":
        for widget in app.winfo_children():
            widget.destroy()
        mostrar_sistema()
    elif usuario == "mariana" and contraseña == "420":
        for widget in app.winfo_children():
            widget.destroy()
        mostrar_sistema()
    else:
        messagebox.showerror("Error", "Usuario o contraseña incorrectos")


def mostrar_login():
    global entry_usuario, entry_contraseña

    login_frame = ctk.CTkFrame(app)
    login_frame.pack(expand=True)

    ctk.CTkLabel(
        login_frame,
        text="Iniciar Sesión",
        font=ctk.CTkFont(size=22, weight="bold")
    ).pack(pady=20)

    entry_usuario = ctk.CTkEntry(login_frame, placeholder_text="Usuario")
    entry_usuario.pack(pady=10)

    entry_contraseña = ctk.CTkEntry(
        login_frame,
        placeholder_text="Contraseña",
        show="*"
    )
    entry_contraseña.pack(pady=10)

    ctk.CTkButton(
        login_frame,
        text="Ingresar",
        command=verificar_login
    ).pack(pady=20)


def cerrar_sesion():
    for widget in app.winfo_children():
        widget.destroy()
    mostrar_login()

# =========================
# SISTEMA PRINCIPAL
# =========================

def mostrar_sistema():
    global entry_monto, label_balance, tree

    sidebar = ctk.CTkFrame(app, width=200, corner_radius=0)
    sidebar.pack(side="left", fill="y")

    ctk.CTkLabel(
        sidebar,
        text="💳 FARCTURA",
        font=ctk.CTkFont(size=18, weight="bold")
    ).pack(pady=30)

    ctk.CTkButton(
        sidebar,
        text="Cerrar Sesión",
        fg_color="#b91c1c",
        hover_color="#ef4444",
        command=cerrar_sesion
    ).pack(pady=10)

    main_frame = ctk.CTkFrame(app)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    ctk.CTkLabel(
        main_frame,
        text="Balance Actual",
        font=ctk.CTkFont(size=20)
    ).pack()

    label_balance = ctk.CTkLabel(
        main_frame,
        text="$0.00",
        font=ctk.CTkFont(size=32, weight="bold")
    )
    label_balance.pack(pady=10)

    entry_monto = ctk.CTkEntry(
        main_frame,
        placeholder_text="Ingrese monto"
    )
    entry_monto.pack(pady=10)

    botones_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    botones_frame.pack(pady=10)

    ctk.CTkButton(
        botones_frame,
        text="Ingreso",
        fg_color="#16a34a",
        command=lambda: registrar("Ingreso")
    ).pack(side="left", padx=10)

    ctk.CTkButton(
        botones_frame,
        text="Gasto",
        fg_color="#f71d00",
        command=lambda: registrar("Gasto")
    ).pack(side="left", padx=10)

    ctk.CTkButton(
        main_frame,
        text="Generar Factura PDF",
        fg_color="#2563eb",
        command=generar_factura
    ).pack(pady=10)

    tree = ttk.Treeview(main_frame,
                    columns=("ID", "Tipo", "Monto", "Fecha"),
                    show="headings",
                    selectmode="extended")
    
    for col in ("ID", "Tipo", "Monto", "Fecha"):
        tree.heading(col, text=col)
        tree.column(col, anchor="center")

    tree.pack(fill="both", expand=True, pady=20)

    actualizar_tabla()
    actualizar_balance()

# =========================
# VENTANA PRINCIPAL
# =========================

app = ctk.CTk()
app.geometry("1000x600")
app.title("BOST YOUR LIFE")

app.iconbitmap("ficticio.ico")

mostrar_login()


app.mainloop()