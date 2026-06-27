import secrets
import hashlib
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from app.services.convex_service import convex_query, convex_mutation

ph = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def login(email: str, password: str):
    # 1. Buscar como admin/prefecto
    user = convex_query("users:getByEmail", {"email": email})
    if user:
        if not verify_password(password, user["passwordHash"]):
            raise Exception("Contraseña incorrecta")
        token = generate_session_token()
        token_hash = hash_token(token)
        convex_mutation("sessions:create", {
            "userId":    user["_id"],
            "schoolId":  user["schoolId"],
            "role":      user["role"],
            "tokenHash": token_hash,
        })
        return token, {**user, "role": user["role"]}

    # 2. Buscar como alumno
    student = convex_query("users:getStudentByEmail", {"email": email})
    if student:
        pwd_hash = student.get("passwordHash")
        if not pwd_hash:
            raise Exception("Este alumno no tiene contraseña. Regístrate primero.")
        if not verify_password(password, pwd_hash):
            raise Exception("Contraseña incorrecta")
        token = generate_session_token()
        token_hash = hash_token(token)
        convex_mutation("studentSessions:create", {
            "studentId": student["_id"],
            "schoolId":  student["schoolId"],
            "tokenHash": token_hash,
        })
        return token, {**student, "role": "student"}

    raise Exception("Usuario no encontrado")


def register(name: str, email: str, password: str, role: str, school_name: str = ""):
    """Registra admin o prefecto."""
    if len(password) < 6:
        raise Exception("La contraseña debe tener al menos 6 caracteres")
    password_hash = hash_password(password)
    convex_mutation("users:register", {
        "name":         name,
        "email":        email,
        "passwordHash": password_hash,
        "role":         role,
        "schoolName":   school_name or "Mi Escuela",
    })
    return login(email, password)


def register_student(name: str, email: str, password: str,
                     grade: str, group: str):
    """
    Registra un alumno nuevo con correo y contraseña.
    - Genera su perfil de alumno automáticamente
    - Genera su QR automáticamente
    - Aparece al instante en el panel del admin
    - NO requiere intervención del admin
    """
    if len(password) < 6:
        raise Exception("La contraseña debe tener al menos 6 caracteres")

    password_hash = hash_password(password)

    result = convex_mutation("students:registerWithAccount", {
        "name":         name,
        "email":        email,
        "passwordHash": password_hash,
        "grade":        grade,
        "group":        group,
    })

    return login(email, password)