import hashlib
from app.services.convex_service import convex_query
from app.core.state import _state

# Obtener el token de sesión guardado
state = _state.get("current")
if not state:
    print("No hay sesión activa. Ejecuta el login primero.")
else:
    token_hash = hashlib.sha256(state.token.encode()).hexdigest()
    alumnos = convex_query("students:getWithQR", {"tokenHash": token_hash})
    for a in alumnos:
        print(f"Alumno: {a['name']} — QR: {a['qrToken']}")