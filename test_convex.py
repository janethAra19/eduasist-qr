from app.services.convex_service import convex_mutation, convex_query

# Crear escuela de prueba
print("Creando escuela...")
school_id = convex_mutation("schools:create", {
    "name": "Escuela Vicente Guerrero",
    "code": "VG001",
    "timezone": "America/Mexico_City",
})
print(f"Escuela creada: {school_id}")

# Consultar escuela
print("Consultando escuela...")
school = convex_query("schools:getByCode", {"code": "VG001"})
print(f"Escuela encontrada: {school}")