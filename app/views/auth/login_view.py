import flet as ft
from app.core.state import set_app_state

class LoginView:
    def __init__(self, page: ft.Page, on_login_success):
        self.page = page
        self.on_login_success = on_login_success

    def build(self):
        self.email = ft.TextField(label="Correo", width=300)
        self.password = ft.TextField(
            label="Contraseña",
            password=True,
            can_reveal_password=True,
            width=300,
        )
        self.error = ft.Text("", color=ft.Colors.RED_400)

        self.login_form = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            controls=[
                ft.Text("EduAsist QR", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("Sistema de Asistencia Escolar", size=14),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                self.email,
                self.password,
                self.error,
                ft.ElevatedButton(
                    "Iniciar sesión",
                    width=300,
                    on_click=self.handle_login,
                ),
                ft.TextButton(
                    "¿No tienes cuenta? Regístrate",
                    on_click=lambda e: self.show_register(),
                ),
            ],
        )
        return self.login_form

    def show_register(self):
        self.page.controls.clear()
        self.page.add(RegisterView(self.page, on_back=self.show_login).build())
        self.page.update()

    def show_login(self):
        self.page.controls.clear()
        self.page.add(self.build())
        self.page.update()

    def handle_login(self, e):
        if self.email.value == "admin@test.com" and self.password.value == "1234":
            set_app_state(self.page, {
                "_id": "user_001",
                "schoolId": "school_001",
                "role": "admin",
                "name": "Administrador",
            })
            self.on_login_success()
        elif self.email.value == "prefecto@test.com" and self.password.value == "1234":
            set_app_state(self.page, {
                "_id": "user_002",
                "schoolId": "school_001",
                "role": "prefect",
                "name": "Prefecto",
            })
            self.on_login_success()
        else:
            self.error.value = "Correo o contraseña incorrectos"
            self.page.update()


class RegisterView:
    def __init__(self, page: ft.Page, on_back):
        self.page = page
        self.on_back = on_back

    def build(self):
        self.nombre = ft.TextField(label="Nombre completo", width=300)
        self.email = ft.TextField(label="Correo", width=300)
        self.password = ft.TextField(
            label="Contraseña",
            password=True,
            can_reveal_password=True,
            width=300,
        )
        self.rol = ft.Dropdown(
            label="Rol",
            width=300,
            options=[
                ft.dropdown.Option("admin", "Administrador"),
                ft.dropdown.Option("prefect", "Prefecto/Maestro"),
                ft.dropdown.Option("student", "Alumno"),
            ],
        )
        self.grado = ft.TextField(label="Grado (solo alumnos)", width=300)
        self.grupo = ft.TextField(label="Grupo (solo alumnos)", width=300)
        self.error = ft.Text("", color=ft.Colors.RED_400)
        self.exito = ft.Text("", color=ft.Colors.GREEN_400)

        self.btn_crear = ft.ElevatedButton(
    "Crear cuenta",
    width=300,
    on_click=self.handle_register,
)

        self.btn_ir_login = ft.ElevatedButton(
    "Ir al inicio de sesión",
    width=300,
    visible=False,
    on_click=lambda e: self.on_back(),
)

        return ft.Column(
    alignment=ft.MainAxisAlignment.CENTER,
    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    expand=True,
    scroll=ft.ScrollMode.AUTO,
    controls=[
        ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    tooltip="Regresar al inicio de sesión",
                    on_click=lambda e: self.on_back(),
                ),
            ],
            width=300,
        ),
        ft.Text("Crear cuenta", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("EduAsist QR", size=14, color=ft.Colors.GREY_500),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                self.nombre,
                self.email,
                self.password,
                self.rol,
                self.grado,
                self.grupo,
                self.error,
                self.exito,
               self.btn_crear,
self.btn_ir_login,
                ft.TextButton(
                    "¿Ya tienes cuenta? Inicia sesión",
                    on_click=lambda e: self.on_back(),
                ),
            ],
        )

    def handle_register(self, e):
        # Validación básica
        if not self.nombre.value or not self.email.value or not self.password.value:
            self.error.value = "Completa todos los campos obligatorios"
            self.page.update()
            return

        if not self.rol.value:
            self.error.value = "Selecciona un rol"
            self.page.update()
            return

        if self.rol.value == "student":
            if not self.grado.value or not self.grupo.value:
                self.error.value = "Alumnos deben ingresar grado y grupo"
                self.page.update()
                return

        # Mock — en Fase 3 esto se conecta a Convex

        self.error.value = ""
        self.exito.value = f"✅ Cuenta creada para {self.nombre.value}. Ya puedes iniciar sesión."
        self.btn_crear.visible = False
        self.btn_ir_login.visible = True
        self.page.update()