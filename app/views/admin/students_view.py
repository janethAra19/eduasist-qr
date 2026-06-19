import flet as ft
import hashlib
import os
import threading
import cv2
import tkinter as tk
from tkinter import filedialog
import requests
import qrcode
import io

from app.services.convex_service import convex_query, convex_mutation
from app.core.config import AZUL_MARINO, DORADO, ROJO


class StudentsView:
    def __init__(self, page: ft.Page, state, file_picker=None):
        self.page = page
        self.state = state
        self.token_hash = hashlib.sha256(
            self.state.token.encode()
        ).hexdigest()
        self.foto_path = None

    def build(self):
        self.foto_path = None
        self.lista = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        self.campo_nombre = ft.TextField(label="Nombre completo", width=320)
        self.campo_codigo = ft.TextField(label="Código de alumno", width=320)
        self.campo_grado = ft.Dropdown(
            label="Grado", width=320,
            options=[
                ft.dropdown.Option(key="1", text="1"),
                ft.dropdown.Option(key="2", text="2"),
                ft.dropdown.Option(key="3", text="3"),
            ],
        )
        self.campo_grupo = ft.Dropdown(
            label="Grupo", width=320,
            options=[
                ft.dropdown.Option(key="A", text="A"),
                ft.dropdown.Option(key="B", text="B"),
                ft.dropdown.Option(key="C", text="C"),
            ],
        )
        self.foto_preview = ft.Image(
            src="assets/logo.png", width=80, height=80,
            fit="cover", visible=False,
        )
        self.foto_label = ft.Text("Sin foto seleccionada", size=12)
        self.error_form = ft.Text("", color=ROJO, size=12)

        self.panel_form = ft.Container(
            visible=False,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            padding=20,
            border=ft.Border(
                top=ft.BorderSide(1, ft.Colors.GREY_300),
                bottom=ft.BorderSide(1, ft.Colors.GREY_300),
                left=ft.BorderSide(1, ft.Colors.GREY_300),
                right=ft.BorderSide(1, ft.Colors.GREY_300),
            ),
            content=ft.Column(
                tight=True,
                spacing=10,
                controls=[
                    ft.Text("Agregar alumno", size=16,
                            weight=ft.FontWeight.BOLD, color=AZUL_MARINO),
                    self.campo_nombre,
                    self.campo_codigo,
                    self.campo_grado,
                    self.campo_grupo,
                    ft.Divider(),
                    self.foto_preview,
                    self.foto_label,
                    ft.Row(controls=[
                        ft.ElevatedButton(
                            "Subir foto",
                            icon=ft.Icons.UPLOAD_FILE,
                            on_click=lambda e: threading.Thread(
                                target=self._abrir_explorador,
                                daemon=True,
                            ).start(),
                        ),
                        ft.ElevatedButton(
                            "Usar cámara",
                            icon=ft.Icons.CAMERA_ALT,
                            on_click=lambda e: threading.Thread(
                                target=self._capturar_camara,
                                daemon=True,
                            ).start(),
                        ),
                    ]),
                    self.error_form,
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.ElevatedButton(
                                "Guardar",
                                icon=ft.Icons.SAVE,
                                style=ft.ButtonStyle(
                                    bgcolor=AZUL_MARINO,
                                    color=ft.Colors.WHITE,
                                ),
                                on_click=self._guardar_alumno,
                            ),
                            ft.OutlinedButton(
                                "Cancelar",
                                icon=ft.Icons.CANCEL_OUTLINED,
                                on_click=lambda e: self._ocultar_formulario(),
                            ),
                        ],
                    ),
                ],
            ),
        )

        self.confirm_nombre = ft.Text("")
        self._alumno_a_eliminar = None
        self.panel_confirm = ft.Container(
            visible=False,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            padding=20,
            border=ft.Border(
                top=ft.BorderSide(2, ROJO),
                bottom=ft.BorderSide(2, ROJO),
                left=ft.BorderSide(2, ROJO),
                right=ft.BorderSide(2, ROJO),
            ),
            content=ft.Column(
                tight=True,
                spacing=10,
                controls=[
                    ft.Text("Eliminar alumno", size=16,
                            weight=ft.FontWeight.BOLD, color=ROJO),
                    self.confirm_nombre,
                    ft.Text("Esta acción no se puede deshacer.",
                            color=ft.Colors.GREY_600, size=12),
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.ElevatedButton(
                                "Eliminar",
                                icon=ft.Icons.DELETE,
                                style=ft.ButtonStyle(
                                    bgcolor=ROJO,
                                    color=ft.Colors.WHITE,
                                ),
                                on_click=self._confirmar_eliminar,
                            ),
                            ft.OutlinedButton(
                                "Cancelar",
                                icon=ft.Icons.CANCEL_OUTLINED,
                                on_click=lambda e: self._ocultar_confirm(),
                            ),
                        ],
                    ),
                ],
            ),
        )

        self.cargar_alumnos()

        return ft.Column(
            expand=True,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Gestión de Alumnos", size=20,
                                weight=ft.FontWeight.BOLD, color=AZUL_MARINO),
                        ft.ElevatedButton(
                            "Agregar alumno",
                            icon=ft.Icons.ADD,
                            style=ft.ButtonStyle(
                                bgcolor=AZUL_MARINO,
                                color=ft.Colors.WHITE,
                            ),
                            on_click=lambda e: self._mostrar_formulario(),
                        ),
                    ],
                ),
                ft.Divider(),
                self.panel_form,
                self.panel_confirm,
                self.lista,
            ],
        )

    def _mostrar_formulario(self):
        self.foto_path = None
        self.campo_nombre.value = ""
        self.campo_codigo.value = ""
        self.campo_grado.value = None
        self.campo_grupo.value = None
        self.foto_preview.src = "assets/logo.png"
        self.foto_preview.visible = False
        self.foto_label.value = "Sin foto seleccionada"
        self.error_form.value = ""
        self.panel_confirm.visible = False
        self.panel_form.visible = True
        self.page.update()

    def _ocultar_formulario(self):
        self.panel_form.visible = False
        self.page.update()

    def _guardar_alumno(self, e):
        errores = []
        if not (self.campo_nombre.value or "").strip():
            errores.append("Nombre requerido")
        if not (self.campo_codigo.value or "").strip():
            errores.append("Código requerido")
        if not self.campo_grado.value:
            errores.append("Selecciona un grado")
        if not self.campo_grupo.value:
            errores.append("Selecciona un grupo")

        if errores:
            self.error_form.value = " | ".join(errores)
            self.page.update()
            return

        try:
            student_id = convex_mutation("students:create", {
                "tokenHash": self.token_hash,
                "studentCode": self.campo_codigo.value.strip(),
                "name": self.campo_nombre.value.strip(),
                "grade": self.campo_grado.value,
                "group": self.campo_grupo.value,
            })
            if self.foto_path and student_id:
                self.subir_foto(student_id)
            self._ocultar_formulario()
            self.cargar_alumnos()
        except Exception as ex:
            self.error_form.value = str(ex)
            self.page.update()

    def _mostrar_confirm(self, alumno):
        self._alumno_a_eliminar = alumno
        self.confirm_nombre.value = f"¿Estás seguro de eliminar a {alumno['name']}?"
        self.panel_form.visible = False
        self.panel_confirm.visible = True
        self.page.update()

    def _ocultar_confirm(self):
        self.panel_confirm.visible = False
        self._alumno_a_eliminar = None
        self.page.update()

    def _confirmar_eliminar(self, e):
        if not self._alumno_a_eliminar:
            return
        try:
            convex_mutation("students:deleteStudent", {
                "tokenHash": self.token_hash,
                "studentId": self._alumno_a_eliminar["_id"],
            })
            self._ocultar_confirm()
            self.cargar_alumnos()
        except Exception as ex:
            print(f"Error eliminando: {ex}")

    def cargar_alumnos(self):
        self.lista.controls.clear()
        try:
            alumnos = convex_query("students:listBySchool", {
                "tokenHash": self.token_hash
            })
            if not alumnos:
                self.lista.controls.append(
                    ft.Text("No hay alumnos registrados.",
                            color=ft.Colors.GREY_500, italic=True)
                )
            else:
                for alumno in alumnos:
                    self.lista.controls.append(self._tarjeta_alumno(alumno))
        except Exception as ex:
            self.lista.controls.append(ft.Text(f"Error: {ex}", color=ROJO))
        self.page.update()

    def _tarjeta_alumno(self, alumno):
        if alumno.get("photoUrl"):
            foto_widget = ft.Image(
                src=alumno["photoUrl"],
                width=50, height=50,
                fit="cover", border_radius=25,
            )
        else:
            foto_widget = ft.Icon(ft.Icons.PERSON, color=AZUL_MARINO, size=40)

        return ft.Container(
            border=ft.Border(
                top=ft.BorderSide(1, ft.Colors.GREY_300),
                bottom=ft.BorderSide(1, ft.Colors.GREY_300),
                left=ft.BorderSide(1, ft.Colors.GREY_300),
                right=ft.BorderSide(1, ft.Colors.GREY_300),
            ),
            border_radius=8,
            padding=12,
            margin=ft.Margin(left=0, top=0, right=0, bottom=6),
            content=ft.Row(
                controls=[
                    foto_widget,
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            ft.Text(alumno["name"], weight=ft.FontWeight.BOLD),
                            ft.Text(
                                f"Grado {alumno['grade']}° Grupo {alumno['group']} — Código: {alumno['studentCode']}",
                                size=12, color=ft.Colors.GREY_600,
                            ),
                        ],
                    ),
                    ft.IconButton(
                        icon=ft.Icons.QR_CODE,
                        icon_color=AZUL_MARINO,
                        tooltip="Ver código QR",
                        on_click=lambda e, a=alumno: self._mostrar_qr(a),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=ROJO,
                        tooltip="Eliminar alumno",
                        on_click=lambda e, a=alumno: self._mostrar_confirm(a),
                    ),
                ],
            ),
        )

    def _mostrar_qr(self, alumno):
        try:
            alumnos_qr = convex_query("students:getWithQR", {
                "tokenHash": self.token_hash,
            })
            qr_token = None
            for a in alumnos_qr:
                if a["_id"] == alumno["_id"]:
                    qr_token = a.get("qrToken")
                    break

            if not qr_token:
                self._dialogo_error("Este alumno no tiene QR activo.")
                return

            qr_img = qrcode.make(qr_token)
            buf = io.BytesIO()
            qr_img.save(buf, format="PNG")
            buf.seek(0)

            base_dir = os.path.dirname(os.path.abspath(__file__))
            qr_dir = os.path.abspath(os.path.join(base_dir, "..", "..", "..", "assets", "qr"))
            os.makedirs(qr_dir, exist_ok=True)
            qr_path = os.path.join(qr_dir, f"qr_{alumno['_id']}.png")
            with open(qr_path, "wb") as f:
                f.write(buf.read())

            # ✅ CORRECTO para Flet 0.85: usar page.show_dialog() y page.pop_dialog()
            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"QR de {alumno['name']}",
                              weight=ft.FontWeight.BOLD, color=AZUL_MARINO),
                content=ft.Column(
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Image(src=qr_path, width=250, height=250,
                                 fit="contain"),
                        ft.Text(f"Código: {alumno['studentCode']}",
                                size=12, color=ft.Colors.GREY_600),
                        ft.Text(
                            f"Grado {alumno['grade']}° Grupo {alumno['group']}",
                            size=12, color=ft.Colors.GREY_600),
                    ],
                ),
                actions=[
                    ft.TextButton(
                        "Cerrar",
                        on_click=lambda e: self.page.pop_dialog(),
                    ),
                    ft.ElevatedButton(
                        "Imprimir",
                        icon=ft.Icons.PRINT,
                        style=ft.ButtonStyle(
                            bgcolor=AZUL_MARINO,
                            color=ft.Colors.WHITE,
                        ),
                        on_click=lambda e: self._imprimir_qr(qr_path),
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page.show_dialog(dlg)

        except Exception as ex:
            self._dialogo_error(str(ex))

    def _imprimir_qr(self, qr_path):
        try:
            import subprocess, sys
            if sys.platform == "win32":
                os.startfile(qr_path, "print")
            else:
                subprocess.run(["lpr", qr_path])
        except Exception as ex:
            print(f"Error al imprimir: {ex}")

    def _dialogo_error(self, mensaje: str):
        dlg = ft.AlertDialog(
            title=ft.Text("Error", color=ROJO),
            content=ft.Text(mensaje),
            actions=[
                ft.TextButton(
                    "Cerrar",
                    on_click=lambda e: self.page.pop_dialog(),
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dlg)

    def _abrir_explorador(self):
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        ruta = filedialog.askopenfilename(
            title="Seleccionar foto",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png")],
        )
        root.destroy()
        if ruta:
            self.foto_path = ruta
            self.foto_preview.src = ruta
            self.foto_preview.visible = True
            self.foto_label.value = os.path.basename(ruta)
            self.page.update()

    def _capturar_camara(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.foto_label.value = "No se pudo acceder a la cámara"
            self.page.update()
            return
        for _ in range(5):
            cap.read()
        ret, frame = cap.read()
        cap.release()
        if ret:
            os.makedirs("assets/fotos", exist_ok=True)
            ruta = os.path.join("assets", "fotos", "temp_foto.jpg")
            cv2.imwrite(ruta, frame)
            self.foto_path = ruta
            self.foto_preview.src = ruta
            self.foto_preview.visible = True
            self.foto_label.value = "Foto tomada con cámara"
            self.page.update()
        else:
            self.foto_label.value = "No se pudo capturar la foto"
            self.page.update()

    def subir_foto(self, student_id: str):
        try:
            upload_url = convex_mutation("students:generateUploadUrl", {
                "tokenHash": self.token_hash
            })
            with open(self.foto_path, "rb") as f:
                foto_bytes = f.read()
            ext = os.path.splitext(self.foto_path)[1].lower()
            mime = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"
            res = requests.post(
                upload_url,
                headers={"Content-Type": mime},
                data=foto_bytes,
                timeout=30,
            )
            storage_id = res.json().get("storageId")
            if storage_id:
                convex_mutation("students:updatePhoto", {
                    "tokenHash": self.token_hash,
                    "studentId": student_id,
                    "storageId": storage_id,
                })
        except Exception as ex:
            print(f"Error subiendo foto: {ex}")