from app.services.auth_service import login, hash_password
from app.services.convex_service import convex_mutation, convex_query

# Paso 1: Crear usuario admin de prueba
print("Creando usuario admin...")
school = convex_query("schools:getByCode", {"code": "VG001"})
school_id = school["_id"]

password_hash = hash_password("admin123")
user_id = convex_mutation("users:create", {
    "schoolId": school_id,
    "name": "Administrador",
    "email": "admin@vicente.edu.mx",
    "passwordHash": password_hash,
    "role": "admin",
})
print(f"Usuario creado: {user_id}")

# Paso 2: Login
print("Haciendo login...")
token, user = login("admin@vicente.edu.mx", "admin123")
print(f"Login exitoso. Token: {token[:20]}...")
print(f"Usuario: {user['name']} - Rol: {user['role']}")