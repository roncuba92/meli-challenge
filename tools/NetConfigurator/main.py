import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
import threading
import datetime
import os
import sys
import csv
import ipaddress

from core import GestorRed

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

COLOR_FONDO_VENTANA = "#F0F2F5"
COLOR_PANEL         = "#FFFFFF"
COLOR_BTN_BASE      = "#E4E6EB"
COLOR_BTN_HOVER     = "#D8DADF"
COLOR_TEXTO         = "#333333"
COLOR_BORDE         = "#CCCCCC"
COLOR_ACCION_PRINCIPAL = "#3b5998"

BTN_HEIGHT = 34
INPUT_HEIGHT = 30
VLAN_MIN = 1
VLAN_MAX = 4094
FONT_UI = ("Segoe UI", 11)
FONT_BOLD = ("Segoe UI", 11, "bold")
if sys.platform == "darwin":
    FONT_MONO = ("Menlo", 10)
elif os.name == "nt":
    FONT_MONO = ("Consolas", 10)
else:
    FONT_MONO = ("DejaVu Sans Mono", 10)

class AplicacionRed(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.backend = GestorRed()
        self.tareas = {}
        self.switches = []
        self.modo_multi = False
        self._run_log_path = None
        self._run_summary_path = None
        self._run_summary = []
        self._run_dir = None
        self.title("NetConfigurator")
        self.geometry("1100x720")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_FONDO_VENTANA)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        self._inicializar_ui()

    def _inicializar_ui(self):
        self._construir_encabezado()
        self._construir_panel_izquierdo()
        self._construir_panel_derecho()
        self._construir_logs()

    def _construir_encabezado(self):
        self.marco_conexion = ctk.CTkFrame(self, corner_radius=0, fg_color=COLOR_PANEL, border_width=0)
        self.marco_conexion.grid(row=0, column=0, columnspan=2, sticky="ew")
        ctk.CTkFrame(self.marco_conexion, height=1, fg_color=COLOR_BORDE).pack(side="bottom", fill="x")

        barra_encabezado = ctk.CTkFrame(self.marco_conexion, fg_color="transparent")
        barra_encabezado.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(barra_encabezado, text="CONEXIÓN", font=FONT_BOLD, text_color="#555").pack(side="left", padx=(0,15))
        self.entrada_ip = self._crear_entrada(barra_encabezado, "Dirección IP", width=110)
        self.entrada_usuario = self._crear_entrada(barra_encabezado, "Usuario", width=100)
        self.entrada_password = self._crear_entrada(barra_encabezado, "Password", es_password=True, width=100)
        self.entrada_enable = self._crear_entrada(barra_encabezado, "Enable", es_password=True, width=100)

        boton_desconectar = ctk.CTkButton(barra_encabezado, text="Desconectar", command=self.desconectar_sesion,
                                   height=BTN_HEIGHT, font=FONT_UI, text_color="#C0392B",
                                   fg_color=COLOR_BTN_BASE, hover_color="#ffcccc",
                                   border_width=1, border_color=COLOR_BORDE, width=100)
        boton_desconectar.pack(side="right", padx=5)

        boton_conectar = ctk.CTkButton(barra_encabezado, text="Conectar", command=self.probar_conexion,
                                   height=BTN_HEIGHT, font=FONT_BOLD, text_color="white",
                                   fg_color=COLOR_ACCION_PRINCIPAL, hover_color="#2c4a8c", width=120)
        boton_conectar.pack(side="right", padx=5)
        
        self.etiqueta_estado = ctk.CTkLabel(barra_encabezado, text="Desconectado", font=("Segoe UI", 10, "bold"), text_color="gray")
        self.etiqueta_estado.pack(side="right", padx=(5, 15))
        self.etiqueta_punto = ctk.CTkLabel(barra_encabezado, text="●", font=("Arial", 22), text_color="gray", height=10, anchor="center")
        self.etiqueta_punto.pack(side="right", padx=0)

    def _construir_panel_izquierdo(self):
        self.panel_izquierdo = ctk.CTkFrame(self, corner_radius=8, fg_color=COLOR_PANEL, border_width=1, border_color=COLOR_BORDE)
        self.panel_izquierdo.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=20)
        
        ctk.CTkLabel(self.panel_izquierdo, text="TAREAS", font=FONT_BOLD, text_color="#555").pack(pady=(20,15))

        self._construir_seccion_hostname()
        self._agregar_separador(self.panel_izquierdo)
        self._construir_seccion_vlan()
        self._agregar_separador(self.panel_izquierdo)
        self._construir_seccion_respaldo()

    def _construir_seccion_hostname(self):
        grp1 = ctk.CTkFrame(self.panel_izquierdo, fg_color="transparent")
        grp1.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(grp1, text="Hostname", font=("Segoe UI", 12), text_color="#666", anchor="w").pack(fill="x")
        self.entrada_hostname = ctk.CTkEntry(grp1, placeholder_text="Nuevo nombre", height=INPUT_HEIGHT, font=FONT_UI, border_color=COLOR_BORDE, fg_color="#F9F9F9", text_color="black")
        self.entrada_hostname.pack(fill="x", pady=(2,5))
        self.boton_hostname = self._crear_boton(grp1, "Agregar", self.agregar_tarea_hostname)

    def _construir_seccion_vlan(self):
        grp2 = ctk.CTkFrame(self.panel_izquierdo, fg_color="transparent")
        grp2.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(grp2, text="VLAN", font=("Segoe UI", 12), text_color="#666", anchor="w").pack(fill="x")
        fila_vlan = ctk.CTkFrame(grp2, fg_color="transparent")
        fila_vlan.pack(fill="x", pady=(2,5))
        self.entrada_vlan_id = ctk.CTkEntry(fila_vlan, placeholder_text="ID", width=60, height=INPUT_HEIGHT, font=FONT_UI, border_color=COLOR_BORDE, fg_color="#F9F9F9", text_color="black")
        self.entrada_vlan_id.pack(side="left", padx=(0,5))
        self.entrada_vlan_nombre = ctk.CTkEntry(fila_vlan, placeholder_text="Nombre VLAN", height=INPUT_HEIGHT, font=FONT_UI, border_color=COLOR_BORDE, fg_color="#F9F9F9", text_color="black")
        self.entrada_vlan_nombre.pack(side="left", fill="x", expand=True)
        self._crear_boton(grp2, "Agregar", self.agregar_tarea_vlan)

    def _construir_seccion_respaldo(self):
        grp3 = ctk.CTkFrame(self.panel_izquierdo, fg_color="transparent")
        grp3.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(grp3, text="Respaldo", font=("Segoe UI", 12), text_color="#666", anchor="w").pack(fill="x", pady=(0, 5))
        
        self.modo_respaldo = ctk.CTkSegmentedButton(grp3, values=["Local (PC)", "Servidor Remoto (TFTP)"], 
                                                  command=self.alternar_modo_respaldo, font=FONT_UI)
        self.modo_respaldo.set("Local (PC)") 
        self.modo_respaldo.pack(fill="x", pady=(0, 10))

        self.marco_tftp = ctk.CTkFrame(grp3, fg_color="transparent")
        self.entrada_tftp_ip = ctk.CTkEntry(self.marco_tftp, placeholder_text="IP Servidor TFTP", 
                                          height=INPUT_HEIGHT, font=FONT_UI, border_color=COLOR_BORDE, 
                                          fg_color="#F9F9F9", text_color="black")
        self.entrada_tftp_ip.pack(fill="x", pady=(0, 10))

        self.boton_respaldo = self._crear_boton(grp3, "Guardar en PC", self.respaldar_en_hilo)

    def _construir_panel_derecho(self):
        self.panel_derecho = ctk.CTkFrame(self, corner_radius=8, fg_color=COLOR_PANEL, border_width=1, border_color=COLOR_BORDE)
        self.panel_derecho.grid(row=1, column=1, sticky="nsew", padx=(0, 20), pady=20)
        self.panel_derecho.grid_rowconfigure(0, weight=0)
        self.panel_derecho.grid_rowconfigure(1, weight=1)
        self.panel_derecho.grid_rowconfigure(2, weight=0)
        self.panel_derecho.grid_columnconfigure(0, weight=1)

        cabecera_derecha = ctk.CTkFrame(self.panel_derecho, fg_color="transparent", height=30)
        cabecera_derecha.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))
        ctk.CTkLabel(cabecera_derecha, text="TAREAS A EJECUTAR", font=FONT_BOLD, text_color="#555").pack(side="left")

        acciones_csv = ctk.CTkFrame(cabecera_derecha, fg_color="transparent")
        acciones_csv.pack(side="right")
        boton_csv = ctk.CTkButton(
            acciones_csv,
            text="Cargar Datos (.txt)",
            command=self.cargar_csv_switches,
            height=28,
            font=("Segoe UI", 10),
            text_color=COLOR_TEXTO,
            fg_color=COLOR_BTN_BASE,
            hover_color=COLOR_BTN_HOVER,
            border_width=1,
            border_color=COLOR_BORDE,
            width=100,
        )
        boton_csv.pack(side="left", padx=(0, 6))

        boton_limpiar_csv = ctk.CTkButton(
            acciones_csv,
            text="Limpiar Datos (.txt)",
            command=self.limpiar_switches,
            height=28,
            font=("Segoe UI", 10),
            text_color="#C0392B",
            fg_color=COLOR_BTN_BASE,
            hover_color="#ffcccc",
            border_width=1,
            border_color=COLOR_BORDE,
            width=100,
        )
        boton_limpiar_csv.pack(side="left")

        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("Command.Treeview", background="white", foreground=COLOR_TEXTO, fieldbackground="white", 
                        borderwidth=0, rowheight=28, font=FONT_MONO)
        estilo.map("Command.Treeview", background=[("selected", "#E8F0FE")], foreground=[("selected", "#1967D2")])
        estilo.layout("Command.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

        lista_frame = ctk.CTkFrame(self.panel_derecho, fg_color="transparent")
        lista_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))
        lista_frame.grid_rowconfigure(0, weight=1)
        lista_frame.grid_columnconfigure(0, weight=1)

        self.arbol_tareas = ttk.Treeview(lista_frame, show="tree", style="Command.Treeview")
        self.arbol_tareas.column("#0", width=520, stretch=True, anchor="w")
        
        barra_desplazamiento = ctk.CTkScrollbar(lista_frame, orientation="vertical", command=self.arbol_tareas.yview)
        self.arbol_tareas.configure(yscrollcommand=barra_desplazamiento.set)
        
        self.arbol_tareas.grid(row=0, column=0, sticky="nsew")
        barra_desplazamiento.grid(row=0, column=1, sticky="ns", padx=(8, 0))

        acciones_container = ctk.CTkFrame(self.panel_derecho, fg_color="transparent")
        acciones_container.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        ctk.CTkFrame(acciones_container, height=1, fg_color=COLOR_BORDE).pack(fill="x", pady=(0, 10))

        self.marco_acciones = ctk.CTkFrame(
            acciones_container,
            corner_radius=8,
            fg_color="#F9FAFB",
            border_width=1,
            border_color=COLOR_BORDE,
        )
        self.marco_acciones.pack(fill="x")
        self.marco_acciones.grid_columnconfigure(0, weight=1)
        self.marco_acciones.grid_columnconfigure(1, weight=0)

        progreso_frame = ctk.CTkFrame(self.marco_acciones, fg_color="transparent")
        progreso_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=10)
        progreso_frame.grid_columnconfigure(0, weight=1)
        self.etiqueta_progreso = ctk.CTkLabel(progreso_frame, text="Progreso: 0%", font=("Segoe UI", 10), text_color="#777")
        self.etiqueta_progreso.grid(row=0, column=0, sticky="w")
        self.barra_progreso = ctk.CTkProgressBar(progreso_frame, height=10, progress_color=COLOR_ACCION_PRINCIPAL)
        self.barra_progreso.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.barra_progreso.set(0)

        botones_frame = ctk.CTkFrame(self.marco_acciones, fg_color="transparent")
        botones_frame.grid(row=0, column=1, sticky="e", padx=12, pady=10)

        boton_aplicar = ctk.CTkButton(botones_frame, text="Aplicar Cambios", command=self.ejecutar_cola_en_hilo,
                                   height=BTN_HEIGHT, font=FONT_BOLD, text_color="white",
                                   fg_color=COLOR_ACCION_PRINCIPAL, hover_color="#2c4a8c")
        boton_aplicar.grid(row=0, column=0, padx=(0, 8))

        boton_quitar = ctk.CTkButton(botones_frame, text="Quitar Seleccionado", command=self.quitar_tarea,
                                   height=BTN_HEIGHT, font=FONT_UI, text_color="#C0392B",
                                   fg_color=COLOR_BTN_BASE, hover_color="#ffcccc",
                                   border_width=1, border_color=COLOR_BORDE, width=100)
        boton_quitar.grid(row=0, column=1)

    def _construir_logs(self):
        self.marco_logs = ctk.CTkFrame(self, corner_radius=0, fg_color="#F9F9F9", height=100)
        self.marco_logs.grid(row=2, column=0, columnspan=2, sticky="ew")
        ctk.CTkFrame(self.marco_logs, height=1, fg_color=COLOR_BORDE).pack(fill="x", side="top")
        self.caja_logs = ctk.CTkTextbox(self.marco_logs, height=80, font=("Consolas", 10), 
                                      fg_color="transparent", text_color="#555", activate_scrollbars=True)
        self.caja_logs.pack(fill="both", expand=True, padx=20, pady=10)
        self.registrar("Sistema listo...")

    def _crear_entrada(self, contenedor, texto_guia, width=100, es_password=False):
        entrada = ctk.CTkEntry(contenedor, placeholder_text=texto_guia, show="*" if es_password else "", 
                             width=width, height=INPUT_HEIGHT, font=FONT_UI, 
                             border_color=COLOR_BORDE, border_width=1, fg_color="#F9F9F9", text_color="black")
        entrada.pack(side="left", padx=5)
        return entrada

    def _crear_boton(self, contenedor, texto, comando, lado="top", ancho=None):
        boton = ctk.CTkButton(contenedor, text=texto, command=comando,
                            height=BTN_HEIGHT, font=FONT_UI, text_color=COLOR_TEXTO,
                            fg_color=COLOR_BTN_BASE, hover_color=COLOR_BTN_HOVER,
                            border_width=1, border_color=COLOR_BORDE,
                            width=ancho if ancho else 140)
        if lado == "top": boton.pack(fill="x", pady=5)
        else: boton.pack(side=lado, padx=5)
        return boton

    @staticmethod
    def _agregar_separador(contenedor):
        ttk.Separator(contenedor, orient="horizontal").pack(fill="x", padx=25, pady=15)

    def alternar_modo_respaldo(self, valor):
        if valor == "Servidor Remoto (TFTP)":
            self.marco_tftp.pack(fill="x", after=self.modo_respaldo)
            self.boton_respaldo.configure(text="Enviar a TFTP")
        else:
            self.marco_tftp.pack_forget()
            self.boton_respaldo.configure(text="Guardar en PC")

    def registrar(self, msg):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        linea = f"[{timestamp}] {msg}\n"
        self.caja_logs.insert("end", linea)
        self.caja_logs.see("end")
        if self._run_log_path:
            try:
                with open(self._run_log_path, "a", encoding="utf-8") as archivo:
                    archivo.write(linea)
            except Exception:
                pass

    def _iniciar_ejecucion(self, etiqueta):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_dir = os.path.abspath(os.path.dirname(__file__))
        runs_dir = os.path.join(base_dir, "runs")
        run_dir = os.path.join(runs_dir, timestamp)
        os.makedirs(run_dir, exist_ok=True)
        self._run_dir = run_dir
        self._run_log_path = os.path.join(run_dir, "run.log")
        self._run_summary_path = os.path.join(run_dir, "summary.csv")
        self._run_summary = []
        try:
            with open(self._run_log_path, "w", encoding="utf-8") as archivo:
                archivo.write(f"Inicio de ejecucion: {etiqueta}\n")
        except Exception:
            pass

    def _finalizar_ejecucion(self):
        if not self._run_summary_path:
            return
        try:
            with open(self._run_summary_path, "w", encoding="utf-8", newline="") as archivo:
                writer = csv.DictWriter(archivo, fieldnames=["ip", "hostname", "status", "details"])
                writer.writeheader()
                writer.writerows(self._run_summary)
        except Exception:
            pass
        if self._run_dir:
            self.registrar(f">>> Logs guardados en: {self._run_dir}")
        self._run_log_path = None
        self._run_summary_path = None
        self._run_summary = []
        self._run_dir = None

    def cargar_csv_switches(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar TXT de switches",
            filetypes=[("TXT (comas)", "*.txt"), ("CSV", "*.csv"), ("Todos los archivos", "*.*")],
        )
        if not ruta:
            return

        try:
            with open(ruta, "r", encoding="utf-8-sig", newline="") as archivo:
                muestra = archivo.read(2048)
                archivo.seek(0)
                try:
                    dialecto = csv.Sniffer().sniff(muestra)
                except csv.Error:
                    dialecto = csv.excel

                lector = csv.reader(archivo, dialecto)
                filas = [fila for fila in lector if any(c.strip() for c in fila)]
        except Exception as exc:
            messagebox.showerror("TXT", f"No se pudo leer el archivo: {exc}")
            return

        if not filas:
            messagebox.showwarning("TXT", "El archivo TXT está vacío.")
            return

        encabezado = [c.strip().lower() for c in filas[0]]
        tiene_encabezado = any("ip" in c for c in encabezado) and any(
            "hostname" in c or c in ("host", "nombre", "name") for c in encabezado
        )

        switches = []
        if tiene_encabezado:
            def _buscar_columna(nombres, candidatos):
                for cand in candidatos:
                    for idx, nombre in enumerate(nombres):
                        if cand in nombre:
                            return idx
                return None

            idx_ip = _buscar_columna(encabezado, ["ip", "address", "direccion"])
            idx_hostname = _buscar_columna(encabezado, ["hostname", "nombre", "name", "host"])

            if idx_ip is None or idx_hostname is None:
                messagebox.showerror("TXT", "Faltan columnas requeridas (ip, hostname).")
                return

            datos = filas[1:]
            for idx, fila in enumerate(datos, start=2):
                if len(fila) <= max(idx_ip, idx_hostname):
                    continue
                ip = fila[idx_ip].strip()
                hostname = fila[idx_hostname].strip()
                if ip and hostname:
                    switches.append({"ip": ip, "hostname": hostname, "linea": idx})
        else:
            for idx, fila in enumerate(filas, start=1):
                if len(fila) < 2:
                    continue
                ip = fila[0].strip()
                hostname = fila[1].strip()
                if ip and hostname:
                    switches.append({"ip": ip, "hostname": hostname, "linea": idx})

        if not switches:
            messagebox.showwarning("TXT", "No se encontraron filas válidas (ip, hostname).")
            return

        errores = self._validar_switches_csv(switches)
        if errores:
            resumen = "\n".join(errores[:5])
            extra = ""
            if len(errores) > 5:
                extra = f"\n... y {len(errores) - 5} más."
            messagebox.showerror("TXT", f"Errores en TXT:\n{resumen}{extra}")
            return

        self.switches = switches
        self._actualizar_lista_switches()
        self._set_modo_multi(True)
        self._sincronizar_tareas_csv()
        self.registrar(f">>> Switches cargados desde TXT: {len(self.switches)}")

    def limpiar_switches(self):
        self.switches = []
        self._actualizar_lista_switches()
        self._limpiar_tareas_csv()
        self._set_modo_multi(False)
        self.registrar(">>> Lista de switches limpiada.")

    def _actualizar_lista_switches(self):
        return

    def _limpiar_tareas_csv(self):
        for item_id, tarea in list(self.tareas.items()):
            if tarea.get("origen") == "csv":
                self.arbol_tareas.delete(item_id)
                self.tareas.pop(item_id, None)

    def _sincronizar_tareas_csv(self):
        self._limpiar_tareas_csv()
        for sw in self.switches:
            hostname = sw.get("hostname")
            ip = sw.get("ip")
            if not hostname or not ip:
                continue
            comando = f"hostname {hostname}  [{ip}]"
            descripcion = f"Configurar Hostname: {hostname} ({ip})"
            self._insertar_tarea(
                "HOSTNAME",
                descripcion,
                {"hostname": hostname, "target_ip": ip, "origen": "csv"},
                comando,
            )

    def _set_modo_multi(self, activo):
        self.modo_multi = activo
        estado = "disabled" if activo else "normal"
        self.entrada_hostname.configure(state=estado)
        self.boton_hostname.configure(state=estado)

    def _validar_switches_csv(self, switches):
        errores = []
        vistos = set()
        for sw in switches:
            ip = sw.get("ip", "").strip()
            hostname = sw.get("hostname", "").strip()
            linea = sw.get("linea", "?")
            if not ip or not hostname:
                errores.append(f"Linea {linea}: faltan ip/hostname")
                continue
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                errores.append(f"Linea {linea}: IP inválida ({ip})")
            if ip in vistos:
                errores.append(f"Linea {linea}: IP duplicada ({ip})")
            vistos.add(ip)
            if " " in hostname:
                errores.append(f"Linea {linea}: hostname con espacios ({hostname})")
            if len(hostname) > 63:
                errores.append(f"Linea {linea}: hostname muy largo ({hostname})")
        return errores

    def _actualizar_progreso(self, fraccion, texto=None):
        fraccion = max(0.0, min(1.0, fraccion))

        def _update():
            self.barra_progreso.set(fraccion)
            if texto:
                self.etiqueta_progreso.configure(text=texto)
            else:
                porcentaje = int(fraccion * 100)
                self.etiqueta_progreso.configure(text=f"Progreso: {porcentaje}%")

        self.after(0, _update)

    def _insertar_tarea(self, tipo, descripcion, payload, comando=None):
        texto_mostrar = comando or descripcion
        item_id = self.arbol_tareas.insert("", "end", text=texto_mostrar)
        self.tareas[item_id] = {"tipo": tipo, "descripcion": descripcion, **payload}
        return item_id

    def agregar_tarea_hostname(self):
        nombre = self.entrada_hostname.get().strip()
        if not nombre:
            messagebox.showwarning("Hostname", "Ingrese un nombre válido.")
            return
        comando = f"hostname {nombre}"
        self._insertar_tarea("HOSTNAME", f"Configurar Hostname: {nombre}", {"hostname": nombre}, comando)
        self.entrada_hostname.delete(0, "end")

    def agregar_tarea_vlan(self):
        vlan_id = self.entrada_vlan_id.get().strip()
        vlan_nombre = self.entrada_vlan_nombre.get().strip()
        if not vlan_id.isdigit():
            messagebox.showwarning("VLAN", "El ID debe ser válido (1-4094).")
            return
        if not vlan_nombre:
            messagebox.showwarning("VLAN", "Ingrese un nombre para la VLAN.")
            return
        if not VLAN_MIN <= int(vlan_id) <= VLAN_MAX:
            messagebox.showwarning("VLAN", f"ID fuera de rango ({VLAN_MIN}-{VLAN_MAX}).")
            return

        comando = f"vlan {vlan_id} name {vlan_nombre}"
        self._insertar_tarea(
            "VLAN",
            f"Configurar VLAN {vlan_id}: Nombre '{vlan_nombre}'",
            {"vlan_id": vlan_id, "vlan_nombre": vlan_nombre},
            comando,
        )
        self.entrada_vlan_id.delete(0, "end")
        self.entrada_vlan_nombre.delete(0, "end")

    def quitar_tarea(self):
        for item in self.arbol_tareas.selection():
            self.tareas.pop(item, None)
            self.arbol_tareas.delete(item)

    def desconectar_sesion(self):
        threading.Thread(target=self._worker_desconectar).start()

    def _obtener_credenciales(self):
        return self.backend.obtener_info_dispositivo(
            self.entrada_ip.get(),
            self.entrada_usuario.get(),
            self.entrada_password.get(),
            self.entrada_enable.get()
        )

    def probar_conexion(self): 
        threading.Thread(target=self._worker_probar_conexion).start()

    def ejecutar_cola_en_hilo(self): 
        threading.Thread(target=self._worker_ejecutar_cola).start()

    def respaldar_en_hilo(self): 
        threading.Thread(target=self._worker_respaldo).start()

    def _worker_probar_conexion(self):
        self.etiqueta_estado.configure(text="Conectando...", text_color="#F39C12")
        self.etiqueta_punto.configure(text_color="#F39C12")
        try:
            prompt = self.backend.probar_conexion(self._obtener_credenciales())
            self.etiqueta_estado.configure(text=f"Online: {prompt}", text_color="#27AE60")
            self.etiqueta_punto.configure(text_color="#27AE60")
            self.registrar(f"Conexión exitosa a {prompt}")
        except Exception as e:
            self.etiqueta_estado.configure(text="Error", text_color="#C0392B")
            self.etiqueta_punto.configure(text_color="#C0392B")
            self.registrar(f"Error: {e}")

    def _worker_ejecutar_cola(self):
        elementos = self.arbol_tareas.get_children()
        if not elementos and not self.switches:
            self._actualizar_progreso(0, "Progreso: 0%")
            messagebox.showinfo("Info", "Lista vacía")
            return

        lista_tareas = [self.tareas.get(item) for item in elementos if item in self.tareas]
        lista_tareas = [t for t in lista_tareas if t]  # filtra nulos por si faltan entradas

        if self.switches:
            tareas_vlan = [t for t in lista_tareas if t.get("tipo") == "VLAN"]
            tareas_hostname = [
                t for t in lista_tareas
                if t.get("tipo") == "HOSTNAME" and t.get("target_ip")
            ]
            usuarios = self._obtener_credenciales()
            if not usuarios.get("username") or not usuarios.get("password") or not usuarios.get("secret"):
                messagebox.showwarning("Credenciales", "Ingrese usuario, password y enable.")
                return

            self._iniciar_ejecucion("multi-switch")
            self._actualizar_progreso(0, "Preparando... (0%)")
            errores = []
            total_switches = len(self.switches)

            try:
                for indice, sw in enumerate(self.switches, start=1):
                    ip = sw["ip"]
                    hostname = sw.get("hostname", "")
                    credenciales = self.backend.obtener_info_dispositivo(ip, usuarios["username"], usuarios["password"], usuarios["secret"])

                    tareas_dispositivo = list(tareas_vlan)
                    tareas_dispositivo.extend(t for t in tareas_hostname if t.get("target_ip") == ip)
                    if not tareas_dispositivo:
                        self.registrar(f">>> Switch {indice}/{total_switches}: {ip} sin tareas asignadas.")
                        self._run_summary.append({
                            "ip": ip,
                            "hostname": hostname,
                            "status": "SKIPPED",
                            "details": "Sin tareas asignadas",
                        })
                        continue

                    def progreso_cb(fraccion, descripcion, idx=indice, ip_actual=ip, total=total_switches):
                        fraccion_global = (idx - 1 + fraccion) / total
                        prefijo = f"Switch {idx}/{total} {ip_actual}"
                        detalle = f"{prefijo} - {descripcion}" if descripcion else prefijo
                        porcentaje = int(fraccion_global * 100)
                        self._actualizar_progreso(fraccion_global, f"{detalle} ({porcentaje}%)")

                    try:
                        self.registrar(f">>> Switch {indice}/{total_switches}: {ip}")
                        _, desviaciones = self.backend.aplicar_cambios(
                            credenciales,
                            tareas_dispositivo,
                            callback_log=self.registrar,
                            callback_progreso=progreso_cb,
                        )
                        if desviaciones:
                            self._run_summary.append({
                                "ip": ip,
                                "hostname": hostname,
                                "status": "WARN",
                                "details": "Desviaciones en validación",
                            })
                        else:
                            self._run_summary.append({
                                "ip": ip,
                                "hostname": hostname,
                                "status": "OK",
                                "details": "",
                            })
                    except Exception as exc:
                        errores.append(f"{ip}: {exc}")
                        self.registrar(f"ERROR SWITCH {ip}: {exc}")
                        self._run_summary.append({
                            "ip": ip,
                            "hostname": hostname,
                            "status": "ERROR",
                            "details": str(exc),
                        })
                        continue
            finally:
                self._finalizar_ejecucion()

            if errores:
                messagebox.showwarning("Multi-switch", "Algunos switches fallaron. Ver consola de logs.")
            else:
                messagebox.showinfo("Éxito", "Cambios aplicados en todos los switches.")

            for item in elementos:
                self.tareas.pop(item, None)
                self.arbol_tareas.delete(item)

            self._actualizar_progreso(0, "Progreso: 0%")
            self.limpiar_switches()
            return

        try:
            self._iniciar_ejecucion("single-switch")
            def progreso_cb(fraccion, descripcion):
                porcentaje = int(fraccion * 100)
                if descripcion:
                    detalle = f"{descripcion} ({porcentaje}%)"
                else:
                    detalle = f"Progreso: {porcentaje}%"
                self._actualizar_progreso(fraccion, detalle)

            self._actualizar_progreso(0, "Preparando... (0%)")
            nuevo_prompt, desviaciones = self.backend.aplicar_cambios(
                self._obtener_credenciales(),
                lista_tareas,
                callback_log=self.registrar,
                callback_progreso=progreso_cb,
            )
            self._actualizar_progreso(1, "Progreso: 100%")

            ip = self.entrada_ip.get().strip()
            hostname = next((t.get("hostname") for t in lista_tareas if t.get("tipo") == "HOSTNAME"), "")
            if desviaciones:
                self._run_summary.append({
                    "ip": ip,
                    "hostname": hostname,
                    "status": "WARN",
                    "details": "Desviaciones en validación",
                })
            else:
                self._run_summary.append({
                    "ip": ip,
                    "hostname": hostname,
                    "status": "OK",
                    "details": "",
                })

            if nuevo_prompt:
                self.etiqueta_estado.configure(text=f"Online: {nuevo_prompt}", text_color="#27AE60")
                self.etiqueta_punto.configure(text_color="#27AE60")

            if desviaciones:
                self.registrar(">>> VALIDACIÓN CON ALERTAS. Revise mensajes anteriores.")
                messagebox.showwarning("Validación", "Algunos cambios no se aplicaron. Ver consola de logs.")
            else:
                self.registrar(">>> FINALIZADO CON ÉXITO. Validación OK.")
                messagebox.showinfo("Éxito", "Cambios aplicados y validados.")
            
            for item in elementos:
                self.tareas.pop(item, None)
                self.arbol_tareas.delete(item)

            self._actualizar_progreso(0, "Progreso: 0%")
            
        except Exception as e:
            self.registrar(f"ERROR CRÍTICO: {e}")
            messagebox.showerror("Error", str(e))
            ip = self.entrada_ip.get().strip()
            self._run_summary.append({
                "ip": ip,
                "hostname": "",
                "status": "ERROR",
                "details": str(e),
            })
            self._actualizar_progreso(0, "Progreso: 0%")
        finally:
            self._finalizar_ejecucion()

    def _worker_desconectar(self):
        self.etiqueta_estado.configure(text="Cerrando...", text_color="#F39C12")
        self.etiqueta_punto.configure(text_color="#F39C12")
        credenciales = self._obtener_credenciales()
        if credenciales['host'] and credenciales['username'] and credenciales['password']:
            try:
                self.backend.desconectar_dispositivo(credenciales, callback_log=self.registrar)
            except Exception as e:
                self.registrar(f"Error al cerrar sesión: {e}")
        self.etiqueta_estado.configure(text="Desconectado", text_color="gray")
        self.etiqueta_punto.configure(text_color="gray")
        self.entrada_password.delete(0, 'end')
        self.entrada_enable.delete(0, 'end')
        self.registrar(">>> Sesión finalizada.")
        messagebox.showinfo("Info", "Desconectado. Credenciales borradas.")

    def _worker_respaldo(self):
        modo = self.modo_respaldo.get()
        ip_tftp = self.entrada_tftp_ip.get().strip()

        if modo == "Servidor Remoto (TFTP)" and not ip_tftp:
            messagebox.showwarning("TFTP", "Ingrese la IP del servidor TFTP.")
            return
        
        try:
            tipo_resultado, resultado = self.backend.realizar_respaldo(
                self._obtener_credenciales(), modo, ip_tftp, callback_log=self.registrar
            )
            
            if tipo_resultado == "LOCAL":
                messagebox.showinfo("Backup Local", f"Respaldo guardado localmente:\nUbicación y nombre de archivo: {resultado}")
                try:
                    if os.name == 'nt': os.startfile("repositorio_backups")
                except: pass
            else:
                messagebox.showinfo("Backup Remoto", f"Respaldo guardado en servidor TFTP: {ip_tftp}\nNombre de archivo: {resultado}")

        except Exception as e:
            self.registrar(f"ERROR BACKUP: {e}")
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = AplicacionRed()
    app.mainloop()
