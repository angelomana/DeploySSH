import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import os
import datetime as dt
import paramiko
import sys
import shutil
from ttkthemes import ThemedTk
import threading
import queue
import base64

# Dependencia externa, requiere: pip install cryptography
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

class CryptoManager:
    """Gestiona el cifrado y descifrado de datos usando una contraseña maestra."""
    def __init__(self, password: str, salt: bytes):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.fernet = Fernet(key)

    def encrypt(self, data: str) -> str:
        if not data:
            return ""
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        if not encrypted_data:
            return ""
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return "DECRYPT_FAILED"

class GUIAuthHandler(paramiko.auth_handler.AuthHandler):
    """Manejador para la autenticación interactiva (2FA) que muestra un diálogo en la GUI."""
    def __init__(self, root: tk.Tk, mfa_queue: queue.Queue):
        self.root = root
        self.mfa_queue = mfa_queue
        # CORRECCIÓN: El super().__init__ no es necesario aquí y causaba un error.
    
    def __call__(self, title, instructions, prompt_list):
        # pylint: disable=unused-argument
        self.root.after(0, self.ask_for_code, title, prompt_list)
        response = self.mfa_queue.get()
        return [response] if response is not None else []

    def ask_for_code(self, title, prompt_list):
        prompt_text = prompt_list[0][0] if prompt_list else "Código de Verificación:"
        code = simpledialog.askstring(title, prompt_text, parent=self.root)
        self.mfa_queue.put(code)

class UtilitiesWindow(tk.Toplevel):
    """Ventana secundaria para gestionar y ver comandos de utilería."""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Utilerias")
        self.geometry("900x600")
        self.minsize(600, 400)
        self.transient(parent)
        self.grab_set()
        self.json_path = "utilities.json"
        self.utilities_data: list[dict] = []
        self.selected_item_index: int | None = None
        self.columns = ('Categoria', 'Comando', 'Descripcion', 'Ejemplo')
        self.search_var = tk.StringVar()
        self._search_after_id: str | None = None
        self.search_var.trace_add("write", self.schedule_filter_update)
        self.load_utilities_data()
        self.create_widgets()
        self.populate_table()

    def load_utilities_data(self):
        default_data = [{'Categoria': 'Gestión de Carpetas', 'Comando': 'ls', 'Descripcion': 'Lista el contenido de un directorio.', 'Ejemplo': 'ls -l (lista detallada)\nls -la (lista detallada con archivos ocultos)'}, {'Categoria': 'Gestión de Carpetas', 'Comando': 'cd', 'Descripcion': 'Cambia de directorio (navegar).', 'Ejemplo': 'cd /var/log\ncd ~ (ir al directorio home)\ncd .. (subir un nivel)'}, {'Categoria': 'Gestión de Permisos', 'Comando': 'chmod', 'Descripcion': 'Cambia los permisos.', 'Ejemplo': 'chmod 755 script.sh'}]
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.utilities_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.utilities_data = default_data
            self.save_utilities_data()

    def save_utilities_data(self):
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(self.utilities_data, f, indent=4, ensure_ascii=False)

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10"); main_frame.pack(fill="both", expand=True)
        main_frame.grid_rowconfigure(2, weight=1); main_frame.grid_columnconfigure(0, weight=1)
        filter_frame = ttk.Frame(main_frame); filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10)); filter_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(filter_frame, text="Buscar:").grid(row=0, column=0, padx=(0, 5))
        ttk.Entry(filter_frame, textvariable=self.search_var).grid(row=0, column=1, sticky="ew")
        button_frame = ttk.Frame(main_frame); button_frame.grid(row=1, column=0, sticky="ew", pady=(0, 5)); button_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        ttk.Button(button_frame, text="Agregar", command=self.open_add_edit_popup).grid(row=0, column=0, padx=2, sticky="ew")
        ttk.Button(button_frame, text="Editar", command=lambda: self.open_add_edit_popup(edit_mode=True)).grid(row=0, column=1, padx=2, sticky="ew")
        ttk.Button(button_frame, text="Eliminar", command=self.delete_utility).grid(row=0, column=2, padx=2, sticky="ew")
        self.copy_button = ttk.Button(button_frame, text="Copiar Comando", command=self.copy_selected_command)
        self.copy_button.grid(row=0, column=3, padx=2, sticky="ew")
        table_frame = ttk.Frame(main_frame); table_frame.grid(row=2, column=0, sticky="nsew"); table_frame.grid_rowconfigure(0, weight=1); table_frame.grid_columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(table_frame, columns=self.columns, show="headings")
        for col in self.columns:
            self.tree.heading(col, text=col)
            # CORRECCIÓN: Se reescribe el if/else para que sea más claro y no un "ternary"
            if col in ['Descripcion', 'Ejemplo']:
                self.tree.column(col, width=220, minwidth=120)
            else:
                self.tree.column(col, width=120, minwidth=80)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        yscrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview); xscrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscrollbar.set, xscrollcommand=xscrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew"); yscrollbar.grid(row=0, column=1, sticky="ns"); xscrollbar.grid(row=1, column=0, sticky="ew")

    def copy_selected_command(self):
        if self.selected_item_index is None: messagebox.showwarning("Sin Selección", "Por favor, seleccione un comando para copiar.", parent=self); return
        if command_text := self.utilities_data[self.selected_item_index].get("Comando", ""):
            self.clipboard_clear(); self.clipboard_append(command_text)
            original_text = self.copy_button.cget("text"); self.copy_button.config(text="¡Copiado!")
            self.after(2000, lambda: self.copy_button.config(text=original_text))

    def on_tree_select(self, event):
        # pylint: disable=unused-argument
        if selected_items := self.tree.selection():
            values = self.tree.item(selected_items[0], 'values'); self.selected_item_index = next((i for i, item in enumerate(self.utilities_data) if item["Comando"] == values[1]), None)

    def populate_table(self, data=None):
        data = data if data is not None else self.utilities_data
        self.tree.delete(*self.tree.get_children()); self.selected_item_index = None
        for item in data: self.tree.insert("", "end", values=[item.get(col, "") for col in self.columns])

    def schedule_filter_update(self, *args):
        # pylint: disable=unused-argument
        if self._search_after_id: self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(300, self.filter_table)

    def filter_table(self):
        search_term = self.search_var.get().lower()
        self.populate_table([item for item in self.utilities_data if any(search_term in str(value).lower() for value in item.values())] if search_term else self.utilities_data)

    def delete_utility(self):
        if self.selected_item_index is None: messagebox.showwarning("Advertencia", "Por favor, seleccione un comando para eliminar.", parent=self); return
        if messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar el comando '{self.utilities_data[self.selected_item_index]['Comando']}'?", parent=self):
            del self.utilities_data[self.selected_item_index]; self.save_utilities_data(); self.filter_table()

    def open_add_edit_popup(self, edit_mode=False):
        if edit_mode and self.selected_item_index is None: messagebox.showwarning("Advertencia", "Por favor, seleccione un comando para editar.", parent=self); return
        popup = tk.Toplevel(self); popup.transient(self); popup.grab_set(); popup.title("Editar Comando" if edit_mode else "Agregar Comando")
        record = self.utilities_data[self.selected_item_index] if edit_mode and self.selected_item_index is not None else {col: "" for col in self.columns}
        entry_vars = {}
        for i, col in enumerate(self.columns):
            ttk.Label(popup, text=f"{col}:").grid(row=i*2, column=0, padx=10, pady=5, sticky="w")
            if col in ['Descripcion', 'Ejemplo']:
                entry = tk.Text(popup, height=4, width=40, wrap="word"); entry.insert("1.0", record.get(col, "")); entry.grid(row=i*2+1, column=0, columnspan=2, padx=10, pady=2, sticky="ew")
            else:
                entry = ttk.Entry(popup, textvariable=tk.StringVar(value=record.get(col, "")), width=50); entry.grid(row=i*2+1, column=0, columnspan=2, padx=10, pady=2, sticky="ew")
            entry_vars[col] = entry
        def on_save():
            new_data = {col: widget.get("1.0", "end-1c") if isinstance(widget, tk.Text) else widget.get() for col, widget in entry_vars.items()}
            if not new_data.get("Comando"): messagebox.showerror("Error", "El campo 'Comando' es obligatorio.", parent=popup); return
            if edit_mode and self.selected_item_index is not None: self.utilities_data[self.selected_item_index] = new_data
            else: self.utilities_data.append(new_data)
            self.save_utilities_data(); self.filter_table(); popup.destroy()
        ttk.Button(popup, text="Guardar", command=on_save).grid(row=len(self.columns)*2, column=0, columnspan=2, pady=10)

class JsonTableApp:
    DEFAULT_COLUMNS_ORDER = [ "id", "hostname", "tag", "ip", "user", "auth_method", "password", "key_path", "port", "cargar", "subir" ]
    COLUMN_LABELS = { "id": "ID", "hostname": "Hostname", "tag": "Tag", "ip": "IP", "user": "Usuario", "auth_method": "Método Auth", "password": "Password / Passphrase", "key_path": "Ruta de Llave SSH", "port": "Puerto", "cargar": "Cargar (Archivo Origen)", "subir": "Subir (Ruta Destino Absoluta)" }
    SALT = b'\x12\xfa\x8e\x90\x1a\xde\xcc\xee\x11\x22\x33\x44\x55\x66\x77\x88'
    
    def __init__(self, root: ThemedTk):
        self.root = root
        self.initialized_ok = False
        master_password = simpledialog.askstring("Seguridad", "Ingrese su Contraseña Maestra:", show='*')
        if not master_password:
            return
        self.crypto = CryptoManager(master_password, self.SALT)
        self.root.set_theme("arc") 
        self.root.title("KIOsko")
        try:
            self.root.iconbitmap("uno.ico")
        except tk.TclError: print("No se pudo encontrar el archivo 'uno.ico'.")
        self.root.geometry("1400x700")
        self.root.minsize(900, 500) 
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # --- Declaración de Atributos con Tipos ---
        self.json_file_path = "ssh_configs.json"; self.deploy_source_folder = "deploy"; self.log_folder = "logs"; self.error_log_folder = os.path.join(self.log_folder, "errors")
        os.makedirs(self.deploy_source_folder, exist_ok=True); os.makedirs(self.log_folder, exist_ok=True); os.makedirs(self.error_log_folder, exist_ok=True)
        self.tree: ttk.Treeview | None = None
        self.data: list[dict] = []
        self.checked_items: dict[str, bool] = {}
        self.entry_fields: dict[str, tk.Widget] = {}
        self.log_text_widget: tk.Text | None = None
        self.error_log_widget: tk.Text | None = None
        self.commands_text_area: tk.Text | None = None
        self.columns = ["*"] + self.DEFAULT_COLUMNS_ORDER
        self.search_var = tk.StringVar(); self._search_after_id: str | None = None; self.search_var.trace_add("write", self.schedule_filter_update)
        self.mfa_queue: "queue.Queue[str | None]" = queue.Queue()
        self.select_all_var = tk.BooleanVar()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        self.create_widgets()
        if not self.load_json_data():
            return
        self.filter_table() 
        self.load_today_log()
        sys.stdout = self.TextRedirector(self.log_text_widget, 'stdout')
        sys.stderr = self.TextRedirector(self.error_log_widget, 'stderr')
        self.initialized_ok = True

    # ... (El resto de la clase JsonTableApp con todas las correcciones)
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10"); main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=1); main_frame.grid_rowconfigure(1, weight=0); main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=3); main_frame.grid_columnconfigure(1, weight=1, minsize=350)
        left_panel = ttk.Frame(main_frame); left_panel.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(0, 5))
        left_panel.grid_rowconfigure(0, weight=1); left_panel.grid_rowconfigure(1, weight=0); left_panel.grid_rowconfigure(2, weight=1); left_panel.grid_columnconfigure(0, weight=1)
        table_frame = ttk.LabelFrame(left_panel, text="Servidores"); table_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        table_frame.grid_rowconfigure(1, weight=1); table_frame.grid_columnconfigure(0, weight=1)
        filter_frame = ttk.Frame(table_frame); filter_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5); filter_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(filter_frame, text="Buscar:").grid(row=0, column=0, padx=(0, 5))
        ttk.Entry(filter_frame, textvariable=self.search_var).grid(row=0, column=1, sticky="ew")
        ttk.Button(filter_frame, text="Limpiar", command=self.clear_filter).grid(row=0, column=2, padx=(5, 0))
        self.select_all_checkbutton = ttk.Checkbutton(filter_frame, text="Seleccionar Visibles", variable=self.select_all_var, command=self.toggle_select_all)
        self.select_all_checkbutton.grid(row=0, column=3, padx=(10, 0))
        yscrollbar_table = ttk.Scrollbar(table_frame, orient="vertical"); xscrollbar_table = ttk.Scrollbar(table_frame, orient="horizontal")
        self.tree = ttk.Treeview(table_frame, yscrollcommand=yscrollbar_table.set, xscrollcommand=xscrollbar_table.set, show="headings")
        yscrollbar_table.config(command=self.tree.yview); xscrollbar_table.config(command=self.tree.xview)
        self.tree.grid(row=1, column=0, sticky="nsew"); yscrollbar_table.grid(row=1, column=1, sticky="ns"); xscrollbar_table.grid(row=2, column=0, sticky="ew")
        self.tree.bind("<Button-1>", self.on_item_click); self.tree.bind("<Double-1>", self.edit_record_popup)
        button_frame = ttk.Frame(left_panel); button_frame.grid(row=1, column=0, sticky="ew", pady=5); button_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        ttk.Button(button_frame, text="Agregar", command=self.add_record_popup).grid(row=0, column=0, sticky="ew", padx=2)
        ttk.Button(button_frame, text="Editar", command=self.edit_selected_record).grid(row=0, column=1, sticky="ew", padx=2)
        ttk.Button(button_frame, text="Eliminar", command=self.delete_selected_records).grid(row=0, column=2, sticky="ew", padx=2)
        ttk.Button(button_frame, text="Cargar Archivo", command=self.load_file_for_deploy).grid(row=0, column=3, sticky="ew", padx=2)
        ttk.Button(button_frame, text="Utilerias", command=self.open_utilities_window).grid(row=0, column=4, sticky="ew", padx=2)
        log_frame = ttk.LabelFrame(left_panel, text="Registro de Actividad"); log_frame.grid(row=2, column=0, sticky="nsew", pady=(5, 0))
        log_frame.grid_rowconfigure(0, weight=1); log_frame.grid_columnconfigure(0, weight=1)
        self.log_text_widget = tk.Text(log_frame, wrap="word", state="disabled", bg="black", fg="white", font=("Courier New", 9)); log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text_widget.yview)
        self.log_text_widget.config(yscrollcommand=log_scrollbar.set); log_scrollbar.pack(side="right", fill="y"); self.log_text_widget.pack(side="left", fill="both", expand=True)
        right_panel = ttk.Frame(main_frame); right_panel.grid(row=0, column=1, rowspan=3, sticky="nsew", padx=(5, 0))
        right_panel.grid_rowconfigure(0, weight=1); right_panel.grid_rowconfigure(1, weight=0); right_panel.grid_columnconfigure(0, weight=1)
        error_log_frame = ttk.LabelFrame(right_panel, text="Errores de Conexión / Despliegue"); error_log_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        error_log_frame.grid_rowconfigure(0, weight=1); error_log_frame.grid_columnconfigure(0, weight=1)
        self.error_log_widget = tk.Text(error_log_frame, wrap="word", state="disabled", bg="#5e0000", fg="white", font=("Courier New", 9)); error_log_scrollbar = ttk.Scrollbar(error_log_frame, orient="vertical", command=self.error_log_widget.yview)
        self.error_log_widget.config(yscrollcommand=error_log_scrollbar.set); error_log_scrollbar.pack(side="right", fill="y"); self.error_log_widget.pack(side="left", fill="both", expand=True)
        commands_frame = ttk.LabelFrame(right_panel, text="Comandos a Enviar"); commands_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        commands_frame.grid_rowconfigure(0, weight=1); commands_frame.grid_rowconfigure(1, weight=0); commands_frame.grid_columnconfigure(0, weight=1)
        self.commands_text_area = tk.Text(commands_frame, wrap="word", height=6, font=("Courier New", 9)); commands_scrollbar = ttk.Scrollbar(commands_frame, orient="vertical", command=self.commands_text_area.yview)
        self.commands_text_area.config(yscrollcommand=commands_scrollbar.set); self.commands_text_area.grid(row=0, column=0, sticky="nsew", padx=5, pady=5); commands_scrollbar.grid(row=0, column=1, sticky="ns")
        ttk.Button(commands_frame, text="Lanzar Actividad", command=self.start_ssh_thread).grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
    def open_utilities_window(self): _ = UtilitiesWindow(self.root)
    def clear_filter(self): self.search_var.set("")
    def schedule_filter_update(self, *args):
        # pylint: disable=unused-argument
        if self._search_after_id: self.root.after_cancel(self._search_after_id)
        self._search_after_id = self.root.after(300, self.filter_table)
    def filter_table(self):
        search_term = self.search_var.get().lower()
        self.populate_table([r for r in self.data if any(search_term in str(v).lower() for k, v in r.items() if k != 'password')] if search_term else self.data)
    def toggle_select_all(self):
        new_state = self.select_all_var.get()
        for item_id in self.tree.get_children(): self.checked_items[item_id],_ = new_state, self.update_selection_marker(item_id, new_state)
    def update_select_all_state(self):
        items = self.tree.get_children()
        if not items: self.select_all_checkbutton.state(['!alternate']); self.select_all_var.set(False); return
        is_all = all(self.checked_items.get(i, False) for i in items)
        self.select_all_checkbutton.state(['!alternate']); self.select_all_var.set(is_all)
        if not is_all and any(self.checked_items.get(i, False) for i in items): self.select_all_checkbutton.state(['alternate'])
    def on_item_click(self, event):
        if (item_id := self.tree.identify_row(event.y)) and self.tree.identify_region(event.x, event.y) == "cell" and self.tree.identify_column(event.x) == "#0":
            new_state = not self.checked_items.get(item_id, False); self.checked_items[item_id] = new_state
            self.update_selection_marker(item_id, new_state); self.update_select_all_state()
    def _get_next_id(self):
        return (max(int(r.get('id',0)) for r in self.data if str(r.get('id','0')).isdigit()) + 1) if self.data else 1
    def save_json_data(self):
        try:
            encrypted_data = [ {**record, 'password': self.crypto.encrypt(record.get('password', ''))} for record in self.data ]
            with open(self.json_file_path, 'w', encoding='utf-8') as f: json.dump(encrypted_data, f, indent=4, ensure_ascii=False)
            self.log_message("Configuraciones cifradas y guardadas.")
        except Exception as e: messagebox.showerror("Error de Guardado", f"No se pudieron guardar las configuraciones: {e}")
    def load_json_data(self):
        if not os.path.exists(self.json_file_path): self.data = []; return True
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f: data = json.load(f)
            self.data = []
            for record in data:
                decrypted_record = record.copy()
                password = self.crypto.decrypt(record.get('password', ''))
                if password == "DECRYPT_FAILED": messagebox.showerror("Error de Contraseña", "La Contraseña Maestra es incorrecta."); return False
                decrypted_record['password'] = password
                if 'tag' not in decrypted_record: decrypted_record['tag'] = ''
                self.data.append(decrypted_record)
            self.log_message("Configuraciones descifradas y cargadas.")
            return True
        except Exception as e: messagebox.showerror("Error de Carga", f"No se pudo cargar/descifrar el archivo: {e}"); return False
    def populate_table(self, data_to_display=None):
        data = data_to_display if data_to_display is not None else self.data
        for i in self.tree.get_children(): self.tree.delete(i)
        self.checked_items.clear()
        self.tree["columns"] = ("*",) + tuple(self.DEFAULT_COLUMNS_ORDER); self.tree.column("#0", width=0, stretch=tk.NO); self.tree.column("*", width=40, minwidth=40, anchor="center"); self.tree.heading("*", text="✔")
        for col in self.DEFAULT_COLUMNS_ORDER:
            self.tree.heading(col, text=self.COLUMN_LABELS.get(col, col.title()), anchor="center")
            if col == 'id': self.tree.column(col, width=40, minwidth=40, anchor="center")
            elif col == 'tag': self.tree.column(col, width=100, minwidth=80, anchor="w")
            elif col in ["key_path"]: self.tree.column(col, width=150, minwidth=120, anchor="w")
            else: self.tree.column(col, width=120, minwidth=80, anchor="w")
        for item_data in data:
            values = [""] + ["********" if col == "password" and item_data.get(col) else item_data.get(col, "") for col in self.DEFAULT_COLUMNS_ORDER]
            item_id = self.tree.insert("", "end", values=tuple(values)); self.checked_items[item_id] = False
        self.update_select_all_state()
    def update_selection_marker(self, item_id, checked): self.tree.set(item_id, column="*", value="✔" if checked else "")
    def add_record_popup(self, edit_mode=False, item_id=None):
        if edit_mode and not item_id: messagebox.showwarning("Advertencia", "Seleccione un registro para editar."); return
        popup = tk.Toplevel(self.root); popup.transient(self.root); popup.grab_set(); popup.title("Editar Configuración" if edit_mode else "Agregar")
        if edit_mode:
            record = next((r for r in self.data if r.get('id') == int(self.tree.item(item_id,'values')[1])), None)
            if not record: messagebox.showerror("Error", "No se pudo encontrar el registro."); popup.destroy(); return
        else: record = {'id': self._get_next_id(), 'auth_method': 'password', 'tag': ''}
        self.entry_fields, auth_method_var = {}, tk.StringVar(value=record.get('auth_method', 'password'))
        def toggle_auth_fields(*args):
            is_key = auth_method_var.get() in ['key', 'interactive']
            self.entry_fields['password_frame'].grid(); self.entry_fields['key_path_frame'].grid() if is_key else self.entry_fields['key_path_frame'].grid_remove()
        for i, col in enumerate(self.DEFAULT_COLUMNS_ORDER):
            frame = ttk.Frame(popup); frame.grid(row=i, column=0, columnspan=2, padx=10, pady=3, sticky="ew"); frame.grid_columnconfigure(1, weight=1)
            ttk.Label(frame, text=f"{self.COLUMN_LABELS.get(col, col.title())}:").grid(row=0, column=0, padx=(0, 5), sticky="w"); self.entry_fields[f"{col}_frame"] = frame
            if col == 'auth_method': widget = ttk.Combobox(frame, textvariable=auth_method_var, values=['password', 'key', 'interactive'], state='readonly'); widget.bind('<<ComboboxSelected>>', toggle_auth_fields)
            elif col == 'password': widget = ttk.Entry(frame, show="*")
            elif col == 'key_path': widget = ttk.Entry(frame); ttk.Button(frame, text="Buscar...", command=lambda e=widget: self._browse_key_file(e)).grid(row=0, column=2, padx=(5,0))
            else: widget = ttk.Entry(frame)
            widget.grid(row=0, column=1, sticky="ew")
            if record.get(col) is not None and col != 'password': widget.insert(0, str(record.get(col, "")))
            if col == 'id': widget.config(state='readonly')
            self.entry_fields[col] = widget
        def on_save():
            new_record = {col: widget.get() for col, widget in self.entry_fields.items() if not isinstance(widget, ttk.Frame)}
            if edit_mode and not new_record['password']: new_record['password'] = record.get('password', '')
            new_record['auth_method'] = auth_method_var.get()
            try: new_record['port'], new_record['id'] = int(new_record.get('port') or 22), int(new_record['id'])
            except ValueError: messagebox.showwarning("Advertencia", "Puerto e ID deben ser números.", parent=popup); return
            if edit_mode: self.data[next(i for i, r in enumerate(self.data) if r.get('id') == new_record['id'])] = new_record
            else: self.data.append(new_record)
            self.save_json_data(); self.filter_table(); popup.destroy()
        ttk.Button(popup, text="Guardar", command=on_save).grid(row=len(self.DEFAULT_COLUMNS_ORDER), column=0, columnspan=2, pady=10); toggle_auth_fields()
    def _browse_key_file(self, entry_widget):
        if file_path := filedialog.askopenfilename(title="Seleccionar llave SSH privada"): entry_widget.delete(0, tk.END); entry_widget.insert(0, file_path)
    def edit_selected_record(self):
        selected_items = [i for i, c in self.checked_items.items() if c]
        if len(selected_items) != 1: messagebox.showwarning("Advertencia", "Seleccione un único registro para editar."); return
        self.add_record_popup(edit_mode=True, item_id=selected_items[0])
    def edit_record_popup(self, event=None):
        # pylint: disable=unused-argument
        if item_id := self.tree.focus(): self.add_record_popup(edit_mode=True, item_id=item_id)
    def delete_selected_records(self):
        selected_item_ids = [i for i, c in self.checked_items.items() if c]
        if not selected_item_ids or not messagebox.askyesno("Confirmar", f"¿Eliminar {len(selected_item_ids)} configuración(es)?"): return
        ids_to_delete = {int(self.tree.item(i, 'values')[1]) for i in selected_item_ids}
        self.data = [r for r in self.data if r.get('id') not in ids_to_delete]; self.save_json_data(); self.filter_table(); self.log_message(f"Se eliminaron {len(ids_to_delete)} configuración(es).")
    def _browse_local_file(self, entry_widget):
        if file_path := filedialog.askopenfilename(initialdir=os.getcwd()):
            file_name, dest_path = os.path.basename(file_path), os.path.join(self.deploy_source_folder, os.path.basename(file_path))
            try:
                if not os.path.exists(dest_path) or not os.path.samefile(file_path, dest_path): shutil.copy(file_path, dest_path)
                entry_widget.delete(0, tk.END); entry_widget.insert(0, file_name)
            except Exception as e: messagebox.showerror("Error", f"Error al copiar archivo: {e}")
    def load_file_for_deploy(self):
        selected_items = [i for i, c in self.checked_items.items() if c]
        if not selected_items: messagebox.showwarning("Advertencia", "Seleccione al menos una configuración."); return
        if not (file_path := filedialog.askopenfilename()): return
        file_name = os.path.basename(file_path)
        try:
            dest_path = os.path.join(self.deploy_source_folder, file_name)
            if not os.path.exists(dest_path) or not os.path.samefile(file_path, dest_path): shutil.copy(file_path, dest_path)
        except Exception as e: messagebox.showerror("Error", f"Error al copiar archivo: {e}"); return
        for item_id in selected_items:
            if (idx := next((i for i,r in enumerate(self.data) if r.get('id')==int(self.tree.item(item_id,'values')[1])),-1))!=-1: self.data[idx]['cargar']=file_name
        self.save_json_data(); self.filter_table(); self.log_message(f"Archivo '{file_name}' asociado a {len(selected_items)} configs.")
    def start_ssh_thread(self): threading.Thread(target=self.launch_ssh_operations, daemon=True).start()
    def launch_ssh_operations(self):
        selected_configs = [c for i, ch in self.checked_items.items() if ch and (c := next((r for r in self.data if r.get('id') == int(self.tree.item(i,'values')[1])),None))]
        if not selected_configs: self.root.after(0, lambda: messagebox.showwarning("Advertencia", "Seleccione al menos una configuración.")); return
        commands_list = [cmd.strip() for cmd in self.commands_text_area.get(1.0, tk.END).strip().split('\n') if cmd.strip()]
        if not commands_list: self.root.after(0, lambda: messagebox.showwarning("Advertencia", "Ingrese comandos SSH.")); return
        self.log_message("\n--- Iniciando Operaciones SSH ---")
        for config in selected_configs:
            host, ip, user, password, port, auth_method, key_path = [config.get(k, "") for k in ["hostname", "ip", "user", "password", "port", "auth_method", "key_path"]]
            self.log_message(f"\n--- Procesando: {host} ({ip}) ---")
            transport = None
            try:
                transport = paramiko.Transport((ip, int(port or 22))); transport.connect()
                if auth_method == 'interactive':
                    handler = GUIAuthHandler(self.root, self.mfa_queue)
                    if key_path: transport.auth_publickey(user, paramiko.Ed25519Key.from_private_key_file(key_path, password or None))
                    else: transport.auth_password(user, password)
                    if not transport.is_authenticated(): transport.auth_interactive(user, handler)
                    if not transport.is_authenticated(): raise paramiko.AuthenticationException("Falló la autenticación 2FA.")
                else:
                    pkey = paramiko.Ed25519Key.from_private_key_file(key_path, password or None) if auth_method == 'key' and key_path else None
                    transport.auth_password(user, password, fallback_keys=[pkey] if pkey else None)
                ssh_client = paramiko.SSHClient(); ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy()); ssh_client._transport = transport
                self.log_message(f"Conexión exitosa a {host} ({ip}).")
                for command in commands_list:
                    if command.lower() == 'deploy': self._deploy_file(ssh_client, config.get("cargar"), config.get("subir"), config['id'], host)
                    else: self._execute_ssh_command(ssh_client, command, config['id'], host)
            except Exception as e: self.error_log_message(f"ID {config.get('id', 'N/A')} - {host}: {e}")
            finally:
                if transport: transport.close(); self.log_message(f"Conexión cerrada para {host} ({ip}).")
        self.log_message("\n--- Proceso de Operaciones SSH Finalizado ---")
    def _deploy_file(self, ssh_client, local_file, remote_path, record_id, hostname):
        if not local_file or not remote_path: self.log_message(f"ID {record_id} - {hostname}: Falta ruta local/remota."); return
        local_full = os.path.join(self.deploy_source_folder, local_file)
        if not os.path.exists(local_full): self.log_message(f"ID {record_id} - {hostname}: Archivo no encontrado: {local_full}"); return
        try:
            with ssh_client.open_sftp() as sftp:
                dest = os.path.join(remote_path, os.path.basename(local_file))
                sftp.put(local_full, dest); self.log_message(f"ID {record_id} - {hostname}: Archivo '{local_file}' subido a '{dest}'.")
        except Exception as e: self.error_log_message(f"ID {record_id} - {hostname}: Error al subir: {e}")
    def _execute_ssh_command(self, ssh_client, command, record_id, hostname):
        try:
            _, stdout, stderr = ssh_client.exec_command(command, timeout=300)
            if error := stderr.read().decode('utf-8', 'ignore').strip(): self.error_log_message(f"ID {record_id} - {hostname} | Cmd: '{command}' | ERROR: {error}")
            else:
                self.log_message(f"ID {record_id} - {hostname} | Cmd: '{command}' ejecutado.")
                if output := stdout.read().decode('utf-8', 'ignore').strip(): self.log_message(f"Salida: {output}")
        except Exception as e: self.error_log_message(f"ID {record_id} - {hostname} | Cmd: '{command}' | Error: {e}")
    def load_today_log(self):
        log_file = os.path.join(self.log_folder, f"{dt.date.today()}.log")
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    self.log_text_widget.config(state="normal"); self.log_text_widget.insert(tk.END, f.read()); self.log_text_widget.config(state="disabled")
            except Exception as e: self.log_message(f"Error al cargar log: {e}")
    def log_message(self, message):
        entry = f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n"
        self.root.after(0, self._update_log_widget, self.log_text_widget, entry)
        try:
            with open(os.path.join(self.log_folder, f"{dt.date.today()}.log"), 'a', encoding='utf-8') as f: f.write(entry)
        except Exception as e: print(f"Error al escribir en log: {e}\n")
    def error_log_message(self, message):
        entry = f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n"
        self.root.after(0, self._update_log_widget, self.error_log_widget, entry)
        try:
            with open(os.path.join(self.error_log_folder, f"error_{dt.date.today()}.log"), 'a', encoding='utf-8') as f: f.write(entry)
        except Exception as e: print(f"Error al escribir en log de errores: {e}\n")
    def _update_log_widget(self, widget, text):
        if widget and widget.winfo_exists():
            widget.config(state="normal"); widget.insert(tk.END, text); widget.see(tk.END); widget.config(state="disabled")
    class TextRedirector:
        def __init__(self, widget, tag="stdout"): self.widget, self.original_stream = widget, (sys.__stdout__ if tag == 'stdout' else sys.__stderr__)
        def write(self, text):
            if self.widget and self.widget.winfo_exists():
                self.widget.config(state="normal"); self.widget.insert(tk.END, text); self.widget.see(tk.END); self.widget.config(state="disabled")
            self.original_stream.write(text)
        def flush(self): self.original_stream.flush()

if __name__ == "__main__":
    root = ThemedTk()
    root.withdraw()
    
    app = JsonTableApp(root)
    
    if app.initialized_ok:
        app.root.deiconify()
        app.root.mainloop()
    elif root.winfo_exists():
        root.destroy()
