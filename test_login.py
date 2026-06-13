import hashlib
from app.services.convex_service import convex_query
from app.services.auth_service import login

# Login
print("Haciendo login...")
token, user = login("admin@vicente.edu.mx", "admin123")
print(f"Login exitoso: {user['name']}")

# Probar getWithQR
token_hash = hashlib.sha256(token.encode()).hexdigest()
alumnos = convex_query("students:getWithQR", {"tokenHash": token_hash})
print("\nAlumnos con QR:")
for a in alumnos:
    print(f"  {a['name']} — QR: {a['qrToken']}")

    from app.services.qr_service import generar_qr

print("\nGenerando QR...")
for a in alumnos:
    if a["qrToken"]:
        ruta = generar_qr(a["qrToken"], a["name"])
        print(f"  QR generado: {ruta}")