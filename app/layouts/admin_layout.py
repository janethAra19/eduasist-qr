import flet as ft
from app.views.admin.dashboard_view import DashboardView
from app.views.admin.students_view import StudentsView


class AdminLayout:
    def __init__(self, page: ft.Page, state):
        self.page = page
        self.state = state
        self.selected_index = 0

    def build(self):
        # Crear vistas UNA SOLA VEZ — no recrearlas en cada cambio de nav
        self.dashboard_view = DashboardView(self.page, self.state)
        self.students_view = StudentsView(self.page, self.state)

        self.content = ft.Container(
            expand=True,
            padding=20,
            content=self.dashboard_view.build(),
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
            ],
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

        if self.selected_index == 0:
            self.content.content = self.dashboard_view.build()
        elif self.selected_index == 1:
            # Reusar la instancia existente — no crear una nueva
            self.content.content = self.students_view.build()

        self.page.update()