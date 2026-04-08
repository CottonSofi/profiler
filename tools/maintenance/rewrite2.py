import sys

content = r'''import tkinter as tk
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
        print("\a") # Beep fallback

def load_cookies(driver, filepath):
    if not os.path.exists(filepath):
        return False
    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.strip().split("\t")
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
        filas = driver.find_elements(By.CSS_SELECTOR, "table.control_citas tbody tr")
        perfil_info = ""
        if filas and len(filas) > 0:
            perfil_info = f"Tienes {len(filas)} citas vigentes:\n\n"
            for i, fila in enumerate(filas):
                celdas = fila.find_elements(By.TAG_NAME, "td")  
                if len(celdas) >= 4:
                    fecha = celdas[0].text.strip()
                    servicio = celdas[2].text.strip()
                    doctor = celdas[3].text.strip()
                    perfil_info += f"➤ Cita {i+1}: {fecha}\nServicio: {servicio}\nDoctor: {doctor}\n\n"
        else:
            perfil_info = "No tienes citas programadas actualmente en el sistema."

        if gui_callback:
            gui_callback("update_profile", perfil_info)
    except Exception as e:
        if gui_callback:
            gui_callback("update_profile", "No se pudo extraer la info del perfil actualmente.")

    time.sleep(2)

def check_appointments(headless=True, days_ahead=30, specific_date="", interval=60, use_popup=True, use_sound=True, stop_event=None, update_callback=None, gui_callback=None):
    try:
        base_domain_url = "https://agendaweb.suramericana.com"
        cita_url = "https://agendaweb.suramericana.com/agenda/internet/internet-asignarCita.do#no-back-button"

        if not HAS_SELENIUM:
            update_callback("ERROR CRÍTICO: La librería Selenium no está instalada.")
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
        
        # Compartir el driver con la GUI para poder ejecutar Agendar
        if gui_callback:
            gui_callback("set_driver", driver)

        update_callback("Cargando sesión (Cookies)...")
        driver.get(base_domain_url)
        time.sleep(3)

        cookie_path = os.path.join(os.path.dirname(__file__), "cookies", "agendaweb.suramericana.com_cookies.txt")
        if not os.path.exists(cookie_path):
            cookie_path = os.path.join(os.getcwd(), "alerter", "cookies", "agendaweb.suramericana.com_cookies.txt")

        if load_cookies(driver, cookie_path):
            update_callback("✅ Cookies cargadas correctamente.")
        else:
            update_callback("⚠️ Problema con las cookies de sesión.")

        human_like_navigation(driver, update_callback, gui_callback)

        update_callback("Ingresando a Asignación de Citas...")
        driver.get(cita_url)
        time.sleep(4)

        count = 0
        while not stop_event.is_set():
            update_callback(f"[{count+1}] Revisando disponibilidad...")

            try:
                btn_previa = driver.find_elements(By.XPATH, "//button[contains(@onclick, 'consultarDisponibilidadCitas()')]")
                if btn_previa:
                    update_callback("-> Pantalla previa detectada. Avanzando...")
                    driver.execute_script("consultarDisponibilidadCitas();")    
                    time.sleep(2)
                    driver.execute_script("consultarDisponibilidadCitasResolucion();")
                    time.sleep(6)
            except Exception:
                pass

            try:
                select_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "listaDisponibilidad"))
                )

                select = Select(select_element)
                opciones = select.options

                if len(opciones) <= 1:
                    raise ValueError("Desplegable vacío.")

                citas_encontradas = []
                
                # Iteramos sobre varias fechas/médicos para tenerlas TODAS en la GUI (Multiplexado)
                max_opciones_a_revisar = min(len(opciones), 6) # Extrae los primeros 5 grupos sin demorar tanto
                
                for idx in range(1, max_opciones_a_revisar):
                    option = opciones[idx]
                    option_text = option.text
                    update_callback(f"Extrayendo bloque {idx}: {option_text}")
                    select.select_by_index(idx)
                    
                    try:
                        driver.execute_script("if(typeof consultarCitasDisponibles === 'function') consultarCitasDisponibles();")
                    except:
                        pass
                    
                    time.sleep(5)
                    
                    doc_parts = option_text.split(" - ")
                    doctor_name = doc_parts[0].strip() if len(doc_parts) > 0 else "Médico"
                    fecha_disp = doc_parts[1].strip() if len(doc_parts) > 1 else "Fecha"

                    filas_citas = driver.find_elements(By.CSS_SELECTOR, "table.control_citas tbody tr")
                    
                    for row_idx, fila in enumerate(filas_citas):
                        celdas = fila.find_elements(By.TAG_NAME, "td")
                        
                        if len(celdas) >= 3:
                            hora = celdas[0].text.strip()
                            lugar = celdas[1].text.strip()
                            
                            # Intentar sacar enlace para agendar (click)
                            js_action = ""
                            try:
                                if len(celdas) >= 4:
                                    enlace = celdas[3].find_element(By.TAG_NAME, "a")
                                    js_action = enlace.get_attribute("href")
                            except: pass
                            
                            if hora and lugar:
                                citas_encontradas.append({
                                    'id_internal': f"{idx}_{row_idx}",
                                    'fecha': fecha_disp,
                                    'hora': hora,
                                    'doctor': doctor_name,
                                    'lugar': lugar,
                                    'js_action': js_action
                                })
                                
                if citas_encontradas:
                    update_callback(f"¡ÉXITO! Se extrajeron {len(citas_encontradas)} citas conjuntas.")
                    if gui_callback:
                        gui_callback("update_table", citas_encontradas)     

                    if use_sound:
                        play_alert_sound()
                else:
                    update_callback("Las tablas cargaron pero no hay filas válidas.")
                    if gui_callback:
                        gui_callback("update_table", [])

            except (TimeoutException, ValueError) as ex:
                update_callback("⚠️ La tabla quedó atrapada en blanco o sesion caducada. Aplicando contramedida...")
                if gui_callback:
                    gui_callback("update_table", [])
                
                try:
                    human_like_navigation(driver, update_callback, gui_callback)
                    driver.get(cita_url)
                    time.sleep(5)
                except Exception as e:
                    update_callback(f"Error re-orientando: {e}")   

            update_callback(f"Esperando {interval} segundos para el próximo chequeo general...")
            espera_restante = interval
            while espera_restante > 0:
                if stop_event.is_set():
                    break
                time.sleep(1)
                espera_restante -= 1

            count += 1

        driver.quit()
        if gui_callback: gui_callback("set_driver", None)
        update_callback("Proceso y navegador detenidos.")
    except Exception as e:
        if update_callback:
            update_callback(f"ERROR INESPERADO:\n{traceback.format_exc()}")     

class AlerterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Suramericana - Gestor de Citas Avanzado")
        self.root.geometry("900x750")

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
        self.perfil_data = "El sistema extraerá tus citas vigentes al iniciar el navegador..."
        self.driver = None
        self.all_citas = []
        self.citas_map = {}

        self._build_gui()

    def gui_callback_handler(self, action, data):
        if action == "update_table":
            self.root.after(0, lambda: self.update_table(data))
        elif action == "update_profile":
            self.perfil_data = data
            self.root.after(0, lambda: self.btn_perfil.config(text="👤 Ver Mi Perfil / Citas Activas (Actualizado)"))
        elif action == "set_driver":
            self.driver = data

    def update_table(self, data_list):
        self.all_citas = data_list
        self.apply_filters()

    def apply_filters(self, *args):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.citas_map.clear()
        filter_text = self.str_filter.get().lower()
        
        for row in self.all_citas:
            if (not filter_text or 
                filter_text in row['doctor'].lower() or 
                filter_text in row['lugar'].lower() or 
                filter_text in row['fecha'].lower() or
                filter_text in row['hora'].lower()):
                row_id = self.tree.insert("", "end", values=(row['fecha'], row['hora'], row['doctor'], row['lugar']))
                self.citas_map[row_id] = row

    def sort_column(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l):
            self.tree.move(k, "", index)
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def exec_agendar(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Atención", "Selecciona una cita de la tabla antes de agendar.")
            return

        cita_info = self.citas_map.get(selected_item[0])
        if cita_info and self.driver:
            js_code = cita_info.get("js_action", "")
            if not js_code:
                messagebox.showerror("Error", "La cita seleccionada no tiene accion de JavaScript cargada.")
                return

            confirm = messagebox.askyesno("Confirmar Agendamiento", f"¿Seguro que deseas agendar la cita para {cita_info['fecha']} a las {cita_info['hora']}?")
            if confirm:
                try:
                    self.log(f"Ejecutando Agendamiento: {js_code[:40]}...")
                    clean_js = js_code.replace("javascript:", "")
                    self.driver.execute_script(clean_js)
                    messagebox.showinfo("Cita en Proceso", "Comando enviado. Revisa Suramericana para confirmar si se asignó con éxito.")
                except Exception as e:
                    messagebox.showerror("Error de Script", f"No se pudo ejecutar: {str(e)}")
        else:
            messagebox.showerror("Error", "No hay navegador activo o datos inválidos.")

    def show_profile(self):
        top = tk.Toplevel(self.root)
        top.title("Mis Citas Activas (Perfil SURA)")
        top.geometry("450x300")
        top.configure(bg="#f0f4f8")
        
        ttk.Label(top, text="Tus Citas Programadas", font=("Segoe UI", 12, "bold"), background="#f0f4f8").pack(pady=10)
        
        txt = tk.Text(top, wrap=tk.WORD, font=("Segoe UI", 10), bg="#ffffff")
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        txt.insert(tk.END, self.perfil_data)
        txt.config(state=tk.DISABLED)
        
        ttk.Button(top, text="Cerrar", command=top.destroy).pack(pady=10)

    def _build_gui(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text=" Gestor de Citas Sura", style="Title.TLabel").pack(side=tk.LEFT)

        self.btn_perfil = ttk.Button(header_frame, text="👤 Ver Mi Perfil / Citas Activas", command=self.show_profile)
        self.btn_perfil.pack(side=tk.RIGHT, padx=2)

        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=5)

        left_panel = ttk.Frame(paned)
        right_panel = ttk.Frame(paned)
        paned.add(left_panel, weight=1)
        paned.add(right_panel, weight=2)

        filtros_frame = ttk.LabelFrame(left_panel, text=" Opciones de Búsqueda ", padding="10")
        filtros_frame.pack(fill=tk.X, pady=5)

        ttk.Label(filtros_frame, text="Intervalo de revisión (seg):").pack(anchor=tk.W)
        self.interval_var = tk.IntVar(value=60)
        ttk.Spinbox(filtros_frame, from_=10, to=3600, textvariable=self.interval_var, width=10).pack(anchor=tk.W, pady=2)

        prefs_frame = ttk.LabelFrame(left_panel, text=" Preferencias ", padding="10")
        prefs_frame.pack(fill=tk.X, pady=5)

        self.headless_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(prefs_frame, text="Modo Oculto (Fondo)", variable=self.headless_var).pack(anchor=tk.W, pady=2)

        self.sound_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(prefs_frame, text="Alerta de Sonido", variable=self.sound_var).pack(anchor=tk.W, pady=2)

        self.popup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(prefs_frame, text="Popup de Aviso", variable=self.popup_var).pack(anchor=tk.W, pady=2)

        btn_frame = ttk.Frame(left_panel)
        btn_frame.pack(fill=tk.X, pady=(15, 5))

        self.btn_start = ttk.Button(btn_frame, text="▶ Iniciar Monitor", command=self.start_monitoring, style="Action.TButton")
        self.btn_start.pack(fill=tk.X, pady=2)

        self.btn_stop = ttk.Button(btn_frame, text="⏹ Detener", command=self.stop_monitoring, state=tk.DISABLED, style="Action.TButton")
        self.btn_stop.pack(fill=tk.X, pady=2)

        results_frame = ttk.LabelFrame(right_panel, text=" Disponibilidad Encontrada (Multiplexada) ", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        filter_bar = ttk.Frame(results_frame)
        filter_bar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(filter_bar, text="Filtrar Médico/Día/Lugar:").pack(side=tk.LEFT, padx=2)
        self.str_filter = tk.StringVar()
        self.str_filter.trace("w", self.apply_filters)
        ttk.Entry(filter_bar, textvariable=self.str_filter, width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(filter_bar, text="Limpiar", command=lambda: self.str_filter.set("")).pack(side=tk.LEFT, padx=2)
        ttk.Label(filter_bar, text="(Click en cabecera para Ordenar)").pack(side=tk.RIGHT, padx=2)

        columns = ("Fecha", "Hora", "Especialidad/Doctor", "Lugar")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_column(c, False))
            self.tree.column(col, width=120)
        self.tree.pack(fill=tk.BOTH, expand=True)

        ttk.Button(results_frame, text="✔️ Agendar Seleccionada en este Instante", command=self.exec_agendar, style="Action.TButton").pack(pady=5, anchor=tk.E)

        log_frame = ttk.LabelFrame(right_panel, text=" Logs del Sistema ", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = tk.Text(log_frame, height=6, state=tk.DISABLED, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9), relief=tk.FLAT)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def log(self, message):
        self.root.after(0, self._append_log, message)

    def _append_log(self, message):
        self.log_text.config(state=tk.NORMAL)
        current_time = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{current_time}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def start_monitoring(self):
        try:
            intervalo = self.interval_var.get()
            if intervalo < 10: intervalo = 60
        except:
            intervalo = 60

        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

        self.stop_event.clear()
        self.log("Búsqueda iniciada. Acoplando múltiples agendas...")

        headless = self.headless_var.get()
        use_sound = self.sound_var.get()
        use_popup = self.popup_var.get()

        self.worker_thread = threading.Thread(
            target=check_appointments,
            args=(headless, 30, "", intervalo, use_popup, use_sound, self.stop_event, self.log, self.gui_callback_handler),
            daemon=True
        )
        self.worker_thread.start()

    def stop_monitoring(self):
        self.log("Deteniendo búsquedas...")
        self.stop_event.set()
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = AlerterGUI(root)
    root.mainloop()
'''

with open(r'c:\Users\wumiw\Downloads\message\alerter\gui_app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
