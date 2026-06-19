import flet as ft
from app.views.admin.dashboard_view import DashboardView
from app.views.admin.students_view import StudentsView
from app.views.admin.qr_view import QRView
from app.core.config import AZUL_MARINO, ROJO


class AdminLayout:
    def __init__(self, page: ft.Page, state):
        self.page = page
        self.state = state
        self.selected_index = 0
        self.students_view = StudentsView(page, state)
        self.views = [
            DashboardView(page, state),
            self.students_view,
            QRView(page, state),
        ]

    def _cerrar_sesion(self, e=None):
        from app.core.state import clear_app_state
        clear_app_state()
        self.page.controls.clear()
        # Volver al login llamando render() en main
        from app.views.auth.login_view import LoginView

        def render():
            from app.core.state import get_app_state
            from app.layouts.admin_layout import AdminLayout
            from app.layouts.prefect_layout import PrefectLayout
            self.page.controls.clear()
            state = get_app_state(self.page)
            if state is None:
                self.page.add(LoginView(self.page, on_login_success=render).build())
            elif state.role == "admin":
                self.page.add(AdminLayout(self.page, state).build())
            elif state.role == "prefect":
                self.page.add(PrefectLayout(self.page, state).build())
            self.page.update()

        self.page.add(LoginView(self.page, on_login_success=render).build())
        self.page.update()

    def build(self):
        self.content = ft.Container(
            expand=True,
            padding=20,
            content=self.views[0].build(),
        )

        nav = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.DASHBOARD_OUTLINED,
                    selected_icon=ft.Icons.DASHBOARD,
                    label="Dashboard",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.PEOPLE_OUTLINED,
                    selected_icon=ft.Icons.PEOPLE,
                    label="Alumnos",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.QR_CODE_OUTLINED,
                    selected_icon=ft.Icons.QR_CODE,
                    label="Códigos QR",
                ),
            ],
            # Botón de cerrar sesión al fondo del rail
            trailing=ft.Container(
                padding=ft.Padding(left=0, top=20, right=0, bottom=20),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.LOGOUT,
                            icon_color=ROJO,
                            tooltip="Cerrar sesión",
                            on_click=self._cerrar_sesion,
                        ),
                        ft.Text("Salir", size=11, color=ROJO),
                    ],
                ),
            ),
            on_change=self.on_nav_change,
        )

        return ft.Row(
            expand=True,
            controls=[
                nav,
                ft.VerticalDivider(width=1),
                self.content,
            ],
        )

    def on_nav_change(self, e):
        self.selected_index = e.control.selected_index
        self.content.content = self.views[self.selected_index].build()
        self.page.update()