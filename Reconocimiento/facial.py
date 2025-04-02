import cv2
import tkinter as tk
from tkinter import Label, Button, Entry, messagebox
from PIL import Image, ImageTk
import os
import sqlite3
from datetime import datetime

DB_FILE = "asistencias.db"
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS asistencias (
    id TEXT NOT NULL,
    nombre TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    edad INTEGER NOT NULL,
    fecha TEXT NOT NULL
)
""")
conn.commit()

# Función para capturar la foto y registrar los datos
def capturar_foto():
    nombre = entry_nombre.get().strip()
    apellidos = entry_apellidos.get().strip()
    id = entry_id.get().strip()
    edad = entry_edad.get().strip()

    if not nombre or not apellidos or not id or not edad:
        messagebox.showerror("Error", "Por favor, completa todos los campos.")
        return

    if not edad.isdigit():
        messagebox.showerror("Error", "La edad debe ser un número válido.")
        return

    # Validar ID único
    cursor.execute("SELECT * FROM asistencias WHERE id = ?", (id,))
    if len(id) != 7:
        messagebox.showerror("Error", "El ID no es válido. Debería ser de 7 caracteres.")
        return
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT * FROM asistencias WHERE id = ? AND fecha LIKE ?", (id, f"{fecha_actual}%"))
    
    if cursor.fetchone():
        messagebox.showinfo("Informacion", "Ya se ha registrado a esta persona hoy.")
        return
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "No se pudo acceder a la cámara.")
        return

    ret, frame = cap.read()
    cap.release()

    if not ret:
        messagebox.showerror("Error", "No se pudo capturar la imagen.")
        return

    try:
        ruta_foto = f"capturas/{id}.jpg"
        os.makedirs("capturas", exist_ok=True)
        cv2.imwrite(ruta_foto, frame)
        actualizar_imagen(ruta_foto)

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO asistencias (id, nombre, apellidos, edad, fecha) VALUES (?, ?, ?, ?, ?)",
                       (id, nombre, apellidos, int(edad), ahora))
        conn.commit()

        label_bienvenida.config(text=f"Bienvenido {nombre}, edad {edad} años", fg="green")
        mostrar_ultima_asistencia()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar la información: {e}")

# Función para actualizar la imagen en Tkinter
def actualizar_imagen(ruta_imagen):
    img = Image.open(ruta_imagen)
    img = img.resize((200, 200), Image.Resampling.LANCZOS)
    img = ImageTk.PhotoImage(img)
    label_imagen.config(image=img)
    label_imagen.image = img

# Función para mostrar la última asistencia registrada
def mostrar_ultima_asistencia():
    cursor.execute("SELECT * FROM asistencias ORDER BY fecha DESC LIMIT 1")
    ultima = cursor.fetchone()
    if ultima:
        label_ultima_asistencia.config(
            text=f"Última asistencia: {ultima[1]} {ultima[2]}, {ultima[3]} años ({ultima[0]})\nFecha y Hora del Registro: {ultima[4]}", fg="blue"
        )

# Función para buscar registros
def buscar_registro():
    criterio = entry_busqueda.get().strip()
    if not criterio:
        messagebox.showerror("Error", "Por favor, ingresa un criterio de búsqueda.")
        return

    cursor.execute("""
    SELECT * FROM asistencias
    WHERE id = ? OR nombre LIKE ? OR apellidos LIKE ? OR edad = ?
    """, (criterio, f"%{criterio}%", f"%{criterio}%", criterio if criterio.isdigit() else None))
    resultados = cursor.fetchall()

    if resultados:
        texto_resultados = "\n".join(
            [f"ID: {r[0]}\n Nombre: {r[1]} {r[2]}\n Edad: {r[3]}\n Fecha de Registro: {r[4]}\n" for r in resultados]
        )
        messagebox.showinfo("Resultados de Búsqueda", texto_resultados)
    else:
        messagebox.showinfo("Resultados de Búsqueda", "No se encontraron registros.")

# Crear ventana principal
root = tk.Tk()
root.title("Registro de Asistencia")
root.geometry("400x600")

# Etiqueta y campo de entrada para el nombre
tk.Label(root, text="Nombre:").pack()
entry_nombre = Entry(root)
entry_nombre.pack()

tk.Label(root, text="Apellidos:").pack()
entry_apellidos = Entry(root)
entry_apellidos.pack()

tk.Label(root, text="ID:").pack()
entry_id = Entry(root)
entry_id.pack()

tk.Label(root, text="Edad:").pack()
entry_edad = Entry(root)
entry_edad.pack()

# Botón para capturar foto
btn_capturar = Button(root, text="Registrar Asistencia", command=capturar_foto)
btn_capturar.pack(pady=10)

# Etiqueta para mostrar la imagen
label_imagen = Label(root)
label_imagen.pack(pady=10)

# Etiqueta para el mensaje de bienvenida
label_bienvenida = Label(root, text="", font=("Arial", 12))
label_bienvenida.pack()

# Etiqueta para mostrar la última asistencia registrada
label_ultima_asistencia = Label(root, text="Última asistencia: Ninguna", font=("Arial", 10), fg="blue")
label_ultima_asistencia.pack()

# Campo de búsqueda
tk.Label(root, text="Buscar por ID, Nombre, Apellidos o Edad:").pack()
entry_busqueda = Entry(root)
entry_busqueda.pack()

# Botón para buscar registros
btn_buscar = Button(root, text="Buscar", command=buscar_registro)
btn_buscar.pack(pady=10)

# Mostrar la última asistencia al iniciar
mostrar_ultima_asistencia()

root.mainloop()
