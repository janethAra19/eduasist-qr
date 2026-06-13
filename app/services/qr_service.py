import qrcode
import os
from PIL import Image

def generar_qr(token: str, nombre: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(token)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1B2A4A", back_color="white")

    # Nombre de archivo seguro
    nombre_limpio = nombre.replace(" ", "_").replace("/", "_")
    ruta = os.path.join("assets", "qr", f"{nombre_limpio}.png")
    img.save(ruta)
    return ruta