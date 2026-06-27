import os, shutil, glob

# Borrar cache
for d in glob.glob(os.path.join("app", "**", "__pycache__"), recursive=True):
    shutil.rmtree(d, ignore_errors=True)

RUTA = os.path.join("app", "views", "student", "my_qr_view.py")

with open(RUTA, "r", encoding="utf-8") as f:
    lineas = f.readlines()

QUITAR = [
    "escuela = ft.TextField",
    "codigo  = ft.TextField",
    'label="Codigo de escuela',
    'label="Número de control',
    'hint_text="Ej: VG001',
    'hint_text="Si no tienes',
    "caps_lock=True",
    "esc = escuela.value",
    "cod = codigo.value",
    "if not n or not g or not gr or not esc:",
    '"schoolCode":',
    '"studentCode": cod',
    "escuela, codigo,",
    "campo_codigo  = ft.TextField",
    "campo_escuela = ft.TextField",
    'label="Tu codigo de alumno',
    'label="Tu codigo de escuela',
    'label="Tu c\u00f3digo de alumno',
    'label="C\u00f3digo de escuela',
    "cod = campo_codigo",
    "esc = campo_escuela",
    "Ingresa tu codigo y el codigo",
    "campo_codigo, campo_escuela,",
    "campo_codigo.on_submit",
    "campo_escuela.on_submit",
]

nuevas = []
i = 0
while i < len(lineas):
    linea = lineas[i]
    saltar = False
    for patron in QUITAR:
        if patron.lower() in linea.lower():
            saltar = True
            break
    if not saltar:
        nuevas.append(linea)
    i += 1

# Arreglar validacion que quedo rota
resultado = "".join(nuevas)
resultado = resultado.replace(
    "if not n or not g or not gr or not esc:",
    "if not n or not g or not gr:"
)

with open(RUTA, "w", encoding="utf-8") as f:
    f.write(resultado)

print("LISTO: Campo codigo de escuela eliminado")
print("LISTO: Cache borrado")
print("Ejecuta: python main.py")

# Segunda pasada — arreglar referencias que quedaron
with open(RUTA, "r", encoding="utf-8") as f:
    texto = f.read()

import re

# Reemplazar validacion rota
texto = texto.replace(
    'if not cod or not esc:',
    'if not cod:'
)
texto = texto.replace(
    'error.value = "Ingresa tu codigo y el codigo de escuela"',
    'error.value = "Ingresa tu codigo de alumno"'
)
texto = texto.replace(
    'error.value = "Ingresa tu c\u00f3digo y el c\u00f3digo de escuela"',
    'error.value = "Ingresa tu codigo de alumno"'
)

with open(RUTA, "w", encoding="utf-8") as f:
    f.write(texto)

print("Segunda pasada completada")