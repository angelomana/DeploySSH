# ... (importaciones y la clase GUIAuthHandler permanecen igual) ...
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import os
import datetime as dt
import paramiko
import time
import sys
import shutil
from ttkthemes import ThemedTk
import threading
import queue

# La clase GUIAuthHandler no necesita cambios
class GUIAuthHandler(paramiko.auth_handler.AuthHandler):
    def __init__(self, root, mfa_queue):
        self.root = root
        self.mfa_queue = mfa_queue
        super().__init__()
    def __call__(self, title, instructions, prompt_list):
        self.root.after(0, self.ask_for_code, title, prompt_list)
        response = self.mfa_queue.get()
        return [response] if response is not None else []
    def ask_for_code(self, title, prompt_list):
        prompt_text = prompt_list[0][0] if prompt_list else "Código de Verificación:"
        code = simpledialog.askstring(title, prompt_text, parent=self.root)
        self.mfa_queue.put(code)


### MODIFICADO: Clase para la ventana de utilerías con título y botón de copiar actualizados ###
class UtilitiesWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        ### MODIFICADO: Título de la ventana ###
        self.title("Utilerias")
        self.geometry("900x600")
        self.minsize(600, 400)
        self.transient(parent)
        self.grab_set()

        self.json_path = "utilities.json"
        self.utilities_data = []
        self.selected_item_index = None

        self.columns = ('Categoria', 'Comando', 'Descripcion', 'Ejemplo')
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_table)
        
        self.load_utilities_data()
        self.create_widgets()
        self.populate_table()

    def load_utilities_data(self):
        """Carga datos desde utilities.json o crea el archivo con datos por defecto."""
        default_data = [
            {'Categoria': 'Gestión de Carpetas', 'Comando': 'ls', 'Descripcion': 'Lista el contenido de un directorio.', 'Ejemplo': 'ls -l (lista detallada)\nls -la (lista detallada con archivos ocultos)'},
            {'Categoria': 'Gestión de Carpetas', 'Comando': 'cd', 'Descripcion': 'Cambia de directorio (navegar).', 'Ejemplo': 'cd /var/log\ncd ~ (ir al directorio home)\ncd .. (subir un nivel)'},
            {'Categoria': 'Gestión de Carpetas', 'Comando': 'pwd', 'Descripcion': 'Muestra el directorio de trabajo actual.', 'Ejemplo': 'pwd'},
            {'Categoria': 'Gestión de Carpetas', 'Comando': 'mkdir', 'Descripcion': 'Crea un nuevo directorio.', 'Ejemplo': 'mkdir nuevo_directorio'},
            {'Categoria': 'Gestión de Carpetas', 'Comando': 'rmdir', 'Descripcion': 'Elimina un directorio vacío.', 'Ejemplo': 'rmdir directorio_vacio'},
            {'Categoria': 'Gestión de Carpetas', 'Comando': 'cp', 'Descripcion': 'Copia archivos o directorios.', 'Ejemplo': 'cp archivo.txt /tmp/\ncp -r directorio/ /tmp/ (copia recursiva)'},
            {'Categoria': 'Gestión de Carpetas', 'Comando': 'mv', 'Descripcion': 'Mueve o renombra archivos/directorios.', 'Ejemplo': 'mv archivo.txt /tmp/\nmv archivo_viejo.txt archivo_nuevo.txt'},
            {'Categoria': 'Gestión de Carpetas', 'Comando': 'rm', 'Descripcion': 'Elimina archivos o directorios.', 'Ejemplo': 'rm archivo.txt\nrm -r directorio/ (elimina directorio y contenido)'},
            {'Categoria': 'Gestión de Permisos', 'Comando': 'chmod', 'Descripcion': 'Cambia los permisos de archivos/directorios.', 'Ejemplo': 'chmod 755 script.sh (permisos rwx para owner, rx para grupo y otros)\nchmod +x archivo'},
            {'Categoria': 'Gestión de Permisos', 'Comando': 'chown', 'Descripcion': 'Cambia el propietario de archivos/directorios.', 'Ejemplo': 'chown usuario:grupo archivo.txt\nchown -R usuario:grupo directorio/'},
            {'Categoria': 'Gestión de Permisos', 'Comando': 'chgrp', 'Descripcion': 'Cambia el grupo de archivos/directorios.', 'Ejemplo': 'chgrp nuevo_grupo archivo.txt'}
        ]
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.utilities_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.utilities_data = default_data
            self.save_utilities_data()

    def save_utilities_data(self):
        """Guarda los datos actuales en utilities.json."""
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(self.utilities_data, f, indent=4, ensure_ascii=False)

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_rowconfigure(2, weight=1) # Fila para la tabla
        main_frame.grid_columnconfigure(0, weight=1)

        filter_frame = ttk.Frame(main_frame)
        filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        filter_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(filter_frame, text="Buscar:").grid(row=0, column=0, padx=(0, 5))
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew")

        ### MODIFICADO: Frame de botones CRUD con el nuevo botón de copiar ###
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        button_frame.grid_columnconfigure((0, 1, 2, 3), weight=1) # Se añade una columna
        ttk.Button(button_frame, text="Agregar", command=self.open_add_edit_popup).grid(row=0, column=0, padx=2, sticky="ew")
        ttk.Button(button_frame, text="Editar", command=lambda: self.open_add_edit_popup(edit_mode=True)).grid(row=0, column=1, padx=2, sticky="ew")
        ttk.Button(button_frame, text="Eliminar", command=self.delete_utility).grid(row=0, column=2, padx=2, sticky="ew")
        
        ### NUEVO: Botón para copiar el comando ###
        self.copy_button = ttk.Button(button_frame, text="Copiar Comando", command=self.copy_selected_command)
        self.copy_button.grid(row=0, column=3, padx=2, sticky="ew")

        table_frame = ttk.Frame(main_frame)
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_frame, columns=self.columns, show="headings")
        
        for col in self.columns:
            self.tree.heading(col, text=col)
            if col == 'Descripcion' or col == 'Ejemplo':
                self.tree.column(col, width=300, minwidth=150)
            else:
                self.tree.column(col, width=120, minwidth=80)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        yscrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        xscrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscrollbar.set, xscrollcommand=xscrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscrollbar.grid(row=0, column=1, sticky="ns")
        xscrollbar.grid(row=1, column=0, sticky="ew")

    ### NUEVO: Función para copiar el comando seleccionado al portapapeles ###
    def copy_selected_command(self):
        if self.selected_item_index is None:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un comando de la lista para copiar.", parent=self)
            return

        record = self.utilities_data[self.selected_item_index]
        command_text = record.get("Comando", "")

        if command_text:
            self.clipboard_clear()
            self.clipboard_append(command_text)
            # Feedback visual para el usuario
            original_text = self.copy_button.cget("text")
            self.copy_button.config(text="¡Copiado!")
            self.after(2000, lambda: self.copy_button.config(text=original_text))

    def on_tree_select(self, event):
        selected_items = self.tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            values = self.tree.item(selected_item, 'values')
            comando = values[1]
            self.selected_item_index = next((i for i, item in enumerate(self.utilities_data) if item["Comando"] == comando), None)

    def populate_table(self, data=None):
        if data is None:
            data = self.utilities_data

        self.tree.delete(*self.tree.get_children())
        self.selected_item_index = None
        
        for item in data:
            self.tree.insert("", "end", values=[item.get(col, "") for col in self.columns])
            
    def filter_table(self, *args):
        search_term = self.search_var.get().lower()
        if not search_term:
            filtered_data = self.utilities_data
        else:
            filtered_data = [
                item for item in self.utilities_data
                if any(search_term in str(value).lower() for value in item.values())
            ]
        self.populate_table(filtered_data)

    def delete_utility(self):
        if self.selected_item_index is None:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un comando para eliminar.", parent=self)
            return

        comando = self.utilities_data[self.selected_item_index]["Comando"]
        if messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar el comando '{comando}'?", parent=self):
            del self.utilities_data[self.selected_item_index]
            self.save_utilities_data()
            self.filter_table()

    def open_add_edit_popup(self, edit_mode=False):
        if edit_mode and self.selected_item_index is None:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un comando para editar.", parent=self)
            return
            
        popup = tk.Toplevel(self)
        popup.transient(self)
        popup.grab_set()
        
        entry_vars = {}
        
        if edit_mode:
            popup.title("Editar Comando")
            record = self.utilities_data[self.selected_item_index]
        else:
            popup.title("Agregar Comando")
            record = {col: "" for col in self.columns}
            
        for i, col in enumerate(self.columns):
            ttk.Label(popup, text=f"{col}:").grid(row=i*2, column=0, padx=10, pady=5, sticky="w")
            if col in ['Descripcion', 'Ejemplo']:
                entry = tk.Text(popup, height=4, width=40, wrap="word")
                entry.insert("1.0", record.get(col, ""))
                entry.grid(row=i*2+1, column=0, columnspan=2, padx=10, pady=2, sticky="ew")
            else:
                var = tk.StringVar(value=record.get(col, ""))
                entry = ttk.Entry(popup, textvariable=var, width=50)
                entry.grid(row=i*2+1, column=0, columnspan=2, padx=10, pady=2, sticky="ew")

            entry_vars[col] = entry

        def on_save():
            new_data = {}
            for col, widget in entry_vars.items():
                if isinstance(widget, tk.Text):
                    new_data[col] = widget.get("1.0", tk.END).strip()
                else:
                    new_data[col] = widget.get().strip()

            if not new_data.get("Comando"):
                messagebox.showerror("Error", "El campo 'Comando' es obligatorio.", parent=popup)
                return

            if edit_mode:
                self.utilities_data[self.selected_item_index] = new_data
            else:
                self.utilities_data.append(new_data)
            
            self.save_utilities_data()
            self.filter_table()
            popup.destroy()

        save_button = ttk.Button(popup, text="Guardar", command=on_save)
        save_button.grid(row=len(self.columns)*2, column=0, columnspan=2, padx=10, pady=10)

# La clase JsonTableApp permanece sin cambios
class JsonTableApp:
    # ... (Todo el código de JsonTableApp va aquí, exactamente como en la respuesta anterior) ...
    # ...
    # ...
    DEFAULT_COLUMNS_ORDER = [ "id", "hostname", "ip", "user", "auth_method", "password", "key_path", "port", "cargar", "subir" ]
    COLUMN_LABELS = { "id": "ID", "hostname": "Hostname", "ip": "IP", "user": "Usuario", "auth_method": "Método Auth", "password": "Password / Passphrase", "key_path": "Ruta de Llave SSH", "port": "Puerto", "cargar": "Cargar (Archivo Origen)", "subir": "Subir (Ruta Destino Absoluta)" }
    def __init__(self, root):
        self.root = root
        self.root.set_theme("arc") 
        self.root.title("KIOsko")
        try:
            self.root.iconbitmap("uno.ico")
        except tk.TclError:
            print("No se pudo encontrar el archivo 'uno.ico'.")
        self.root.geometry("1300x700")
        self.root.minsize(800, 500) 
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.json_file_path = "ssh_configs.json"
        self.deploy_source_folder = "deploy"
        self.log_folder = "logs"
        self.error_log_folder = os.path.join(self.log_folder, "errors")
        os.makedirs(self.deploy_source_folder, exist_ok=True)
        os.makedirs(self.log_folder, exist_ok=True)
        os.makedirs(self.error_log_folder, exist_ok=True)
        self.tree = None
        self.data = []
        self.columns = ["*"] + self.DEFAULT_COLUMNS_ORDER
        self.checked_items = {}
        self.log_text_widget = None
        self.error_log_widget = None
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.entry_fields = {}
        self.commands_text_area = None
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_table)
        self.mfa_queue = queue.Queue()
        self.create_widgets()
        self.load_json_data()
        self.filter_table() 
        self.load_today_log()
        sys.stdout = self.TextRedirector(self.log_text_widget, 'stdout')
        sys.stderr = self.TextRedirector(self.error_log_widget, 'stderr')
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=2)
        main_frame.grid_rowconfigure(1, weight=0)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=1)
        left_panel = ttk.Frame(main_frame)
        left_panel.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(0, 5))
        left_panel.grid_rowconfigure(0, weight=2) 
        left_panel.grid_rowconfigure(1, weight=0) 
        left_panel.grid_rowconfigure(2, weight=1) 
        left_panel.grid_columnconfigure(0, weight=1)
        table_frame = ttk.LabelFrame(left_panel, text="Servidores")
        table_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        filter_frame = ttk.Frame(table_frame)
        filter_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        filter_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(filter_frame, text="Buscar:").grid(row=0, column=0, padx=(0, 5))
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew")
        clear_button = ttk.Button(filter_frame, text="Limpiar", command=self.clear_filter)
        clear_button.grid(row=0, column=2, padx=(5, 0))
        yscrollbar_table = ttk.Scrollbar(table_frame, orient="vertical")
        xscrollbar_table = ttk.Scrollbar(table_frame, orient="horizontal")
        self.tree = ttk.Treeview(table_frame, yscrollcommand=yscrollbar_table.set,
                                 xscrollcommand=xscrollbar_table.set, show="headings")
        yscrollbar_table.config(command=self.tree.yview)
        xscrollbar_table.config(command=self.tree.xview)
        self.tree.grid(row=1, column=0, sticky="nsew")
        yscrollbar_table.grid(row=1, column=1, sticky="ns")
        xscrollbar_table.grid(row=2, column=0, sticky="ew")
        self.tree.bind("<Button-1>", self.on_item_click)
        self.tree.bind("<Double-1>", self.edit_record_popup)
        button_frame = ttk.Frame(left_panel)
        button_frame.grid(row=1, column=0, sticky="ew", pady=5)
        button_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        ttk.Button(button_frame, text="Agregar", command=self.add_record_popup).grid(row=0, column=0, sticky="ew", padx=2)
        ttk.Button(button_frame, text="Editar", command=self.edit_selected_record).grid(row=0, column=1, sticky="ew", padx=2)
        ttk.Button(button_frame, text="Eliminar", command=self.delete_selected_records).grid(row=0, column=2, sticky="ew", padx=2)
        ttk.Button(button_frame, text="Cargar Archivo", command=self.load_file_for_deploy).grid(row=0, column=3, sticky="ew", padx=2)
        ttk.Button(button_frame, text="Utilerias", command=self.open_utilities_window).grid(row=0, column=4, sticky="ew", padx=2)
        log_frame = ttk.LabelFrame(left_panel, text="Registro de Actividad")
        log_frame.grid(row=2, column=0, sticky="nsew", pady=(5, 0))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        self.log_text_widget = tk.Text(log_frame, wrap="word", state="disabled", bg="black", fg="white", font=("Courier New", 9))
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text_widget.yview)
        self.log_text_widget.config(yscrollcommand=log_scrollbar.set)
        log_scrollbar.pack(side="right", fill="y")
        self.log_text_widget.pack(side="left", fill="both", expand=True)
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=0, column=1, rowspan=3, sticky="nsew", padx=(5, 0))
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        error_log_frame = ttk.LabelFrame(right_panel, text="Errores de Conexión / Despliegue")
        error_log_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        error_log_frame.grid_rowconfigure(0, weight=1)
        error_log_frame.grid_columnconfigure(0, weight=1)
        self.error_log_widget = tk.Text(error_log_frame, wrap="word", state="disabled", bg="#5e0000", fg="white", font=("Courier New", 9))
        error_log_scrollbar = ttk.Scrollbar(error_log_frame, orient="vertical", command=self.error_log_widget.yview)
        self.error_log_widget.config(yscrollcommand=error_log_scrollbar.set)
        error_log_scrollbar.pack(side="right", fill="y")
        self.error_log_widget.pack(side="left", fill="both", expand=True)
        commands_frame = ttk.LabelFrame(right_panel, text="Comandos a Enviar")
        commands_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        commands_frame.grid_rowconfigure(0, weight=1)
        commands_frame.grid_rowconfigure(1, weight=0)
        commands_frame.grid_columnconfigure(0, weight=1)
        self.commands_text_area = tk.Text(commands_frame, wrap="word", height=6, font=("Courier New", 9))
        commands_scrollbar = ttk.Scrollbar(commands_frame, orient="vertical", command=self.commands_text_area.yview)
        self.commands_text_area.config(yscrollcommand=commands_scrollbar.set)
        self.commands_text_area.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        commands_scrollbar.grid(row=0, column=1, sticky="ns")
        ttk.Button(commands_frame, text="Lanzar Actividad", command=self.start_ssh_thread).grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
    def open_utilities_window(self):
        _ = UtilitiesWindow(self.root)
    def clear_filter(self):
        self.search_var.set("")
    def filter_table(self, *args):
        search_term = self.search_var.get().lower()
        if not search_term:
            filtered_data = self.data
        else:
            filtered_data = []
            for record in self.data:
                for value in record.values():
                    if str(value).lower() in str(record.get('password', '')).lower():
                        continue
                    if search_term in str(value).lower():
                        filtered_data.append(record)
                        break 
        self.populate_table(data_to_display=filtered_data)
    def _get_next_id(self):
        if not self.data:
            return 1
        existing_ids = [int(record.get('id', 0)) for record in self.data if isinstance(record.get('id'), (int, str)) and str(record.get('id')).isdigit()]
        return (max(existing_ids) + 1) if existing_ids else 1
    def load_json_data(self):
        if not os.path.exists(self.json_file_path):
            message = f"Info: Archivo JSON '{self.json_file_path}' no encontrado. Se creará uno vacío."
            messagebox.showinfo("Información", message)
            self.log_message(message)
            self.data = []
            self.save_json_data()
            return
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            self.log_message(f"Configuraciones cargadas desde {self.json_file_path}. Total: {len(self.data)}.")
            seen_ids = set()
            new_data = []
            id_changed_count = 0
            for record in self.data:
                record_id = record.get('id')
                if record_id is None or not isinstance(record_id, int) or record_id in seen_ids:
                    original_id = record_id
                    record['id'] = self._get_next_id()
                    id_changed_count += 1
                    self.log_message(f"ID duplicado o inválido '{original_id}'. Asignando nuevo ID: {record['id']}.")
                seen_ids.add(record['id'])
                if 'auth_method' not in record:
                    record['auth_method'] = 'password'
                new_data.append(record)
            self.data = new_data
            if id_changed_count > 0:
                self.save_json_data()
        except json.JSONDecodeError as e:
            message = f"Error al decodificar JSON: {e}. Se inicializará una lista vacía."
            messagebox.showerror("Error de JSON", message)
            self.log_message(message)
            self.data = []
        except Exception as e:
            message = f"Error al cargar archivo: {e}. Se inicializará una lista vacía."
            messagebox.showerror("Error", message)
            self.log_message(message)
            self.data = []
        self.log_message(f"Columnas de configuración: {', '.join(self.columns)}")
    def save_json_data(self):
        try:
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            self.log_message(f"Configuraciones guardadas en {self.json_file_path}")
        except Exception as e:
            self.log_message(f"Error al guardar configuraciones en {self.json_file_path}: {e}")
            messagebox.showerror("Error de Guardado", f"No se pudieron guardar las configuraciones: {e}")
    def populate_table(self, data_to_display=None):
        if data_to_display is None:
            data_to_display = self.data
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.checked_items.clear()
        self.tree["columns"] = self.columns
        self.tree.column("#0", width=0, stretch=tk.NO)
        self.tree.column("*", width=40, minwidth=40, anchor="center")
        self.tree.heading("*", text="Selección", anchor="center")
        for col in self.DEFAULT_COLUMNS_ORDER:
            header_text = self.COLUMN_LABELS.get(col, col.title())
            self.tree.heading(col, text=header_text, anchor="center")
            if col == 'id':
                self.tree.column(col, width=40, minwidth=40, anchor="center")
            elif col in ["cargar", "subir", "key_path"]:
                self.tree.column(col, width=200, minwidth=150, anchor="w")
            else:
                self.tree.column(col, width=120, minwidth=80, anchor="w")
        for item_data in data_to_display:
            values = [""] 
            for col in self.DEFAULT_COLUMNS_ORDER:
                if col == "password" and item_data.get(col):
                    values.append("********")
                else:
                    values.append(item_data.get(col, ""))
            item_id = self.tree.insert("", "end", values=values)
            self.checked_items[item_id] = False
        if not self.search_var.get():
             self.log_message(f"Tabla poblada con {len(data_to_display)} registros.")
        else:
             self.log_message(f"Filtro aplicado. Mostrando {len(data_to_display)} de {len(self.data)} registros.")
    def update_selection_marker(self, item_id, checked):
        if checked:
            self.tree.set(item_id, column="*", value="*")
        else:
            self.tree.set(item_id, column="*", value="")
    def on_item_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            current_state = self.checked_items.get(item_id, False)
            new_state = not current_state
            self.checked_items[item_id] = new_state
            self.update_selection_marker(item_id, new_state)
    def add_record_popup(self, edit_mode=False, item_id=None):
        if edit_mode and not item_id:
            messagebox.showwarning("Advertencia", "No se seleccionó ningún registro para editar.")
            return
        popup = tk.Toplevel(self.root)
        popup.transient(self.root)
        popup.grab_set()
        if edit_mode:
            popup.title("Editar Configuración")
            tree_values = self.tree.item(item_id, 'values')
            record_id = int(tree_values[1])
            record = next((r for r in self.data if r.get('id') == record_id), None)
            if not record:
                messagebox.showerror("Error", "No se pudo encontrar el registro original.")
                popup.destroy()
                return
        else:
            popup.title("Agregar Nueva Configuración")
            record = {'id': self._get_next_id(), 'auth_method': 'password'}
        self.entry_fields = {}
        auth_method_var = tk.StringVar(value=record.get('auth_method', 'password'))
        def toggle_auth_fields(*args):
            method = auth_method_var.get()
            if method == 'password':
                self.entry_fields['password_frame'].grid()
                self.entry_fields['key_path_frame'].grid_remove()
            elif method == 'key' or method == 'interactive':
                self.entry_fields['password_frame'].grid()
                self.entry_fields['key_path_frame'].grid()
        for i, col in enumerate(self.DEFAULT_COLUMNS_ORDER):
            frame = ttk.Frame(popup)
            frame.grid(row=i, column=0, columnspan=2, padx=10, pady=3, sticky="ew")
            frame.grid_columnconfigure(1, weight=1)
            label_text = self.COLUMN_LABELS.get(col, col.title())
            label = ttk.Label(frame, text=f"{label_text}:")
            label.grid(row=0, column=0, padx=(0, 5), sticky="w")
            self.entry_fields[f"{col}_frame"] = frame
            if col == 'auth_method':
                widget = ttk.Combobox(frame, textvariable=auth_method_var, values=['password', 'key', 'interactive'], state='readonly')
                widget.bind('<<ComboboxSelected>>', toggle_auth_fields)
            elif col == 'password':
                widget = ttk.Entry(frame, show="*")
            elif col == 'key_path':
                widget = ttk.Entry(frame)
                browse_btn = ttk.Button(frame, text="Buscar...", command=lambda e=widget: self._browse_key_file(e))
                browse_btn.grid(row=0, column=2, padx=(5,0))
            else:
                widget = ttk.Entry(frame)
            if col != 'auth_method':
                widget.grid(row=0, column=1, sticky="ew")
            else:
                widget.grid(row=0, column=1, sticky="ew")
            if record.get(col) is not None:
                if col != 'password':
                    widget.insert(0, str(record.get(col, "")))
            if col == 'id':
                widget.config(state='readonly')
            self.entry_fields[col] = widget
        def on_save():
            new_record = {}
            for col, widget in self.entry_fields.items():
                if isinstance(widget, ttk.Frame): continue
                if col == 'password':
                    if edit_mode and not widget.get():
                        new_record[col] = record.get('password', '')
                    else:
                        new_record[col] = widget.get()
                elif col != 'auth_method':
                    new_record[col] = widget.get()
            new_record['auth_method'] = auth_method_var.get()
            try:
                new_record['port'] = int(new_record['port']) if new_record.get('port') else 22
                new_record['id'] = int(new_record['id'])
            except ValueError:
                messagebox.showwarning("Advertencia", "Puerto e ID deben ser números.", parent=popup)
                return
            if edit_mode:
                record_index = next((i for i, r in enumerate(self.data) if r.get('id') == new_record['id']), -1)
                if record_index != -1:
                    self.data[record_index] = new_record
            else:
                self.data.append(new_record)
            self.save_json_data()
            self.filter_table()
            popup.destroy()
        save_button = ttk.Button(popup, text="Guardar", command=on_save)
        save_button.grid(row=len(self.DEFAULT_COLUMNS_ORDER), column=0, columnspan=2, pady=10)
        toggle_auth_fields()
    def _browse_key_file(self, entry_widget):
        file_path = filedialog.askopenfilename(title="Seleccionar llave SSH privada")
        if file_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, file_path)
    def edit_selected_record(self):
        selected_items = [item_id for item_id, is_checked in self.checked_items.items() if is_checked]
        if not selected_items:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un registro para editar.")
            return
        if len(selected_items) > 1:
            messagebox.showwarning("Advertencia", "Por favor, seleccione solo un registro para editar.")
            return
        self.add_record_popup(edit_mode=True, item_id=selected_items[0])
    def edit_record_popup(self, event=None, item_id=None):
        if item_id is None:
            item_id = self.tree.focus()
        if not item_id:
            return
        self.add_record_popup(edit_mode=True, item_id=item_id)
    def delete_selected_records(self):
        selected_item_ids = [item_id for item_id, is_checked in self.checked_items.items() if is_checked]
        if not selected_item_ids:
            messagebox.showwarning("Advertencia", "Por favor, seleccione al menos una configuración para eliminar.")
            return
        if not messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar {len(selected_item_ids)} configuración(es) seleccionada(s)?"):
            return
        ids_to_delete = set()
        for item_id in selected_item_ids:
            try:
                record_id = int(self.tree.item(item_id, 'values')[1])
                ids_to_delete.add(record_id)
            except (ValueError, IndexError):
                self.log_message(f"Advertencia: No se pudo obtener el ID del registro para eliminación.")
        if not ids_to_delete:
            return
        original_data_count = len(self.data)
        self.data = [record for record in self.data if record.get('id') not in ids_to_delete]
        deleted_count = original_data_count - len(self.data)
        self.save_json_data()
        self.filter_table()
        self.log_message(f"Se eliminaron {deleted_count} configuración(es).")
    def _browse_local_file(self, entry_widget):
        file_path = filedialog.askopenfilename(initialdir=os.getcwd(), title="Seleccionar archivo para despliegue", filetypes=(("Todos los archivos", "*.*"),))
        if file_path:
            file_name = os.path.basename(file_path)
            destination_path = os.path.join(self.deploy_source_folder, file_name)
            try:
                if not os.path.exists(destination_path) or not os.path.samefile(file_path, destination_path):
                    shutil.copy(file_path, destination_path)
                    self.log_message(f"Archivo '{file_name}' copiado a '{self.deploy_source_folder}'.")
                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, file_name)
            except Exception as e:
                msg = f"Error al copiar el archivo '{file_name}': {e}"
                self.log_message(msg)
                messagebox.showerror("Error de Archivo", msg)
    def load_file_for_deploy(self):
        selected_items = [item_id for item_id, is_checked in self.checked_items.items() if is_checked]
        if not selected_items:
            messagebox.showwarning("Advertencia", "Por favor, seleccione al menos una configuración en la tabla.")
            return
        file_path = filedialog.askopenfilename(initialdir=os.getcwd(), title="Seleccionar archivo", filetypes=(("Todos los archivos", "*.*"),))
        if not file_path:
            self.log_message("Selección de archivo cancelada.")
            return
        file_name = os.path.basename(file_path)
        destination_path = os.path.join(self.deploy_source_folder, file_name)
        try:
            if not os.path.exists(destination_path) or not os.path.samefile(file_path, destination_path):
                shutil.copy(file_path, destination_path)
                self.log_message(f"Archivo '{file_name}' copiado a '{self.deploy_source_folder}'.")
        except Exception as e:
            msg = f"Error al copiar el archivo '{file_name}': {e}"
            self.log_message(msg)
            messagebox.showerror("Error de Archivo", msg)
            return
        updated_count = 0
        for item_id in selected_items:
            try:
                record_id = int(self.tree.item(item_id, 'values')[1])
                record_index = next((i for i, r in enumerate(self.data) if r.get('id') == record_id), -1)
                if record_index != -1:
                    self.data[record_index]['cargar'] = file_name
                    updated_count += 1
            except (ValueError, IndexError):
                self.log_message(f"Advertencia: No se pudo actualizar el registro.")
        self.save_json_data()
        self.filter_table()
        self.log_message(f"Se asoció el archivo '{file_name}' a {updated_count} configuración(es).")
    def start_ssh_thread(self):
        self.log_message("Iniciando operaciones SSH en un hilo separado...")
        ssh_thread = threading.Thread(target=self.launch_ssh_operations, daemon=True)
        ssh_thread.start()
    def launch_ssh_operations(self):
        selected_configs = []
        for item_id, is_checked in self.checked_items.items():
            if is_checked:
                try:
                    record_id = int(self.tree.item(item_id, 'values')[1])
                    config = next((r for r in self.data if r.get('id') == record_id), None)
                    if config:
                        selected_configs.append(config)
                except (ValueError, IndexError):
                    continue
        if not selected_configs:
            self.root.after(0, lambda: messagebox.showwarning("Advertencia", "Por favor, seleccione al menos una configuración."))
            return
        commands_raw = self.commands_text_area.get(1.0, tk.END).strip()
        commands_list = [cmd.strip() for cmd in commands_raw.split('\n') if cmd.strip()]
        if not commands_list:
            self.root.after(0, lambda: messagebox.showwarning("Advertencia", "Por favor, ingrese comandos SSH."))
            return
        self.log_message("\n--- Iniciando Operaciones SSH ---")
        self.error_log_widget.config(state="normal")
        self.error_log_widget.delete(1.0, tk.END)
        self.error_log_widget.insert(tk.END, "--- Errores Detectados (Sesión Actual) ---\n")
        self.error_log_widget.config(state="disabled")
        for config in selected_configs:
            host, ip, user, password, port = (config.get(k, "") for k in ["hostname", "ip", "user", "password", "port"])
            port = int(port) if port else 22
            auth_method = config.get('auth_method', 'password')
            key_path = config.get('key_path')
            self.log_message(f"\n--- Procesando: {host} ({ip}) usando método '{auth_method}' ---")
            ssh_client = None
            transport = None
            try:
                if auth_method == 'interactive':
                    handler = GUIAuthHandler(self.root, self.mfa_queue)
                    transport = paramiko.Transport((ip, port))
                    transport.connect()
                    if key_path:
                        self.log_message(f"Intentando autenticación con llave: {key_path}")
                        pkey = paramiko.Ed25519Key.from_private_key_file(key_path, password=password or None)
                        transport.auth_publickey(user, pkey)
                    else:
                        self.log_message("Intentando autenticación con password...")
                        transport.auth_password(user, password)
                    if not transport.is_authenticated():
                        self.log_message("Password/Llave aceptada, se necesita segundo factor...")
                        transport.auth_interactive(user, handler)
                    if not transport.is_authenticated():
                        raise paramiko.AuthenticationException("Falló la autenticación interactiva de dos factores.")
                    ssh_client = paramiko.SSHClient()
                    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh_client._transport = transport
                else:
                    ssh_client = paramiko.SSHClient()
                    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    pkey = None
                    if auth_method == 'key' and key_path:
                        self.log_message(f"Cargando llave privada desde: {key_path}")
                        pkey = paramiko.Ed25519Key.from_private_key_file(key_path, password=password or None)
                    ssh_client.connect(hostname=ip, port=port, username=user, password=password, pkey=pkey, timeout=10)
                self.log_message(f"Conexión exitosa a {host} ({ip}).")
                for command in commands_list:
                    if command.lower() == 'deploy':
                        local_file = config.get("cargar")
                        remote_path = config.get("subir")
                        carga = os.path.join(remote_path, os.path.basename(local_file)) if remote_path and local_file else None
                        self._deploy_file(ssh_client, local_file, carga, config['id'], host, ip)
                    else:
                        self._execute_ssh_command(ssh_client, command, config['id'], host, ip)
            except Exception as e:
                msg = f"ID {config.get('id', 'N/A')} - {host} ({ip}) - Error: {e}"
                self.log_message(msg)
                self.error_log_message(msg)
            finally:
                if ssh_client and auth_method != 'interactive':
                    ssh_client.close()
                    self.log_message(f"Sesión SSH directa cerrada para {host} ({ip}).")
                if transport:
                    transport.close()
                    self.log_message(f"Transporte SSH cerrado para {host} ({ip}).")
        self.log_message("\n--- Proceso de Operaciones SSH Finalizado ---")
    def _deploy_file(self, ssh_client, local_file_name, remote_dest_path, record_id, hostname, ip_address):
        if not local_file_name or not remote_dest_path:
            msg = f"ID {record_id} - {hostname}: Falta ruta local ('cargar') o remota ('subir') en la configuración."
            self.log_message(msg)
            self.error_log_message(msg)
            return
        local_full_path = os.path.join(self.deploy_source_folder, local_file_name)
        if not os.path.exists(local_full_path):
            msg = f"ID {record_id} - {hostname}: Archivo local NO encontrado en '{local_full_path}'."
            self.log_message(msg)
            self.error_log_message(msg)
            return
        sftp = None
        try:
            sftp = ssh_client.open_sftp()
            sftp.put(local_full_path, remote_dest_path)
            self.log_message(f"ID {record_id} - {hostname}: Archivo '{local_file_name}' subido a '{remote_dest_path}'.")
        except Exception as e:
            msg = f"ID {record_id} - {hostname}: Error al subir '{local_file_name}': {e}"
            self.log_message(msg)
            self.error_log_message(msg)
        finally:
            if sftp:
                sftp.close()
    def _execute_ssh_command(self, ssh_client, command, record_id, hostname, ip_address):
        try:
            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=300)
            output = stdout.read().decode('utf-8', errors='ignore').strip()
            error = stderr.read().decode('utf-8', errors='ignore').strip()
            if error:
                msg = f"ID {record_id} - {hostname} | Comando: '{command}' | ERROR: {error}"
                self.log_message(msg)
                self.error_log_message(msg)
            else:
                self.log_message(f"ID {record_id} - {hostname} | Comando: '{command}' ejecutado.")
                if output:
                    self.log_message(f"Salida: {output}")
        except Exception as e:
            msg = f"ID {record_id} - {hostname} | Comando: '{command}' | Error: {e}"
            self.log_message(msg)
            self.error_log_message(msg)
    def load_today_log(self):
        today_log_file = os.path.join(self.log_folder, f"{dt.date.today()}.log")
        self.log_text_widget.config(state="normal")
        self.log_text_widget.delete(1.0, tk.END)
        if os.path.exists(today_log_file):
            try:
                with open(today_log_file, 'r', encoding='utf-8') as f:
                    self.log_text_widget.insert(tk.END, f.read())
                self.log_message("Log de actividad del día cargado.")
            except Exception as e:
                self.log_message(f"Error al cargar log: {e}")
        else:
            self.log_message("No existe log para hoy. Se creará uno nuevo.")
        self.log_text_widget.see(tk.END)
        self.log_text_widget.config(state="disabled")
    def log_message(self, message):
        log_entry = f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n"
        self.root.after(0, self._update_log_widget, self.log_text_widget, log_entry)
        today_log_file = os.path.join(self.log_folder, f"{dt.date.today()}.log")
        try:
            with open(today_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            self.original_stdout.write(f"Error al escribir en log: {e}\n")
    def error_log_message(self, message):
        log_entry = f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n"
        self.root.after(0, self._update_log_widget, self.error_log_widget, log_entry)
        today_error_log_file = os.path.join(self.error_log_folder, f"error_{dt.date.today()}.log")
        try:
            with open(today_error_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            self.original_stderr.write(f"Error al escribir en log de errores: {e}\n")
    def _update_log_widget(self, widget, text):
        widget.config(state="normal")
        widget.insert(tk.END, text)
        widget.see(tk.END)
        widget.config(state="disabled")
    class TextRedirector(object):
        def __init__(self, widget, tag="stdout"):
            self.widget = widget
            self.original_stream = sys.__stdout__ if tag == 'stdout' else sys.__stderr__
        def write(self, text):
            self.widget.config(state="normal")
            self.widget.insert(tk.END, text)
            self.widget.see(tk.END)
            self.widget.config(state="disabled")
            self.original_stream.write(text)
        def flush(self):
            self.original_stream.flush()

if __name__ == "__main__":
    root = ThemedTk()
    app = JsonTableApp(root)
    root.mainloop()
