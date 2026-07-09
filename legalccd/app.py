"""
LegalCCD — Interfaz gráfica principal
Sistema de Cadena de Custodia de Vestigios Digitales
v0.2 · Python + CustomTkinter

Requisitos:
    pip install customtkinter
"""

import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk

import customtkinter as ctk

from legalccd.hashing import calcular_hash_archivo, calcular_hash_texto, ALGORITMOS
from legalccd.registro import Registro, guardar_reporte, generar_reporte_txt
from legalccd.cardano import registrar_en_cardano, verificar_txid

# ─── Apariencia ────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

COLOR_HEADER     = "#0C2340"
COLOR_ACENTO     = "#1E90D4"
COLOR_FONDO      = "#F4F6FA"
COLOR_TARJETA    = "#FFFFFF"
COLOR_BORDE      = "#D0D7E3"
COLOR_TEXTO      = "#0C2340"
COLOR_APAGADO    = "#6B7FA3"
COLOR_EXITO      = "#0B7A4F"
COLOR_ALERTA     = "#92400E"

FUENTE_TITULO    = ("Segoe UI", 13, "bold")
FUENTE_LABEL     = ("Segoe UI", 11, "bold")
FUENTE_NORMAL    = ("Segoe UI", 11)
FUENTE_MONO      = ("Courier New", 10)
FUENTE_PEQUEÑA   = ("Segoe UI", 10)


# ─── Ventana principal ─────────────────────────────────────────────────────────
class AppLegalCCD(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("LegalCCD — Cadena de Custodia Digital  v0.2")
        self.geometry("900x780")
        self.minsize(820, 700)
        self.configure(fg_color=COLOR_FONDO)

        self._archivo_ruta: Path | None = None
        self._hashes_calculados: dict = {}
        self._historial: list[Registro] = []
        self._registro_actual: Registro | None = None

        self._construir_cabecera()
        self._construir_tabs()

    # ── Cabecera ───────────────────────────────────────────────────────────────
    def _construir_cabecera(self):
        cab = ctk.CTkFrame(self, fg_color=COLOR_HEADER, corner_radius=0, height=56)
        cab.pack(fill="x")
        cab.pack_propagate(False)

        ctk.CTkLabel(
            cab,
            text="⬡  LegalCCD",
            font=("Segoe UI", 16, "bold"),
            text_color="white",
        ).pack(side="left", padx=20, pady=12)

        ctk.CTkLabel(
            cab,
            text="Sistema de Cadena de Custodia de Vestigios Digitales  ·  v0.2 Prototipo",
            font=("Segoe UI", 10),
            text_color="#8AADC4",
        ).pack(side="left", padx=4)

        self._lbl_estado_red = ctk.CTkLabel(
            cab,
            text="Comprobando red…",
            font=("Segoe UI", 10),
            text_color="#F59E0B",
        )
        self._lbl_estado_red.pack(side="right", padx=20)
        # Comprobación inicial en segundo plano y refresco periódico.
        self._actualizar_estado_red()

    def _actualizar_estado_red(self):
        """Consulta el estado de conexión sin bloquear la interfaz."""
        import threading

        def _worker():
            try:
                from legalccd.cardano import estado_conexion
                conectado, mensaje = estado_conexion()
            except Exception as e:  # noqa: BLE001
                conectado, mensaje = False, f"Sin conexión ({type(e).__name__})"
            color = "#16A34A" if conectado else "#F59E0B"
            # Volcado seguro al hilo de la GUI.
            self.after(0, lambda: self._lbl_estado_red.configure(text=mensaje, text_color=color))

        threading.Thread(target=_worker, daemon=True).start()
        # Reintento periódico cada 30 s.
        self.after(30_000, self._actualizar_estado_red)

    # ── Pestañas ───────────────────────────────────────────────────────────────
    def _construir_tabs(self):
        self._tabs = ctk.CTkTabview(self, fg_color=COLOR_FONDO, segmented_button_fg_color=COLOR_HEADER)
        self._tabs.pack(fill="both", expand=True, padx=16, pady=12)

        self._tabs.add("📋  Registrar vestigio")
        self._tabs.add("📄  Resumen del registro")
        self._tabs.add("🔍  Verificar TxID")
        self._tabs.add("🗂  Historial de sesión")

        self._tab_entrada    = self._tabs.tab("📋  Registrar vestigio")
        self._tab_resumen    = self._tabs.tab("📄  Resumen del registro")
        self._tab_verificar  = self._tabs.tab("🔍  Verificar TxID")
        self._tab_historial  = self._tabs.tab("🗂  Historial de sesión")

        self._construir_tab_entrada()
        self._construir_tab_resumen()
        self._construir_tab_verificar()
        self._construir_tab_historial()

    # ══════════════════════════════════════════════════════════════════
    #  TAB 1 — ENTRADA
    # ══════════════════════════════════════════════════════════════════
    def _construir_tab_entrada(self):
        p = self._tab_entrada
        scroll = ctk.CTkScrollableFrame(p, fg_color=COLOR_FONDO)
        scroll.pack(fill="both", expand=True)

        # Aviso privacidad
        aviso = ctk.CTkFrame(scroll, fg_color="#FEF3C7", corner_radius=8)
        aviso.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            aviso,
            text="🔒  Los datos personales de este formulario se guardan SOLO en el reporte local. "
                 "La blockchain recibirá únicamente hashes e identificadores, sin datos personales.",
            font=FUENTE_PEQUEÑA,
            text_color=COLOR_ALERTA,
            wraplength=780,
            justify="left",
        ).pack(padx=12, pady=8)

        # ── Sección: Caso ──────────────────────────────────────────────
        self._seccion(scroll, "Datos del caso")
        f1 = self._fila(scroll)
        self._num_caso     = self._campo(f1, "Número de caso *", "Ej: 2024/UDYCO/00312")
        self._fecha_acto   = self._campo(f1, "Fecha del acto", datetime.today().strftime("%d/%m/%Y"))
        f2 = self._fila(scroll)
        self._hora_acto    = self._campo(f2, "Hora del acto", datetime.now().strftime("%H:%M"))
        self._desc_caso    = self._campo(f2, "Descripción del caso", "Breve descripción de la diligencia")

        # ── Sección: Vestigio ──────────────────────────────────────────
        self._seccion(scroll, "Vestigio digital")
        f3 = self._fila(scroll)
        self._id_vestigio  = self._campo(f3, "Identificador del vestigio *", "Ej: VD-001-2024")
        self._tipo_options = [
            "— Seleccionar tipo —", "Documento electrónico", "Imagen digital",
            "Audio", "Vídeo", "Base de datos", "Correo electrónico",
            "Registro de sistema", "Volcado de memoria", "Captura de pantalla",
            "Texto libre / oficio", "Otro",
        ]
        tipo_var = ctk.StringVar(value=self._tipo_options[0])
        self._tipo_vestigio_var = tipo_var
        tipo_frame = ctk.CTkFrame(f3, fg_color="transparent")
        tipo_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ctk.CTkLabel(tipo_frame, text="Tipo de vestigio", font=FUENTE_LABEL, text_color=COLOR_APAGADO).pack(anchor="w")
        ctk.CTkOptionMenu(tipo_frame, values=self._tipo_options, variable=tipo_var,
                          fg_color="white", button_color=COLOR_ACENTO,
                          text_color=COLOR_TEXTO).pack(fill="x", pady=(2, 0))

        f4 = self._fila(scroll)
        self._desc_vestigio = self._campo(f4, "Descripción del vestigio",
                                          "Ej: Oficio de intervención de efectos de fecha 12/05/2024", ancho=True)

        # ── Sección: Actuante ──────────────────────────────────────────
        self._seccion(scroll, "Datos del actuante")
        f5 = self._fila(scroll)
        self._nombre_actuante = self._campo(f5, "Nombre y apellidos *", "Nombre completo")
        self._id_profesional  = self._campo(f5, "Identificador profesional", "TIP, placa, ID empleado…")
        f6 = self._fila(scroll)
        roles = ["— Seleccionar rol —", "Analista forense", "Técnico forense",
                 "Investigador", "Instructor del procedimiento", "Agente judicial",
                 "Perito designado", "Otro"]
        rol_var = ctk.StringVar(value=roles[0])
        self._rol_var = rol_var
        rol_frame = ctk.CTkFrame(f6, fg_color="transparent")
        rol_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ctk.CTkLabel(rol_frame, text="Rol", font=FUENTE_LABEL, text_color=COLOR_APAGADO).pack(anchor="w")
        ctk.CTkOptionMenu(rol_frame, values=roles, variable=rol_var,
                          fg_color="white", button_color=COLOR_ACENTO,
                          text_color=COLOR_TEXTO).pack(fill="x", pady=(2, 0))
        self._num_control = self._campo(f6, "Número de control", "Para seguimiento interno")

        # ── Sección: Contenido ─────────────────────────────────────────
        self._seccion(scroll, "Contenido a registrar")

        # Modo de entrada
        modo_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        modo_frame.pack(fill="x", pady=(0, 8))
        self._modo_var = ctk.StringVar(value="archivo")
        for val, txt in [("archivo", "📁  Subir archivo"), ("texto", "✏️  Texto libre"), ("hash", "🔢  Introducir hash")]:
            ctk.CTkRadioButton(
                modo_frame, text=txt, value=val, variable=self._modo_var,
                command=self._cambiar_modo, font=FUENTE_NORMAL,
                text_color=COLOR_TEXTO, fg_color=COLOR_ACENTO,
            ).pack(side="left", padx=(0, 16))

        # Panel archivo
        self._panel_archivo = ctk.CTkFrame(scroll, fg_color=COLOR_TARJETA, corner_radius=8,
                                            border_width=1, border_color=COLOR_BORDE)
        self._panel_archivo.pack(fill="x", pady=(0, 6))
        self._btn_seleccionar = ctk.CTkButton(
            self._panel_archivo, text="📂  Seleccionar archivo…",
            command=self._seleccionar_archivo,
            fg_color=COLOR_ACENTO, hover_color="#1565C0",
        )
        self._btn_seleccionar.pack(side="left", padx=12, pady=10)
        self._lbl_archivo = ctk.CTkLabel(
            self._panel_archivo,
            text="Ningún archivo seleccionado",
            font=FUENTE_PEQUEÑA, text_color=COLOR_APAGADO,
        )
        self._lbl_archivo.pack(side="left", padx=8)

        # Panel texto
        self._panel_texto = ctk.CTkFrame(scroll, fg_color="transparent")
        ctk.CTkLabel(self._panel_texto, text="Texto a registrar", font=FUENTE_LABEL,
                     text_color=COLOR_APAGADO).pack(anchor="w")
        self._txt_libre = ctk.CTkTextbox(self._panel_texto, height=90, font=FUENTE_NORMAL,
                                          fg_color=COLOR_TARJETA, border_color=COLOR_BORDE, border_width=1)
        self._txt_libre.pack(fill="x")
        self._txt_libre.insert("0.0", "Ej: Oficio de intervención de efectos de fecha 12/05/2024…")

        # Panel hash manual
        self._panel_hash = ctk.CTkFrame(scroll, fg_color="transparent")
        fh1 = self._fila(self._panel_hash)
        self._hash_manual   = self._campo(fh1, "Valor del hash (calculado externamente)",
                                          "Ej: 84d89877f0d4041efb6bf91a16f0248f2fd573e6…", ancho=True)
        fh2 = self._fila(self._panel_hash)
        self._origen_hash   = self._campo(fh2, "Origen del hash",
                                          "Ej: hola.txt — sha256sum Ubuntu 22.04", ancho=True)

        self._cambiar_modo()  # muestra solo el panel activo

        # ── Algoritmos ─────────────────────────────────────────────────
        self._seccion(scroll, "Algoritmos de hash")
        algo_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        algo_frame.pack(fill="x", pady=(0, 4))
        self._algo_vars = {}
        for i, algo in enumerate(["SHA-256", "MD5", "SHA-1", "SHA-512"]):
            var = ctk.BooleanVar(value=(algo == "SHA-256"))
            self._algo_vars[algo] = var
            ctk.CTkCheckBox(
                algo_frame, text=algo, variable=var,
                font=FUENTE_NORMAL, text_color=COLOR_TEXTO,
                fg_color=COLOR_ACENTO, hover_color="#1565C0",
            ).pack(side="left", padx=(0, 20))

        ctk.CTkLabel(scroll,
            text="⚠  MD5 y SHA-1 tienen vulnerabilidades conocidas. Para cadena de custodia judicial, "
                 "use SHA-256. Se incluyen por compatibilidad con sistemas heredados.",
            font=FUENTE_PEQUEÑA, text_color=COLOR_ALERTA, wraplength=760, justify="left",
        ).pack(anchor="w", pady=(0, 8))

        # ── Resultado hash ─────────────────────────────────────────────
        self._seccion(scroll, "Resultado del hash")
        self._txt_hash = ctk.CTkTextbox(scroll, height=80, font=FUENTE_MONO,
                                         fg_color="#F0F4F8", border_color=COLOR_BORDE, border_width=1,
                                         state="disabled", text_color=COLOR_TEXTO)
        self._txt_hash.pack(fill="x", pady=(0, 6))

        self._lbl_progreso = ctk.CTkLabel(scroll, text="", font=FUENTE_PEQUEÑA, text_color=COLOR_ACENTO)
        self._lbl_progreso.pack(anchor="w")

        # ── Otros datos ────────────────────────────────────────────────
        self._seccion(scroll, "Otros datos / Observaciones")
        ctk.CTkLabel(scroll,
            text="Este campo se incluye en el reporte local. No se envía a la blockchain.",
            font=FUENTE_PEQUEÑA, text_color=COLOR_APAGADO,
        ).pack(anchor="w", pady=(0, 4))
        self._txt_otros = ctk.CTkTextbox(scroll, height=80, font=FUENTE_NORMAL,
                                          fg_color=COLOR_TARJETA, border_color=COLOR_BORDE, border_width=1)
        self._txt_otros.pack(fill="x", pady=(0, 10))

        # ── Botones ────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(4, 16))

        ctk.CTkButton(
            btn_frame, text="🔐  Calcular y registrar",
            command=self._calcular_y_registrar,
            fg_color=COLOR_HEADER, hover_color="#1A3D6B",
            font=("Segoe UI", 12, "bold"), height=40,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame, text="🔄  Limpiar",
            command=self._limpiar,
            fg_color="transparent", border_width=1,
            border_color=COLOR_ACENTO, text_color=COLOR_ACENTO,
            hover_color="#EBF4FC",
        ).pack(side="left")

        # Nota Cardano (el envío se realiza desde la pestaña Resumen)
        card_frame = ctk.CTkFrame(scroll, fg_color="#F0F4F8", corner_radius=8,
                                   border_width=1, border_color=COLOR_BORDE)
        card_frame.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(card_frame,
            text="🔗  Registro en Cardano",
            font=FUENTE_LABEL, text_color=COLOR_APAGADO,
        ).pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(card_frame,
            text="Tras calcular el hash, desde la pestaña Resumen podrás anclar el registro "
                 "como metadato nativo en la red Cardano y obtener un TxID verificable "
                 "públicamente. Solo se transmitirán: ID de registro, ID de vestigio, "
                 "hashes y timestamp.",
            font=FUENTE_PEQUEÑA, text_color=COLOR_APAGADO, wraplength=760, justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 8))

    # ══════════════════════════════════════════════════════════════════
    #  TAB 2 — RESUMEN
    # ══════════════════════════════════════════════════════════════════
    def _construir_tab_resumen(self):
        p = self._tab_resumen
        self._frame_resumen_vacio = ctk.CTkFrame(p, fg_color="transparent")
        self._frame_resumen_vacio.pack(expand=True)
        ctk.CTkLabel(
            self._frame_resumen_vacio,
            text="📋\n\nAún no hay ningún registro activo.\nCompleta el formulario y pulsa Calcular y registrar.",
            font=FUENTE_NORMAL, text_color=COLOR_APAGADO, justify="center",
        ).pack(pady=60)

        self._frame_resumen_contenido = ctk.CTkScrollableFrame(p, fg_color=COLOR_FONDO)

        # Los widgets de resumen se construyen dinámicamente en _mostrar_resumen()
        self._txt_resumen = ctk.CTkTextbox(
            self._frame_resumen_contenido,
            font=FUENTE_MONO, fg_color=COLOR_TARJETA,
            border_color=COLOR_BORDE, border_width=1,
            state="disabled", text_color=COLOR_TEXTO,
            wrap="none",
        )
        self._txt_resumen.pack(fill="both", expand=True, pady=(0, 10))

        btn_frame = ctk.CTkFrame(self._frame_resumen_contenido, fg_color="transparent")
        btn_frame.pack(fill="x")

        ctk.CTkButton(
            btn_frame, text="💾  Exportar reporte .txt",
            command=self._exportar_txt,
            fg_color=COLOR_EXITO, hover_color="#065F46",
            font=("Segoe UI", 12, "bold"),
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame, text="📌  Guardar en historial",
            command=self._guardar_historial,
            fg_color="transparent", border_width=1,
            border_color=COLOR_ACENTO, text_color=COLOR_ACENTO,
            hover_color="#EBF4FC",
        ).pack(side="left")

        # ── Panel Cardano ──────────────────────────────────────────────
        panel_cardano = ctk.CTkFrame(self._frame_resumen_contenido,
                                     fg_color=COLOR_TARJETA, corner_radius=8,
                                     border_width=1, border_color=COLOR_BORDE)
        panel_cardano.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(panel_cardano, text="🔗  Anclaje en Cardano",
                     font=FUENTE_LABEL, text_color=COLOR_TEXTO,
                     ).pack(anchor="w", padx=12, pady=(10, 2))

        fila_cardano = ctk.CTkFrame(panel_cardano, fg_color="transparent")
        fila_cardano.pack(fill="x", padx=12, pady=(0, 4))
        self._btn_cardano = ctk.CTkButton(
            fila_cardano, text="🔗  Registrar en Cardano",
            command=self._registrar_cardano,
            fg_color=COLOR_ACENTO, hover_color="#1565C0",
            font=("Segoe UI", 12, "bold"),
        )
        self._btn_cardano.pack(side="left", padx=(0, 10))
        self._btn_copiar_txid = ctk.CTkButton(
            fila_cardano, text="📋  Copiar TxID", width=110,
            command=self._copiar_txid, state="disabled",
            fg_color="transparent", border_width=1,
            border_color=COLOR_ACENTO, text_color=COLOR_ACENTO,
            hover_color="#EBF4FC",
        )
        self._btn_copiar_txid.pack(side="left")

        self._lbl_cardano = ctk.CTkLabel(
            panel_cardano, text="Sin registrar en la red.",
            font=FUENTE_PEQUEÑA, text_color=COLOR_APAGADO,
            wraplength=760, justify="left",
        )
        self._lbl_cardano.pack(anchor="w", padx=12, pady=(0, 10))

    # ══════════════════════════════════════════════════════════════════
    #  TAB 3 — HISTORIAL
    # ══════════════════════════════════════════════════════════════════
    def _construir_tab_historial(self):
        p = self._tab_historial
        cabecera = ctk.CTkFrame(p, fg_color="transparent")
        cabecera.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(cabecera, text="Registros de esta sesión",
                     font=FUENTE_TITULO, text_color=COLOR_TEXTO).pack(side="left")
        ctk.CTkButton(
            cabecera, text="⬇  Exportar todo",
            command=self._exportar_historial,
            fg_color="transparent", border_width=1,
            border_color=COLOR_ACENTO, text_color=COLOR_ACENTO,
            hover_color="#EBF4FC", width=120,
        ).pack(side="right")

        ctk.CTkLabel(p,
            text="Los registros se eliminan al cerrar la aplicación. No se persiste ningún dato fuera del reporte exportado.",
            font=FUENTE_PEQUEÑA, text_color=COLOR_APAGADO,
        ).pack(anchor="w", pady=(0, 8))

        self._frame_historial = ctk.CTkScrollableFrame(p, fg_color=COLOR_FONDO)
        self._frame_historial.pack(fill="both", expand=True)

        self._lbl_hist_vacio = ctk.CTkLabel(
            self._frame_historial,
            text="El historial está vacío.",
            font=FUENTE_NORMAL, text_color=COLOR_APAGADO,
        )
        self._lbl_hist_vacio.pack(pady=40)

    # ══════════════════════════════════════════════════════════════════
    #  HELPERS DE CONSTRUCCIÓN UI
    # ══════════════════════════════════════════════════════════════════
    def _seccion(self, parent, texto):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", pady=(10, 4))
        ctk.CTkLabel(f, text=texto,
                     font=FUENTE_TITULO, text_color=COLOR_TEXTO).pack(side="left")
        sep = ctk.CTkFrame(f, fg_color=COLOR_BORDE, height=1)
        sep.pack(side="left", fill="x", expand=True, padx=(10, 0), pady=6)

    def _fila(self, parent):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", pady=(0, 6))
        return f

    def _campo(self, parent, label, placeholder="", ancho=False):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        if ancho:
            f.pack(fill="x", expand=True)
        else:
            f.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ctk.CTkLabel(f, text=label, font=FUENTE_LABEL, text_color=COLOR_APAGADO).pack(anchor="w")
        entry = ctk.CTkEntry(f, placeholder_text=placeholder, font=FUENTE_NORMAL,
                             fg_color=COLOR_TARJETA, border_color=COLOR_BORDE,
                             text_color=COLOR_TEXTO)
        entry.pack(fill="x", pady=(2, 0))
        return entry

    # ══════════════════════════════════════════════════════════════════
    #  LÓGICA DE MODO DE ENTRADA
    # ══════════════════════════════════════════════════════════════════
    def _cambiar_modo(self):
        modo = self._modo_var.get()
        self._panel_archivo.pack_forget()
        self._panel_texto.pack_forget()
        self._panel_hash.pack_forget()
        if modo == "archivo":
            self._panel_archivo.pack(fill="x", pady=(0, 6))
        elif modo == "texto":
            self._panel_texto.pack(fill="x", pady=(0, 6))
        else:
            self._panel_hash.pack(fill="x", pady=(0, 6))

    def _seleccionar_archivo(self):
        ruta = filedialog.askopenfilename(title="Seleccionar vestigio digital")
        if ruta:
            self._archivo_ruta = Path(ruta)
            nombre = self._archivo_ruta.name
            tam = self._archivo_ruta.stat().st_size
            tam_fmt = (f"{tam} bytes" if tam < 1024 else
                       f"{tam/1024:.1f} KB" if tam < 1_048_576 else
                       f"{tam/1_048_576:.2f} MB")
            self._lbl_archivo.configure(
                text=f"{nombre}  ·  {tam_fmt}",
                text_color=COLOR_TEXTO,
            )

    # ══════════════════════════════════════════════════════════════════
    #  CALCULAR Y REGISTRAR
    # ══════════════════════════════════════════════════════════════════
    def _calcular_y_registrar(self):
        # Validaciones básicas
        if not self._num_caso.get().strip():
            messagebox.showerror("Campo requerido", "El número de caso es obligatorio.")
            return
        if not self._id_vestigio.get().strip():
            messagebox.showerror("Campo requerido", "El identificador del vestigio es obligatorio.")
            return
        if not self._nombre_actuante.get().strip():
            messagebox.showerror("Campo requerido", "El nombre del actuante es obligatorio.")
            return

        algos = [a for a, v in self._algo_vars.items() if v.get()]
        if not algos:
            messagebox.showerror("Sin algoritmo", "Selecciona al menos un algoritmo de hash.")
            return

        modo = self._modo_var.get()

        if modo == "hash":
            hm = self._hash_manual.get().strip()
            if not hm:
                messagebox.showerror("Campo requerido", "Introduce el valor del hash.")
                return
            self._hashes_calculados = {"Manual": hm}
            self._finalizar_registro()
            return

        # Calcular en hilo para no bloquear la UI
        self._lbl_progreso.configure(text="⏳  Calculando hash…")
        self._btn_seleccionar.configure(state="disabled")

        def tarea():
            if modo == "archivo":
                if not self._archivo_ruta:
                    self.after(0, lambda: messagebox.showerror("Sin archivo", "Selecciona un archivo."))
                    self.after(0, lambda: self._lbl_progreso.configure(text=""))
                    return
                res = calcular_hash_archivo(
                    self._archivo_ruta, algos,
                    callback_progreso=lambda b, t: self.after(0, lambda b=b, t=t:
                        self._lbl_progreso.configure(text=f"⏳  {b/t*100:.0f}%  leyendo archivo…")
                    )
                )
                if res["error"]:
                    self.after(0, lambda: messagebox.showerror("Error", res["error"]))
                    self.after(0, lambda: self._lbl_progreso.configure(text=""))
                    return
                self._hashes_calculados = res["hashes"]
            else:
                texto = self._txt_libre.get("0.0", "end").strip()
                if not texto:
                    self.after(0, lambda: messagebox.showerror("Sin contenido", "Introduce el texto a registrar."))
                    self.after(0, lambda: self._lbl_progreso.configure(text=""))
                    return
                res = calcular_hash_texto(texto, algos)
                if res["error"]:
                    self.after(0, lambda: messagebox.showerror("Error", res["error"]))
                    return
                self._hashes_calculados = res["hashes"]

            self.after(0, self._finalizar_registro)

        threading.Thread(target=tarea, daemon=True).start()

    def _finalizar_registro(self):
        self._lbl_progreso.configure(text="✅  Hash calculado correctamente")
        self._btn_seleccionar.configure(state="normal")

        # Mostrar en el cuadro de texto
        self._txt_hash.configure(state="normal")
        self._txt_hash.delete("0.0", "end")
        for algo, valor in self._hashes_calculados.items():
            self._txt_hash.insert("end", f"{algo:<10}  {valor}\n")
        self._txt_hash.configure(state="disabled")

        # Construir objeto registro
        modo = self._modo_var.get()
        r = Registro(
            num_caso         = self._num_caso.get().strip(),
            desc_caso        = self._desc_caso.get().strip(),
            fecha_acto       = self._fecha_acto.get().strip(),
            hora_acto        = self._hora_acto.get().strip(),
            id_vestigio      = self._id_vestigio.get().strip(),
            tipo_vestigio    = (self._tipo_vestigio_var.get()
                                if self._tipo_vestigio_var.get() != self._tipo_options[0] else ""),
            desc_vestigio    = self._desc_vestigio.get().strip(),
            nombre_archivo   = (self._archivo_ruta.name if self._archivo_ruta and modo == "archivo" else ""),
            tamaño_archivo   = (self._lbl_archivo.cget("text").split("·")[-1].strip()
                                if self._archivo_ruta and modo == "archivo" else ""),
            tamaño_bytes     = (self._archivo_ruta.stat().st_size
                                if self._archivo_ruta and modo == "archivo" else 0),
            modo_entrada     = {"archivo": "Archivo", "texto": "Texto libre", "hash": "Hash manual"}[modo],
            origen_hash      = (self._origen_hash.get().strip() if modo == "hash" else ""),
            hashes           = self._hashes_calculados,
            nombre_actuante  = self._nombre_actuante.get().strip(),
            id_profesional   = self._id_profesional.get().strip(),
            rol              = (self._rol_var.get() if "—" not in self._rol_var.get() else ""),
            num_control      = self._num_control.get().strip(),
            otros_datos      = self._txt_otros.get("0.0", "end").strip(),
        )
        self._registro_actual = r
        self._mostrar_resumen(r)
        self._tabs.set("📄  Resumen del registro")

    # ══════════════════════════════════════════════════════════════════
    #  RESUMEN
    # ══════════════════════════════════════════════════════════════════
    def _mostrar_resumen(self, r: Registro):
        self._frame_resumen_vacio.pack_forget()
        self._frame_resumen_contenido.pack(fill="both", expand=True)

        texto = generar_reporte_txt(r)
        self._txt_resumen.configure(state="normal")
        self._txt_resumen.delete("0.0", "end")
        self._txt_resumen.insert("0.0", texto)
        self._txt_resumen.configure(state="disabled")

        # Sincronizar panel Cardano con el estado del registro mostrado
        if getattr(self, "_lbl_cardano", None):
            if r.cardano_txid:
                self._lbl_cardano.configure(
                    text=f"✅  {r.cardano_estado.capitalize()} en {r.cardano_red}\n"
                         f"TxID: {r.cardano_txid}",
                    text_color=COLOR_EXITO,
                )
                self._btn_copiar_txid.configure(state="normal")
            else:
                self._lbl_cardano.configure(
                    text="Sin registrar en la red.", text_color=COLOR_APAGADO)
                self._btn_copiar_txid.configure(state="disabled")

    def _exportar_txt(self):
        if not self._registro_actual:
            return
        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=f"LegalCCD_{self._registro_actual.id_registro}.txt",
            filetypes=[("Archivo de texto", "*.txt")],
            title="Guardar reporte",
        )
        if ruta:
            Path(ruta).write_text(generar_reporte_txt(self._registro_actual), encoding="utf-8")
            messagebox.showinfo("Exportado", f"Reporte guardado en:\n{ruta}")

    def _guardar_historial(self):
        if not self._registro_actual:
            return
        self._historial.append(self._registro_actual)
        self._actualizar_historial()
        try:
            ruta = guardar_reporte(self._registro_actual)
            messagebox.showinfo(
                "Guardado",
                f"Registro añadido al historial de sesión.\n"
                f"Reporte autoguardado en:\n{ruta}")
        except OSError as e:
            messagebox.showwarning(
                "Guardado",
                f"Registro añadido al historial, pero no se pudo "
                f"autoguardar el reporte:\n{e}")

    # ══════════════════════════════════════════════════════════════════
    #  CARDANO — registro desde la GUI
    # ══════════════════════════════════════════════════════════════════
    def _registrar_cardano(self):
        if not self._registro_actual:
            messagebox.showinfo("Sin registro", "Primero calcula el hash de un vestigio.")
            return
        if self._registro_actual.cardano_txid:
            messagebox.showinfo(
                "Ya registrado",
                f"Este registro ya tiene TxID:\n{self._registro_actual.cardano_txid}",
            )
            return

        r = self._registro_actual
        self._btn_cardano.configure(state="disabled")
        self._lbl_cardano.configure(
            text="⏳  Construyendo y enviando transacción… "
                 "(la confirmación puede tardar hasta ~2 min)",
            text_color=COLOR_APAGADO,
        )

        def tarea():
            payload = r.payload_blockchain()
            res = registrar_en_cardano(payload, esperar_confirmacion=True)

            def actualizar():
                self._btn_cardano.configure(state="normal")
                if not res.exito:
                    self._lbl_cardano.configure(
                        text=f"❌  {res.mensaje}", text_color=COLOR_ALERTA)
                    r.cardano_estado = "error"
                    return
                r.cardano_txid = res.txid
                r.cardano_red = res.red
                r.cardano_estado = ("confirmada" if res.bloque
                                    else "enviada (sin confirmar)")
                bloque_txt = f" · bloque {res.bloque}" if res.bloque else ""
                fee_txt = (f" · fee {res.fee_lovelace/1e6:.4f} ADA"
                           if res.fee_lovelace else "")
                self._lbl_cardano.configure(
                    text=f"✅  {r.cardano_estado.capitalize()} en {res.red}"
                         f"{bloque_txt}{fee_txt}\nTxID: {res.txid}\n"
                         f"Verificación pública: https://"
                         f"{'preprod.' if res.red == 'preprod' else ('preview.' if res.red == 'preview' else '')}"
                         f"cardanoscan.io/transaction/{res.txid}",
                    text_color=COLOR_EXITO,
                )
                self._btn_copiar_txid.configure(state="normal")
                # refrescar resumen y autoguardar reporte definitivo
                self._mostrar_resumen(r)
                try:
                    ruta = guardar_reporte(r)
                    self._lbl_cardano.configure(
                        text=self._lbl_cardano.cget("text")
                             + f"\n💾 Reporte autoguardado: {ruta}")
                except OSError as e:
                    messagebox.showwarning(
                        "Autoguardado",
                        f"Registro correcto, pero no se pudo autoguardar el reporte:\n{e}")

            self.after(0, actualizar)

        threading.Thread(target=tarea, daemon=True).start()

    def _copiar_txid(self):
        if self._registro_actual and self._registro_actual.cardano_txid:
            self.clipboard_clear()
            self.clipboard_append(self._registro_actual.cardano_txid)
            messagebox.showinfo("Copiado", "TxID copiado al portapapeles.")

    # ══════════════════════════════════════════════════════════════════
    #  TAB — VERIFICAR TXID
    # ══════════════════════════════════════════════════════════════════
    def _construir_tab_verificar(self):
        p = self._tab_verificar
        cont = ctk.CTkFrame(p, fg_color=COLOR_FONDO)
        cont.pack(fill="both", expand=True)

        ctk.CTkLabel(
            cont,
            text="Verificación independiente de un registro anclado en Cardano.\n"
                 "Introduce el TxID que consta en el reporte: se consultará la red y se "
                 "mostrarán los metadatos inmutables (ID de registro, ID de vestigio, "
                 "hashes y timestamp) para su cotejo.",
            font=FUENTE_PEQUEÑA, text_color=COLOR_APAGADO,
            wraplength=780, justify="left",
        ).pack(anchor="w", pady=(4, 8))

        fila = ctk.CTkFrame(cont, fg_color="transparent")
        fila.pack(fill="x", pady=(0, 8))
        self._entry_txid = ctk.CTkEntry(
            fila, placeholder_text="TxID (64 caracteres hexadecimales)",
            font=FUENTE_MONO, fg_color="white", text_color=COLOR_TEXTO,
        )
        self._entry_txid.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._btn_verificar = ctk.CTkButton(
            fila, text="🔍  Verificar", width=130,
            command=self._verificar_txid_gui,
            fg_color=COLOR_ACENTO, hover_color="#1565C0",
        )
        self._btn_verificar.pack(side="left")

        self._txt_verificacion = ctk.CTkTextbox(
            cont, font=FUENTE_MONO, fg_color=COLOR_TARJETA,
            border_color=COLOR_BORDE, border_width=1,
            state="disabled", text_color=COLOR_TEXTO, wrap="word",
        )
        self._txt_verificacion.pack(fill="both", expand=True)

    def _verificar_txid_gui(self):
        txid = self._entry_txid.get().strip().lower()
        if len(txid) != 64 or any(c not in "0123456789abcdef" for c in txid):
            messagebox.showerror(
                "TxID no válido",
                "El TxID debe tener 64 caracteres hexadecimales.")
            return

        self._btn_verificar.configure(state="disabled")
        self._escribir_verificacion("⏳  Consultando la red…")

        def tarea():
            res = verificar_txid(txid)

            def actualizar():
                self._btn_verificar.configure(state="normal")
                if not res.exito:
                    self._escribir_verificacion(f"❌  {res.mensaje}")
                    return
                lineas = [
                    f"✅  Transacción confirmada en la red {res.red}",
                    f"Bloque: {res.bloque}",
                    "",
                ]
                if res.metadatos:
                    md = res.metadatos
                    hashes = md.get("hashes", {}) or {}
                    lineas.append("METADATOS LEGALCCD (etiqueta 1984)")
                    lineas.append("-" * 60)
                    lineas.append(f"  Aplicación / versión     {md.get('app', '?')} {md.get('v', '')}")
                    lineas.append(f"  ID de registro           {md.get('id', '')}")
                    lineas.append(f"  ID de vestigio           {md.get('vid', '')}")
                    lineas.append(f"  Timestamp (UTC)          {md.get('ts', '')}")
                    lineas.append("  Hashes:")
                    for alg, v in hashes.items():
                        valor = "".join(v) if isinstance(v, list) else str(v)
                        lineas.append(f"    {alg:<10} {valor}")
                    # Cotejo con el registro actual, si existe
                    r = self._registro_actual
                    if r and r.hashes:
                        lineas.append("")
                        lineas.append("COTEJO CON EL REGISTRO ACTUAL")
                        lineas.append("-" * 60)
                        for alg, local in r.hashes.items():
                            rec = hashes.get(alg, "")
                            rec = "".join(rec) if isinstance(rec, list) else str(rec)
                            estado = ("✅ COINCIDE" if rec and rec == local
                                      else ("❌ NO COINCIDE" if rec else "—  no consta en la cadena"))
                            lineas.append(f"    {alg:<10} {estado}")
                else:
                    lineas.append("⚠️  La transacción existe pero no contiene metadatos "
                                  "de LegalCCD (etiqueta 1984).")
                self._escribir_verificacion("\n".join(lineas))

            self.after(0, actualizar)

        threading.Thread(target=tarea, daemon=True).start()

    def _escribir_verificacion(self, texto: str):
        self._txt_verificacion.configure(state="normal")
        self._txt_verificacion.delete("0.0", "end")
        self._txt_verificacion.insert("0.0", texto)
        self._txt_verificacion.configure(state="disabled")

    # ══════════════════════════════════════════════════════════════════
    #  HISTORIAL
    # ══════════════════════════════════════════════════════════════════
    def _actualizar_historial(self):
        for widget in self._frame_historial.winfo_children():
            widget.destroy()

        if not self._historial:
            ctk.CTkLabel(self._frame_historial, text="El historial está vacío.",
                         font=FUENTE_NORMAL, text_color=COLOR_APAGADO).pack(pady=40)
            return

        for i, r in enumerate(reversed(self._historial)):
            idx = len(self._historial) - 1 - i
            fila = ctk.CTkFrame(self._frame_historial, fg_color=COLOR_TARJETA,
                                corner_radius=8, border_width=1, border_color=COLOR_BORDE)
            fila.pack(fill="x", pady=(0, 6))

            info = ctk.CTkFrame(fila, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, padx=12, pady=8)

            ctk.CTkLabel(info, text=f"Caso: {r.num_caso}",
                         font=FUENTE_PEQUEÑA, text_color=COLOR_APAGADO).pack(anchor="w")
            ctk.CTkLabel(info, text=f"{r.id_vestigio}  {r.desc_vestigio}",
                         font=FUENTE_LABEL, text_color=COLOR_TEXTO).pack(anchor="w")
            hash_preview = "  |  ".join(f"{a}: {v[:20]}…" for a, v in r.hashes.items())
            ctk.CTkLabel(info, text=hash_preview,
                         font=FUENTE_MONO, text_color=COLOR_APAGADO).pack(anchor="w")

            acciones = ctk.CTkFrame(fila, fg_color="transparent")
            acciones.pack(side="right", padx=8)
            ctk.CTkButton(acciones, text="👁 Ver", width=60,
                          command=lambda r=r: self._ver_registro(r),
                          fg_color="transparent", border_width=1,
                          border_color=COLOR_ACENTO, text_color=COLOR_ACENTO,
                          hover_color="#EBF4FC").pack(pady=2)
            ctk.CTkButton(acciones, text="⬇ TXT", width=60,
                          command=lambda r=r: self._exportar_registro(r),
                          fg_color="transparent", border_width=1,
                          border_color=COLOR_EXITO, text_color=COLOR_EXITO,
                          hover_color="#ECFDF5").pack(pady=2)

    def _ver_registro(self, r: Registro):
        self._registro_actual = r
        self._mostrar_resumen(r)
        self._tabs.set("📄  Resumen del registro")

    def _exportar_registro(self, r: Registro):
        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=f"LegalCCD_{r.id_registro}.txt",
            filetypes=[("Archivo de texto", "*.txt")],
            title="Guardar reporte",
        )
        if ruta:
            Path(ruta).write_text(generar_reporte_txt(r), encoding="utf-8")
            messagebox.showinfo("Exportado", f"Reporte guardado en:\n{ruta}")

    def _exportar_historial(self):
        if not self._historial:
            messagebox.showinfo("Historial vacío", "No hay registros en el historial.")
            return
        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=f"LegalCCD_historial_{datetime.today().strftime('%Y%m%d')}.txt",
            filetypes=[("Archivo de texto", "*.txt")],
            title="Exportar historial completo",
        )
        if ruta:
            sep = "=" * 62
            bloques = [f"LEGALCCD — HISTORIAL DE SESIÓN\nTotal: {len(self._historial)} registros\n"]
            for i, r in enumerate(self._historial, 1):
                bloques.append(f"\n{sep}\nREGISTRO {i} / {len(self._historial)}\n{sep}")
                bloques.append(generar_reporte_txt(r))
            Path(ruta).write_text("\n".join(bloques), encoding="utf-8")
            messagebox.showinfo("Exportado", f"Historial guardado en:\n{ruta}")

    # ══════════════════════════════════════════════════════════════════
    #  LIMPIAR
    # ══════════════════════════════════════════════════════════════════
    def _limpiar(self):
        for entry in [self._num_caso, self._fecha_acto, self._hora_acto, self._desc_caso,
                      self._id_vestigio, self._desc_vestigio, self._nombre_actuante,
                      self._id_profesional, self._num_control]:
            entry.delete(0, "end")
        self._fecha_acto.insert(0, datetime.today().strftime("%d/%m/%Y"))
        self._hora_acto.insert(0, datetime.now().strftime("%H:%M"))
        self._tipo_vestigio_var.set(self._tipo_options[0])
        self._rol_var.set("— Seleccionar rol —")
        self._txt_libre.delete("0.0", "end")
        self._txt_otros.delete("0.0", "end")
        for e in [self._hash_manual, self._origen_hash]:
            e.delete(0, "end")
        self._archivo_ruta = None
        self._hashes_calculados = {}
        self._lbl_archivo.configure(text="Ningún archivo seleccionado", text_color=COLOR_APAGADO)
        self._txt_hash.configure(state="normal")
        self._txt_hash.delete("0.0", "end")
        self._txt_hash.configure(state="disabled")
        self._lbl_progreso.configure(text="")
        for var in self._algo_vars.values():
            var.set(False)
        self._algo_vars["SHA-256"].set(True)


# ─── Entry point ───────────────────────────────────────────────────────────────
def main():
    app = AppLegalCCD()
    app.mainloop()


if __name__ == "__main__":
    main()
