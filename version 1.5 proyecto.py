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

# ===================== BASE DE DATOS SEGURA =====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "finanzas.db")

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
    tipo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    monto REAL NOT NULL
)
""")

conn.commit()

# ===================== FUNCIONES LOGIN =====================

def verificar_login():
    usuario = entry_usuario.get().strip()
    contraseña = entry_contraseña.get().strip()

    if not usuario or not contraseña:
        messagebox.showwarning("Aviso", "Completa todos los campos.")
        return

    cursor.execute(
        "SELECT * FROM usuarios WHERE usuario = ? AND contraseña = ?",
        (usuario, contraseña)
    )

    if cursor.fetchone():
        limpiar_ventana()
        mostrar_sistema(usuario)
    else:
        messagebox.showerror("Error", "Usuario o contraseña incorrectos")


def cerrar_sesion():
    limpiar_ventana()
    mostrar_login()


def limpiar_ventana():
    for widget in app.winfo_children():
        widget.destroy()


# ===================== REGISTRO =====================

def registrar_usuario():
    usuario = entry_nuevo_usuario.get().strip()
    contraseña = entry_nueva_contraseña.get().strip()

    if not usuario or not contraseña:
        messagebox.showwarning("Aviso", "Completa todos los campos.")
        return

    try:
        cursor.execute(
            "INSERT INTO usuarios (usuario, contraseña) VALUES (?, ?)",
            (usuario, contraseña)
        )
        conn.commit()
        messagebox.showinfo("Éxito", "Usuario registrado correctamente.")
        ventana_registro.destroy()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "El usuario ya existe.")


def abrir_registro():
    global entry_nuevo_usuario, entry_nueva_contraseña, ventana_registro

    ventana_registro = ctk.CTkToplevel(app)
    ventana_registro.geometry("300x250")
    ventana_registro.title("Registrar Usuario")

    ctk.CTkLabel(ventana_registro, text="Nuevo Usuario").pack(pady=10)

    entry_nuevo_usuario = ctk.CTkEntry(ventana_registro, placeholder_text="Usuario")
    entry_nuevo_usuario.pack(pady=5)

    entry_nueva_contraseña = ctk.CTkEntry(
        ventana_registro,
        placeholder_text="Contraseña",
        show="*"
    )
    entry_nueva_contraseña.pack(pady=5)

    ctk.CTkButton(
        ventana_registro,
        text="Registrar",
        command=registrar_usuario
    ).pack(pady=15)


# ===================== MOVIMIENTOS =====================

def agregar_movimiento():
    tipo = combo_tipo.get()
    descripcion = entry_descripcion.get().strip()
    monto = entry_monto.get().strip()

    if not descripcion or not monto:
        messagebox.showwarning("Aviso", "Completa todos los campos.")
        return

    try:
        monto = float(monto)
    except ValueError:
        messagebox.showerror("Error", "El monto debe ser numérico.")
        return

    cursor.execute(
        "INSERT INTO movimientos (tipo, descripcion, monto) VALUES (?, ?, ?)",
        (tipo, descripcion, monto)
    )

    conn.commit()
    actualizar_tabla()
    actualizar_balance()

    entry_descripcion.delete(0, "end")
    entry_monto.delete(0, "end")


def actualizar_tabla():
    for row in tree.get_children():
        tree.delete(row)

    cursor.execute("SELECT * FROM movimientos ORDER BY id DESC")
    for row in cursor.fetchall():
        tree.insert("", "end", values=row)


def actualizar_balance():
    cursor.execute("SELECT SUM(monto) FROM movimientos WHERE tipo='Ingreso'")
    ingresos = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(monto) FROM movimientos WHERE tipo='Gasto'")
    gastos = cursor.fetchone()[0] or 0

    balance = ingresos - gastos
    label_balance.configure(text=f"Balance: ${balance:,.2f}")


def eliminar_registro():
    seleccion = tree.selection()

    if not seleccion:
        messagebox.showwarning("Aviso", "Selecciona un registro.")
        return

    for item in seleccion:
        valores = tree.item(item)["values"]
        cursor.execute("DELETE FROM movimientos WHERE id = ?", (valores[0],))

    conn.commit()
    actualizar_tabla()
    actualizar_balance()


# ===================== EXPORTAR =====================

def exportar_csv():
    cursor.execute("SELECT * FROM movimientos")
    datos = cursor.fetchall()

    ruta = os.path.join(BASE_DIR, "movimientos_exportados.csv")

    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Tipo", "Descripción", "Monto"])
        writer.writerows(datos)

    messagebox.showinfo("Exportado", "CSV generado correctamente.")


def exportar_pdf():
    cursor.execute("SELECT * FROM movimientos")
    datos = cursor.fetchall()

    ruta = os.path.join(BASE_DIR, "movimientos_exportados.pdf")
    doc = SimpleDocTemplate(ruta, pagesize=pagesizes.A4)

    elementos = []
    estilos = getSampleStyleSheet()

    elementos.append(Paragraph("Reporte de Movimientos", estilos["Title"]))
    elementos.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilos["Normal"]))
    elementos.append(Spacer(1, 20))

    tabla_data = [["ID", "Tipo", "Descripción", "Monto"]]

    for fila in datos:
        tabla_data.append([str(fila[0]), fila[1], fila[2], f"${fila[3]:,.2f}"])

    tabla = Table(tabla_data)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ]))

    elementos.append(tabla)
    doc.build(elementos)

    messagebox.showinfo("Exportado", "PDF generado correctamente.")


# ===================== INTERFAZ =====================

def mostrar_login():
    global entry_usuario, entry_contraseña

    frame = ctk.CTkFrame(app)
    frame.pack(expand=True)

    ctk.CTkLabel(frame, text="INICIAR SESIÓN", font=("Arial", 22)).pack(pady=20)

    entry_usuario = ctk.CTkEntry(frame, placeholder_text="Usuario")
    entry_usuario.pack(pady=10)

    entry_contraseña = ctk.CTkEntry(frame, placeholder_text="Contraseña", show="*")
    entry_contraseña.pack(pady=10)

    ctk.CTkButton(frame, text="Ingresar", command=verificar_login).pack(pady=10)
    ctk.CTkButton(frame, text="Registrar Nuevo Usuario", command=abrir_registro).pack()


def mostrar_sistema(usuario):
    global tree, entry_descripcion, entry_monto, combo_tipo, label_balance

    frame = ctk.CTkFrame(app)
    frame.pack(fill="both", expand=True, padx=20, pady=20)

    ctk.CTkLabel(frame, text=f"Bienvenido {usuario}", font=("Arial", 18)).pack()
    ctk.CTkLabel(frame, text="Sistema de Finanzas", font=("Arial", 22)).pack(pady=10)

    combo_tipo = ctk.CTkComboBox(frame, values=["Ingreso", "Gasto"])
    combo_tipo.pack()
    combo_tipo.set("Ingreso")

    entry_descripcion = ctk.CTkEntry(frame, placeholder_text="Descripción")
    entry_descripcion.pack(pady=5)

    entry_monto = ctk.CTkEntry(frame, placeholder_text="Monto")
    entry_monto.pack(pady=5)

    ctk.CTkButton(frame, text="Agregar Movimiento", command=agregar_movimiento).pack(pady=5)

    tree = ttk.Treeview(frame, columns=("ID", "Tipo", "Descripción", "Monto"), show="headings")
    for col in ("ID", "Tipo", "Descripción", "Monto"):
        tree.heading(col, text=col)
    tree.pack(fill="both", expand=True, pady=10)

    ctk.CTkButton(frame, text="Eliminar Registro", command=eliminar_registro).pack(pady=5)
    ctk.CTkButton(frame, text="Exportar CSV", command=exportar_csv).pack(pady=5)
    ctk.CTkButton(frame, text="Exportar PDF", command=exportar_pdf).pack(pady=5)

    label_balance = ctk.CTkLabel(frame, text="Balance: $0.00", font=("Arial", 18))
    label_balance.pack(pady=10)

    ctk.CTkButton(frame, text="Cerrar Sesión", command=cerrar_sesion).pack(pady=5)

    actualizar_tabla()
    actualizar_balance()


# ===================== APP =====================

app = ctk.CTk()
app.geometry("900x600")
app.title("BOOST YOUR LIFE")

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(BASE_DIR, "hucha.ico")

if os.path.exists(icon_path):
    app.iconbitmap(icon_path)

mostrar_login()
app.mainloop()