import os
import win32api
import win32file
import wmi
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import ctypes

# 1. Identificación precisa de discos físicos
def obtener_discos_fisicos():
    """Obtiene discos físicos con sus índices, modelos y tamaños"""
    discos = []
    try:
        conexion = wmi.WMI()
        for fisico in conexion.Win32_DiskDrive():
            discos.append({
                'indice': fisico.Index,
                'modelo': fisico.Model,
                'tamaño': int(fisico.Size),
                'interfaz': fisico.InterfaceType,
                'particiones': []
            })
    except Exception as e:
        print(f"Error obteniendo discos físicos: {e}")
    return discos

# 2. Detectar particiones de cada disco
def obtener_particiones():
    """Obtiene información de particiones y las relaciona con discos físicos"""
    discos = obtener_discos_fisicos()
    try:
        conexion = wmi.WMI()

        for logica in conexion.Win32_LogicalDisk(DriveType=3):
            # Verifica que logica tenga DiskIndex
            if not hasattr(logica, "DiskIndex"):
                continue
            for disco in discos:
                if disco['indice'] == logica.DiskIndex:
                    disco['particiones'].append({
                        'letra': logica.DeviceID,
                        'tamaño': int(logica.Size),
                        'libre': int(logica.FreeSpace)
                    })

    except Exception as e:
        print(f"Error obteniendo particiones: {e!r}")
    return discos

# 3. Clonación real con herramienta externa (requiere ejecutar como administrador)
def clonar_disco(origen_idx, destino_idx):
    """
    Clona usando herramienta de bajo nivel (ej. dd para Windows)
    Requiere: https://chrysocome.net/dd
    """
    try:
        comando = f"dd if=\\.\\PhysicalDrive{origen_idx} of=\\.\\PhysicalDrive{destino_idx} bs=1M --progress"
        proceso = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Leer salida en tiempo real
        while True:
            salida = proceso.stdout.readline()
            if salida == '' and proceso.poll() is not None:
                break
            if salida:
                print(salida.strip())
        
        if proceso.returncode != 0:
            raise subprocess.CalledProcessError(proceso.returncode, comando)
            
    except Exception as e:
        raise Exception(f"Error en clonación: {e}")

# 4. Interfaz mejorada
def crear_interfaz():
    def actualizar_listas():
        discos = obtener_particiones()
        lista_origen['values'] = [
            f"Disco {d['indice']}: {d['modelo']} ({d['tamaño']//(1024**3)}GB)" 
            for d in discos
        ]
        lista_destino['values'] = lista_origen['values']
    
    def iniciar_clonacion():
        origen = lista_origen.get()
        destino = lista_destino.get()
        
        if not origen or not destino:
            messagebox.showwarning("Error", "Seleccione ambos discos")
            return
            
        origen_idx = int(origen.split()[1][:-1])
        destino_idx = int(destino.split()[1][:-1])
        
        # Confirmación crítica
        confirm = messagebox.askyesno(
            "¡ADVERTENCIA!",
            f"¿Clonar DISCO {origen_idx} a DISCO {destino_idx}?\n"
            f"¡TODOS LOS DATOS EN EL DESTINO SERÁN DESTRUIDOS!",
            icon='warning'
        )
        if not confirm:
            return
        
        # Ejecutar en hilo separado para no bloquear la GUI
        def tarea_clonacion():
            try:
                btn_clonar.config(state=tk.DISABLED)
                clonar_disco(origen_idx, destino_idx)
                messagebox.showinfo("Éxito", "Clonación completada")
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                btn_clonar.config(state=tk.NORMAL)
        
        threading.Thread(target=tarea_clonacion, daemon=True).start()

    # Configuración de ventana
    ventana = tk.Tk()
    ventana.title("Clonador de Discos - Admin")
    ventana.geometry("560x370")
    ventana.resizable(False, False)
    try:
        ventana.iconbitmap("icon.ico")
    except Exception:
        pass

    # Estilo ttk mejorado
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TLabel', font=('Segoe UI', 12))
    style.configure('TButton', font=('Segoe UI', 12), padding=8)
    style.configure('TCombobox', font=('Segoe UI', 12), padding=4)
    style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'))
    style.configure('Warning.TLabel', font=('Segoe UI', 11, 'bold'), foreground='red')
    # Botón verde personalizado
    style.configure('Green.TButton', font=('Segoe UI', 12), padding=8, background='#4CAF50', foreground='white')
    style.map('Green.TButton',
              background=[('active', '#45a049'), ('!active', '#4CAF50')],
              foreground=[('disabled', '#cccccc'), ('!disabled', 'white')])

    ventana.configure(bg="#f5f5f5")

    frame = ttk.Frame(ventana, padding=30, style='My.TFrame')
    frame.pack(expand=True, fill='both')
    style.configure('My.TFrame', background="#f5f5f5")

    # Encabezado
    ttk.Label(frame, text="Clonador de Discos", style='Header.TLabel', anchor='center').grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky='ew')

    # Disco Origen
    ttk.Label(frame, text="Disco Origen:").grid(row=1, column=0, sticky='e', pady=10, padx=10)
    lista_origen = ttk.Combobox(frame, width=55, state="readonly")
    lista_origen.grid(row=1, column=1, pady=10, padx=10, sticky='w')

    # Disco Destino
    ttk.Label(frame, text="Disco Destino:").grid(row=2, column=0, sticky='e', pady=10, padx=10)
    lista_destino = ttk.Combobox(frame, width=55, state="readonly")
    lista_destino.grid(row=2, column=1, pady=10, padx=10, sticky='w')

    # Botones en un frame centrado
    frame_botones = ttk.Frame(frame, style='My.TFrame')
    frame_botones.grid(row=3, column=0, columnspan=2, pady=25, sticky='ew')
    frame_botones.columnconfigure(0, weight=1)
    frame_botones.columnconfigure(1, weight=1)

    btn_clonar = ttk.Button(frame_botones, text="Clonar", command=iniciar_clonacion, style='Green.TButton')
    btn_clonar.grid(row=0, column=0, padx=20, sticky='e')

    btn_actualizar = ttk.Button(frame_botones, text="Actualizar", command=actualizar_listas)
    btn_actualizar.grid(row=0, column=1, padx=20, sticky='w')

    # Separador visual
    sep = ttk.Separator(frame, orient='horizontal')
    sep.grid(row=4, column=0, columnspan=2, sticky='ew', pady=10)

    # Pie de página y advertencia
    ttk.Label(
        frame,
        text="Advertencia: ¡Todos los datos del disco destino serán eliminados!",
        style='Warning.TLabel',
        anchor='center',
        justify='center'
    ).grid(row=5, column=0, columnspan=2, pady=(10, 0), sticky='ew')

    ttk.Label(
        frame,
        text="Utilice esta herramienta con precaución. Requiere permisos de administrador.",
        font=('Segoe UI', 10),
        anchor='center',
        justify='center'
    ).grid(row=6, column=0, columnspan=2, pady=(5, 0), sticky='ew')

    # Inicializar listas
    actualizar_listas()

    ventana.mainloop()

if __name__ == "__main__":
    # Requiere administrador
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("Debes ejecutar este programa como administrador.")
        messagebox.showerror("Permisos", "Ejecutar como administrador")
        input("Presiona Enter para salir...")
        sys.exit(1)
    crear_interfaz()