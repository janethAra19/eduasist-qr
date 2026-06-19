import flet as ft
import hashlib
import threading
import time
from datetime import date, datetime

import cv2
from pyzbar import pyzbar

from app.services.convex_service import convex_query, convex_mutation
from app.core.config import AZUL_MARINO, DORADO, ROJO


class ScannerView:
    def __init__(self, page: ft.Page, state):
        self.page = page
        self.state = state
        self.token_hash = hashlib.sha256(
            self.state.token.encode()
        ).hexdigest()
        self._scanning = False
        self._scan_thread = None
        self._cap = None  # guardamos referencia para liberarla limpiamente

    # ── build ─────────────────────────────────────────────────────────────────

    def build(self):
        self._scanning = False

        # Indicador visual
        self.estado_icon = ft.Icon(
            ft.Icons.QR_CODE_SCANNER,
            size=80,
            color=ft.Colors.GREY_400,
        )
        self.estado_texto = ft.Text(
            "Presiona 'Iniciar escáner' para comenzar",
            size=16,
            color=ft.Colors.GREY_600,
            text_align=ft.TextAlign.CENTER,
        )
        self.estado_subtexto = ft.Text(
            "",
            size=13,
            color=ft.Colors.GREY_500,
            text_align=ft.TextAlign.CENTER,
        )

        # Resultado del último escaneo
        self.resultado_card = ft.Container(
            visible=False,
            border_radius=12,
            padding=20,
            margin=ft.Margin(left=0, top=10, right=0, bottom=0),
        )

        # Historial del día
        self.historial = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=4,
        )

        # Botones
        self.btn_iniciar = ft.ElevatedButton(
            "Iniciar escáner",
            icon=ft.Icons.PLAY_ARROW,
            style=ft.ButtonStyle(
                bgcolor=AZUL_MARINO,
                color=ft.Colors.WHITE,
            ),
            on_click=self._iniciar_escaneo,
        )
        self.btn_detener = ft.ElevatedButton(
            "Detener",
            icon=ft.Icons.STOP,
            style=ft.ButtonStyle(
                bgcolor=ROJO,
                color=ft.Colors.WHITE,
            ),
            visible=False,
            on_click=self._detener_escaneo,
        )

        self._cargar_historial_hoy()

        return ft.Column(
            expand=True,
            controls=[
                ft.Text(
                    "Escáner de Asistencia",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=AZUL_MARINO,
                ),
                ft.Text(
                    f"Prefecto: {self.state.name}",
                    size=13,
                    color=ft.Colors.GREY_600,
                ),
                ft.Divider(),

                # Zona del escáner
                ft.Container(
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=16,
                    padding=30,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                        controls=[
                            self.estado_icon,
                            self.estado_texto,
                            self.estado_subtexto,
                            ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    self.btn_iniciar,
                                    self.btn_detener,
                                ],
                            ),
                        ],
                    ),
                ),

                self.resultado_card,
                ft.Divider(),

                ft.Text(
                    "Registros de hoy",
                    size=15,
                    weight=ft.FontWeight.BOLD,
                    color=AZUL_MARINO,
                ),
                ft.Container(
                    expand=True,
                    content=self.historial,
                ),
            ],
        )

    # ── Control del escáner ───────────────────────────────────────────────────

    def _iniciar_escaneo(self, e):
        if self._scanning:
            return  # evitar doble click

        self._scanning = True
        self.btn_iniciar.visible = False
        self.btn_detener.visible = True
        self.estado_icon.color = DORADO
        self.estado_texto.value = "Escáner activo — apunta al QR del alumno"
        self.estado_subtexto.value = "Leyendo cámara…"
        self.resultado_card.visible = False
        self.page.update()

        self._scan_thread = threading.Thread(
            target=self._loop_escaneo,
            daemon=True,
        )
        self._scan_thread.start()

    def _detener_escaneo(self, e=None):
        self._scanning = False   # el loop revisa esta bandera cada frame
        # La cámara se liberará dentro del loop cuando salga
        self._actualizar_ui_detenido()

    def _actualizar_ui_detenido(self):
        self.btn_iniciar.visible = True
        self.btn_detener.visible = False
        self.estado_icon.color = ft.Colors.GREY_400
        self.estado_texto.value = "Escáner detenido"
        self.estado_subtexto.value = ""
        try:
            self.page.update()
        except Exception:
            pass

    # ── Loop de la cámara (hilo separado) ────────────────────────────────────

    def _loop_escaneo(self):
        # Intentar abrir la cámara (índice 0 primero, luego 1)
        self._cap = None
        for idx in [0, 1]:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                self._cap = cap
                break
            cap.release()

        if self._cap is None:
            self._ui_error_camara("No se encontró ninguna cámara disponible")
            return

        # Reducir resolución para mejorar velocidad en Android/PC
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        ultimo_qr = None
        ultimo_tiempo = 0
        COOLDOWN = 3  # segundos entre registros del mismo QR

        while self._scanning:
            ret, frame = self._cap.read()
            if not ret:
                # Si el frame falla, esperar un momento y reintentar
                time.sleep(0.05)
                continue

            # Decodificar QR en el frame (sin mostrar ventana)
            qrs = pyzbar.decode(frame)

            for qr in qrs:
                datos = qr.data.decode("utf-8", errors="ignore").strip()
                if not datos:
                    continue

                ahora = time.time()
                if datos == ultimo_qr and (ahora - ultimo_tiempo) < COOLDOWN:
                    continue  # mismo QR demasiado rápido, ignorar

                ultimo_qr = datos
                ultimo_tiempo = ahora

                # Dar feedback visual inmediato (antes de la consulta a Convex)
                self.estado_subtexto.value = "QR detectado, verificando…"
                try:
                    self.page.update()
                except Exception:
                    pass

                # Procesar en este mismo hilo (Convex es rápido)
                self._procesar_qr(datos)

            # Sin cv2.imshow ni waitKey — compatible con Android y escritorio
            time.sleep(0.05)  # ~20 fps, sin bloquear

        # Liberar cámara al salir del loop
        if self._cap:
            self._cap.release()
            self._cap = None

    def _ui_error_camara(self, mensaje: str):
        self._scanning = False
        self.estado_icon.color = ROJO
        self.estado_texto.value = f"Error: {mensaje}"
        self.estado_subtexto.value = "Verifica que la cámara esté conectada y libre"
        self.btn_iniciar.visible = True
        self.btn_detener.visible = False
        try:
            self.page.update()
        except Exception:
            pass

    # ── Procesar QR escaneado ─────────────────────────────────────────────────

    def _procesar_qr(self, qr_token: str):
        try:
            resultado = convex_mutation(
                "attendance:registerByQr",
                {
                    "sessionTokenHash": self.token_hash,
                    "qrTokenHash": qr_token,
                }
            )

            nombre = resultado.get("studentName", "Alumno")
            ya_registrado = resultado.get("alreadyRegistered", False)

            if ya_registrado:
                self._mostrar_resultado(
                    nombre=nombre,
                    mensaje="Ya registrado hoy",
                    color=ft.Colors.ORANGE_400,
                    icono=ft.Icons.WARNING_AMBER,
                )
            else:
                self._mostrar_resultado(
                    nombre=nombre,
                    mensaje="✓ Asistencia registrada",
                    color=ft.Colors.GREEN_600,
                    icono=ft.Icons.CHECK_CIRCLE,
                )
                self._agregar_al_historial(nombre)

                # Notificaciones en hilo separado (no bloquea el escáner)
                attendance_id = resultado.get("attendanceId")
                student_id = resultado.get("studentId")
                if attendance_id and student_id:
                    threading.Thread(
                        target=self._enviar_notificaciones,
                        args=(attendance_id, student_id, resultado),
                        daemon=True,
                    ).start()

        except Exception as ex:
            self._mostrar_resultado(
                nombre="Error al registrar",
                mensaje=str(ex),
                color=ROJO,
                icono=ft.Icons.ERROR_OUTLINE,
            )

    def _enviar_notificaciones(self, attendance_id: str, student_id: str, resultado: dict):
        try:
            from app.services.convex_service import convex_action
            convex_action("notifications:notifyGuardians", {
                "attendanceId":   attendance_id,
                "studentId":      student_id,
                "studentName":    resultado.get("studentName", ""),
                "studentGrade":   resultado.get("studentGrade", ""),
                "studentGroup":   resultado.get("studentGroup", ""),
                "attendanceDate": date.today().isoformat(),
                "scannedAt":      int(time.time() * 1000),
                "status":         "present",
            })
        except Exception as ex:
            print(f"[notificaciones] error: {ex}")

    # ── UI: resultado del escaneo ─────────────────────────────────────────────

    def _mostrar_resultado(self, nombre: str, mensaje: str, color, icono):
        self.resultado_card.bgcolor = color
        self.resultado_card.content = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12,
            controls=[
                ft.Icon(icono, color=ft.Colors.WHITE, size=32),
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text(
                            nombre,
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Text(
                            mensaje,
                            size=13,
                            color=ft.Colors.WHITE,
                        ),
                    ],
                ),
            ],
        )
        self.resultado_card.visible = True
        self.estado_subtexto.value = f"Último: {nombre}"
        try:
            self.page.update()
        except Exception:
            pass

    # ── Historial del día ─────────────────────────────────────────────────────

    def _cargar_historial_hoy(self):
        self.historial.controls.clear()
        try:
            hoy = date.today().isoformat()
            registros = convex_query(
                "attendance:getByDate",
                {"tokenHash": self.token_hash, "date": hoy},
            )
            if not registros:
                self.historial.controls.append(
                    ft.Text(
                        "Sin registros aún hoy.",
                        color=ft.Colors.GREY_400,
                        italic=True,
                        size=13,
                    )
                )
            else:
                for r in registros:
                    self.historial.controls.append(self._fila_historial(r))
        except Exception as ex:
            self.historial.controls.append(
                ft.Text(f"Error cargando historial: {ex}", color=ROJO, size=12)
            )

    def _agregar_al_historial(self, nombre: str):
        hora = datetime.now().strftime("%H:%M:%S")
        self.historial.controls.insert(
            0,
            ft.Container(
                bgcolor=ft.Colors.GREEN_50,
                border_radius=6,
                padding=ft.Padding(left=10, top=6, right=10, bottom=6),
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CHECK, color=ft.Colors.GREEN_600, size=16),
                        ft.Text(
                            nombre,
                            size=13,
                            weight=ft.FontWeight.W_500,
                            expand=True,
                        ),
                        ft.Text(hora, size=12, color=ft.Colors.GREY_500),
                    ],
                ),
            ),
        )
        try:
            self.page.update()
        except Exception:
            pass

    def _fila_historial(self, registro: dict) -> ft.Control:
        ts = registro.get("scannedAt", 0)
        hora = datetime.fromtimestamp(ts / 1000).strftime("%H:%M:%S") if ts else ""
        nombre = registro.get("studentName", "Desconocido")
        grado = registro.get("studentGrade", "")
        grupo = registro.get("studentGroup", "")

        return ft.Container(
            border_radius=6,
            padding=ft.Padding(left=10, top=6, right=10, bottom=6),
            bgcolor=ft.Colors.GREY_50,
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE_OUTLINE,
                        color=ft.Colors.GREEN_500,
                        size=16,
                    ),
                    ft.Column(
                        spacing=0,
                        expand=True,
                        controls=[
                            ft.Text(nombre, size=13, weight=ft.FontWeight.W_500),
                            ft.Text(
                                f"Grado {grado}° Grupo {grupo}",
                                size=11,
                                color=ft.Colors.GREY_500,
                            ),
                        ],
                    ),
                    ft.Text(hora, size=12, color=ft.Colors.GREY_400),
                ],
            ),
        )
