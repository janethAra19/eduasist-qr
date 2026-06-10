import flet as ft
from app.core.state import set_app_state
from app.core.config import (
    AZUL_MARINO, DORADO, ROJO, FONDO,
    ESCUELA_NOMBRE, ESCUELA_LEMA
)


class LoginView:
    def __init__(self, page: ft.Page, on_login_success):
        self.page = page
        self.on_login_success = on_login_success

    def build(self):
        self.page.bgcolor = FONDO
        self.email = ft.TextField(
            label="Correo", width=320,
            border_color=AZUL_MARINO, focused_border_color=DORADO,
        )
        self.password = ft.TextField(
            label="Contraseña", password=True,
            can_reveal_password=True, width=320,
            border_color=AZUL_MARINO, focused_border_color=DORADO,
        )
        self.error = ft.Text("", color=ROJO, size=13)

        card = ft.Container(
            width=400, bgcolor=ft.Colors.WHITE,
            border_radius=16, padding=40,
            shadow=ft.BoxShadow(
                spread_radius=1, blur_radius=20,
                color=ft.Colors.with_opacity(0.15, "#000000"),
            ),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    ft.Image(src="assets/logo.png", width=120, height=120, fit="contain"),
                    ft.Text(ESCUELA_NOMBRE, size=18, weight=ft.FontWeight.BOLD,
                            color=AZUL_MARINO, text_align=ft.TextAlign.CENTER),
                    ft.Text(ESCUELA_LEMA, size=11, color=DORADO,
                            italic=True, text_align=ft.TextAlign.CENTER),
                    ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
                    self.email,
                    self.password,
                    self.error,
                    ft.Container(height=4),
                    ft.ElevatedButton(
                        "Iniciar sesión", width=320, height=48,
                        style=ft.ButtonStyle(
                            bgcolor=AZUL_MARINO, color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                        on_click=self.handle_login,
                    ),
                    ft.TextButton(
                        "¿No tienes cuenta? Regístrate",
                        style=ft.ButtonStyle(color=DORADO),
                        on_click=lambda e: self.show_register(),
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

    def handle_login(self, e):
        self.error.value = ""
        email = self.email.value.strip()
        password = self.password.value

        if not email or not password:
            self.error.value = "Completa todos los campos"
            self.page.update()
            return

        try:
            from app.services.auth_service import login
            token, user = login(email, password)
            set_app_state(self.page, {
                "_id": user["_id"],
                "schoolId": user["schoolId"],
                "role": user["role"],
                "name": user["name"],
                "token": token,
            })
            self.on_login_success()
        except Exception as ex:
            self.error.value = str(ex)
            self.page.update()

    def show_register(self):
        self.page.controls.clear()
        self.page.add(RegisterView(self.page, on_back=self.show_login).build())
        self.page.update()

    def show_login(self):
        self.page.controls.clear()
        self.page.add(self.build())
        self.page.update()


class RegisterView:
    def __init__(self, page: ft.Page, on_back):
        self.page = page
        self.on_back = on_back

    def build(self):
        self.page.bgcolor = FONDO
        self.nombre = ft.TextField(label="Nombre completo", width=320,
            border_color=AZUL_MARINO, focused_border_color=DORADO)
        self.email = ft.TextField(label="Correo", width=320,
            border_color=AZUL_MARINO, focused_border_color=DORADO)
        self.password = ft.TextField(label="Contraseña", password=True,
            can_reveal_password=True, width=320,
            border_color=AZUL_MARINO, focused_border_color=DORADO)
        self.rol = ft.Dropdown(
            label="Rol", width=320,
            options=[
                ft.dropdown.Option("admin", "Administrador"),
                ft.dropdown.Option("prefect", "Prefecto/Maestro"),
            ],
        )
        self.grado = ft.TextField(label="Grado (solo alumnos)", width=320,
            border_color=AZUL_MARINO, focused_border_color=DORADO)
        self.grupo = ft.TextField(label="Grupo (solo alumnos)", width=320,
            border_color=AZUL_MARINO, focused_border_color=DORADO)
        self.error = ft.Text("", color=ROJO, size=13)
        self.exito = ft.Text("", color=ft.Colors.GREEN_700, size=13)

        card = ft.Container(
            width=400, bgcolor=ft.Colors.WHITE,
            border_radius=16, padding=40,
            shadow=ft.BoxShadow(
                spread_radius=1, blur_radius=20,
                color=ft.Colors.with_opacity(0.15, "#000000"),
            ),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10, scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                icon_color=AZUL_MARINO,
                                tooltip="Regresar",
                                on_click=lambda e: self.on_back(),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START, width=320,
                    ),
                    ft.Image(src="assets/logo.png", width=80, height=80, fit="contain"),
                    ft.Text("Crear cuenta", size=22, weight=ft.FontWeight.BOLD,
                            color=AZUL_MARINO),
                    ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                    self.nombre,
                    self.email,
                    self.password,
                    self.rol,
                    self.error,
                    self.exito,
                    ft.ElevatedButton(
                        "Crear cuenta", width=320, height=48,
                        style=ft.ButtonStyle(
                            bgcolor=AZUL_MARINO, color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                        on_click=self.handle_register,
                    ),
                    ft.TextButton(
                        "¿Ya tienes cuenta? Inicia sesión",
                        style=ft.ButtonStyle(color=DORADO),
                        on_click=lambda e: self.on_back(),
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

    def handle_register(self, e):
        if not self.nombre.value or not self.email.value or not self.password.value:
            self.error.value = "Completa todos los campos obligatorios"
            self.page.update()
            return
        if not self.rol.value:
            self.error.value = "Selecciona un rol"
            self.page.update()
            return
        self.error.value = ""
        self.exito.value = f"✅ Cuenta creada para {self.nombre.value}. Ya puedes iniciar sesión."
        self.page.update()