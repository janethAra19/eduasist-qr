import flet as ft
from app.views.prefect.scanner_view import ScannerView
from app.core.config import AZUL_MARINO, DORADO, ROJO


class PrefectLayout:
    def __init__(self, page: ft.Page, state):
        self.page = page
        self.state = state

    def _cerrar_sesion(self, e=None):
        from app.core.state import clear_app_state
        clear_app_state()

        from app.views.auth.login_view import LoginView

        def render():
            from app.core.state import get_app_state
            from app.layouts.admin_layout import AdminLayout
            self.page.controls.clear()
            state = get_app_state(self.page)
            if state is None:
                self.page.add(LoginView(self.page, on_login_success=render).build())
            elif state.role == "admin":
                self.page.add(AdminLayout(self.page, state).build())
            elif state.role == "prefect":
                self.page.add(PrefectLayout(self.page, state).build())
            self.page.update()

        self.page.controls.clear()
        self.page.add(LoginView(self.page, on_login_success=render).build())
        self.page.update()

    def build(self):
        self.scanner_view = ScannerView(self.page, self.state)

        header = ft.Container(
            bgcolor=AZUL_MARINO,
            padding=ft.Padding(left=20, top=12, right=20, bottom=12),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.QR_CODE_SCANNER,
                                color=DORADO,
                                size=28,
                            ),
                            ft.Text(
                                "EduAsist QR — Prefecto",
                                color=ft.Colors.WHITE,
                                size=18,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Row(
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                self.state.name,
                                color=ft.Colors.WHITE70,
                                size=13,
                            ),
                            ft.TextButton(
                                "Cerrar sesión",
                                icon=ft.Icons.LOGOUT,
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE70,
                                    icon_color=ft.Colors.WHITE70,
                                ),
                                on_click=self._cerrar_sesion,
                            ),
                        ],
                    ),
                ],
            ),
        )

        content = ft.Container(
            expand=True,
            padding=20,
            content=self.scanner_view.build(),
        )

        return ft.Column(
            expand=True,
            spacing=0,
            controls=[
                header,
                content,
            ],
        )