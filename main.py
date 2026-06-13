import flet as ft
import traceback
from app.core.state import get_app_state
from app.views.auth.login_view import LoginView
from app.layouts.admin_layout import AdminLayout
from app.layouts.prefect_layout import PrefectLayout


def main(page: ft.Page):
    page.title = "EduAsist QR"
    page.window.width = 1100
    page.window.height = 700

    def render():
        page.clean()

        try:
            state = get_app_state(page)

            if state is None:
                login = LoginView(
                    page,
                    on_login_success=render
                )
                page.add(login.build())

            elif state.role == "admin":
                layout = AdminLayout(page, state)
                page.add(layout.build())

            elif state.role == "prefect":
                layout = PrefectLayout(page, state)
                page.add(layout.build())

            else:
                page.add(
                    ft.Text(
                        "Rol no reconocido",
                        color="red"
                    )
                )

        except Exception as e:
            page.add(
                ft.Text(
                    f"ERROR EN RENDER:\n{str(e)}",
                    color="red",
                    size=20
                )
            )
            print(traceback.format_exc())

        page.update()

    render()


ft.app(target=main)