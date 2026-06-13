import flet as ft
import hashlib
import os
from app.services.convex_service import convex_query
from app.services.qr_service import generar_qr
from app.core.config import AZUL_MARINO, DORADO, ROJO


class QRView:
    def __init__(self, page: ft.Page, state):
        self.page = page
        self.state = state
        self.token_hash = hashlib.sha256(
            self.state.token.encode()
        ).hexdigest()

    def build(self):
        self.lista = ft.Row(
            wrap=True,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.cargar_qr()

        return ft.Column(
            expand=True,
            controls=[
                ft.Text("Códigos QR de Alumnos", size=20,
                        weight=ft.FontWeight.BOLD, color=AZUL_MARINO),
                ft.Text("Haz click en un QR para imprimirlo",
                        size=12, color=ft.Colors.GREY_500),
                ft.Divider(),
                self.lista,
            ],
        )

    def cargar_qr(self):
        self.lista.controls.clear()
        try:
            alumnos = convex_query("students:getWithQR", {
                "tokenHash": self.token_hash
            })
            for a in alumnos:
                if a.get("qrToken"):
                    ruta = generar_qr(a["qrToken"], a["name"])
                    self.lista.controls.append(
                        self.tarjeta_qr(a, ruta)
                    )
        except Exception as ex:
            self.lista.controls.append(
                ft.Text(f"Error: {ex}", color=ROJO)
            )
        self.page.update()

    def tarjeta_qr(self, alumno, ruta_qr):
        return ft.Container(
            width=180,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=16,
            margin=ft.Margin(0, 0, 12, 12),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.1, "#000000"),
            ),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Image(
                        src=ruta_qr,
                        width=140, height=140,
                        fit="contain",
                    ),
                    ft.Text(
                        alumno["name"],
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=AZUL_MARINO,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        f"{alumno['grade']}° {alumno['group']}",
                        size=11,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Text(
                        f"Código: {alumno['studentCode']}",
                        size=10,
                        color=ft.Colors.GREY_500,
                    ),
                    ft.ElevatedButton(
                        "Imprimir",
                        icon=ft.Icons.PRINT,
                        width=140,
                        style=ft.ButtonStyle(
                            bgcolor=AZUL_MARINO,
                            color=ft.Colors.WHITE,
                        ),
                        on_click=lambda e, r=ruta_qr, a=alumno: self.imprimir_qr(r, a),
                    ),
                ],
            ),
        )

    def imprimir_qr(self, ruta_qr, alumno):
        try:
            os.startfile(ruta_qr, "print")
        except Exception as ex:
            print(f"Error imprimiendo: {ex}")