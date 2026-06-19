"""
email_service.py — Envío de correos para recuperar contraseña.

CONFIGURACIÓN (una sola vez):
1. Ve a tu cuenta Gmail → Seguridad → Verificación en 2 pasos (activar)
2. Luego → Contraseñas de aplicación → Genera una para "Correo / Windows"
3. Copia esa contraseña de 16 caracteres
4. Pon tus datos en app/core/config.py:
     GMAIL_USER         = "tucorreo@gmail.com"
     GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"
"""

import smtplib
import secrets
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.services.convex_service import convex_query, convex_mutation

try:
    from app.core.config import GMAIL_USER, GMAIL_APP_PASSWORD, ESCUELA_NOMBRE
except ImportError:
    GMAIL_USER         = ""
    GMAIL_APP_PASSWORD = ""
    ESCUELA_NOMBRE     = "EduAsist"

EXPIRA_MINUTOS = 15


def _enviar_email(destinatario: str, asunto: str, html: str):
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        raise Exception(
            "Configura GMAIL_USER y GMAIL_APP_PASSWORD en app/core/config.py\n"
            "Necesitas una Contraseña de aplicación de Google."
        )
    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"]    = f"{ESCUELA_NOMBRE} <{GMAIL_USER}>"
    msg["To"]      = destinatario
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, destinatario, msg.as_string())


def send_reset_token(email: str):
    """
    1. Verifica que el correo exista (admin/prefecto o alumno)
    2. Genera código de 6 dígitos
    3. Lo guarda en Convex con expiración de 15 minutos
    4. Envía el correo
    """
    # Verificar que el correo existe
    user = convex_query("users:getByEmail", {"email": email})
    if not user:
        student = convex_query("users:getStudentByEmail", {"email": email})
        if not student:
            raise Exception("No encontramos ninguna cuenta con ese correo.")

    # Código de 6 dígitos
    codigo = str(secrets.randbelow(900000) + 100000)
    expira = int(time.time()) + (EXPIRA_MINUTOS * 60)

    # Guardar en Convex
    convex_mutation("passwordResets:create", {
        "email":     email,
        "token":     codigo,
        "expiresAt": expira,
    })

    # Enviar email
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;
                padding:20px;background:#f9f9f9;border-radius:12px;">
      <div style="text-align:center;margin-bottom:20px;">
        <div style="background:#1B2A4A;color:white;padding:16px;border-radius:8px;">
          <h2 style="margin:0;">🔒 {ESCUELA_NOMBRE}</h2>
          <p style="margin:4px 0 0;font-size:14px;opacity:0.8;">
            Recuperación de contraseña
          </p>
        </div>
      </div>
      <div style="background:white;padding:24px;border-radius:8px;">
        <p style="color:#333;">Hola,</p>
        <p style="color:#333;">
          Recibimos una solicitud para cambiar tu contraseña.<br>
          Tu código de verificación es:
        </p>
        <div style="font-size:42px;font-weight:bold;letter-spacing:10px;
                    color:#1B2A4A;text-align:center;padding:24px 0;
                    background:#EEF2FF;border-radius:12px;margin:16px 0;">
          {codigo}
        </div>
        <p style="color:#666;font-size:13px;">
          ⏱ Este código expira en <strong>{EXPIRA_MINUTOS} minutos</strong>.
        </p>
        <p style="color:#666;font-size:13px;">
          Si no solicitaste este cambio, ignora este mensaje.
          Tu contraseña no cambiará.
        </p>
      </div>
      <p style="color:#aaa;font-size:11px;text-align:center;margin-top:16px;">
        {ESCUELA_NOMBRE} — Sistema EduAsist
      </p>
    </div>
    """
    _enviar_email(
        email,
        f"Código de verificación — {ESCUELA_NOMBRE}",
        html,
    )


def verify_reset_token_and_change(email: str, token: str, new_password: str):
    """
    Verifica el token y cambia la contraseña.
    No requiere la contraseña anterior.
    """
    if len(new_password) < 6:
        raise Exception("La contraseña debe tener al menos 6 caracteres")

    # Verificar token en Convex
    reset = convex_query("passwordResets:getValid", {
        "email": email,
        "token": token,
    })
    if not reset:
        raise Exception(
            "Código inválido o expirado.\n"
            "Solicita un nuevo código e intenta de nuevo."
        )

    # Hashear nueva contraseña
    from app.services.auth_service import hash_password
    nuevo_hash = hash_password(new_password)

    # Actualizar en Convex (busca en users y en students)
    convex_mutation("users:updatePasswordByEmail", {
        "email":        email,
        "passwordHash": nuevo_hash,
    })

    # Invalidar token para que no se pueda reutilizar
    convex_mutation("passwordResets:invalidate", {
        "email": email,
        "token": token,
    })
