import secrets
import hashlib
import time
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
    user = convex_query("users:getByEmail", {"email": email})
    if not user:
        raise Exception("Usuario no encontrado")
    if not verify_password(password, user["passwordHash"]):
        raise Exception("Contraseña incorrecta")

    token = generate_session_token()
    token_hash = hash_token(token)

    convex_mutation("sessions:create", {
        "userId": user["_id"],
        "schoolId": user["schoolId"],
        "role": user["role"],
        "tokenHash": token_hash,
    })

    return token, user