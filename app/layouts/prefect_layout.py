import flet as ft
from app.views.prefect.scanner_view import ScannerView
from app.core.config import AZUL_MARINO, DORADO


class PrefectLayout:
    def __init__(self, page: ft.Page, state):
        self.page = page
        self.state = state

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
                    ft.Text(
                        self.state.name,
                        color=ft.Colors.WHITE70,
                        size=13,
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