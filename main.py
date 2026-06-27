import flet as ft

from app.core.state import get_app_state
from app.views.auth.login_view import LoginView
from app.layouts.admin_layout import AdminLayout
from app.layouts.prefect_layout import PrefectLayout
from app.views.student.my_qr_view import MyQRView

MODO_PRUEBA = "none"


def main(page: ft.Page):
    page.title = "EduAsist QR"
    page.bgcolor = "#F0F4F8"

    is_mobile = page.platform in [
        ft.PagePlatform.ANDROID,
        ft.PagePlatform.IOS,
    ]

    def render():
        page.controls.clear()
        state = get_app_state(page)

        if state is None:
            page.window.width = 900
            page.window.height = 600
            page.add(LoginView(page, on_login_success=render).build())

        elif state.role == "admin":
            page.window.width = 900
            page.window.height = 600
            page.add(AdminLayout(page, state).build())

        elif state.role == "prefect":
            page.window.width = 900
            page.window.height = 600
            page.add(PrefectLayout(page, state).build())

        elif state.role == "student":
            page.window.width = 420
            page.window.height = 750
            page.add(MyQRView(page, state=state).build())

        else:
            page.add(ft.Text(f"Rol no reconocido: {state.role}", color="red"))

        page.update()

    if MODO_PRUEBA == "alumno" or is_mobile:
        page.window.width = 420
        page.window.height = 750
        page.add(MyQRView(page).build())
        page.update()
        return

    render()


if __name__ == "__main__":
    ft.run(main)