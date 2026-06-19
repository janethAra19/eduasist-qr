import flet as ft
import qrcode
import io
import base64
import os
import threading
import time

from app.services.convex_service import convex_query, convex_mutation
from app.core.config import AZUL_MARINO, DORADO, ROJO, FONDO, ESCUELA_NOMBRE
from app.core.state import get_app_state, clear_app_state

INACTIVIDAD_SEG = 300   # 5 minutos


def _hacer_qr_b64(token: str) -> str:
    qr = qrcode.QRCode(version=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_H,
                       box_size=10, border=4)
    qr.add_data(token)
    qr.make(fit=True)
    img = qr.make_image(fill_color=AZUL_MARINO, back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


class MyQRView:
    def __init__(self, page: ft.Page):
        self.page        = page
        self._alumno     = None
        self._qr_b64     = None
        self._pantalla   = "inicio"   # inicio|registro|buscar|qr|perfil|cambiar_pass
        self._timer      = None
        self._foto_path  = None

    # ── Timer inactividad ─────────────────────────────────────────────────────
    def _reset_timer(self):
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(INACTIVIDAD_SEG, self._timeout)
        self._timer.daemon = True
        self._timer.start()

    def _cancel_timer(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def _timeout(self):
        """Se llama tras 5 min sin actividad — cierra sesión automáticamente."""
        if self._pantalla in ("qr", "perfil", "cambiar_pass"):
            self._alumno    = None
            self._qr_b64    = None
            self._foto_path = None
            clear_app_state()
            self._ir("inicio")

    # ── Navegación ────────────────────────────────────────────────────────────
    def _ir(self, pantalla: str):
        self._pantalla = pantalla
        self.page.controls.clear()
        self.page.add(self.build())
        self.page.update()

    def build(self):
        self.page.bgcolor = FONDO
        mapa = {
            "inicio":       self._p_inicio,
            "registro":     self._p_registro,
            "buscar":       self._p_buscar,
            "qr":           self._p_qr,
            "perfil":       self._p_perfil,
            "cambiar_pass": self._p_cambiar_pass,
        }
        return mapa.get(self._pantalla, self._p_inicio)()

    # ══════════════════════════════════════════════════════════════════════════
    # P1 ─ Inicio
    # ══════════════════════════════════════════════════════════════════════════
    def _p_inicio(self):
        self._cancel_timer()
        return ft.Container(expand=True, bgcolor=FONDO,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[ft.Container(
                    width=380, bgcolor=ft.Colors.WHITE,
                    border_radius=20, padding=40,
                    shadow=ft.BoxShadow(spread_radius=1, blur_radius=24,
                        color=ft.Colors.with_opacity(0.12, "#000")),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=16,
                        controls=[
                            ft.Container(width=72, height=72, border_radius=36,
                                bgcolor=AZUL_MARINO,
                                alignment=ft.alignment.Alignment(0, 0),
                                content=ft.Icon(ft.Icons.QR_CODE_2,
                                    color=ft.Colors.WHITE, size=40)),
                            ft.Text(ESCUELA_NOMBRE, size=17,
                                    weight=ft.FontWeight.BOLD, color=AZUL_MARINO,
                                    text_align=ft.TextAlign.CENTER),
                            ft.Text("Portal del Alumno", size=13,
                                    color=ft.Colors.GREY_500,
                                    text_align=ft.TextAlign.CENTER),
                            ft.Divider(height=8),
                            ft.ElevatedButton("Crear mi cuenta",
                                icon=ft.Icons.PERSON_ADD_ALT_1,
                                width=300, height=50,
                                style=ft.ButtonStyle(bgcolor=AZUL_MARINO,
                                    color=ft.Colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(radius=12)),
                                on_click=lambda e: self._ir("registro")),
                            ft.OutlinedButton("Ya tengo cuenta — Iniciar sesión",
                                icon=ft.Icons.QR_CODE_SCANNER,
                                width=300, height=50,
                                style=ft.ButtonStyle(color=AZUL_MARINO,
                                    side=ft.BorderSide(1.5, AZUL_MARINO),
                                    shape=ft.RoundedRectangleBorder(radius=12)),
                                on_click=lambda e: self._ir("buscar")),
                        ],
                    ),
                )],
            ),
        )

    # ══════════════════════════════════════════════════════════════════════════
    # P2 ─ Registro (crea cuenta + genera QR automáticamente)
    # ══════════════════════════════════════════════════════════════════════════
    def _p_registro(self):
        nombre  = ft.TextField(label="Nombre completo *", width=300,
                               border_color=AZUL_MARINO, focused_border_color=DORADO)
        email   = ft.TextField(label="Correo electrónico *", width=300,
                               border_color=AZUL_MARINO, focused_border_color=DORADO,
                               keyboard_type=ft.KeyboardType.EMAIL)
        pwd     = ft.TextField(label="Contraseña * (mín. 6 caracteres)",
                               password=True, can_reveal_password=True, width=300,
                               border_color=AZUL_MARINO, focused_border_color=DORADO)
        grado   = ft.Dropdown(label="Grado *", width=143, border_color=AZUL_MARINO,
                              options=[ft.dropdown.Option(str(g), f"{g}°") for g in range(1,13)])
        grupo   = ft.Dropdown(label="Grupo *", width=143, border_color=AZUL_MARINO,
                              options=[ft.dropdown.Option(g) for g in ["A","B","C","D","E","F","G","H"]])
        cod_esc = ft.TextField(label="Código de escuela *", width=300,
                               border_color=AZUL_MARINO, focused_border_color=DORADO,
                               hint_text="Pídelo a tu administrador")
        error   = ft.Text("", color=ROJO, size=13, text_align=ft.TextAlign.CENTER)
        btn     = ft.ElevatedButton("Registrarme y ver mi QR",
                    width=300, height=50,
                    style=ft.ButtonStyle(bgcolor=AZUL_MARINO, color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=12)))
        progress = ft.ProgressRing(visible=False, color=AZUL_MARINO, width=28, height=28)

        def registrar(e):
            error.value = ""
            n   = nombre.value.strip()
            em  = email.value.strip()
            pw  = pwd.value
            g   = grado.value
            gr  = grupo.value
            esc = cod_esc.value.strip()
            if not n or not em or not pw or not g or not gr or not esc:
                error.value = "Completa todos los campos (*)"
                self.page.update()
                return
            if len(pw) < 6:
                error.value = "La contraseña debe tener al menos 6 caracteres"
                self.page.update()
                return
            btn.visible      = False
            progress.visible = True
            self.page.update()
            try:
                from app.services.auth_service import register_student
                from app.core.state import set_app_state
                token, user = register_student(
                    name=n, email=em, password=pw,
                    grade=g, group=gr, school_code=esc,
                )
                set_app_state(self.page, {
                    "_id":      user["_id"],
                    "schoolId": user["schoolId"],
                    "role":     "student",
                    "name":     user["name"],
                    "token":    token,
                    "email":    em,
                })
                # Cargar perfil completo con qrToken
                import hashlib
                token_hash = hashlib.sha256(token.encode()).hexdigest()
                alumno = convex_query("students:getMyProfileBySession",
                                      {"tokenHash": token_hash})
                alumno["_es_nuevo"] = True
                self._alumno = alumno
                self._qr_b64 = _hacer_qr_b64(alumno["qrToken"])
                self._ir("qr")
            except Exception as ex:
                error.value      = str(ex)
                btn.visible      = True
                progress.visible = False
                self.page.update()

        btn.on_click = registrar

        return ft.Container(expand=True, bgcolor=FONDO,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True,
                controls=[ft.Container(
                    width=380, bgcolor=ft.Colors.WHITE, border_radius=20, padding=30,
                    shadow=ft.BoxShadow(spread_radius=1, blur_radius=24,
                        color=ft.Colors.with_opacity(0.12, "#000")),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12, scroll=ft.ScrollMode.AUTO,
                        controls=[
                            ft.Row(controls=[
                                ft.IconButton(icon=ft.Icons.ARROW_BACK,
                                    icon_color=AZUL_MARINO,
                                    on_click=lambda e: self._ir("inicio")),
                                ft.Text("Crear mi cuenta", size=16,
                                    weight=ft.FontWeight.BOLD, color=AZUL_MARINO),
                            ], width=300),
                            ft.Text(
                                "¡Llena tus datos y tu QR se genera\n"
                                "automáticamente! El admin te verá al instante.",
                                size=12, color=ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER),
                            ft.Divider(height=4),
                            nombre, email, pwd,
                            ft.Row(controls=[grado, grupo], width=300, spacing=14),
                            cod_esc,
                            error, progress, btn,
                            ft.TextButton("¿Ya tienes cuenta? Iniciar sesión",
                                style=ft.ButtonStyle(color=DORADO),
                                on_click=lambda e: self._ir("buscar")),
                        ],
                    ),
                )],
            ),
        )

    # ══════════════════════════════════════════════════════════════════════════
    # P3 ─ Buscar / Iniciar sesión alumno
    # ══════════════════════════════════════════════════════════════════════════
    def _p_buscar(self):
        campo_email = ft.TextField(label="Tu correo *", width=300,
            border_color=AZUL_MARINO, focused_border_color=DORADO,
            keyboard_type=ft.KeyboardType.EMAIL)
        campo_pwd   = ft.TextField(label="Tu contraseña *", password=True,
            can_reveal_password=True, width=300,
            border_color=AZUL_MARINO, focused_border_color=DORADO)
        error    = ft.Text("", color=ROJO, size=13, text_align=ft.TextAlign.CENTER)
        btn      = ft.ElevatedButton("Iniciar sesión", width=300, height=50,
                     style=ft.ButtonStyle(bgcolor=AZUL_MARINO, color=ft.Colors.WHITE,
                         shape=ft.RoundedRectangleBorder(radius=12)))
        progress = ft.ProgressRing(visible=False, color=AZUL_MARINO, width=28, height=28)

        def buscar(e):
            error.value = ""
            em  = campo_email.value.strip()
            pw  = campo_pwd.value
            if not em or not pw:
                error.value = "Ingresa tu correo y contraseña"
                self.page.update()
                return
            btn.visible      = False
            progress.visible = True
            self.page.update()
            try:
                from app.services.auth_service import login
                from app.core.state import set_app_state
                import hashlib
                token, user = login(em, pw)
                if user.get("role") != "student":
                    raise Exception(
                        "Esta pantalla es solo para alumnos.\n"
                        "Los maestros y admins usan el sistema de escritorio.")
                set_app_state(self.page, {
                    "_id":      user["_id"],
                    "schoolId": user["schoolId"],
                    "role":     "student",
                    "name":     user["name"],
                    "token":    token,
                    "email":    em,
                })
                token_hash = hashlib.sha256(token.encode()).hexdigest()
                alumno = convex_query("students:getMyProfileBySession",
                                      {"tokenHash": token_hash})
                self._alumno = alumno
                self._qr_b64 = _hacer_qr_b64(alumno["qrToken"])
                self._ir("qr")
            except Exception as ex:
                error.value      = str(ex)
                btn.visible      = True
                progress.visible = False
                self.page.update()

        btn.on_click        = buscar
        campo_email.on_submit = buscar
        campo_pwd.on_submit   = buscar

        return ft.Container(expand=True, bgcolor=FONDO,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True,
                controls=[ft.Container(
                    width=380, bgcolor=ft.Colors.WHITE, border_radius=20, padding=36,
                    shadow=ft.BoxShadow(spread_radius=1, blur_radius=24,
                        color=ft.Colors.with_opacity(0.12, "#000")),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=14,
                        controls=[
                            ft.Row(controls=[
                                ft.IconButton(icon=ft.Icons.ARROW_BACK,
                                    icon_color=AZUL_MARINO,
                                    on_click=lambda e: self._ir("inicio")),
                                ft.Text("Iniciar sesión", size=16,
                                    weight=ft.FontWeight.BOLD, color=AZUL_MARINO),
                            ], width=300),
                            ft.Icon(ft.Icons.QR_CODE_SCANNER, color=AZUL_MARINO, size=48),
                            campo_email, campo_pwd,
                            error, progress, btn,
                            ft.TextButton("¿No tienes cuenta? Crear una",
                                style=ft.ButtonStyle(color=DORADO),
                                on_click=lambda e: self._ir("registro")),
                        ],
                    ),
                )],
            ),
        )

    # ══════════════════════════════════════════════════════════════════════════
    # P4 ─ Mostrar QR + botones de acción
    # ══════════════════════════════════════════════════════════════════════════
    def _p_qr(self):
        self._reset_timer()
        a        = self._alumno or {}
        es_nuevo = a.get("_es_nuevo", False)

        # Foto de perfil
        if a.get("photoUrl"):
            foto = ft.Image(src=a["photoUrl"], width=72, height=72,
                            fit=ft.ImageFit.COVER, border_radius=36)
        elif self._foto_path:
            foto = ft.Image(src=self._foto_path, width=72, height=72,
                            fit=ft.ImageFit.COVER, border_radius=36)
        else:
            foto = ft.Container(width=72, height=72, border_radius=36,
                bgcolor=ft.Colors.BLUE_GREY_100,
                alignment=ft.alignment.Alignment(0, 0),
                content=ft.Icon(ft.Icons.PERSON, color=AZUL_MARINO, size=40))

        banner_nuevo = ft.Container(visible=es_nuevo,
            bgcolor=ft.Colors.GREEN_100, border_radius=8,
            padding=ft.Padding(10, 8, 10, 8),
            content=ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=6,
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_700, size=18),
                    ft.Text("¡Cuenta creada! Ya apareces en el sistema.",
                            color=ft.Colors.GREEN_800, size=12,
                            weight=ft.FontWeight.W_500),
                ]),
        )

        return ft.Container(expand=True, bgcolor=FONDO,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True, scroll=ft.ScrollMode.AUTO,
                controls=[
                    # ── Encabezado azul ──
                    ft.Container(
                        bgcolor=AZUL_MARINO,
                        padding=ft.Padding(20, 44, 20, 24),
                        width=float("inf"),
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6,
                            controls=[
                                ft.Row(controls=[
                                    ft.Container(expand=True),
                                    ft.IconButton(icon=ft.Icons.MANAGE_ACCOUNTS,
                                        icon_color=ft.Colors.WHITE,
                                        tooltip="Mi perfil",
                                        on_click=lambda e: self._ir("perfil")),
                                ], width=float("inf")),
                                foto,
                                ft.Text(a.get("name",""), size=20,
                                        weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                ft.Text(
                                    f"Grado {a.get('grade','')}° — Grupo {a.get('group','')}",
                                    size=13, color=ft.Colors.WHITE70),
                                ft.Text(f"Código: {a.get('studentCode','')}",
                                        size=12, color=ft.Colors.WHITE60),
                            ],
                        ),
                    ),
                    # ── Card QR ──
                    ft.Container(
                        margin=ft.Margin(20, -24, 20, 20),
                        bgcolor=ft.Colors.WHITE, border_radius=20, padding=24,
                        shadow=ft.BoxShadow(spread_radius=1, blur_radius=20,
                            color=ft.Colors.with_opacity(0.12, "#000")),
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12,
                            controls=[
                                banner_nuevo,
                                ft.Text("Tu código QR de asistencia", size=14,
                                        color=ft.Colors.GREY_600,
                                        weight=ft.FontWeight.W_500),
                                ft.Image(src_base64=self._qr_b64,
                                         width=220, height=220,
                                         fit=ft.ImageFit.CONTAIN),
                                ft.Text("Muestra este QR al prefecto al entrar",
                                        size=12, color=DORADO, italic=True,
                                        text_align=ft.TextAlign.CENTER),
                                ft.Text("⏱ Sesión se cierra tras 5 min de inactividad",
                                        size=11, color=ft.Colors.GREY_400, italic=True,
                                        text_align=ft.TextAlign.CENTER),
                                ft.Divider(),
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER, spacing=12,
                                    controls=[
                                        ft.OutlinedButton("Mi perfil",
                                            icon=ft.Icons.PERSON,
                                            style=ft.ButtonStyle(color=AZUL_MARINO,
                                                side=ft.BorderSide(1.5, AZUL_MARINO)),
                                            on_click=lambda e: self._ir("perfil")),
                                        ft.OutlinedButton("Cerrar sesión",
                                            icon=ft.Icons.LOGOUT,
                                            style=ft.ButtonStyle(color=ft.Colors.GREY_600,
                                                side=ft.BorderSide(1, ft.Colors.GREY_400)),
                                            on_click=lambda e: self._cerrar_sesion()),
                                    ],
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )

    def _cerrar_sesion(self):
        self._cancel_timer()
        self._alumno    = None
        self._qr_b64    = None
        self._foto_path = None
        clear_app_state()
        self._ir("inicio")

    # ══════════════════════════════════════════════════════════════════════════
    # P5 ─ Mi Perfil (foto de galería o cámara + botón cambiar contraseña)
    # ══════════════════════════════════════════════════════════════════════════
    def _p_perfil(self):
        self._reset_timer()
        a = self._alumno or {}

        if a.get("photoUrl"):
            foto_w = ft.Image(src=a["photoUrl"], width=90, height=90,
                              fit=ft.ImageFit.COVER, border_radius=45)
        elif self._foto_path:
            foto_w = ft.Image(src=self._foto_path, width=90, height=90,
                              fit=ft.ImageFit.COVER, border_radius=45)
        else:
            foto_w = ft.Container(width=90, height=90, border_radius=45,
                bgcolor=ft.Colors.BLUE_GREY_100,
                alignment=ft.alignment.Alignment(0, 0),
                content=ft.Icon(ft.Icons.PERSON, color=AZUL_MARINO, size=50))

        status_foto = ft.Text("", size=12, color=ft.Colors.GREEN_700,
                              text_align=ft.TextAlign.CENTER)

        def desde_galeria(e):
            self._reset_timer()
            threading.Thread(
                target=self._abrir_galeria, args=(foto_w, status_foto), daemon=True
            ).start()

        def desde_camara(e):
            self._reset_timer()
            threading.Thread(
                target=self._tomar_foto, args=(foto_w, status_foto), daemon=True
            ).start()

        return ft.Container(expand=True, bgcolor=FONDO,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True, scroll=ft.ScrollMode.AUTO,
                controls=[ft.Container(
                    width=380, bgcolor=ft.Colors.WHITE, border_radius=20, padding=30,
                    shadow=ft.BoxShadow(spread_radius=1, blur_radius=24,
                        color=ft.Colors.with_opacity(0.12, "#000")),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=14,
                        controls=[
                            ft.Row(controls=[
                                ft.IconButton(icon=ft.Icons.ARROW_BACK,
                                    icon_color=AZUL_MARINO,
                                    on_click=lambda e: self._ir("qr")),
                                ft.Text("Mi perfil", size=16,
                                    weight=ft.FontWeight.BOLD, color=AZUL_MARINO),
                            ], width=320),
                            foto_w,
                            ft.Text(a.get("name",""), size=17,
                                    weight=ft.FontWeight.BOLD, color=AZUL_MARINO),
                            ft.Text(
                                f"Grado {a.get('grade','')}° — Grupo {a.get('group','')}",
                                size=13, color=ft.Colors.GREY_600),
                            ft.Text(f"Correo: {a.get('email','')}",
                                    size=12, color=ft.Colors.GREY_500),
                            ft.Divider(),
                            # ── Foto ──
                            ft.Text("Foto de perfil", size=14,
                                    weight=ft.FontWeight.W_500, color=AZUL_MARINO),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER, spacing=10,
                                controls=[
                                    ft.ElevatedButton("Galería",
                                        icon=ft.Icons.PHOTO_LIBRARY,
                                        style=ft.ButtonStyle(bgcolor=AZUL_MARINO,
                                            color=ft.Colors.WHITE),
                                        on_click=desde_galeria),
                                    ft.ElevatedButton("Cámara",
                                        icon=ft.Icons.CAMERA_ALT,
                                        style=ft.ButtonStyle(bgcolor=AZUL_MARINO,
                                            color=ft.Colors.WHITE),
                                        on_click=desde_camara),
                                ],
                            ),
                            status_foto,
                            ft.Divider(),
                            # ── Seguridad ──
                            ft.Text("Seguridad", size=14,
                                    weight=ft.FontWeight.W_500, color=AZUL_MARINO),
                            ft.ElevatedButton("Cambiar contraseña",
                                icon=ft.Icons.LOCK_RESET, width=280,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.ORANGE_800,
                                    color=ft.Colors.WHITE),
                                on_click=lambda e: self._ir("cambiar_pass")),
                            ft.Divider(),
                            ft.OutlinedButton("Cerrar sesión",
                                icon=ft.Icons.LOGOUT, width=280,
                                style=ft.ButtonStyle(color=ft.Colors.GREY_600,
                                    side=ft.BorderSide(1, ft.Colors.GREY_400)),
                                on_click=lambda e: self._cerrar_sesion()),
                        ],
                    ),
                )],
            ),
        )

    def _abrir_galeria(self, foto_w, status):
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            ruta = filedialog.askopenfilename(
                title="Seleccionar foto",
                filetypes=[("Imágenes", "*.jpg *.jpeg *.png")],
            )
            root.destroy()
            if ruta:
                self._foto_path        = ruta
                foto_w.src             = ruta
                foto_w.border_radius   = 45
                status.value           = "✅ Foto actualizada"
                self._subir_foto(ruta, status)
        except Exception as ex:
            status.value = f"Error: {ex}"
        self.page.update()

    def _tomar_foto(self, foto_w, status):
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                status.value = "❌ No se pudo acceder a la cámara"
                self.page.update()
                return
            for _ in range(5):
                cap.read()
            ret, frame = cap.read()
            cap.release()
            if ret:
                os.makedirs("assets/fotos", exist_ok=True)
                ruta = os.path.abspath("assets/fotos/alumno_temp.jpg")
                cv2.imwrite(ruta, frame)
                self._foto_path      = ruta
                foto_w.src           = ruta
                foto_w.border_radius = 45
                status.value         = "✅ Foto tomada"
                self._subir_foto(ruta, status)
            else:
                status.value = "❌ No se pudo capturar la foto"
        except Exception as ex:
            status.value = f"Error: {ex}"
        self.page.update()

    def _subir_foto(self, ruta: str, status):
        """Sube la foto a Convex Storage y actualiza el perfil del alumno."""
        try:
            import requests as req_lib
            import hashlib
            state = get_app_state(self.page)
            if not state:
                return
            token_hash = hashlib.sha256(state.token.encode()).hexdigest()
            upload_url = convex_mutation("students:generateUploadUrl",
                                        {"tokenHash": token_hash})
            ext  = os.path.splitext(ruta)[1].lower()
            mime = "image/jpeg" if ext in [".jpg",".jpeg"] else "image/png"
            with open(ruta, "rb") as f:
                data = f.read()
            res = req_lib.post(upload_url,
                               headers={"Content-Type": mime},
                               data=data, timeout=30)
            storage_id = res.json().get("storageId")
            if storage_id:
                updated = convex_mutation("students:updateMyPhoto", {
                    "tokenHash": token_hash,
                    "storageId": storage_id,
                })
                if updated and updated.get("photoUrl"):
                    self._alumno["photoUrl"] = updated["photoUrl"]
        except Exception as ex:
            status.value = f"Guardado local (error al subir: {ex})"
            self.page.update()

    # ══════════════════════════════════════════════════════════════════════════
    # P6 ─ Cambiar contraseña (token por email, sin poner contraseña anterior)
    # ══════════════════════════════════════════════════════════════════════════
    def _p_cambiar_pass(self):
        self._reset_timer()
        a     = self._alumno or {}
        state = get_app_state(self.page)
        email = a.get("email") or (state.email if state else "") or ""

        status   = ft.Text("", size=13, text_align=ft.TextAlign.CENTER)
        progress = ft.ProgressRing(visible=False, color=AZUL_MARINO, width=28, height=28)

        token_f = ft.TextField(
            label="Código recibido en tu correo", width=300,
            border_color=AZUL_MARINO, focused_border_color=DORADO,
            keyboard_type=ft.KeyboardType.NUMBER, visible=False)
        nueva_f = ft.TextField(
            label="Nueva contraseña (mín. 6 caracteres)",
            password=True, can_reveal_password=True, width=300,
            border_color=AZUL_MARINO, focused_border_color=DORADO, visible=False)
        btn_cambiar = ft.ElevatedButton(
            "Actualizar contraseña", width=300, height=48,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10)),
            visible=False)

        def enviar_token(e):
            self._reset_timer()
            status.value = ""
            if not email:
                status.color = ROJO
                status.value = "No se encontró tu correo registrado"
                self.page.update()
                return
            btn_env.visible  = False
            progress.visible = True
            self.page.update()
            try:
                from app.services.email_service import send_reset_token
                send_reset_token(email)
                status.color         = ft.Colors.GREEN_700
                status.value         = f"✅ Código enviado a {email}"
                token_f.visible      = True
                nueva_f.visible      = True
                btn_cambiar.visible  = True
            except Exception as ex:
                status.color    = ROJO
                status.value    = str(ex)
                btn_env.visible = True
            finally:
                progress.visible = False
                self.page.update()

        def confirmar(e):
            self._reset_timer()
            status.value = ""
            tok   = token_f.value.strip()
            npass = nueva_f.value
            if not tok or not npass:
                status.color = ROJO
                status.value = "Ingresa el código y la nueva contraseña"
                self.page.update()
                return
            if len(npass) < 6:
                status.color = ROJO
                status.value = "La contraseña debe tener al menos 6 caracteres"
                self.page.update()
                return
            btn_cambiar.visible = False
            progress.visible    = True
            self.page.update()
            try:
                from app.services.email_service import verify_reset_token_and_change
                verify_reset_token_and_change(email, tok, npass)
                status.color = ft.Colors.GREEN_700
                status.value = "✅ ¡Contraseña actualizada!"
                progress.visible = False
                self.page.update()
                time.sleep(2)
                self._ir("qr")
            except Exception as ex:
                status.color        = ROJO
                status.value        = str(ex)
                btn_cambiar.visible = True
                progress.visible    = False
                self.page.update()

        btn_env = ft.ElevatedButton(
            "Enviar código a mi correo", width=300, height=48,
            style=ft.ButtonStyle(bgcolor=AZUL_MARINO, color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10)),
            on_click=enviar_token)
        btn_cambiar.on_click = confirmar

        return ft.Container(expand=True, bgcolor=FONDO,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[ft.Container(
                    width=380, bgcolor=ft.Colors.WHITE, border_radius=20, padding=30,
                    shadow=ft.BoxShadow(spread_radius=1, blur_radius=24,
                        color=ft.Colors.with_opacity(0.12, "#000")),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=14,
                        controls=[
                            ft.Row(controls=[
                                ft.IconButton(icon=ft.Icons.ARROW_BACK,
                                    icon_color=AZUL_MARINO,
                                    on_click=lambda e: self._ir("perfil")),
                                ft.Text("Cambiar contraseña", size=16,
                                    weight=ft.FontWeight.BOLD, color=AZUL_MARINO),
                            ], width=300),
                            ft.Icon(ft.Icons.LOCK_RESET, color=AZUL_MARINO, size=50),
                            ft.Text(
                                f"Enviaremos un código de verificación a:\n{email}",
                                size=12, color=ft.Colors.GREY_600,
                                text_align=ft.TextAlign.CENTER),
                            ft.Text(
                                "Con ese código podrás crear tu nueva contraseña\n"
                                "sin necesidad de recordar la anterior.",
                                size=12, color=ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER),
                            ft.Divider(height=4),
                            btn_env,
                            progress,
                            status,
                            token_f,
                            nueva_f,
                            btn_cambiar,
                        ],
                    ),
                )],
            ),
        )
