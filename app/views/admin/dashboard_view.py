import flet as ft
from datetime import date
from app.services.convex_service import convex_query
from app.core.config import AZUL_MARINO, DORADO, ROJO


class DashboardView:
    def __init__(self, page: ft.Page, state):
        self.page = page
        self.state = state

    def build(self):
        token_hash = __import__('hashlib').sha256(
            self.state.token.encode()
        ).hexdigest()
        today = date.today().isoformat()

        try:
            summary = convex_query("attendance:getTodaySummary", {
                "tokenHash": token_hash
            })
            records = convex_query("attendance:getByDate", {
                "tokenHash": token_hash,
                "date": today
            })
        except Exception as ex:
            return ft.Column(controls=[
                ft.Text(f"Error cargando datos: {ex}", color=ROJO)
            ])

        filas = []
        for r in records:
            es_presente = r["status"] == "present"
            color = ft.Colors.GREEN_100 if es_presente else ft.Colors.RED_100
            icono = ft.Icons.CHECK_CIRCLE if es_presente else ft.Icons.CANCEL
            color_icono = ft.Colors.GREEN if es_presente else ft.Colors.RED

            filas.append(
                ft.Container(
                    bgcolor=color,
                    border_radius=8,
                    padding=10,
                    margin=ft.Margin(0, 0, 0, 6),
                    content=ft.Row(controls=[
                        ft.Icon(icono, color=color_icono),
                        ft.Text(r["studentName"], expand=True),
                        ft.Text(f"{r['studentGrade']}° {r['studentGroup']}"),
                    ]),
                )
            )

        if not filas:
            filas.append(ft.Text(
                "Sin registros hoy aún.",
                color=ft.Colors.GREY_500,
                italic=True,
            ))

        return ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("Dashboard — Asistencia de hoy",
                        size=20, weight=ft.FontWeight.BOLD, color=AZUL_MARINO),
                ft.Row(controls=[
                    ft.Card(content=ft.Container(
                        padding=20,
                        content=ft.Column([
                            ft.Text("Presentes", size=12),
                            ft.Text(str(int(summary["present"])), size=28,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.GREEN),
                        ])
                    )),
                    ft.Card(content=ft.Container(
                        padding=20,
                        content=ft.Column([
                            ft.Text("Ausentes", size=12),
                            ft.Text(str(int(summary["absent"])), size=28,
                                    weight=ft.FontWeight.BOLD,
                                    color=ROJO),
                        ])
                    )),
                    ft.Card(content=ft.Container(
                        padding=20,
                        content=ft.Column([
                            ft.Text("Total", size=12),
                            ft.Text(str(int(summary["total"])), size=28,
                                    weight=ft.FontWeight.BOLD,
                                    color=AZUL_MARINO),
                        ])
                    )),
                ]),
                ft.Divider(),
                ft.Text("Registros de hoy", size=16),
                *filas,
            ],
        )