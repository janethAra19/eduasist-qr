import flet as ft
from app.core.state import get_app_state
from app.views.auth.login_view import LoginView
from app.layouts.admin_layout import AdminLayout


def main(page: ft.Page):
    page.title = "EduAsist QR"
    page.window.width = 900
    page.window.height = 600

    def render():
        page.controls.clear()
        state = get_app_state(page)

        if state is None:
            page.add(LoginView(page, on_login_success=render).build())
        elif state.role == "admin":
            layout = AdminLayout(page, state)
            page.add(layout.build())
        else:
            page.add(ft.Text("Rol no reconocido"))

        page.update()

    render()


ft.run(main)