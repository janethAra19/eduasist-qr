import flet as ft
import hashlib
import threading
import cv2
from pyzbar import pyzbar
import time

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

    def build(self):
        # ── Estado del escáner ─────────────────────────────────────────────
        self._scanning = False

        # ── Indicador visual de estado ────────────────────────────────────
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

        # ── Resultado del último escaneo ──────────────────────────────────
        self.resultado_card = ft.Container(
            visible=False,
            border_radius=12,
            padding=20,
            margin=ft.Margin(left=0, top=10, right=0, bottom=0),
        )

        # ── Historial del día ─────────────────────────────────────────────
        self.historial = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=4,
        )
        self._escaneados_hoy = []  # lista local para no recargar todo el tiempo

        # ── Botones ───────────────────────────────────────────────────────
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
                # Encabezado
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

                # Zona central del escáner
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

                # Resultado del último escaneo
                self.resultado_card,

                ft.Divider(),

                # Historial del día
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
        self._scanning = True
        self.btn_iniciar.visible = False
        self.btn_detener.visible = True
        self.estado_icon.color = DORADO
        self.estado_texto.value = "Escáner activo — apunta la cámara al QR"
        self.estado_subtexto.value = "La cámara se abrirá en una ventana separada"
        self.resultado_card.visible = False
        self.page.update()

        self._scan_thread = threading.Thread(
            target=self._loop_escaneo,
            daemon=True,
        )
        self._scan_thread.start()

    def _detener_escaneo(self, e):
        self._scanning = False
        self.btn_iniciar.visible = True
        self.btn_detener.visible = False
        self.estado_icon.color = ft.Colors.GREY_400
        self.estado_texto.value = "Escáner detenido"
        self.estado_subtexto.value = ""
        self.page.update()

    # ── Loop de la cámara (hilo separado) ────────────────────────────────────

    def _loop_escaneo(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.estado_texto.value = "Error: no se pudo abrir la cámara"
            self.estado_icon.color = ROJO
            self._scanning = False
            self.btn_iniciar.visible = True
            self.btn_detener.visible = False
            self.page.update()
            return

        ultimo_qr = None
        ultimo_tiempo = 0
        COOLDOWN = 3  # segundos entre escaneos del mismo QR

        while self._scanning:
            ret, frame = cap.read()
            if not ret:
                break

            # Decodificar QR codes en el frame
            qrs = pyzbar.decode(frame)

            for qr in qrs:
                datos = qr.data.decode("utf-8").strip()
                ahora = time.time()

                # Evitar registrar el mismo QR dos veces seguidas rápidamente
                if datos == ultimo_qr and (ahora - ultimo_tiempo) < COOLDOWN:
                    continue

                ultimo_qr = datos
                ultimo_tiempo = ahora

                # Dibujar rectángulo en el frame (visual feedback)
                pts = qr.polygon
                if len(pts) == 4:
                    import numpy as np
                    pts_np = np.array([(p.x, p.y) for p in pts], dtype=np.int32)
                    cv2.polylines(frame, [pts_np], True, (0, 255, 0), 3)

                # Procesar en hilo de UI
                self._procesar_qr(datos)

            # Mostrar ventana de cámara
            cv2.imshow("EduAsist QR - Escáner (presiona Q para cerrar)", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

        # Si el loop terminó por tecla Q, actualizar UI
        if self._scanning:
            self._scanning = False
            self.btn_iniciar.visible = True
            self.btn_detener.visible = False
            self.estado_icon.color = ft.Colors.GREY_400
            self.estado_texto.value = "Escáner cerrado"
            self.estado_subtexto.value = ""
            self.page.update()

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

        except Exception as ex:
            self._mostrar_resultado(
                nombre="Error",
                mensaje=str(ex),
                color=ROJO,
                icono=ft.Icons.ERROR_OUTLINE,
            )

    # ── UI: resultado del escaneo ─────────────────────────────────────────────

    def _mostrar_resultado(self, nombre: str, mensaje: str, color, icono):
        self.resultado_card.bgcolor = color
        self.resultado_card.content = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
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
        self.page.update()

    # ── Historial del día ─────────────────────────────────────────────────────

    def _cargar_historial_hoy(self):
        """Carga los registros de asistencia del día desde Convex."""
        self.historial.controls.clear()
        try:
            from datetime import date
            hoy = date.today().isoformat()
            registros = convex_query(
                "attendance:getByDate",
                {
                    "tokenHash": self.token_hash,
                    "date": hoy,
                }
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
                    self.historial.controls.append(
                        self._fila_historial(r)
                    )
        except Exception as ex:
            self.historial.controls.append(
                ft.Text(f"Error cargando historial: {ex}", color=ROJO, size=12)
            )

    def _agregar_al_historial(self, nombre: str):
        """Agrega una fila rápida al historial sin recargar todo."""
        from datetime import datetime
        hora = datetime.now().strftime("%H:%M:%S")
        self.historial.controls.insert(
            0,
            ft.Container(
                bgcolor=ft.Colors.GREEN_50,
                border_radius=6,
                padding=ft.Padding(left=10, top=6, right=10, bottom=6),
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.CHECK,
                            color=ft.Colors.GREEN_600,
                            size=16,
                        ),
                        ft.Text(
                            nombre,
                            size=13,
                            weight=ft.FontWeight.W_500,
                            expand=True,
                        ),
                        ft.Text(
                            hora,
                            size=12,
                            color=ft.Colors.GREY_500,
                        ),
                    ],
                ),
            ),
        )
        self.page.update()

    def _fila_historial(self, registro: dict) -> ft.Control:
        from datetime import datetime
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