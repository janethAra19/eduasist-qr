import flet as ft
from app.views.admin.dashboard_view import DashboardView
from app.views.admin.students_view import StudentsView

class AdminLayout:
    def __init__(self, page: ft.Page, state):
        self.page = page
        self.state = state
        self.selected_index = 0
        self.views = [
            DashboardView(page, state),
            StudentsView(page, state),
        ]

    def build(self):
        self.content = ft.Container(
            expand=True,
            padding=20,
            content=self.views[0].build(),
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
        self.content.content = self.views[self.selected_index].build()
        self.page.update()