import os
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import win32com.client


def obtener_modelo_discos():
    """
    Obtiene información de los discos físicos y los enlaza con sus letras.
    """
    discos_info = {}  # Diccionario para almacenar modelo y tamaño de cada disco
    try:
        wmi = win32com.client.Dispatch("WbemScripting.SWbemLocator")  # Inicializa el cliente WMI
        servicio = wmi.ConnectServer(".", "root\\cimv2")  # Conecta al servicio WMI local
        discos = servicio.ExecQuery("SELECT * FROM Win32_DiskDrive")  # Consulta todos los discos físicos

        for disco in discos:  # Itera sobre cada disco encontrado
            modelo = disco.Model  # Obtiene el modelo del disco
            size = disco.Size  # Obtiene el tamaño en bytes
            if size:
                tamaño_gb = int(size) / (1024**3)  # Convierte el tamaño a GB
                discos_info[modelo] = f"{tamaño_gb:.2f} GB"  # Guarda modelo y tamaño en el diccionario
    except Exception as e:
        print(f"Error obteniendo información de los discos: {e}")  # Muestra error si ocurre
    return discos_info  # Devuelve el diccionario con la información de los discos


def listar_discos_con_detalles():
    """
    Lista las unidades disponibles con su letra, tamaño y modelo.
    """
    discos = []  # Lista para almacenar la información de cada unidad
    modelos = obtener_modelo_discos()  # Obtiene los modelos y tamaños de los discos físicos

    for letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":  # Itera sobre todas las posibles letras de unidad
        ruta = f"{letra}:\\"  # Construye la ruta de la unidad
        if os.path.exists(ruta):  # Verifica si la unidad existe
            try:
                total, _, _ = shutil.disk_usage(ruta)  # Obtiene el tamaño total de la unidad
                tamaño_gb = total / (1024**3)  # Convierte el tamaño a GB
                # Busca el modelo cuyo tamaño coincide aproximadamente con el de la unidad
                modelo = next((key for key, value in modelos.items() if f"{tamaño_gb:.0f}" in value), "Desconocido")
                discos.append(f"{ruta} - {modelo} - {tamaño_gb:.2f} GB")  # Agrega la info a la lista
            except Exception as e:
                discos.append(f"{ruta} - Modelo desconocido - Tamaño desconocido")  # Si hay error, agrega como desconocido
    return discos  # Devuelve la lista de discos con detalles


def clonar_disco(origen, destino):
    """
    Clona un disco de origen a un destino usando el comando diskpart.
    """
    try:
        # Verificamos que el origen y destino sean válidos
        if not origen or not destino:
            messagebox.showwarning("Advertencia", "Debe seleccionar discos válidos.")  # Muestra advertencia si faltan datos
            return

        # Extraemos las letras de las unidades seleccionadas
        origen_letra = origen.split(" - ")[0].strip(":\\")  # Obtiene la letra del disco origen
        destino_letra = destino.split(" - ")[0].strip(":\\")  # Obtiene la letra del disco destino
        
        # Confirmación antes de clonar
        respuesta = messagebox.askyesno(
            "Confirmación",
            f"¿Está seguro de clonar {origen} a {destino}? Esto borrará todos los datos del destino."
        )
        if not respuesta:
            return  # Si el usuario cancela, no hace nada

        # Crear un archivo temporario de script para diskpart
        script_path = "clonar_disco.txt"  # Nombre del archivo temporal
        with open(script_path, "w") as script:  # Abre el archivo para escribir el script
            script.write(f"select volume {origen_letra}\n")  # Selecciona el volumen origen
            script.write(f"clean\n")  # Limpia el disco destino (¡peligroso!)
            script.write(f"create partition primary\n")  # Crea una partición primaria
            script.write(f"format fs=ntfs quick\n")  # Formatea la partición como NTFS rápido
            script.write(f"assign letter={destino_letra}\n")  # Asigna la letra al destino
            script.write(f"exit\n")  # Sale de diskpart

        # Ejecutar el comando diskpart con el script y capturar la salida
        result = subprocess.run(["diskpart", "/s", script_path], check=True, capture_output=True, text=True)

        # Verificar la salida de diskpart
        if result.returncode != 0:
            messagebox.showerror("Error", f"Error en diskpart: {result.stderr}")  # Muestra error si falla
        else:
            messagebox.showinfo("Éxito", f"Disco clonado de {origen} a {destino}.")  # Muestra éxito

        # Eliminar el archivo de script
        os.remove(script_path)  # Borra el archivo temporal
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"No se pudo completar la clonación: {e}")  # Error específico de subprocess
    except Exception as e:
        messagebox.showerror("Error", f"Error inesperado: {e}")  # Otros errores inesperados


def crear_interfaz():
    # Función interna para actualizar la lista de discos en los combobox
    def actualizar_discos():
        discos = listar_discos_con_detalles()  # Obtiene la lista de discos
        if discos:
            lista_origen["values"] = discos  # Actualiza el combobox de origen
            lista_destino["values"] = discos  # Actualiza el combobox de destino
        else:
            messagebox.showinfo("Sin discos", "No se encontraron discos disponibles.")  # Muestra mensaje si no hay discos

    # Función interna para iniciar la clonación al presionar el botón
    def iniciar_clonacion():
        origen = lista_origen.get()  # Obtiene el disco de origen seleccionado
        destino = lista_destino.get()  # Obtiene el disco de destino seleccionado
        clonar_disco(origen, destino)  # Llama a la función de clonación

    ventana = tk.Tk()  # Crea la ventana principal de Tkinter
    ventana.title("Clonación de Discos")  # Título de la ventana
    ventana.geometry("600x400")  # Tamaño de la ventana
    ventana.config(bg="#f0f0f0")  # Fondo gris claro para la ventana

    # Título
    titulo_label = tk.Label(ventana, text="Clonación de Discos", font=("Arial", 20, "bold"), bg="#f0f0f0")
    titulo_label.pack(pady=20)  # Muestra el título con espacio vertical

    # Marco para los combos de origen y destino
    frame_discos = tk.Frame(ventana, bg="#f0f0f0")
    frame_discos.pack(pady=20)  # Añade espacio vertical

    tk.Label(frame_discos, text="Seleccione el disco de origen:", font=("Arial", 12), bg="#f0f0f0").pack(pady=5)
    lista_origen = ttk.Combobox(frame_discos, state="readonly", width=50, font=("Arial", 12))
    lista_origen.pack(pady=5)  # Combobox para seleccionar disco de origen

    tk.Label(frame_discos, text="Seleccione el disco de destino:", font=("Arial", 12), bg="#f0f0f0").pack(pady=5)
    lista_destino = ttk.Combobox(frame_discos, state="readonly", width=50, font=("Arial", 12))
    lista_destino.pack(pady=5)  # Combobox para seleccionar disco de destino

    # Llenar los combobox al iniciar la ventana
    actualizar_discos()
    # Botones
    frame_boton = tk.Frame(ventana, bg="#f0f0f0")
    frame_boton.pack(pady=20)  # Añade espacio vertical

    actualizar_button = tk.Button(
        frame_boton, text="Actualizar Discos", command=actualizar_discos,
        width=20, font=("Arial", 12), bg="#4CAF50", fg="white", relief="flat"
    )
    actualizar_button.pack(pady=10)  # Botón para actualizar la lista de discos

    clonar_button = tk.Button(
        frame_boton, text="Iniciar Clonación", command=iniciar_clonacion,
        width=20, font=("Arial", 12), bg="#2196F3", fg="white", relief="flat"
    )
    clonar_button.pack(pady=10)  # Botón para iniciar la clonación

    ventana.mainloop()  # Inicia el bucle principal de la interfaz gráfica

if __name__ == "__main__":
    crear_interfaz()