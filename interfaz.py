"""Interfaz gráfica local para probar el flujo de monitorización."""

import asyncio
import tkinter as tk
from datetime import datetime, timezone
from tkinter import messagebox, ttk
from uuid import NAMESPACE_URL, uuid5

from monitorizacion.adapters import InMemorySesionRepository, SimuladorSensores
from monitorizacion.application import MonitorizacionService
from monitorizacion.domain import AnomaliaDetectadaEvent, LecturaMetrica, UmbralSeguridad


class PublicadorLocal:
    """Recoge eventos en la demo para mostrarlos como alertas en pantalla."""

    def __init__(self):
        self.eventos: list[AnomaliaDetectadaEvent] = []

    async def publicar(self, evento: AnomaliaDetectadaEvent) -> None:
        self.eventos.append(evento)


class Aplicacion(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Monitor de residencia — demostración")
        self.geometry("900x620")
        self.minsize(760, 520)
        self.publicador = PublicadorLocal()
        self.service = MonitorizacionService(InMemorySesionRepository(), self.publicador, {
            "frecuencia_cardiaca": UmbralSeguridad(50, 110, "frecuencia_cardiaca", "lpm"),
            "temperatura_corporal": UmbralSeguridad(35.5, 38.0, "temperatura_corporal", "°C"),
            "humedad": UmbralSeguridad(30, 70, "humedad", "%"),
            "temperatura_ambiente": UmbralSeguridad(20, 28, "temperatura_ambiente", "°C"),
        })
        self.sesion = None
        self._crear_interfaz()

    def _crear_interfaz(self):
        contenedor = ttk.Frame(self, padding=18)
        contenedor.pack(fill="both", expand=True)
        ttk.Label(contenedor, text="Monitorización de residentes", font=("Segoe UI", 19, "bold")).pack(anchor="w")
        ttk.Label(contenedor, text="Demostración local: las lecturas y alertas se conservan mientras la ventana está abierta.").pack(anchor="w", pady=(2, 14))

        sesion_frame = ttk.LabelFrame(contenedor, text="1. Sesión de monitoreo", padding=10)
        sesion_frame.pack(fill="x")
        ttk.Label(sesion_frame, text="ID del residente:").grid(row=0, column=0, sticky="w")
        self.residente = ttk.Entry(sesion_frame, width=39)
        self.residente.insert(0, "residente-demo-01")
        self.residente.grid(row=0, column=1, padx=8, pady=4, sticky="w")
        ttk.Label(sesion_frame, text="ID del dispositivo:").grid(row=1, column=0, sticky="w")
        self.dispositivo = ttk.Entry(sesion_frame, width=39)
        self.dispositivo.insert(0, "sensor-demo-01")
        self.dispositivo.grid(row=1, column=1, padx=8, pady=4, sticky="w")
        self.boton_sesion = ttk.Button(sesion_frame, text="Iniciar sesión", command=self.iniciar_sesion)
        self.boton_sesion.grid(row=0, column=2, rowspan=2, padx=10)
        self.estado = ttk.Label(sesion_frame, text="Sin sesión activa")
        self.estado.grid(row=2, column=0, columnspan=3, sticky="w", pady=(5, 0))

        lectura_frame = ttk.LabelFrame(contenedor, text="2. Registrar lectura", padding=10)
        lectura_frame.pack(fill="x", pady=12)
        ttk.Label(lectura_frame, text="Métrica:").grid(row=0, column=0, sticky="w")
        self.metrica = tk.StringVar(value="frecuencia_cardiaca")
        selector = ttk.Combobox(lectura_frame, textvariable=self.metrica, state="readonly", width=27, values=list(self.service.umbrales))
        selector.grid(row=0, column=1, padx=7, sticky="w")
        selector.bind("<<ComboboxSelected>>", self._actualizar_unidad)
        ttk.Label(lectura_frame, text="Valor:").grid(row=0, column=2, padx=(10, 0))
        self.valor = ttk.Entry(lectura_frame, width=12)
        self.valor.insert(0, "125")
        self.valor.grid(row=0, column=3, padx=7)
        self.unidad = ttk.Label(lectura_frame, text="lpm")
        self.unidad.grid(row=0, column=4, sticky="w")
        ttk.Button(lectura_frame, text="Registrar valor", command=self.registrar_valor).grid(row=0, column=5, padx=(12, 4))
        ttk.Button(lectura_frame, text="Simular sensor", command=self.simular).grid(row=0, column=6, padx=4)
        self.resultado = ttk.Label(lectura_frame, text="Umbral normal: 50–110 lpm")
        self.resultado.grid(row=1, column=0, columnspan=7, sticky="w", pady=(8, 0))

        listas = ttk.Frame(contenedor)
        listas.pack(fill="both", expand=True)
        lecturas_frame = ttk.LabelFrame(listas, text="Lecturas registradas", padding=8)
        lecturas_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.lecturas = ttk.Treeview(lecturas_frame, columns=("hora", "metrica", "valor", "estado"), show="headings", height=10)
        for col, titulo, ancho in (("hora", "Hora", 90), ("metrica", "Métrica", 170), ("valor", "Valor", 90), ("estado", "Resultado", 110)):
            self.lecturas.heading(col, text=titulo)
            self.lecturas.column(col, width=ancho, anchor="w")
        self.lecturas.pack(fill="both", expand=True)

        alertas_frame = ttk.LabelFrame(listas, text="Alertas detectadas", padding=8)
        alertas_frame.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self.alertas = ttk.Treeview(alertas_frame, columns=("hora", "metrica", "valor", "nivel"), show="headings", height=10)
        for col, titulo, ancho in (("hora", "Hora", 90), ("metrica", "Métrica", 170), ("valor", "Valor", 75), ("nivel", "Severidad", 100)):
            self.alertas.heading(col, text=titulo)
            self.alertas.column(col, width=ancho, anchor="w")
        self.alertas.tag_configure("critica", foreground="#b42318")
        self.alertas.tag_configure("advertencia", foreground="#a15c00")
        self.alertas.pack(fill="both", expand=True)

        pie = ttk.Frame(contenedor)
        pie.pack(fill="x", pady=(10, 0))
        ttk.Label(pie, text="Umbrales de demostración; no son criterios médicos.").pack(side="left")
        self.boton_cerrar = ttk.Button(pie, text="Cerrar sesión", command=self.cerrar_sesion, state="disabled")
        self.boton_cerrar.pack(side="right")

    def _actualizar_unidad(self, _evento=None):
        nombre = self.metrica.get()
        umbral = self.service.umbrales[nombre]
        self.unidad.configure(text=umbral.unidad_medida)
        self.resultado.configure(text=f"Umbral configurado: {umbral.valor_minimo:g}–{umbral.valor_maximo:g} {umbral.unidad_medida}")

    def iniciar_sesion(self):
        if self.sesion and self.sesion.estado == "activa":
            messagebox.showinfo("Sesión activa", "Cierra la sesión actual antes de iniciar otra.")
            return
        residente = self.residente.get().strip()
        dispositivo = self.dispositivo.get().strip()
        if not residente or not dispositivo:
            messagebox.showerror("Faltan datos", "Escribe un ID para el residente y el dispositivo.")
            return
        # IDs de demo estables que cumplen el tipo UUID del dominio.
        residente_id = uuid5(NAMESPACE_URL, f"demo:residente:{residente}")
        dispositivo_id = uuid5(NAMESPACE_URL, f"demo:dispositivo:{dispositivo}")
        self.sesion = self.service.iniciar_sesion(residente_id, dispositivo_id)
        self.estado.configure(text=f"Sesión activa: {self.sesion.session_id}")
        self.boton_sesion.configure(state="disabled")
        self.boton_cerrar.configure(state="normal")

    def _registrar(self, numero):
        if not self.sesion or self.sesion.estado != "activa":
            messagebox.showwarning("Inicia una sesión", "Primero inicia la sesión de monitoreo.")
            return
        nombre = self.metrica.get()
        umbral = self.service.umbrales[nombre]
        lectura = LecturaMetrica(numero, umbral.unidad_medida, datetime.now(timezone.utc))
        try:
            _, evento = asyncio.run(self.service.procesar_lectura(self.sesion.session_id, nombre, lectura))
        except ValueError as exc:
            messagebox.showerror("Lectura inválida", str(exc))
            return
        estado = f"ALERTA {evento.severidad}" if evento else "Normal"
        self.lecturas.insert("", "end", values=(lectura.timestamp.strftime("%H:%M:%S"), nombre, f"{numero:g} {lectura.unidad_medida}", estado))
        self.resultado.configure(text=f"Lectura {estado.lower()}: {numero:g} {lectura.unidad_medida}")
        if evento:
            self.alertas.insert("", "end", values=(evento.ocurrido_en.strftime("%H:%M:%S"), nombre, f"{numero:g} {lectura.unidad_medida}", evento.severidad), tags=(evento.severidad,))

    def registrar_valor(self):
        try:
            numero = float(self.valor.get())
        except ValueError:
            messagebox.showerror("Valor inválido", "Escribe un número, por ejemplo 72 o 125.5.")
            return
        self._registrar(numero)

    def simular(self):
        nombre = self.metrica.get()
        self._registrar(SimuladorSensores.generar_lectura(nombre))

    def cerrar_sesion(self):
        if self.sesion:
            self.service.cerrar_sesion(self.sesion.session_id)
            self.estado.configure(text=f"Sesión cerrada: {self.sesion.session_id}")
            self.boton_cerrar.configure(state="disabled")
            self.boton_sesion.configure(state="normal")


if __name__ == "__main__":
    Aplicacion().mainloop()
