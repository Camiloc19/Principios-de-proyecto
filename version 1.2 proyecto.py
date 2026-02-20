import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ================== BASE DE DATOS ==================
conn = sqlite3.connect("finanzas.db")
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
    tipo TEXT,
    descripcion TEXT,
    monto REAL
)
""")

conn.commit()

# ================== FUNCIONES ==================

def verificar_login():
    usuario = entry_usuario.get()
    contraseña = entry_contraseña.get()

    cursor.execute(
        "SELECT * FROM usuarios WHERE usuario = ? AND contraseña = ?",
        (usuario, contraseña)
    )

    if cursor.fetchone():
        for widget in app.winfo_children():
            widget.destroy()
        mostrar_sistema()
    else:
        messagebox.showerror("Error", "Usuario o contraseña incorrectos")


def registrar_usuario():
    nuevo_usuario = entry_nuevo_usuario.get()
    nueva_contraseña = entry_nueva_contraseña.get()

    if not nuevo_usuario or not nueva_contraseña:
        messagebox.showwarning("Aviso", "Completa todos los campos.")
        return

    try:
        cursor.execute(
            "INSERT INTO usuarios (usuario, contraseña) VALUES (?, ?)",
            (nuevo_usuario, nueva_contraseña)
        )
        conn.commit()
        messagebox.showinfo("Éxito", "Usuario registrado correctamente.")
        ventana_registro.destroy()
    except:
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


def agregar_movimiento():
    tipo = combo_tipo.get()
    descripcion = entry_descripcion.get()
    monto = entry_monto.get()

    if not descripcion or not monto:
        messagebox.showwarning("Aviso", "Completa todos los campos.")
        return

    cursor.execute(
        "INSERT INTO movimientos (tipo, descripcion, monto) VALUES (?, ?, ?)",
        (tipo, descripcion, float(monto))
    )

    conn.commit()
    actualizar_tabla()
    actualizar_balance()

    entry_descripcion.delete(0, "end")
    entry_monto.delete(0, "end")


def actualizar_tabla():
    for row in tree.get_children():
        tree.delete(row)

    cursor.execute("SELECT * FROM movimientos")
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
    seleccionados = tree.selection()

    if not seleccionados:
        messagebox.showwarning("Aviso", "Selecciona un registro.")
        return

    for item in seleccionados:
        valores = tree.item(item)["values"]
        id_mov = valores[0]
        cursor.execute("DELETE FROM movimientos WHERE id = ?", (id_mov,))

    conn.commit()
    actualizar_tabla()
    actualizar_balance()


# ================== INTERFAZ ==================

def mostrar_login():
    global entry_usuario, entry_contraseña

    login_frame = ctk.CTkFrame(app)
    login_frame.pack(expand=True)

    ctk.CTkLabel(login_frame, text="INICIAR SESIÓN", font=("Arial", 22)).pack(pady=20)

    entry_usuario = ctk.CTkEntry(login_frame, placeholder_text="Usuario")
    entry_usuario.pack(pady=10)

    entry_contraseña = ctk.CTkEntry(login_frame, placeholder_text="Contraseña", show="*")
    entry_contraseña.pack(pady=10)

    ctk.CTkButton(login_frame, text="Ingresar", command=verificar_login).pack(pady=10)

    ctk.CTkButton(
        login_frame,
        text="Registrar Nuevo Usuario",
        fg_color="#2563eb",
        command=abrir_registro
    ).pack(pady=5)


def mostrar_sistema():
    global tree, entry_descripcion, entry_monto, combo_tipo, label_balance

    main_frame = ctk.CTkFrame(app)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    ctk.CTkLabel(main_frame, text="Sistema de Finanzas", font=("Arial", 22)).pack(pady=10)

    combo_tipo = ctk.CTkComboBox(main_frame, values=["Ingreso", "Gasto"])
    combo_tipo.pack(pady=5)
    combo_tipo.set("Ingreso")

    entry_descripcion = ctk.CTkEntry(main_frame, placeholder_text="Descripción")
    entry_descripcion.pack(pady=5)

    entry_monto = ctk.CTkEntry(main_frame, placeholder_text="Monto")
    entry_monto.pack(pady=5)

    ctk.CTkButton(main_frame, text="Agregar Movimiento", command=agregar_movimiento).pack(pady=5)

    tree = ttk.Treeview(main_frame, columns=("ID", "Tipo", "Descripción", "Monto"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Tipo", text="Tipo")
    tree.heading("Descripción", text="Descripción")
    tree.heading("Monto", text="Monto")

    tree.pack(pady=10, fill="both", expand=True)

    ctk.CTkButton(
        main_frame,
        text="Eliminar Registro",
        fg_color="#dc2626",
        command=eliminar_registro
    ).pack(pady=5)

    label_balance = ctk.CTkLabel(main_frame, text="Balance: $0.00", font=("Arial", 18))
    label_balance.pack(pady=10)

    actualizar_tabla()
    actualizar_balance()


# ================== APP ==================

app = ctk.CTk()
app.geometry("900x600")
app.title("BOOST YOUR LIFE")

# Si tienes icono.png en la misma carpeta:
if os.path.exists("ficticio.png"):
    icono = tk.PhotoImage(file="icono.png")
    app.iconphoto(True, icono)

mostrar_login()

app.mainloop()