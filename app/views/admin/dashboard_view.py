import flet as ft

class DashboardView:
    def __init__(self, page: ft.Page, state):
        self.page = page
        self.state = state

    def build(self):
        # Datos mock para visualizar
        alumnos_mock = [
            {"nombre": "Juan Pérez", "grado": "1", "grupo": "A", "estado": "presente"},
            {"nombre": "María López", "grado": "1", "grupo": "A", "estado": "ausente"},
            {"nombre": "Carlos Ruiz", "grado": "2", "grupo": "B", "estado": "presente"},
        ]

        filas = []
        for a in alumnos_mock:
            color = ft.Colors.GREEN_100 if a["estado"] == "presente" else ft.Colors.RED_100
            filas.append(
                ft.Container(
                    bgcolor=color,
                    border_radius=8,
                    padding=10,
                    margin=ft.Margin(left=0, top=0, right=0, bottom=6),
                    content=ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE if a["estado"] == "presente"
                                else ft.Icons.CANCEL,
                                color=ft.Colors.GREEN if a["estado"] == "presente"
                                else ft.Colors.RED,
                            ),
                            ft.Text(a["nombre"], expand=True),
                            ft.Text(f"{a['grado']}° {a['grupo']}"),
                        ]
                    ),
                )
            )

        return ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("Dashboard — Asistencia de hoy",
                        size=20, weight=ft.FontWeight.BOLD),
                ft.Row(
                    controls=[
                        ft.Card(content=ft.Container(
                            padding=20,
                            content=ft.Column([
                                ft.Text("Presentes", size=12),
                                ft.Text("2", size=28, weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.GREEN),
                            ])
                        )),
                        ft.Card(content=ft.Container(
                            padding=20,
                            content=ft.Column([
                                ft.Text("Ausentes", size=12),
                                ft.Text("1", size=28, weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.RED),
                            ])
                        )),
                    ]
                ),
                ft.Divider(),
                ft.Text("Lista de alumnos", size=16),
                *filas,
            ],
        )