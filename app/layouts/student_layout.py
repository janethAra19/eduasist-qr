import flet as ft
from app.views.student.my_qr_view import MyQRView


class StudentLayout:
    def __init__(self, page: ft.Page, state):
        self.page  = page
        self.state = state

    def build(self):
        return MyQRView(self.page).build()