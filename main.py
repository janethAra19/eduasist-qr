import flet as ft
from app.core.state import get_app_state
from app.views.auth.login_view import LoginView
from app.layouts.admin_layout import AdminLayout
from app.layouts.prefect_layout import PrefectLayout
from app.views.student.my_qr_view import MyQRView

# ── MODO PRUEBA ───────────────────────────────────────────────────────────────
# Cambia a "alumno", "admin" o "prefecto" para probar cada vista directamente.
# Cuando termines de probar regresa a None para el flujo normal.
MODO_PRUEBA = "none"  # <- cambia aquí
# ─────────────────────────────────────────────────────────────────────────────


def main(page: ft.Page):
    page.title = "EduAsist QR"

    is_mobile = page.platform in [
        ft.PagePlatform.ANDROID,
        ft.PagePlatform.IOS,
    ]

    # Modo prueba en PC
    if MODO_PRUEBA == "alumno":
        page.window.width  = 400
        page.window.height = 750
        page.add(MyQRView(page).build())
        page.update()
        return

    if is_mobile:
        page.add(MyQRView(page).build())
        page.update()
        return

    page.window.width  = 900
    page.window.height = 600

    def render():
        page.controls.clear()
        state = get_app_state(page)

        if state is None:
            page.add(LoginView(page, on_login_success=render).build())
        elif state.role == "admin":
            layout = AdminLayout(page, state)
            page.add(layout.build())
        elif state.role == "prefect":
            layout = PrefectLayout(page, state)
            page.add(layout.build())
        else:
            page.add(ft.Text(f"Rol no reconocido: {state.role}"))

        page.update()

    render()


ft.run(main)