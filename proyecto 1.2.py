import customtkinter as ctk
from tkinter import ttk
import sqlite3
from datetime import datetime

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
# FUNCIONES
# =========================

#comentario
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
        return

    fecha = datetime.now().strftime("%Y-%m-%d")

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

    cursor.execute("SELECT * FROM movimientos ORDER BY fecha DESC")

    for row in cursor.fetchall():
        tree.insert("", "end", values=row)


def actualizar_balance():
    balance = calcular_balance()
    label_balance.configure(text=f"${balance:,.2f}")


# =========================
# INTERFAZ PRINCIPAL
# =========================

app = ctk.CTk()
app.geometry("1000x600")
app.title("Control Financiero Pro")

# Sidebar
sidebar = ctk.CTkFrame(app, width=200, corner_radius=0)
sidebar.pack(side="left", fill="y")

logo = ctk.CTkLabel(
    sidebar,
    text="💳 Finanzas Pro",
    font=ctk.CTkFont(size=18, weight="bold")
)
logo.pack(pady=30)

# Área principal
main_frame = ctk.CTkFrame(app)
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

# Balance
label_title = ctk.CTkLabel(
    main_frame,
    text="Balance Actual",
    font=ctk.CTkFont(size=20)
)
label_title.pack()

label_balance = ctk.CTkLabel(
    main_frame,
    text="$0.00",
    font=ctk.CTkFont(size=32, weight="bold")
)
label_balance.pack(pady=10)

# Registro
entry_monto = ctk.CTkEntry(
    main_frame,
    placeholder_text="Ingrese monto"
)
entry_monto.pack(pady=10)

botones_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
botones_frame.pack(pady=10)

btn_ingreso = ctk.CTkButton(
    botones_frame,
    text="Ingreso",
    fg_color="#16a34a",
    hover_color="#13cc57",
    command=lambda: registrar("Ingreso")
)
btn_ingreso.pack(side="left", padx=10)

btn_gasto = ctk.CTkButton(
    botones_frame,
    text="Gasto",
    fg_color="#17e0e0", #cambio de color 
    hover_color="#1dee0a",#cambio de color
    command=lambda: registrar("Gasto")
)
btn_gasto.pack(side="left", padx=10)

# Tabla (usamos ttk para tabla)
tree = ttk.Treeview(main_frame,
                    columns=("ID", "Tipo", "Monto", "Fecha"),
                    show="headings")

tree.heading("ID", text="ID")
tree.heading("Tipo", text="Tipo")
tree.heading("Monto", text="Monto")
tree.heading("Fecha", text="Fecha")

tree.column("ID", width=50, anchor="center")
tree.column("Tipo", width=100, anchor="center")
tree.column("Monto", width=120, anchor="center")
tree.column("Fecha", width=120, anchor="center")

tree.pack(fill="both", expand=True, pady=20)

# Inicializar
actualizar_tabla()
actualizar_balance()

app.mainloop()