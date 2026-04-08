import os

codigo = '''import tkinter as tk
from tkinter import messagebox, ttk, font
import threading
import time
import os
import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException, TimeoutException

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

def play_alert_sound():
    if HAS_WINSOUND:
        sound_file = "alerta.wav"
        if os.path.exists(sound_file):
            winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
    else:
        print("\\a") # Beep fallback

def get_cookies_path():
    """Obtiene la ruta a las cookies independientemente de donde se ejecute el script"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path_1 = os.path.join(script_dir, "cookies", "agendaweb.suramericana.com_cookies.txt")
    if os.path.exists(path_1):
        return path_1
    path_2 = os.path.join(os.getcwd(), "alerter", "cookies", "agendaweb.suramericana.com_cookies.txt")
    if os.path.exists(path_2):
        return path_2
    path_3 = os.path.join(os.getcwd(), "cookies", "agendaweb.suramericana.com_cookies.txt")
    return path_3 

def load_cookies(driver, filepath):
    if not os.path.exists(filepath):
        return False
    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.strip().split("\\t")
            if len(parts) >= 7:
                cookie = {
                    "domain": parts[0],
                    "path": parts[2],
                    "secure": parts[3].lower() == "true",
                    "name": parts[5],
                    "value": parts[6]
                }
                try:
                    driver.add_cookie(cookie)
                except Exception:
                    pass
    return True

def human_like_navigation(driver, update_callback, gui_callback=None):
    menu_url = "https://agendaweb.suramericana.com/agenda/internet/internet-menu.do"
    consulta_url = "https://agendaweb.suramericana.com/agenda/internet/internet-consultarCitas.do"
    
    update_callback("Navegando al menú principal...")
    driver.get(menu_url)
    time.sleep(3)

    try:
        alert = driver.switch_to.alert
        alert.accept()
    except NoAlertPresentException:
        pass

    update_callback("Extrayendo citas activas desde Consultas y Cancelaciones...")
    driver.get(consulta_url)
    time.sleep(4)
    
    try:
        filas = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        perfil_info = ""
        citas_activas_encontradas = []
        
        for fila in filas:
            celdas = fila.find_elements(By.TAG_NAME, "td")  
            if len(celdas) >= 4: 
                texto_fila = " | ".join([c.text.strip() for c in celdas if c.text.strip()])
                if texto_fila and "Fecha" not in texto_fila: 
                    citas_activas_encontradas.append(texto_fila)

        if citas_activas_encontradas:
            perfil_info = f"Tienes {len(citas_activas_encontradas)} citas vigentes encontradas:\\n\\n"
            for i, c in enumerate(citas_activas_encontradas):
                perfil_info += f"✅ Cita {i+1}: {c}\\n\\n"
        else:
            perfil_info = "No tienes citas programadas actualmente en el sistema o no se detectaron en la tabla."

        if gui_callback:
            gui_callback("update_profile", perfil_info)
    except Exception as e:
        if gui_callback:
            gui_callback("update_profile", f"No se pudo extraer la info del perfil actualmente. {str(e)}")

    time.sleep(2)

def check_appointments(headless=True, days_ahead=30, specific_date="", interval=60, use_popup=True, use_sound=True, stop_event=None, update_callback=None, gui_callback=None):
    driver = None
    try:
        base_domain_url = "https://agendaweb.suramericana.com"
        cita_url = "https://agendaweb.suramericana.com/agenda/internet/internet-asignarCita.do#no-back-button"

        if not HAS_SELENIUM:
            update_callback("ERROR CRÍTICO: Selenium no instalado.")
            return

        update_callback(f"Iniciando navegador Chrome (Oculto: {headless})...")  
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False) 
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

        driver = webdriver.Chrome(options=chrome_options)
        
        if gui_callback:
            gui_callback("set_driver", driver)

        update_callback("Cargando sesión (Cookies)...")
        driver.get(base_domain_url)
        time.sleep(3)

        cookie_path = get_cookies_path()
        if not os.path.exists(cookie_path):
            update_callback(f"⚠️ PROBLEMA GRAVE: No encuentro el archivo: {cookie_path}")
            driver.quit()
            return

        if load_cookies(driver, cookie_path):
            update_callback("✔️ Cookies cargadas correctamente.")
        else:
            update_callback("⚠️ Problema aplicando las cookies de sesión.")

        human_like_navigation(driver, update_callback, gui_callback)

        update_callback("Ingresando a Asignación de Citas...")
        driver.get(cita_url)
        time.sleep(4)

        count = 0
        while not stop_event.is_set():
            update_callback(f"[{count+1}] Revisando disponibilidad principal...")

            try:
                btn_previa = driver.find_elements(By.XPATH, "//button[contains(@onclick, 'consultarDisponibilidadCitas()')]")
                if btn_previa:
                    update_callback("-> Detectada confirmación intermedia de citas. Avanzando...")
                    driver.execute_script("consultarDisponibilidadCitas();")    
                    time.sleep(2)
                    driver.execute_script("consultarDisponibilidadCitasResolucion();")
                    time.sleep(6)
            except Exception:
                pass

            try:
                page_src = driver.page_source
                if "AGEW-05" in page_src or "LOGUEARSE" in page_src:
                    update_callback("Sesión caída. Navegando al menú para regenerar token...")
                    human_like_navigation(driver, update_callback, gui_callback)
                    driver.get(cita_url)
                    time.sleep(5)
            except Exception:
                pass

            try:
                select_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "listaDisponibilidad"))
                )

                select = Select(select_element)
                opciones = select.options

                if len(opciones) <= 1:
                    raise ValueError("El menú de médicos/días está vacío en la pantalla.")

                citas_encontradas = []
                
                max_opciones_a_revisar = min(len(opciones), 6)
                
                for idx in range(1, max_opciones_a_revisar):
                    option = opciones[idx]
                    option_text = option.text
                    update_callback(f"Evaluando Bloque: {option_text}")
                    select.select_by_index(idx)
                    
                    try:
                        driver.execute_script("if(typeof consultarCitasDisponibles === 'function') consultarCitasDisponibles();")
                    except:
                        pass
                    
                    time.sleep(5)
                    
                    doc_parts = option_text.split(" - ")
                    doctor_name = doc_parts[0].strip() if len(doc_parts) > 0 else "Médico General"
                    fecha_disp = doc_parts[1].strip() if len(doc_parts) > 1 else "Fecha N/A"

                    # PARSEO MEJORADO PARA HTML: Sura presenta 3 columnas y en la ultima hay un button con el onclick
                    filas_citas = driver.find_elements(By.CSS_SELECTOR, "table.control_citas tbody tr")
                    
                    for row_idx, fila in enumerate(filas_citas):
                        celdas = fila.find_elements(By.TAG_NAME, "td")
                        
                        if len(celdas) >= 3:
                            hora = celdas[0].text.strip()
                            lugar = celdas[1].text.strip()
                            
                            js_action = ""
                            try:
                                # Prioridad 1: boton onclick en toda la fila (muy común en SURA web)
                                btn = fila.find_elements(By.XPATH, ".//button[contains(@onclick, 'seleccionarCita')]")
                                if btn:
                                    js_action = btn[0].get_attribute("onclick")
                                else:
                                    # Prioridad 2: si hay cualquier enlace
                                    enlace = fila.find_elements(By.XPATH, ".//a[contains(@href, 'seleccionarCita')]")
                                    if enlace:
                                        js_action = enlace[0].get_attribute("href")
                            except Exception: 
                                pass
                            
                            if hora and lugar and "Horas (" not in hora:
                                citas_encontradas.append({
                                    'id_internal': f"{idx}_{row_idx}",
                                    'fecha': fecha_disp,
                                    'hora': hora,
                                    'doctor': doctor_name,
                                    'lugar': lugar,
                                    'js_action': js_action
                                })
                                
                if citas_encontradas:
                    update_callback(f"¡ÉXITO! Encontramos un total de {len(citas_encontradas)} espacios.")
                    if gui_callback:
                        gui_callback("update_table", citas_encontradas)     

                    if use_sound:
                        play_alert_sound()
                else:
                    update_callback("La pagina cargó con éxito pero no pintó filas reales en la tabla para agendar.")
                    if gui_callback:
                        gui_callback("update_table", [])

            except (TimeoutException, ValueError) as ex:
                update_callback("⚠️ No veo la tabla o la sesión se estancó pidiendo reiniciar. Refrescando (Workaround)...")
                if gui_callback:
                    gui_callback("update_table", [])
                
                try:
                    human_like_navigation(driver, update_callback, gui_callback)
                    driver.get(cita_url)
                    time.sleep(5)
                except Exception:
                    pass

            update_callback(f"Esperando {interval} segundos para iniciar nueva batida...")
            espera_restante = interval
            while espera_restante > 0:
                if stop_event.is_set():
                    break
                time.sleep(1)
                espera_restante -= 1

            count += 1

        if driver:
            driver.quit()
        if gui_callback: gui_callback("set_driver", None)
        update_callback("Monitor de Citas Detenido.")
    except Exception as e:
        if update_callback:
            update_callback(f"Error Fatal en el ciclo o Navegador:\\n{str(e)}")
        if driver:
            driver.quit()

class AlerterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Suramericana - Gestor de Citas Avanzado")
        self.root.geometry("900x700")

        self.style = ttk.Style()
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self.style.configure("TFrame", background="#f0f4f8")
        self.style.configure("TLabel", background="#f0f4f8", font=("Segoe UI", 10))
        self.style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), foreground="#004a8f")
        self.style.configure("TCheckbutton", background="#f0f4f8", font=("Segoe UI", 10))
        self.style.configure("TLabelframe", background="#f0f4f8", font=("Segoe UI", 10, "bold"))
        self.style.configure("TLabelframe.Label", background="#f0f4f8", font=("Segoe UI", 10, "bold"), foreground="#333333")
        self.style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=5)

        self.root.configure(bg="#f0f4f8")

        self.stop_event = threading.Event()
        self.worker_thread = None
        self.driver = None
        self.all_citas = []
        self.citas_map = {}

        self._build_gui()

    def gui_callback_handler(self, action, data):
        if action == "update_table":
            self.root.after(0, lambda: self.update_table(data))
        elif action == "update_profile":
            self.root.after(0, lambda: self._update_profile_text(data))
        elif action == "set_driver":
            self.driver = data

    def _update_profile_text(self, text_data):
        self.perfil_text.config(state=tk.NORMAL)
        self.perfil_text.delete(1.0, tk.END)
        self.perfil_text.insert(tk.END, text_data)
        self.perfil_text.config(state=tk.DISABLED)

    def update_table(self, data_list):
        self.all_citas = data_list
        self.apply_filters()

    def apply_filters(self, *args):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.citas_map.clear()
        filter_text = self.str_filter.get().lower()
        combo_filter = self.combo_filter_attr.get()
        
        for row in self.all_citas:
            match = False
            if not filter_text:
                match = True
            else:
                if combo_filter == "Médico" and filter_text in row['doctor'].lower(): match = True
                elif combo_filter == "Sede" and filter_text in row['lugar'].lower(): match = True
                elif combo_filter == "Día/Fecha" and filter_text in row['fecha'].lower(): match = True
                elif combo_filter == "Cualquiera":
                    if (filter_text in row['doctor'].lower() or 
                        filter_text in row['lugar'].lower() or 
                        filter_text in row['fecha'].lower() or
                        filter_text in row['hora'].lower()):
                        match = True

            if match:
                row_id = self.tree.insert("", "end", values=(row['fecha'], row['hora'], row['doctor'], row['lugar']))
                self.citas_map[row_id] = row

    def sort_column(self, col, reverse):
        try:
            l = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
            l.sort(reverse=reverse)
            for index, (val, k) in enumerate(l):
                self.tree.move(k, "", index)
            self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))
        except: pass

    def exec_agendar(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Atención", "Toca una cita de la tabla antes de darle a Agendar.")
            return

        cita_info = self.citas_map.get(selected_item[0])
        if cita_info and self.driver:
            js_code = cita_info.get("js_action", "")
            if not js_code:
                messagebox.showerror("Error", "La tabla cargó esta cita pero parece no tener el botón de confirmación extraído correctamente.\\nProbablemente debas agendarla viendo la tabla en modo No-Oculto.")
                return

            confirm = messagebox.askyesno("Confirmar Agendamiento", f"¿Seguro que deseas agendar la cita para:\\n\\n{cita_info['fecha']}\\na las {cita_info['hora']}?")
            if confirm:
                try:
                    self.log(f"Inyectando acción de la tabla en navegador...")
                    clean_js = js_code.replace("javascript:", "").replace("JavaScript:", "")
                    self.driver.execute_script(clean_js)
                    messagebox.showinfo("Cita en Proceso", "Comando enviado al navegador de Sura.")
                except Exception as e:
                    messagebox.showerror("Error Ejecutando JS", f"No se pudo ejecutar: {str(e)}")
        else:
            messagebox.showerror("Error de Sesión", "No hay navegador activo conectado actualmente a la ventana.")

    def _build_gui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header_frame, text="Gestor de Citas SURA", style="Title.TLabel").pack(side=tk.LEFT)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_monitor = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.tab_monitor, text="🔍 Buscar Citas Disponibles")

        self.tab_profile = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.tab_profile, text="🗓️ Mis Citas Activas (Perfil SURA)")

        self._build_monitor_tab()
        self._build_profile_tab()

    def _build_monitor_tab(self):
        paned = ttk.PanedWindow(self.tab_monitor, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=5)

        left_panel = ttk.Frame(paned)
        right_panel = ttk.Frame(paned)
        paned.add(left_panel, weight=1)
        paned.add(right_panel, weight=3)

        filtros_frame = ttk.LabelFrame(left_panel, text=" Rango Chequeo ", padding="10")
        filtros_frame.pack(fill=tk.X, pady=5)

        ttk.Label(filtros_frame, text="Revisar cada (seg):").pack(anchor=tk.W)
        self.interval_var = tk.IntVar(value=30)
        ttk.Spinbox(filtros_frame, from_=10, to=3600, textvariable=self.interval_var, width=10).pack(anchor=tk.W, pady=2)

        prefs_frame = ttk.LabelFrame(left_panel, text=" Preferencias ", padding="10")
        prefs_frame.pack(fill=tk.X, pady=5)

        self.headless_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(prefs_frame, text="Navegador Oculto", variable=self.headless_var).pack(anchor=tk.W, pady=2)

        self.sound_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(prefs_frame, text="Sonido de Alerta", variable=self.sound_var).pack(anchor=tk.W, pady=2)

        btn_frame = ttk.Frame(left_panel)
        btn_frame.pack(fill=tk.X, pady=(15, 5))

        self.btn_start = ttk.Button(btn_frame, text="▶ Iniciar", command=self.start_monitoring, style="Action.TButton")
        self.btn_start.pack(fill=tk.X, pady=2)

        self.btn_stop = ttk.Button(btn_frame, text="⏹ Detener", command=self.stop_monitoring, state=tk.DISABLED, style="Action.TButton")
        self.btn_stop.pack(fill=tk.X, pady=2)

        results_frame = ttk.LabelFrame(right_panel, text=" Citas Disponibles (Clic en Cabeceras para Ordenar) ", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        filter_bar = ttk.Frame(results_frame)
        filter_bar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(filter_bar, text="Filtrar por:").pack(side=tk.LEFT, padx=2)
        self.combo_filter_attr = ttk.Combobox(filter_bar, values=["Cualquiera", "Día/Fecha", "Médico", "Sede"], width=10, state="readonly")
        self.combo_filter_attr.current(0)
        self.combo_filter_attr.pack(side=tk.LEFT, padx=2)
        self.combo_filter_attr.bind("<<ComboboxSelected>>", self.apply_filters)

        self.str_filter = tk.StringVar()
        self.str_filter.trace("w", self.apply_filters)
        ttk.Entry(filter_bar, textvariable=self.str_filter, width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(filter_bar, text="Limpiar", command=lambda: self.str_filter.set("")).pack(side=tk.LEFT, padx=2)

        columns = ("Fecha", "Hora", "Especialidad/Doctor", "Lugar")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_column(c, False))
            self.tree.column(col, width=120)
        self.tree.pack(fill=tk.BOTH, expand=True)

        ttk.Button(results_frame, text="✅ Agendar Seleccionada Ahora", command=self.exec_agendar, style="Action.TButton").pack(pady=5, anchor=tk.E)

        log_frame = ttk.LabelFrame(right_panel, text=" Visor de Estado ", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = tk.Text(log_frame, height=5, state=tk.DISABLED, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9), relief=tk.FLAT)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _build_profile_tab(self):
        info_lbl = ttk.Label(self.tab_profile, text="Información de Citas extraídas de SURA durante el chequeo:", font=("Segoe UI", 11, "bold"))
        info_lbl.pack(anchor=tk.W, pady=10)

        self.perfil_text = tk.Text(self.tab_profile, wrap=tk.WORD, font=("Segoe UI", 10), bg="#ffffff", relief=tk.SOLID, height=20)
        self.perfil_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.perfil_text.insert(tk.END, "Esperando inicio del sistema...\\n\\n(Las citas vigentes se actualizarán aquí automáticamente)")
        self.perfil_text.config(state=tk.DISABLED)

    def log(self, message):
        self.root.after(0, self._append_log, message)

    def _append_log(self, message):
        self.log_text.config(state=tk.NORMAL)
        current_time = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{current_time}] {message}\\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def start_monitoring(self):
        try:
            intervalo = self.interval_var.get()
            if intervalo < 10: intervalo = 60
        except:
            intervalo = 30

        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

        self.stop_event.clear()
        self.log("Navegador inicializado.")

        headless = self.headless_var.get()
        use_sound = self.sound_var.get()
        use_popup = True

        self.worker_thread = threading.Thread(
            target=check_appointments,
            args=(headless, 30, "", intervalo, use_popup, use_sound, self.stop_event, self.log, self.gui_callback_handler),
            daemon=True
        )
        self.worker_thread.start()

    def stop_monitoring(self):
        self.log("Cancelando proceso...")
        self.stop_event.set()
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = AlerterGUI(root)
    root.mainloop()
'''

with open(r"c:\Users\wumiw\Downloads\message\alerter\gui_app.py", "w", encoding="utf-8") as f:
    f.write(codigo)
