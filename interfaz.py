"""Interfaz gráfica local para probar el flujo de monitorización."""

import tkinter as tk
from datetime import datetime, timezone
from tkinter import messagebox, ttk
from uuid import UUID

import httpx

from cliente_api import ClienteApi


class Aplicacion(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Monitor de residencia — demostración")
        self.geometry("900x620")
        self.minsize(760, 520)
        self.api = ClienteApi()
        self.umbrales = {}
        self.sesion = None
        self.apis_disponibles = False
        self._crear_interfaz()
        self.after(100, self._cargar_umbrales)

    def _crear_interfaz(self):
        contenedor = ttk.Frame(self, padding=18)
        contenedor.pack(fill="both", expand=True)
        ttk.Label(contenedor, text="Monitorización de residentes", font=("Segoe UI", 19, "bold")).pack(anchor="w")
        ttk.Label(contenedor, text="Cliente de las APIs de monitorización y alertas.").pack(anchor="w", pady=(2, 14))

        sesion_frame = ttk.LabelFrame(contenedor, text="1. Sesión de monitoreo", padding=10)
        sesion_frame.pack(fill="x")
        ttk.Label(sesion_frame, text="ID del residente:").grid(row=0, column=0, sticky="w")
        self.residente = ttk.Entry(sesion_frame, width=39)
        self.residente.insert(0, "11111111-1111-4111-8111-111111111111")
        self.residente.grid(row=0, column=1, padx=8, pady=4, sticky="w")
        ttk.Label(sesion_frame, text="ID del dispositivo:").grid(row=1, column=0, sticky="w")
        self.dispositivo = ttk.Entry(sesion_frame, width=39)
        self.dispositivo.insert(0, "22222222-2222-4222-8222-222222222222")
        self.dispositivo.grid(row=1, column=1, padx=8, pady=4, sticky="w")
        self.boton_sesion = ttk.Button(sesion_frame, text="Iniciar sesión", command=self.iniciar_sesion)
        self.boton_sesion.grid(row=0, column=2, rowspan=2, padx=10)
        self.estado = ttk.Label(sesion_frame, text="Sin sesión activa")
        self.estado.grid(row=2, column=0, columnspan=3, sticky="w", pady=(5, 0))

        lectura_frame = ttk.LabelFrame(contenedor, text="2. Registrar lectura", padding=10)
        lectura_frame.pack(fill="x", pady=12)
        ttk.Label(lectura_frame, text="Métrica:").grid(row=0, column=0, sticky="w")
        self.metrica = tk.StringVar(value="frecuencia_cardiaca")
        selector = ttk.Combobox(lectura_frame, textvariable=self.metrica, state="readonly", width=27, values=[])
        selector.grid(row=0, column=1, padx=7, sticky="w")
        selector.bind("<<ComboboxSelected>>", self._actualizar_unidad)
        ttk.Label(lectura_frame, text="Valor:").grid(row=0, column=2, padx=(10, 0))
        self.valor = ttk.Entry(lectura_frame, width=12)
        self.valor.insert(0, "125")
        self.valor.grid(row=0, column=3, padx=7)
        self.unidad = ttk.Label(lectura_frame, text="lpm")
        self.unidad.grid(row=0, column=4, sticky="w")
        self.selector_metrica = selector
        self.boton_registrar = ttk.Button(lectura_frame, text="Registrar valor", command=self.registrar_valor, state="disabled")
        self.boton_registrar.grid(row=0, column=5, padx=(12, 4))
        self.boton_simular = ttk.Button(lectura_frame, text="Simular sensor", command=self.simular, state="disabled")
        self.boton_simular.grid(row=0, column=6, padx=4)
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
        self.estado_apis = ttk.Label(pie, text="Conectando con APIs…")
        self.estado_apis.pack(side="left")
        ttk.Label(pie, text="Umbrales demostrativos; no son criterios médicos.").pack(side="left", padx=12)
        self.boton_cerrar = ttk.Button(pie, text="Cerrar sesión", command=self.cerrar_sesion, state="disabled")
        self.boton_cerrar.pack(side="right")

    def _actualizar_unidad(self, _evento=None):
        nombre = self.metrica.get()
        umbral = self.umbrales.get(nombre)
        if umbral:
            self.unidad.configure(text=umbral["unidad"])
            self.resultado.configure(text=f"Umbral configurado: {umbral['minimo']:g}–{umbral['maximo']:g} {umbral['unidad']}")

    def _cargar_umbrales(self):
        try:
            self.umbrales = self.api.obtener_umbrales()
            nombres = list(self.umbrales)
            self.selector_metrica.configure(values=nombres)
            if nombres and self.metrica.get() not in self.umbrales:
                self.metrica.set(nombres[0])
            self._actualizar_unidad()
            self.apis_disponibles = bool(self.umbrales)
            estado_boton = "normal" if self.apis_disponibles else "disabled"
            self.boton_registrar.configure(state=estado_boton)
            self.boton_simular.configure(state=estado_boton)
            self.estado_apis.configure(text="API de monitorización conectada")
        except httpx.HTTPError:
            self.apis_disponibles = False
            self.boton_registrar.configure(state="disabled")
            self.boton_simular.configure(state="disabled")
            self.estado_apis.configure(text="API no disponible; inicia los dos servicios")
            self.after(5000, self._cargar_umbrales)

    def iniciar_sesion(self):
        if self.sesion:
            messagebox.showinfo("Sesión activa", "Cierra la sesión actual antes de iniciar otra.")
            return
        residente = self.residente.get().strip()
        dispositivo = self.dispositivo.get().strip()
        if not residente or not dispositivo:
            messagebox.showerror("Faltan datos", "Escribe un ID para el residente y el dispositivo.")
            return
        try:
            data = self.api.iniciar_sesion(str(UUID(residente)), str(UUID(dispositivo)))
            self.sesion = data["session_id"]
            self.estado.configure(text=f"Sesión activa: {self.sesion}")
            self.boton_sesion.configure(state="disabled")
            self.boton_cerrar.configure(state="normal")
        except ValueError:
            messagebox.showerror("UUID inválido", "Los IDs deben ser UUID válidos. Puedes generar uno con uuidgen.")
        except httpx.HTTPError as exc:
            messagebox.showerror("API no disponible", f"No se pudo iniciar la sesión: {exc}")

    def _registrar(self, numero):
        if not self.apis_disponibles or not self.umbrales:
            messagebox.showerror("API no disponible", "No se pudieron cargar los umbrales. Comprueba que monitorización esté activa en http://localhost:8000 y vuelve a abrir la interfaz.")
            return
        if not self.sesion:
            messagebox.showwarning("Inicia una sesión", "Primero inicia la sesión de monitoreo.")
            return
        nombre = self.metrica.get()
        try:
            unidad = self.umbrales[nombre]["unidad"]
            data = self.api.registrar_lectura(self.sesion, nombre, numero, unidad, datetime.now(timezone.utc))
        except (httpx.HTTPError, KeyError) as exc:
            messagebox.showerror("Error al registrar", f"No se pudo registrar la lectura: {exc}")
            return
        estado = f"ALERTA {data['severidad']}" if data["anomalia"] else "Normal"
        self.lecturas.insert("", "end", values=(datetime.now().strftime("%H:%M:%S"), nombre, f"{numero:g} {unidad}", estado))
        self.resultado.configure(text=f"Lectura {estado.lower()}: {numero:g} {unidad}")
        self._actualizar_alertas()

    def _actualizar_alertas(self):
        try:
            alertas = self.api.listar_alertas()
            self.alertas.delete(*self.alertas.get_children())
            for evento in alertas:
                self.alertas.insert("", "end", values=(evento["ocurrido_en"].split("T")[-1][:8], evento["metrica"], f"{evento['valor_registrado']:g} {evento['unidad_medida']}", evento["severidad"]), tags=(evento["severidad"],))
        except httpx.HTTPError as exc:
            messagebox.showerror("API de alertas", f"No se pudieron consultar las alertas: {exc}")

    def registrar_valor(self):
        try:
            numero = float(self.valor.get())
        except ValueError:
            messagebox.showerror("Valor inválido", "Escribe un número, por ejemplo 72 o 125.5.")
            return
        self._registrar(numero)

    def simular(self):
        nombre = self.metrica.get()
        if not self.apis_disponibles or nombre not in self.umbrales:
            messagebox.showerror("API no disponible", "No se pudieron cargar los umbrales. Comprueba que monitorización esté activa en http://localhost:8000 y vuelve a abrir la interfaz.")
            return
        if not self.sesion:
            messagebox.showwarning("Inicia una sesión", "Primero inicia la sesión de monitoreo.")
            return
        try:
            data = self.api.simular_lectura(self.sesion, nombre)
            unidad = self.umbrales[nombre]["unidad"]
            estado = f"ALERTA {data['severidad']}" if data["anomalia"] else "Normal"
            self.lecturas.insert("", "end", values=(datetime.now().strftime("%H:%M:%S"), nombre, f"{data['valor']:g} {unidad}", estado))
            self.resultado.configure(text=f"Lectura {estado.lower()}: {data['valor']:g} {unidad}")
            self._actualizar_alertas()
        except httpx.HTTPError as exc:
            messagebox.showerror("Error al simular", f"No se pudo consultar la API: {exc}")

    def cerrar_sesion(self):
        if self.sesion:
            try:
                self.api.cerrar_sesion(self.sesion)
            except httpx.HTTPError as exc:
                messagebox.showerror("Error", f"No se pudo cerrar la sesión: {exc}")
                return
            self.estado.configure(text=f"Sesión cerrada: {self.sesion}")
            self.sesion = None
            self.boton_cerrar.configure(state="disabled")
            self.boton_sesion.configure(state="normal")


if __name__ == "__main__":
    Aplicacion().mainloop()
