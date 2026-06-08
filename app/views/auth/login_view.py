import flet as ft
from app.core.state import set_app_state

class LoginView:
    def __init__(self, page: ft.Page, on_login_success):
        self.page = page
        self.on_login_success = on_login_success

    def build(self):
        self.email = ft.TextField(
            label="Correo",
            width=300,
        )
        self.password = ft.TextField(
            label="Contraseña",
            password=True,
            can_reveal_password=True,
            width=300,
        )
        self.error = ft.Text("", color=ft.Colors.RED_400)

        return ft.Column(
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
            ],
        )

    def handle_login(self, e):
        # Mock temporal para pruebas
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