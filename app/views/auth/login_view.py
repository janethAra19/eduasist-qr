import flet as ft
import time
from app.core.state import set_app_state
from app.core.config import AZUL_MARINO, DORADO, ROJO, FONDO, ESCUELA_NOMBRE, ESCUELA_LEMA


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════════════════════
class LoginView:
    def __init__(self, page: ft.Page, on_login_success):
        self.page = page
        self.on_login_success = on_login_success

    def build(self):
        self.page.bgcolor = FONDO
        self.email = ft.TextField(
            label="Correo electrónico", width=320,
            border_color=AZUL_MARINO, focused_border_color=DORADO,
            keyboard_type=ft.KeyboardType.EMAIL,
            on_submit=self.handle_login,
        )
        self.password = ft.TextField(
            label="Contraseña", password=True,
            can_reveal_password=True, width=320,
            border_color=AZUL_MARINO, focused_border_color=DORADO,
            on_submit=self.handle_login,
        )
        self.error = ft.Text("", color=ROJO, size=13, text_align=ft.TextAlign.CENTER)
        self.btn = ft.ElevatedButton(
            "Iniciar sesión", width=320, height=48,
            style=ft.ButtonStyle(
                bgcolor=AZUL_MARINO, color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=self.handle_login,
        )
        self.progress = ft.ProgressRing(visible=False, color=AZUL_MARINO, width=28, height=28)

        card = ft.Container(
            width=400, bgcolor=ft.Colors.WHITE,
            border_radius=16, padding=40,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=20,
                                color=ft.Colors.with_opacity(0.15, "#000000")),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    ft.Image(src="assets/logo.png", width=100, height=100, fit="contain"),
                    ft.Text(ESCUELA_NOMBRE, size=18, weight=ft.FontWeight.BOLD,
                            color=AZUL_MARINO, text_align=ft.TextAlign.CENTER),
                    ft.Text(ESCUELA_LEMA, size=11, color=DORADO,
                            italic=True, text_align=ft.TextAlign.CENTER),
                    ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                    self.email,
                    self.password,
                    self.error,
                    self.progress,
                    self.btn,
                    ft.TextButton(
                        "¿No tienes cuenta? Registrarse",
                        style=ft.ButtonStyle(color=DORADO),
                        on_click=lambda e: self._ir_registro(),
                    ),
                    ft.TextButton(
                        "¿Olvidaste tu contraseña?",
                        style=ft.ButtonStyle(color=ft.Colors.GREY_500),
                        on_click=lambda e: self._ir_recuperar(),
                    ),
                ],
            ),
        )
        return ft.Container(
            expand=True, bgcolor=FONDO,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True, controls=[card],
            ),
        )

    def handle_login(self, e=None):
        self.error.value = ""
        email    = self.email.value.strip()
        password = self.password.value
        if not email or not password:
            self.error.value = "Completa todos los campos"
            self.page.update()
            return
        self.btn.visible      = False
        self.progress.visible = True
        self.page.update()
        try:
            from app.services.auth_service import login
            token, user = login(email, password)
            set_app_state(self.page, {
                "_id":      user["_id"],
                "schoolId": user["schoolId"],
                "role":     user["role"],
                "name":     user["name"],
                "token":    token,
                "email":    user.get("email", email),
            })
            self.on_login_success()
        except Exception as ex:
            self.error.value      = str(ex)
            self.btn.visible      = True
            self.progress.visible = False
            self.page.update()

    def _ir_registro(self):
        self.page.controls.clear()
        self.page.add(RegisterView(
            self.page,
            on_success=self.on_login_success,
            on_back=self._mostrar_login,
        ).build())
        self.page.update()

    def _ir_recuperar(self):
        self.page.controls.clear()
        self.page.add(RecuperarView(
            self.page,
            on_back=self._mostrar_login,
        ).build())
        self.page.update()

    def _mostrar_login(self):
        self.page.controls.clear()
        self.page.add(self.build())
        self.page.update()


# ══════════════════════════════════════════════════════════════════════════════
# REGISTRO — admin, prefecto o alumno
# ══════════════════════════════════════════════════════════════════════════════
class RegisterView:
    def __init__(self, page: ft.Page, on_success, on_back):
        self.page       = page
        self.on_success = on_success
        self.on_back    = on_back

    def build(self):
        self.page.bgcolor = FONDO

        self.nombre = ft.TextField(label="Nombre completo *", width=320,
            border_color=AZUL_MARINO, focused_border_color=DORADO)
        self.email = ft.TextField(label="Correo electrónico *", width=320,
            border_color=AZUL_MARINO, focused_border_color=DORADO,
            keyboard_type=ft.KeyboardType.EMAIL)
        self.password = ft.TextField(
            label="Contraseña * (mín. 6 caracteres)",
            password=True, can_reveal_password=True, width=320,
            border_color=AZUL_MARINO, focused_border_color=DORADO)
        self.rol = ft.Dropdown(
            label="Soy... *", width=320, border_color=AZUL_MARINO,
            options=[
                ft.dropdown.Option("admin",   "Administrador"),
                ft.dropdown.Option("prefect", "Prefecto / Maestro"),
                ft.dropdown.Option("student", "Alumno"),
            ],
            value="admin",
            on_change=self._on_rol_change,
        )

        # ── Solo para alumnos ──
        self.grado = ft.Dropdown(label="Grado *", width=153, border_color=AZUL_MARINO,
            options=[ft.dropdown.Option(str(i), f"{i}°") for i in range(1, 13)])
        self.grupo = ft.Dropdown(label="Grupo *", width=153, border_color=AZUL_MARINO,
            options=[ft.dropdown.Option(g) for g in ["A","B","C","D","E","F","G","H"]])
        self.cod_escuela = ft.TextField(
            label="Código de escuela *", width=320,
            border_color=AZUL_MARINO, focused_border_color=DORADO,
            hint_text="Pídelo a tu administrador")
        self.fila_alumno = ft.Column(visible=False, spacing=10, controls=[
            ft.Row(controls=[self.grado, self.grupo], width=320, spacing=14),
            self.cod_escuela,
        ])

        # ── Solo para admin/prefecto ──
        self.escuela_nombre = ft.TextField(
            label="Nombre de tu escuela *", width=320,
            border_color=AZUL_MARINO, focused_border_color=DORADO,
            hint_text="Ej: Colegio San José", visible=True)

        self.error    = ft.Text("", color=ROJO, size=13, text_align=ft.TextAlign.CENTER)
        self.exito    = ft.Text("", color=ft.Colors.GREEN_700, size=13,
                                text_align=ft.TextAlign.CENTER)
        self.btn      = ft.ElevatedButton("Crear cuenta", width=320, height=48,
            style=ft.ButtonStyle(bgcolor=AZUL_MARINO, color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10)),
            on_click=self.handle_register)
        self.progress = ft.ProgressRing(visible=False, color=AZUL_MARINO, width=28, height=28)

        card = ft.Container(
            width=400, bgcolor=ft.Colors.WHITE, border_radius=16, padding=40,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=20,
                                color=ft.Colors.with_opacity(0.15, "#000000")),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10, scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Row(controls=[
                        ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=AZUL_MARINO,
                                      on_click=lambda e: self.on_back()),
                        ft.Text("Crear cuenta nueva", size=16,
                                weight=ft.FontWeight.BOLD, color=AZUL_MARINO),
                    ], width=320),
                    ft.Image(src="assets/logo.png", width=80, height=80, fit="contain"),
                    ft.Text("Usa cualquier correo y contraseña",
                            size=12, color=ft.Colors.GREY_500,
                            text_align=ft.TextAlign.CENTER),
                    ft.Divider(height=4, color=ft.Colors.TRANSPARENT),
                    self.nombre,
                    self.email,
                    self.password,
                    self.rol,
                    self.fila_alumno,       # visible solo cuando rol=student
                    self.escuela_nombre,    # visible solo cuando rol=admin/prefect
                    self.error,
                    self.exito,
                    self.progress,
                    self.btn,
                    ft.TextButton("¿Ya tienes cuenta? Iniciar sesión",
                        style=ft.ButtonStyle(color=DORADO),
                        on_click=lambda e: self.on_back()),
                ],
            ),
        )
        return ft.Container(expand=True, bgcolor=FONDO,
            content=ft.Column(alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True, controls=[card]))

    def _on_rol_change(self, e):
        es_alumno = self.rol.value == "student"
        self.fila_alumno.visible    = es_alumno
        self.escuela_nombre.visible = not es_alumno
        self.page.update()

    def handle_register(self, e=None):
        self.error.value = ""
        self.exito.value = ""
        nombre   = self.nombre.value.strip()
        email    = self.email.value.strip()
        password = self.password.value
        rol      = self.rol.value

        if not nombre or not email or not password:
            self.error.value = "Completa los campos obligatorios (*)"
            self.page.update()
            return
        if len(password) < 6:
            self.error.value = "La contraseña debe tener al menos 6 caracteres"
            self.page.update()
            return
        if rol == "student":
            if not self.grado.value or not self.grupo.value:
                self.error.value = "Selecciona grado y grupo"
                self.page.update()
                return
            if not self.cod_escuela.value.strip():
                self.error.value = "Ingresa el código de escuela"
                self.page.update()
                return
        else:
            if not self.escuela_nombre.value.strip():
                self.error.value = "Escribe el nombre de tu escuela"
                self.page.update()
                return

        self.btn.visible      = False
        self.progress.visible = True
        self.page.update()

        try:
            from app.services.auth_service import register, register_student
            if rol == "student":
                token, user = register_student(
                    name=nombre,
                    email=email,
                    password=password,
                    grade=self.grado.value,
                    group=self.grupo.value,
                    school_code=self.cod_escuela.value.strip(),
                )
            else:
                token, user = register(nombre, email, password, rol,
                                       self.escuela_nombre.value.strip())

            set_app_state(self.page, {
                "_id":      user["_id"],
                "schoolId": user["schoolId"],
                "role":     user["role"],
                "name":     user["name"],
                "token":    token,
                "email":    user.get("email", email),
            })
            self.exito.value = f"✅ ¡Bienvenido/a, {user['name']}!"
            self.progress.visible = False
            self.page.update()
            time.sleep(1)
            self.on_success()
        except Exception as ex:
            self.error.value      = str(ex)
            self.btn.visible      = True
            self.progress.visible = False
            self.page.update()


# ══════════════════════════════════════════════════════════════════════════════
# RECUPERAR CONTRASEÑA
# ══════════════════════════════════════════════════════════════════════════════
class RecuperarView:
    def __init__(self, page: ft.Page, on_back):
        self.page    = page
        self.on_back = on_back

    def build(self):
        self.page.bgcolor = FONDO

        self.email_f = ft.TextField(label="Tu correo registrado", width=320,
            border_color=AZUL_MARINO, focused_border_color=DORADO,
            keyboard_type=ft.KeyboardType.EMAIL)

        self.status  = ft.Text("", size=13, text_align=ft.TextAlign.CENTER)
        self.progress = ft.ProgressRing(visible=False, color=AZUL_MARINO, width=28, height=28)

        # Campos que aparecen después de enviar el código
        self.token_f = ft.TextField(
            label="Código que recibiste en tu correo", width=320,
            border_color=AZUL_MARINO, focused_border_color=DORADO,
            keyboard_type=ft.KeyboardType.NUMBER, visible=False)
        self.nueva_f = ft.TextField(
            label="Nueva contraseña (mín. 6 caracteres)",
            password=True, can_reveal_password=True, width=320,
            border_color=AZUL_MARINO, focused_border_color=DORADO, visible=False)
        self.btn_cambiar = ft.ElevatedButton(
            "Actualizar contraseña", width=320, height=48,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10)),
            visible=False, on_click=self._cambiar_pass)

        self.btn_enviar = ft.ElevatedButton(
            "Enviar código a mi correo", width=320, height=48,
            style=ft.ButtonStyle(bgcolor=AZUL_MARINO, color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10)),
            on_click=self._enviar_token)

        card = ft.Container(
            width=400, bgcolor=ft.Colors.WHITE, border_radius=16, padding=40,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=20,
                                color=ft.Colors.with_opacity(0.15, "#000000")),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
                controls=[
                    ft.Row(controls=[
                        ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=AZUL_MARINO,
                                      on_click=lambda e: self.on_back()),
                        ft.Text("Recuperar contraseña", size=16,
                                weight=ft.FontWeight.BOLD, color=AZUL_MARINO),
                    ], width=320),
                    ft.Icon(ft.Icons.LOCK_RESET, color=AZUL_MARINO, size=52),
                    ft.Text(
                        "Ingresa tu correo y te enviaremos un código.\n"
                        "Con ese código podrás crear una nueva contraseña\n"
                        "sin necesidad de recordar la anterior.",
                        size=12, color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER),
                    ft.Divider(height=4, color=ft.Colors.TRANSPARENT),
                    self.email_f,
                    self.progress,
                    self.status,
                    self.btn_enviar,
                    ft.Divider(color=ft.Colors.TRANSPARENT),
                    self.token_f,
                    self.nueva_f,
                    self.btn_cambiar,
                ],
            ),
        )
        return ft.Container(expand=True, bgcolor=FONDO,
            content=ft.Column(alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True, controls=[card]))

    def _enviar_token(self, e=None):
        self.status.value = ""
        email = self.email_f.value.strip()
        if not email:
            self.status.color = ROJO
            self.status.value = "Ingresa tu correo"
            self.page.update()
            return
        self.btn_enviar.visible = False
        self.progress.visible   = True
        self.page.update()
        try:
            from app.services.email_service import send_reset_token
            send_reset_token(email)
            self.status.color = ft.Colors.GREEN_700
            self.status.value = f"✅ Código enviado a {email}\nRevisa tu bandeja de entrada."
            self.token_f.visible     = True
            self.nueva_f.visible     = True
            self.btn_cambiar.visible = True
        except Exception as ex:
            self.status.color       = ROJO
            self.status.value       = str(ex)
            self.btn_enviar.visible = True
        finally:
            self.progress.visible = False
            self.page.update()

    def _cambiar_pass(self, e=None):
        self.status.value = ""
        email    = self.email_f.value.strip()
        token    = self.token_f.value.strip()
        new_pass = self.nueva_f.value
        if not token or not new_pass:
            self.status.color = ROJO
            self.status.value = "Ingresa el código y la nueva contraseña"
            self.page.update()
            return
        if len(new_pass) < 6:
            self.status.color = ROJO
            self.status.value = "La contraseña debe tener al menos 6 caracteres"
            self.page.update()
            return
        self.btn_cambiar.visible = False
        self.progress.visible    = True
        self.page.update()
        try:
            from app.services.email_service import verify_reset_token_and_change
            verify_reset_token_and_change(email, token, new_pass)
            self.status.color = ft.Colors.GREEN_700
            self.status.value = "✅ ¡Contraseña actualizada! Inicia sesión."
            self.progress.visible = False
            self.page.update()
            time.sleep(2)
            self.on_back()
        except Exception as ex:
            self.status.color        = ROJO
            self.status.value        = str(ex)
            self.btn_cambiar.visible = True
            self.progress.visible    = False
            self.page.update()