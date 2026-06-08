import flet as ft

class StudentsView:
    def __init__(self, page: ft.Page, state):
        self.page = page
        self.state = state

    def build(self):
        return ft.Column(
            controls=[
                ft.Text("Gestión de Alumnos",
                        size=20, weight=ft.FontWeight.BOLD),
                ft.Text("(Próximamente — conexión con Convex)",
                        color=ft.Colors.GREY_500),
            ]
        )