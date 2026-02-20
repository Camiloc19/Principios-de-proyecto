import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import csv
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import pagesizes
from datetime import datetime

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ===================== BASE DE DATOS =====================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "Base de datos.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT UNIQUE,
    contraseña TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS movimientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    tipo TEXT,
    categoria TEXT,
    descripcion TEXT,
    monto REAL,
    fecha TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS metas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    meta REAL
)
""")

conn.commit()

usuario_actual = None

# ===================== LOGIN =====================

def verificar_login():
    global usuario_actual

    usuario = entry_usuario.get().strip()
    contraseña = entry_contraseña.get().strip()

    cursor.execute(
        "SELECT * FROM usuarios WHERE usuario = ? AND contraseña = ?",
        (usuario, contraseña)
    )

    if cursor.fetchone():
        usuario_actual = usuario
        limpiar_ventana()
        mostrar_sistema()
    else:
        messagebox.showerror("Error", "Usuario o contraseña incorrectos")

def cerrar_sesion():
    global usuario_actual
    usuario_actual = None
    limpiar_ventana()
    mostrar_login()

def limpiar_ventana():
    for widget in app.winfo_children():
        widget.destroy()

# ===================== REGISTRO =====================

def registrar_usuario():
    usuario = entry_nuevo_usuario.get().strip()
    contraseña = entry_nueva_contraseña.get().strip()

    try:
        cursor.execute(
            "INSERT INTO usuarios (usuario, contraseña) VALUES (?, ?)",
            (usuario, contraseña)
        )
        conn.commit()
        messagebox.showinfo("Éxito", "Usuario registrado.")
        ventana_registro.destroy()
    except:
        messagebox.showerror("Error", "El usuario ya existe.")

def abrir_registro():
    global entry_nuevo_usuario, entry_nueva_contraseña, ventana_registro

    ventana_registro = ctk.CTkToplevel(app)
    ventana_registro.geometry("300x250")
    ventana_registro.title("Registrar Usuario")

    entry_nuevo_usuario = ctk.CTkEntry(ventana_registro, placeholder_text="Usuario")
    entry_nuevo_usuario.pack(pady=10)

    entry_nueva_contraseña = ctk.CTkEntry(ventana_registro, placeholder_text="Contraseña", show="*")
    entry_nueva_contraseña.pack(pady=10)

    ctk.CTkButton(ventana_registro, text="Registrar", command=registrar_usuario).pack(pady=15)

# ===================== MOVIMIENTOS =====================

def agregar_movimiento():
    tipo = combo_tipo.get()
    categoria = combo_categoria.get()
    descripcion = entry_descripcion.get().strip()
    monto = entry_monto.get().strip()
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    try:
        monto = float(monto)
    except:
        messagebox.showerror("Error", "Monto inválido")
        return

    cursor.execute("""
        INSERT INTO movimientos (usuario, tipo, categoria, descripcion, monto, fecha)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (usuario_actual, tipo, categoria, descripcion, monto, fecha))

    conn.commit()
    actualizar_tabla()
    actualizar_balance()

    entry_descripcion.delete(0, "end")
    entry_monto.delete(0, "end")

def actualizar_tabla():
    for row in tree.get_children():
        tree.delete(row)

    cursor.execute("""
        SELECT id, tipo, categoria, descripcion, monto, fecha
        FROM movimientos
        WHERE usuario = ?
        ORDER BY id DESC
    """, (usuario_actual,))

    for row in cursor.fetchall():
        tree.insert("", "end", values=row)

def actualizar_balance():
    cursor.execute("SELECT SUM(monto) FROM movimientos WHERE usuario=? AND tipo='Ingreso'", (usuario_actual,))
    ingresos = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(monto) FROM movimientos WHERE usuario=? AND tipo='Gasto'", (usuario_actual,))
    gastos = cursor.fetchone()[0] or 0

    balance = ingresos - gastos
    label_balance.configure(text=f"Balance: ${balance:,.2f}")

    cursor.execute("SELECT meta FROM metas WHERE usuario=?", (usuario_actual,))
    meta = cursor.fetchone()

    if meta:
        progreso = (balance / meta[0]) * 100 if meta[0] > 0 else 0
        label_meta.configure(text=f"Meta: ${meta[0]:,.2f} | Progreso: {progreso:.1f}%")

def eliminar_registro():
    seleccion = tree.selection()
    for item in seleccion:
        valores = tree.item(item)["values"]
        cursor.execute("DELETE FROM movimientos WHERE id=?", (valores[0],))
    conn.commit()
    actualizar_tabla()
    actualizar_balance()

# ===================== META =====================

def guardar_meta():
    try:
        valor = float(entry_meta.get())
    except:
        return

    cursor.execute("DELETE FROM metas WHERE usuario=?", (usuario_actual,))
    cursor.execute("INSERT INTO metas (usuario, meta) VALUES (?, ?)", (usuario_actual, valor))
    conn.commit()
    actualizar_balance()

# ===================== EXPORTAR =====================

def exportar_csv():
    cursor.execute("SELECT * FROM movimientos WHERE usuario=?", (usuario_actual,))
    datos = cursor.fetchall()
    ruta = os.path.join(BASE_DIR, "movimientos_exportados.csv")

    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID","Usuario","Tipo","Categoria","Descripcion","Monto","Fecha"])
        writer.writerows(datos)

    messagebox.showinfo("Exportado", "CSV generado correctamente.")

def exportar_pdf():
    cursor.execute("SELECT * FROM movimientos WHERE usuario=?", (usuario_actual,))
    datos = cursor.fetchall()

    ruta = os.path.join(BASE_DIR, "movimientos_exportados.pdf")
    doc = SimpleDocTemplate(ruta, pagesize=pagesizes.A4)

    elementos = []
    estilos = getSampleStyleSheet()

    elementos.append(Paragraph("Reporte Financiero", estilos["Title"]))
    elementos.append(Spacer(1, 20))

    tabla_data = [["ID","Tipo","Cat.","Desc.","Monto","Fecha"]]

    for fila in datos:
        tabla_data.append([fila[0], fila[2], fila[3], fila[4], f"${fila[5]:,.2f}", fila[6]])

    tabla = Table(tabla_data)
    tabla.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.grey),
        ("GRID",(0,0),(-1,-1),1,colors.black),
    ]))

    elementos.append(tabla)
    doc.build(elementos)

    messagebox.showinfo("Exportado", "PDF generado correctamente.")

# ===================== INTERFAZ =====================

def mostrar_login():
    global entry_usuario, entry_contraseña

    frame = ctk.CTkFrame(app)
    frame.pack(expand=True)

    entry_usuario = ctk.CTkEntry(frame, placeholder_text="Usuario")
    entry_usuario.pack(pady=10)

    entry_contraseña = ctk.CTkEntry(frame, placeholder_text="Contraseña", show="*")
    entry_contraseña.pack(pady=10)

    ctk.CTkButton(frame, text="Ingresar", command=verificar_login).pack(pady=5)
    ctk.CTkButton(frame, text="Registrar", command=abrir_registro).pack()

def mostrar_sistema():
    global tree, entry_descripcion, entry_monto, combo_tipo, combo_categoria, label_balance, entry_meta, label_meta

    frame = ctk.CTkFrame(app)
    frame.pack(fill="both", expand=True, padx=20, pady=20)

    ctk.CTkLabel(frame, text=f"Bienvenido {usuario_actual}", font=("Arial", 20, "bold")).pack(pady=10)

    frame_form = ctk.CTkFrame(frame)
    frame_form.pack(pady=10)

    combo_tipo = ctk.CTkComboBox(frame_form, values=["Ingreso", "Gasto"], width=150)
    combo_tipo.grid(row=0, column=0, padx=10, pady=5)
    combo_tipo.set("Ingreso")

    combo_categoria = ctk.CTkComboBox(frame_form, values=["General","Comida","Transporte","Entretenimiento","Salario"], width=150)
    combo_categoria.grid(row=0, column=1, padx=10, pady=5)

    entry_descripcion = ctk.CTkEntry(frame_form, placeholder_text="Descripción", width=200)
    entry_descripcion.grid(row=1, column=0, padx=10, pady=5)

    entry_monto = ctk.CTkEntry(frame_form, placeholder_text="Monto", width=150)
    entry_monto.grid(row=1, column=1, padx=10, pady=5)

    ctk.CTkButton(frame_form, text="Agregar Movimiento", command=agregar_movimiento, width=200)\
        .grid(row=2, column=0, columnspan=2, pady=10)

    # ESTILO OSCURO TABLA
    style = ttk.Style()
    style.theme_use("default")
    style.configure("Treeview",
        background="#1e1e1e",
        foreground="white",
        rowheight=25,
        fieldbackground="#1e1e1e"
    )
    style.map("Treeview",
        background=[("selected", "#3498db")]
    )

    tree = ttk.Treeview(frame, columns=("ID","Tipo","Categoria","Descripcion","Monto","Fecha"), show="headings")
    for col in ("ID","Tipo","Categoria","Descripcion","Monto","Fecha"):
        tree.heading(col, text=col)
        tree.column(col, anchor="center")

    tree.pack(fill="both", expand=True, pady=15)

    frame_botones = ctk.CTkFrame(frame)
    frame_botones.pack(pady=10)

    ctk.CTkButton(frame_botones, text="Eliminar", command=eliminar_registro, width=130)\
        .grid(row=0, column=0, padx=10)

    ctk.CTkButton(frame_botones, text="Exportar CSV", command=exportar_csv, width=130)\
        .grid(row=0, column=1, padx=10)

    ctk.CTkButton(frame_botones, text="Exportar PDF", command=exportar_pdf, width=130)\
        .grid(row=0, column=2, padx=10)

    frame_meta = ctk.CTkFrame(frame)
    frame_meta.pack(pady=10)

    entry_meta = ctk.CTkEntry(frame_meta, placeholder_text="Meta de ahorro", width=200)
    entry_meta.grid(row=0, column=0, padx=10)

    ctk.CTkButton(frame_meta, text="Guardar Meta", command=guardar_meta, width=150)\
        .grid(row=0, column=1, padx=10)

    label_meta = ctk.CTkLabel(frame, text="")
    label_meta.pack()

    label_balance = ctk.CTkLabel(frame, text="Balance: $0.00", font=("Arial", 20, "bold"))
    label_balance.pack(pady=15)

    ctk.CTkButton(frame, text="Cerrar Sesión", command=cerrar_sesion).pack(pady=10)

    actualizar_tabla()
    actualizar_balance()

# ===================== APP =====================

app = ctk.CTk()
app.geometry("950x650")
app.title("BOOST YOUR LIFE")

icon_path = os.path.join(BASE_DIR, "hucha.ico")
if os.path.exists(icon_path):
    app.iconbitmap(icon_path)

mostrar_login()
app.mainloop()