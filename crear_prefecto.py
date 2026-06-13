from argon2 import PasswordHasher
from app.services.convex_service import convex_query, convex_mutation

ph = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)

# ── CAMBIA ESTOS 4 DATOS ──────────────────────────────────────────
EMAIL_ADMIN  = "admin@vicente.edu.mx"  # email del admin que ya tienes
EMAIL        = "prefecto@vicente.edu.mx"  # email del prefecto nuevo
PASSWORD     = "123456"                # contraseña del prefecto
NOMBRE       = "Prefecto Juan"         # nombre del prefecto
# ─────────────────────────────────────────────────────────────────

admin = convex_query("users:getByEmail", {"email": EMAIL_ADMIN})
if not admin:
    print(f"❌ No se encontró el admin con email: {EMAIL_ADMIN}")
    exit()

school_id = admin["schoolId"]
password_hash = ph.hash(PASSWORD)

try:
    convex_mutation("users:create", {
        "schoolId": school_id,
        "name": NOMBRE,
        "email": EMAIL,
        "passwordHash": password_hash,
        "role": "prefect",
    })
    print(f"✅ Prefecto creado correctamente")
    print(f"   Nombre:   {NOMBRE}")
    print(f"   Email:    {EMAIL}")
    print(f"   Password: {PASSWORD}")
except Exception as ex:
    print(f"❌ Error: {ex}")
