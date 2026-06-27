import flet as ft
from app.views.student.my_qr_view import MyQRView


class StudentLayout:
    def __init__(self, page: ft.Page, state):
        self.page  = page
        self.state = state

    def build(self):
        print("STATE EMAIL:", self.state.email)
        print("STATE TOKEN:", self.state.token)
        view = MyQRView(self.page, state=self.state)
        widget = view.build()
        return ft.Container(
            expand=True,
            content=widget,
        )