import flet as ft
import qrcode
import io
import base64
import os
import hashlib
import threading
import traceback

from app.services.convex_service import convex_query, convex_mutation
from app.core.config import AZUL_MARINO, DORADO, ROJO, FONDO, ESCUELA_NOMBRE


def _hacer_qr_b64(token: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(token)
    qr.make(fit=True)
    img = qr.make_image(fill_color=AZUL_MARINO, back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


class MyQRView:
    def __init__(self, page: ft.Page, state=None):
        self.page = page
        self.state = state
        self._alumno = None
        self._qr_b64 = None
        self._foto_path = None
        self._pantalla = "inicio"

        if self.state and hasattr(self.state, "token") and self.state.token:
            try:
                email = self.state.email
                if email:
                    alumno = convex_query("users:getStudentByEmail", {"email": email})
                    if alumno:
                        qr = convex_query("students:getQrByStudentId", {"studentId": alumno["_id"]})
                        alumno["qrToken"] = qr if qr else ""
                        self._alumno = alumno
                        if alumno.get("qrToken"):
                            self._qr_b64 = _hacer_qr_b64(alumno["qrToken"])
                        self._pantalla = "qr"
            except Exception:
                traceback.print_exc()
                self._pantalla = "inicio"

    def _ir(self, pantalla: str):
        self._pantalla = pantalla
        self.page.controls.clear()
        self.page.add(self.build())
        self.page.update()

    def build(self):
        self.page.bgcolor = FONDO
        mapa = {
            "inicio": self._p_inicio,
            "registro": self._p_registro,
            "buscar": self._p_buscar,
            "qr": self._p_qr,
            "perfil": self._p_perfil,
        }
        return mapa.get(self._pantalla, self._p_inicio)()

    def _p_inicio(self):
        return ft.Container(
            expand=True,
            bgcolor=FONDO,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[
                    ft.Container(
                        width=380,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=20,
                        padding=40,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=24,
                            color=ft.Colors.with_opacity(0.12, "#000"),
                        ),
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=16,
                            controls=[
                                ft.Container(
                                    width=72,
                                    height=72,
                                    border_radius=36,
                                    bgcolor=AZUL_MARINO,
                                    alignment=ft.alignment.Alignment(0, 0),
                                    content=ft.Icon(
                                        ft.Icons.QR_CODE_2,
                                        color=ft.Colors.WHITE,
                                        size=40,
                                    ),
                                ),
                                ft.Text(
                                    ESCUELA_NOMBRE,
                                    size=17,
                                    weight=ft.FontWeight.BOLD,
                                    color=AZUL_MARINO,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Text(
                                    "Portal del Alumno",
                                    size=13,
                                    color=ft.Colors.GREY_500,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Divider(height=8),
                                ft.ElevatedButton(
                                    "Crear mi cuenta",
                                    icon=ft.Icons.PERSON_ADD_ALT_1,
                                    width=300,
                                    height=50,
                                    style=ft.ButtonStyle(
                                        bgcolor=AZUL_MARINO,
                                        color=ft.Colors.WHITE,
                                        shape=ft.RoundedRectangleBorder(radius=12),
                                    ),
                                    on_click=lambda e: self._ir("registro"),
                                ),
                                ft.OutlinedButton(
                                    "Ya tengo cuenta - Iniciar sesión",
                                    icon=ft.Icons.QR_CODE_SCANNER,
                                    width=300,
                                    height=50,
                                    style=ft.ButtonStyle(
                                        color=AZUL_MARINO,
                                        side=ft.BorderSide(1.5, AZUL_MARINO),
                                        shape=ft.RoundedRectangleBorder(radius=12),
                                    ),
                                    on_click=lambda e: self._ir("buscar"),
                                ),
                            ],
                        ),
                    )
                ],
            ),
        )

    def _p_registro(self):
        nombre = ft.TextField(label="Nombre completo *", width=300, border_color=AZUL_MARINO, focused_border_color=DORADO)
        email = ft.TextField(label="Correo electrónico *", width=300, border_color=AZUL_MARINO, focused_border_color=DORADO, keyboard_type=ft.KeyboardType.EMAIL)
        pwd = ft.TextField(label="Contraseña * (min. 6 caracteres)", password=True, can_reveal_password=True, width=300, border_color=AZUL_MARINO, focused_border_color=DORADO)
        grado = ft.Dropdown(label="Grado *", width=145, border_color=AZUL_MARINO, options=[ft.dropdown.Option(str(g), f"{g} grado") for g in range(1, 13)])
        grupo = ft.Dropdown(label="Grupo *", width=145, border_color=AZUL_MARINO, options=[ft.dropdown.Option(g) for g in ["A", "B", "C", "D", "E", "F", "G", "H"]])
        error = ft.Text("", color=ROJO, size=13, text_align=ft.TextAlign.CENTER)
        btn = ft.ElevatedButton("Registrarme y ver mi QR", width=300, height=50, style=ft.ButtonStyle(bgcolor=AZUL_MARINO, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=12)))
        progress = ft.ProgressRing(visible=False, color=AZUL_MARINO, width=28, height=28)

        def registrar(e):
            error.value = ""
            n = nombre.value.strip()
            em = email.value.strip()
            pw = pwd.value
            g = grado.value
            gr = grupo.value

            if not n or not em or not pw or not g or not gr:
                error.value = "Completa todos los campos (*)"
                self.page.update()
                return

            if len(pw) < 6:
                error.value = "La contraseña debe tener al menos 6 caracteres"
                self.page.update()
                return

            btn.visible = False
            progress.visible = True
            self.page.update()

            try:
                from app.services.auth_service import register_student
                token, user = register_student(name=n, email=em, password=pw, grade=g, group=gr)
                alumno = convex_query("users:getStudentByEmail", {"email": em})
                if not alumno:
                    raise Exception("No se encontró el alumno recién registrado.")

                qr = convex_query("students:getQrByStudentId", {"studentId": alumno["_id"]})
                alumno["qrToken"] = qr if qr else ""
                alumno["_es_nuevo"] = True
                self._alumno = alumno

                if alumno.get("qrToken"):
                    self._qr_b64 = _hacer_qr_b64(alumno["qrToken"])

                self._ir("qr")
            except Exception as ex:
                error.value = str(ex)
                btn.visible = True
                progress.visible = False
                self.page.update()

        btn.on_click = registrar

        return ft.Container(
            expand=True,
            bgcolor=FONDO,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[
                    ft.Container(
                        width=380,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=20,
                        padding=30,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=24,
                            color=ft.Colors.with_opacity(0.12, "#000"),
                        ),
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=12,
                            scroll=ft.ScrollMode.AUTO,
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.IconButton(
                                            icon=ft.Icons.ARROW_BACK,
                                            icon_color=AZUL_MARINO,
                                            on_click=lambda e: self._ir("inicio"),
                                        ),
                                        ft.Text(
                                            "Registro de Alumno",
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color=AZUL_MARINO,
                                        ),
                                    ],
                                    width=300,
                                ),
                                ft.Text(
                                    "Llena tus datos. Tu QR se genera automáticamente.",
                                    size=12,
                                    color=ft.Colors.GREY_500,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Divider(height=4),
                                nombre,
                                email,
                                pwd,
                                ft.Row(controls=[grado, grupo], width=300, spacing=10),
                                error,
                                progress,
                                btn,
                                ft.TextButton(
                                    "¿Ya tengo cuenta? Iniciar sesión",
                                    style=ft.ButtonStyle(color=DORADO),
                                    on_click=lambda e: self._ir("buscar"),
                                ),
                            ],
                        ),
                    )
                ],
            ),
        )

    def _p_buscar(self):
        campo_email = ft.TextField(label="Tu correo electrónico *", width=300, border_color=AZUL_MARINO, focused_border_color=DORADO, keyboard_type=ft.KeyboardType.EMAIL)
        campo_pwd = ft.TextField(label="Tu contraseña *", password=True, can_reveal_password=True, width=300, border_color=AZUL_MARINO, focused_border_color=DORADO)
        error = ft.Text("", color=ROJO, size=13, text_align=ft.TextAlign.CENTER)
        btn = ft.ElevatedButton("Iniciar sesión y ver mi QR", width=300, height=50, style=ft.ButtonStyle(bgcolor=AZUL_MARINO, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=12)))
        progress = ft.ProgressRing(visible=False, color=AZUL_MARINO, width=28, height=28)

        def iniciar(e):
            error.value = ""
            em = campo_email.value.strip()
            pw = campo_pwd.value

            if not em or not pw:
                error.value = "Ingresa tu correo y contraseña"
                self.page.update()
                return

            btn.visible = False
            progress.visible = True
            self.page.update()

            try:
                from app.services.auth_service import login
                token, user = login(em, pw)
                if user.get("role") != "student":
                    raise Exception("Esta pantalla es solo para alumnos.")

                alumno = convex_query("users:getStudentByEmail", {"email": em})
                if not alumno:
                    raise Exception("No se encontró el alumno.")

                qr = convex_query("students:getQrByStudentId", {"studentId": alumno["_id"]})
                alumno["qrToken"] = qr if qr else ""
                self._alumno = alumno

                if alumno.get("qrToken"):
                    self._qr_b64 = _hacer_qr_b64(alumno["qrToken"])

                self._ir("qr")
            except Exception as ex:
                error.value = str(ex)
                btn.visible = True
                progress.visible = False
                self.page.update()

        btn.on_click = iniciar
        campo_email.on_submit = iniciar
        campo_pwd.on_submit = iniciar

        return ft.Container(
            expand=True,
            bgcolor=FONDO,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[
                    ft.Container(
                        width=380,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=20,
                        padding=36,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=24,
                            color=ft.Colors.with_opacity(0.12, "#000"),
                        ),
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=14,
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.IconButton(
                                            icon=ft.Icons.ARROW_BACK,
                                            icon_color=AZUL_MARINO,
                                            on_click=lambda e: self._ir("inicio"),
                                        ),
                                        ft.Text(
                                            "Iniciar sesión",
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color=AZUL_MARINO,
                                        ),
                                    ],
                                    width=300,
                                ),
                                ft.Icon(ft.Icons.QR_CODE_SCANNER, color=AZUL_MARINO, size=48),
                                campo_email,
                                campo_pwd,
                                error,
                                progress,
                                btn,
                                ft.TextButton(
                                    "No tienes cuenta? Crear una",
                                    style=ft.ButtonStyle(color=DORADO),
                                    on_click=lambda e: self._ir("registro"),
                                ),
                            ],
                        ),
                    )
                ],
            ),
        )

    def _p_qr(self):
        a = self._alumno or {}
        es_nuevo = a.get("_es_nuevo", False)

        if a.get("photoUrl"):
            foto_w = ft.Image(src=a["photoUrl"], width=72, height=72, fit=ft.ImageFit.COVER, border_radius=36)
        elif self._foto_path:
            foto_w = ft.Image(src=self._foto_path, width=72, height=72, fit=ft.ImageFit.COVER, border_radius=36)
        else:
            foto_w = ft.Container(
                width=72,
                height=72,
                border_radius=36,
                bgcolor=ft.Colors.BLUE_GREY_100,
                alignment=ft.alignment.Alignment(0, 0),
                content=ft.Icon(ft.Icons.PERSON, color=AZUL_MARINO, size=40),
            )

        qr_control = ft.Text("Sin QR", color=ROJO)
        if self._qr_b64:
            qr_control = ft.Image(
                src_base64=self._qr_b64,
                width=220,
                height=220,
                fit=ft.ImageFit.CONTAIN,
                error_content=ft.Text("No se pudo cargar el QR", color=ROJO),
            )

        return ft.Container(
            expand=True,
            bgcolor=FONDO,
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Container(
                        bgcolor=AZUL_MARINO,
                        padding=ft.padding.only(left=20, right=20, top=30, bottom=24),
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=6,
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.END,
                                    controls=[
                                        ft.IconButton(
                                            icon=ft.Icons.MANAGE_ACCOUNTS,
                                            icon_color=ft.Colors.WHITE,
                                            on_click=lambda e: self._ir("perfil"),
                                        ),
                                    ],
                                ),
                                foto_w,
                                ft.Text(
                                    a.get("name", ""),
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Text(
                                    f"Grado {a.get('grade', '')}  Grupo {a.get('group', '')}",
                                    size=13,
                                    color=ft.Colors.WHITE70,
                                ),
                                ft.Text(
                                    f"Código: {a.get('studentCode', '')}",
                                    size=12,
                                    color=ft.Colors.WHITE60,
                                ),
                            ],
                        ),
                    ),
                    ft.Container(
                        bgcolor=ft.Colors.WHITE,
                        border_radius=20,
                        padding=24,
                        margin=ft.margin.only(left=20, right=20, top=16, bottom=20),
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=20,
                            color=ft.Colors.with_opacity(0.12, "#000"),
                        ),
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=12,
                            controls=[
                                ft.Container(
                                    visible=es_nuevo,
                                    bgcolor=ft.Colors.GREEN_100,
                                    border_radius=8,
                                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                                    content=ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=6,
                                        controls=[
                                            ft.Icon(
                                                ft.Icons.CHECK_CIRCLE,
                                                color=ft.Colors.GREEN_700,
                                                size=18,
                                            ),
                                            ft.Text(
                                                "Cuenta creada! Ya apareces en el sistema.",
                                                color=ft.Colors.GREEN_800,
                                                size=12,
                                                weight=ft.FontWeight.W_500,
                                            ),
                                        ],
                                    ),
                                ),
                                ft.Text(
                                    "Tu código QR de asistencia",
                                    size=14,
                                    color=ft.Colors.GREY_600,
                                    weight=ft.FontWeight.W_500,
                                ),
                                qr_control,
                                ft.Text(
                                    "Muestra este QR al prefecto al entrar",
                                    size=12,
                                    color=DORADO,
                                    italic=True,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Divider(),
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=12,
                                    controls=[
                                        ft.OutlinedButton(
                                            "Mi perfil",
                                            icon=ft.Icons.PERSON,
                                            style=ft.ButtonStyle(
                                                color=AZUL_MARINO,
                                                side=ft.BorderSide(1.5, AZUL_MARINO),
                                            ),
                                            on_click=lambda e: self._ir("perfil"),
                                        ),
                                        ft.OutlinedButton(
                                            "Cerrar sesión",
                                            icon=ft.Icons.LOGOUT,
                                            style=ft.ButtonStyle(
                                                color=ft.Colors.GREY_600,
                                                side=ft.BorderSide(1, ft.Colors.GREY_400),
                                            ),
                                            on_click=lambda e: self._ir("inicio"),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )

    def _p_perfil(self):
        a = self._alumno or {}
        if a.get("photoUrl"):
            self._foto_w = ft.Image(src=a["photoUrl"], width=90, height=90, fit=ft.ImageFit.COVER, border_radius=45)
        elif self._foto_path:
            self._foto_w = ft.Image(src=self._foto_path, width=90, height=90, fit=ft.ImageFit.COVER, border_radius=45)
        else:
            self._foto_w = ft.Container(
                width=90,
                height=90,
                border_radius=45,
                bgcolor=ft.Colors.BLUE_GREY_100,
                alignment=ft.alignment.Alignment(0, 0),
                content=ft.Icon(ft.Icons.PERSON, color=AZUL_MARINO, size=50),
            )

        self._status_foto = ft.Text("", size=12, color=ft.Colors.GREEN_700, text_align=ft.TextAlign.CENTER)
        self._token_f = ft.TextField(label="Código recibido en tu correo", width=300, border_color=AZUL_MARINO, keyboard_type=ft.KeyboardType.NUMBER, visible=False)
        self._nueva_f = ft.TextField(label="Nueva contraseña (min. 6 caracteres)", password=True, can_reveal_password=True, width=300, border_color=AZUL_MARINO, visible=False)
        self._btn_cambiar = ft.ElevatedButton("Actualizar contraseña", width=300, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE), visible=False, on_click=self._confirmar_pass)
        self._status_pass = ft.Text("", size=12, text_align=ft.TextAlign.CENTER)
        self._progress = ft.ProgressRing(visible=False, color=AZUL_MARINO, width=24, height=24)

        return ft.Container(
            expand=True,
            bgcolor=FONDO,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Container(
                        width=380,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=20,
                        padding=30,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=24,
                            color=ft.Colors.with_opacity(0.12, "#000"),
                        ),
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=14,
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.IconButton(
                                            icon=ft.Icons.ARROW_BACK,
                                            icon_color=AZUL_MARINO,
                                            on_click=lambda e: self._ir("qr"),
                                        ),
                                        ft.Text(
                                            "Mi perfil y ajustes",
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color=AZUL_MARINO,
                                        ),
                                    ],
                                    width=320,
                                ),
                                self._foto_w,
                                ft.Text(a.get("name", ""), size=17, weight=ft.FontWeight.BOLD, color=AZUL_MARINO),
                                ft.Text(f"Grado {a.get('grade', '')}  Grupo {a.get('group', '')}", size=13, color=ft.Colors.GREY_600),
                                ft.Text(a.get("email", ""), size=12, color=ft.Colors.GREY_400),
                                ft.Divider(),
                                ft.Text("Foto de perfil", size=14, weight=ft.FontWeight.W_600, color=AZUL_MARINO),
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=12,
                                    controls=[
                                        ft.ElevatedButton(
                                            "Galería",
                                            icon=ft.Icons.PHOTO_LIBRARY,
                                            height=44,
                                            style=ft.ButtonStyle(bgcolor=AZUL_MARINO, color=ft.Colors.WHITE),
                                            on_click=lambda e: threading.Thread(target=self._galeria, daemon=True).start(),
                                        ),
                                        ft.ElevatedButton(
                                            "Cámara",
                                            icon=ft.Icons.CAMERA_ALT,
                                            height=44,
                                            style=ft.ButtonStyle(bgcolor=AZUL_MARINO, color=ft.Colors.WHITE),
                                            on_click=lambda e: threading.Thread(target=self._camara, daemon=True).start(),
                                        ),
                                    ],
                                ),
                                self._status_foto,
                                ft.Divider(),
                                ft.Text("Seguridad", size=14, weight=ft.FontWeight.W_600, color=AZUL_MARINO),
                                ft.Text(
                                    "Te enviaremos un código a tu correo para que\npuedas poner una nueva contraseña sin recordar la anterior.",
                                    size=12,
                                    color=ft.Colors.GREY_500,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.ElevatedButton(
                                    "Enviar código a mi correo",
                                    icon=ft.Icons.LOCK_RESET,
                                    width=300,
                                    height=44,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_800, color=ft.Colors.WHITE),
                                    on_click=self._enviar_token,
                                ),
                                self._progress,
                                self._status_pass,
                                self._token_f,
                                self._nueva_f,
                                self._btn_cambiar,
                                ft.Divider(),
                                ft.OutlinedButton(
                                    "Cerrar sesión",
                                    icon=ft.Icons.LOGOUT,
                                    width=300,
                                    style=ft.ButtonStyle(
                                        color=ft.Colors.GREY_600,
                                        side=ft.BorderSide(1, ft.Colors.GREY_400),
                                    ),
                                    on_click=lambda e: self._ir("inicio"),
                                ),
                            ],
                        ),
                    )
                ],
            ),
        )

    def _galeria(self):
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            ruta = filedialog.askopenfilename(
                title="Seleccionar foto",
                filetypes=[("Imagenes", "*.jpg *.jpeg *.png")],
            )
            root.destroy()
            if ruta:
                self._aplicar_foto(ruta)
        except Exception as ex:
            self._status_foto.value = "Error: " + str(ex)
            self.page.update()

    def _camara(self):
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self._status_foto.value = "No se pudo acceder a la cámara"
                self.page.update()
                return
            for _ in range(5):
                cap.read()
            ret, frame = cap.read()
            cap.release()
            if ret:
                os.makedirs("assets/fotos", exist_ok=True)
                ruta = os.path.abspath("assets/fotos/alumno_foto.jpg")
                cv2.imwrite(ruta, frame)
                self._aplicar_foto(ruta)
            else:
                self._status_foto.value = "No se pudo capturar la foto"
                self.page.update()
        except Exception as ex:
            self._status_foto.value = "Error: " + str(ex)
            self.page.update()

    def _aplicar_foto(self, ruta):
        self._foto_path = ruta
        self._foto_w.src = ruta
        self._foto_w.border_radius = 45
        self._status_foto.value = "Foto actualizada, subiendo..."
        self.page.update()
        threading.Thread(target=self._subir_foto, args=(ruta,), daemon=True).start()

    def _subir_foto(self, ruta):
        try:
            import requests as req
            from app.core.state import get_app_state
            state = get_app_state(self.page)
            if not state:
                return
            token_hash = hashlib.sha256(state.token.encode()).hexdigest()
            upload_url = convex_mutation("students:generateUploadUrl", {"tokenHash": token_hash})
            ext = os.path.splitext(ruta)[1].lower()
            mime = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"
            with open(ruta, "rb") as f:
                data = f.read()
            res = req.post(upload_url, headers={"Content-Type": mime}, data=data, timeout=30)
            storage_id = res.json().get("storageId")
            if storage_id:
                updated = convex_mutation("students:updateMyPhoto", {"tokenHash": token_hash, "storageId": storage_id})
                if updated and updated.get("photoUrl"):
                    self._alumno["photoUrl"] = updated["photoUrl"]
            self._status_foto.value = "Foto guardada correctamente"
        except Exception as ex:
            self._status_foto.value = "Error al subir: " + str(ex)
        self.page.update()

    def _enviar_token(self, e=None):
        self._status_pass.value = ""
        email = (self._alumno or {}).get("email", "")
        if not email:
            self._status_pass.color = ROJO
            self._status_pass.value = "No se encontró tu correo"
            self.page.update()
            return
        self._progress.visible = True
        self.page.update()
        try:
            from app.services.email_service import send_reset_token
            send_reset_token(email)
            self._status_pass.color = ft.Colors.GREEN_700
            self._status_pass.value = "Código enviado a " + email
            self._token_f.visible = True
            self._nueva_f.visible = True
            self._btn_cambiar.visible = True
        except Exception as ex:
            self._status_pass.color = ROJO
            self._status_pass.value = str(ex)
        finally:
            self._progress.visible = False
            self.page.update()

    def _confirmar_pass(self, e=None):
        self._status_pass.value = ""
        email = (self._alumno or {}).get("email", "")
        token = self._token_f.value.strip()
        new_pass = self._nueva_f.value

        if not token or not new_pass:
            self._status_pass.color = ROJO
            self._status_pass.value = "Ingresa el código y la nueva contraseña"
            self.page.update()
            return

        if len(new_pass) < 6:
            self._status_pass.color = ROJO
            self._status_pass.value = "Mínimo 6 caracteres"
            self.page.update()
            return

        self._btn_cambiar.visible = False
        self._progress.visible = True
        self.page.update()

        try:
            from app.services.email_service import verify_reset_token_and_change
            verify_reset_token_and_change(email, token, new_pass)
            self._status_pass.color = ft.Colors.GREEN_700
            self._status_pass.value = "Contraseña actualizada!"
            self._token_f.visible = False
            self._nueva_f.visible = False
            self._btn_cambiar.visible = False
        except Exception as ex:
            self._status_pass.color = ROJO
            self._status_pass.value = str(ex)
            self._btn_cambiar.visible = True
        finally:
            self._progress.visible = False
            self.page.update()