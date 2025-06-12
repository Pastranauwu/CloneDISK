# Clonador de Discos con Interfaz Gráfica en Python

Este proyecto permite listar los discos y particiones de tu equipo Windows, mostrando detalles como modelo y tamaño, y ofrece una interfaz gráfica para clonar discos utilizando `diskpart`.

## Requisitos

- **Sistema operativo:** Windows
- **Python:** 3.7 o superior
- **Dependencias:**  
  - [pywin32](https://pypi.org/project/pywin32/)

## Instalación

1. **Clona o descarga este repositorio.**

2. **Instala las dependencias:**

   Abre una terminal en la carpeta del proyecto y ejecuta:

   ```
   pip install -r requirements.txt
   ```

   El archivo `requirements.txt` debe contener:
   ```
   pywin32
   ```

## Uso

1. **Ejecuta el script principal:**

   Desde la terminal, ejecuta:

   ```
   python listarParticionar.py
   ```

2. **Interfaz gráfica:**

   - Se abrirá una ventana donde podrás:
     - Actualizar la lista de discos disponibles.
     - Seleccionar el disco de origen y el de destino.
     - Iniciar la clonación (¡ATENCIÓN! Esto borrará todos los datos del disco de destino).

3. **Advertencia:**
   - El proceso de clonación utiliza `diskpart` y puede borrar datos de manera irreversible. Úsalo con precaución y asegúrate de seleccionar correctamente los discos.

## Notas

- El script solo funciona en Windows.
- Es necesario ejecutar el script con permisos de administrador para que `diskpart` funcione correctamente.
- La clonación se realiza a nivel de partición, no de sector a sector.
