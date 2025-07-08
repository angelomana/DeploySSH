import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import datetime as dt
import paramiko
import time
import sys
import shutil

class JsonTableApp:
    DEFAULT_COLUMNS_ORDER = [
        "id", "hostname", "ip", "user", "password", "port", "Cargar (ruta origen)", "Subir (ruta absoluta destino)"
    ]

    def __init__(self, root):
        self.root = root
        self.root.title("KIOsko")
        try:
            # Establece la ruta a tu archivo .ico
            self.root.iconbitmap("uno.ico") 
        except tk.TclError:
            print("No se pudo encontrar el archivo 'uno.ico'. Asegúrate de que esté en la misma carpeta y sea un archivo .ico válido.")
        # --- FIN DE LÍNEA PARA CAMBIAR EL ÍCONO ---
        self.root.geometry("1200x700")
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
        self.columns = self.DEFAULT_COLUMNS_ORDER
        self.checked_items = {}

        self.log_text_widget = None
        self.error_log_widget = None
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        self.entry_fields = {}
        self.commands_text_area = None

        self.create_widgets()
        self.load_json_data()
        self.populate_table()
        self.load_today_log()
        sys.stdout = self.TextRedirector(self.log_text_widget, 'stdout')
        sys.stderr = self.TextRedirector(self.error_log_widget, 'stderr')

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=0)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=1)

        table_frame = ttk.Frame(main_frame)
        table_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        yscrollbar_table = ttk.Scrollbar(table_frame, orient="vertical")
        yscrollbar_table.pack(side="right", fill="y")
        xscrollbar_table = ttk.Scrollbar(table_frame, orient="horizontal")
        xscrollbar_table.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(table_frame, yscrollcommand=yscrollbar_table.set,
                                 xscrollcommand=xscrollbar_table.set, show="headings", height=10) # 'show' cambiado a 'headings'
        self.tree.pack(fill="both", expand=True)

        yscrollbar_table.config(command=self.tree.yview)
        xscrollbar_table.config(command=self.tree.xview)

        self.tree.bind("<Button-1>", self.on_item_click)
        self.tree.bind("<Double-1>", self.edit_record_popup)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, sticky="ew", pady=5, padx=10)
        ttk.Button(button_frame, text="Agregar Configuración", command=self.add_record_popup).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Editar Configuración", command=self.edit_selected_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Eliminar Configuración", command=self.delete_selected_records).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cargar Archivo para Deploy", command=self.load_file_for_deploy).pack(side=tk.LEFT, padx=5)

        log_frame = ttk.LabelFrame(main_frame, text="Registro de Actividad")
        log_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_text_widget = tk.Text(log_frame, wrap="word", state="disabled",
                                       bg="black", fg="white", font=("Courier New", 9))
        self.log_text_widget.grid(row=0, column=0, sticky="nsew")

        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text_widget.yview)
        log_scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text_widget.config(yscrollcommand=log_scrollbar.set)

        error_log_frame = ttk.LabelFrame(main_frame, text="Errores de Conexión / Despliegue")
        error_log_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        error_log_frame.grid_rowconfigure(0, weight=1)
        error_log_frame.grid_columnconfigure(0, weight=1)

        self.error_log_widget = tk.Text(error_log_frame, wrap="word", state="disabled",
                                        bg="darkred", fg="white", font=("Courier New", 9))
        self.error_log_widget.grid(row=0, column=0, sticky="nsew")

        error_log_scrollbar = ttk.Scrollbar(error_log_frame, orient="vertical", command=self.error_log_widget.yview)
        error_log_scrollbar.grid(row=0, column=1, sticky="ns")
        self.error_log_widget.config(yscrollcommand=error_log_scrollbar.set)

        commands_frame = ttk.LabelFrame(main_frame, text="Comandos a enviar separados por renglón (escribe 'deploy' para subir archivos)")
        commands_frame.grid(row=1, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)
        commands_frame.grid_rowconfigure(0, weight=1)
        commands_frame.grid_columnconfigure(0, weight=1)

        self.commands_text_area = tk.Text(commands_frame, wrap="word", height=6, font=("Courier New", 9))
        self.commands_text_area.grid(row=0, column=0, sticky="nsew")

        commands_scrollbar = ttk.Scrollbar(commands_frame, orient="vertical", command=self.commands_text_area.yview)
        commands_scrollbar.grid(row=0, column=1, sticky="ns")
        self.commands_text_area.config(yscrollcommand=commands_scrollbar.set)

        action_buttons_frame = ttk.Frame(commands_frame)
        action_buttons_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5,0))

        ttk.Button(action_buttons_frame, text="Lanzar Actividad", command=self.launch_ssh_operations).pack(side=tk.LEFT, padx=5)

    def _get_next_id(self):
        if not self.data:
            return 1
        existing_ids = [int(record.get('id', 0)) for record in self.data if isinstance(record.get('id'), (int, str)) and str(record.get('id')).isdigit()]
        return (max(existing_ids) + 1) if existing_ids else 1

    def load_json_data(self):
        if not os.path.exists(self.json_file_path):
            message = f"Info: Archivo JSON de configuración '{self.json_file_path}' no encontrado. Se creará uno vacío."
            messagebox.showinfo("Información", message)
            self.log_message(message)
            self.data = []
            self.save_json_data()
            return

        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            self.log_message(f"Configuraciones cargadas exitosamente desde {self.json_file_path}. Total: {len(self.data)}.")
            
            # ID validation and correction
            seen_ids = set()
            new_data = []
            id_changed_count = 0
            for record in self.data:
                record_id = record.get('id')
                if record_id is None or not isinstance(record_id, int) or record_id in seen_ids:
                    original_id = record_id
                    record['id'] = self._get_next_id()
                    id_changed_count += 1
                    self.log_message(f"ID duplicado o inválido encontrado '{original_id}'. Asignando nuevo ID: {record['id']}.")
                seen_ids.add(record['id'])
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

        self.columns = ["*"] + self.DEFAULT_COLUMNS_ORDER
        self.log_message(f"Columnas de configuración: {', '.join(self.columns)}")

    def save_json_data(self):
        try:
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            self.log_message(f"Configuraciones guardadas en {self.json_file_path}")
        except Exception as e:
            self.log_message(f"Error al guardar configuraciones en {self.json_file_path}: {e}")
            messagebox.showerror("Error de Guardado", f"No se pudieron guardar las configuraciones: {e}")

    def populate_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.checked_items.clear()

        # Configurar columnas
        self.tree["columns"] = self.columns
        self.tree.column("#0", width=0, stretch=tk.NO) # Ocultar la primera columna real del tree
        
        # Columna para el asterisco de selección
        self.tree.column("*", width=40, minwidth=40, anchor="center")
        self.tree.heading("*", text="Sel", anchor="center")

        for col in self.DEFAULT_COLUMNS_ORDER:
            self.tree.heading(col, text=col.replace("_", " ").title())
            if col == 'id':
                self.tree.column(col, width=50, minwidth=50, anchor="center")
            elif col in ["Cargar (ruta origen)", "Subir (ruta absoluta)"]:
                self.tree.column(col, width=200, minwidth=150, anchor="w")
            else:
                self.tree.column(col, width=120, minwidth=80, anchor="w")

        for item_data in self.data:
            values = [""] # Valor inicial para la columna de selección "*"
            for col in self.DEFAULT_COLUMNS_ORDER:
                if col == "password" and item_data.get(col):
                    values.append("********")
                else:
                    values.append(item_data.get(col, ""))
            
            item_id = self.tree.insert("", "end", values=values)
            self.checked_items[item_id] = False
        
        self.log_message(f"Tabla poblada con {len(self.data)} registros.")

    # === MÉTODO MODIFICADO ===
    def update_selection_marker(self, item_id, checked):
        """Actualiza el marcador de selección (*) en la columna 'Sel'."""
        if checked:
            self.tree.set(item_id, column="*", value="*")
        else:
            self.tree.set(item_id, column="*", value="")

    def on_item_click(self, event):
        item_id = self.tree.identify_row(event.y)
        column_id = self.tree.identify_column(event.x)
        
        # Seleccionar solo si se hace clic en cualquier lugar de la fila
        if item_id:
            current_state = self.checked_items.get(item_id, False)
            new_state = not current_state
            self.checked_items[item_id] = new_state
            # === LLAMADA AL MÉTODO MODIFICADO ===
            self.update_selection_marker(item_id, new_state)

    def add_record_popup(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("Agregar Nueva Configuración")
        add_window.transient(self.root)
        add_window.grab_set()

        self.entry_fields = {}

        for i, col in enumerate(self.DEFAULT_COLUMNS_ORDER):
            frame_row = ttk.Frame(add_window)
            frame_row.grid(row=i, column=0, columnspan=2, padx=5, pady=2, sticky="ew")
            frame_row.grid_columnconfigure(1, weight=1)

            label = ttk.Label(frame_row, text=f"{col.replace('_', ' ').title()}:")
            label.grid(row=0, column=0, padx=(0, 5), sticky="w")
            
            entry = ttk.Entry(frame_row)
            entry.grid(row=0, column=1, sticky="ew")
            self.entry_fields[col] = entry

            if col == 'password':
                entry.config(show="*")

            if col == 'id':
                next_id = self._get_next_id()
                entry.insert(0, str(next_id))
                entry.config(state='readonly')
            elif col == 'Cargar (ruta origen)':
                browse_button = ttk.Button(frame_row, text="Buscar", command=lambda e=entry: self._browse_local_file(e))
                browse_button.grid(row=0, column=2, padx=(5, 0), sticky="e")
            
        add_button = ttk.Button(add_window, text="Agregar", command=lambda: self._add_record(add_window))
        add_button.grid(row=len(self.DEFAULT_COLUMNS_ORDER), column=0, columnspan=2, pady=10)

        add_window.grid_columnconfigure(0, weight=1)
        add_window.grid_columnconfigure(1, weight=1)

    def _add_record(self, window):
        new_record = {col: entry.get() for col, entry in self.entry_fields.items()}

        required_fields = ["hostname", "ip", "user", "password", "port"]
        if not all(new_record.get(field) for field in required_fields):
            messagebox.showwarning("Advertencia", "Por favor, complete al menos los campos: Hostname, IP, Usuario, Contraseña y Puerto.")
            return

        try:
            new_record['port'] = int(new_record['port'])
            new_record['id'] = int(new_record['id'])
        except ValueError:
            messagebox.showwarning("Advertencia", "El campo 'Puerto' e 'ID' deben ser números enteros válidos.")
            return

        for col in self.DEFAULT_COLUMNS_ORDER:
            if col not in new_record:
                new_record[col] = ""

        self.data.append(new_record)
        self.save_json_data()
        self.populate_table()
        self.log_message(f"Configuración agregada: {new_record['hostname']} ({new_record['ip']})")
        window.destroy()
        
    def edit_selected_record(self):
        selected_items = [item_id for item_id, is_checked in self.checked_items.items() if is_checked]

        if not selected_items:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un registro para editar.")
            return
        if len(selected_items) > 1:
            messagebox.showwarning("Advertencia", "Por favor, seleccione solo un registro para editar.")
            return

        item_id = selected_items[0]
        self.edit_record_popup(item_id=item_id)

    def edit_record_popup(self, event=None, item_id=None):
        if item_id is None:
            item_id = self.tree.identify_row(event.y)

        if not item_id:
            return

        tree_values = self.tree.item(item_id, 'values')
        
        try:
            # El ID está en la segunda columna de los valores (índice 1)
            selected_record_id = int(tree_values[1]) 
        except (ValueError, IndexError):
             messagebox.showerror("Error", "No se pudo obtener el ID del registro seleccionado.")
             return

        original_record = next((record for record in self.data if record.get('id') == selected_record_id), None)
        original_record_index = next((i for i, record in enumerate(self.data) if record.get('id') == selected_record_id), -1)

        if original_record is None:
            messagebox.showerror("Error", "No se pudo encontrar la configuración original para editar.")
            return

        edit_window = tk.Toplevel(self.root)
        edit_window.title("Editar Configuración")
        edit_window.transient(self.root)
        edit_window.grab_set()

        self.entry_fields = {}

        for i, col in enumerate(self.DEFAULT_COLUMNS_ORDER):
            frame_row = ttk.Frame(edit_window)
            frame_row.grid(row=i, column=0, columnspan=2, padx=5, pady=2, sticky="ew")
            frame_row.grid_columnconfigure(1, weight=1)

            label = ttk.Label(frame_row, text=f"{col.replace('_', ' ').title()}:")
            label.grid(row=0, column=0, padx=(0, 5), sticky="w")
            
            entry = ttk.Entry(frame_row)
            entry.grid(row=0, column=1, sticky="ew")
            
            if col == 'password':
                entry.config(show="*")

            entry.insert(0, str(original_record.get(col, "")))

            if col == 'id':
                entry.config(state='readonly')
            elif col == 'Cargar (ruta origen)':
                browse_button = ttk.Button(frame_row, text="Buscar", command=lambda e=entry: self._browse_local_file(e))
                browse_button.grid(row=0, column=2, padx=(5, 0), sticky="e")
            
            self.entry_fields[col] = entry

        save_button = ttk.Button(edit_window, text="Guardar Cambios", command=lambda: self._save_edited_record(edit_window, original_record_index))
        save_button.grid(row=len(self.DEFAULT_COLUMNS_ORDER), column=0, padx=5, pady=10, sticky="ew")
        
        close_button = ttk.Button(edit_window, text="Cerrar", command=edit_window.destroy)
        close_button.grid(row=len(self.DEFAULT_COLUMNS_ORDER), column=1, padx=5, pady=10, sticky="ew")

        edit_window.grid_columnconfigure(0, weight=1)
        edit_window.grid_columnconfigure(1, weight=1)


    def _save_edited_record(self, window, record_index):
        updated_record = {col: entry.get() for col, entry in self.entry_fields.items()}

        required_fields = ["hostname", "ip", "user", "password", "port"]
        if not all(updated_record.get(field) for field in required_fields):
            messagebox.showwarning("Advertencia", "Por favor, complete al menos los campos: Hostname, IP, Usuario, Contraseña y Puerto.")
            return

        try:
            updated_record['port'] = int(updated_record['port'])
            updated_record['id'] = int(updated_record['id'])
        except ValueError:
            messagebox.showwarning("Advertencia", "El campo 'Puerto' e 'ID' deben ser números enteros válidos.")
            return

        for col in self.DEFAULT_COLUMNS_ORDER:
            if col not in updated_record:
                updated_record[col] = ""

        self.data[record_index] = updated_record
        self.save_json_data()
        self.populate_table()
        self.log_message(f"Configuración editada: {updated_record.get('hostname', '')} ({updated_record.get('ip', '')})")
        window.destroy()

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
                # El ID está en la columna 'id', que es la segunda columna de valores (índice 1)
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
        self.populate_table()
        self.log_message(f"Se eliminaron {deleted_count} configuración(es).")

    def _browse_local_file(self, entry_widget):
        file_path = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title="Seleccionar archivo para despliegue",
            filetypes=(("Todos los archivos", "*.*"),)
        )
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

        file_path = filedialog.askopenfilename(
            initialdir=os.getcwd(), title="Seleccionar archivo", filetypes=(("Todos los archivos", "*.*"),)
        )

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
                    self.data[record_index]['Cargar (ruta origen)'] = file_name
                    updated_count += 1
            except (ValueError, IndexError):
                 self.log_message(f"Advertencia: No se pudo actualizar el registro.")

        self.save_json_data()
        self.populate_table()
        self.log_message(f"Se asoció el archivo '{file_name}' a {updated_count} configuración(es).")
    
    # --- Métodos de SSH y Logging (sin cambios) ---
    def launch_ssh_operations(self):
        """Inicia las operaciones SSH para las configuraciones seleccionadas."""
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
            messagebox.showwarning("Advertencia", "Por favor, seleccione al menos una configuración para lanzar operaciones.")
            return

        commands_raw = self.commands_text_area.get(1.0, tk.END).strip()
        commands_list = [cmd.strip() for cmd in commands_raw.split('\n') if cmd.strip()]

        if not commands_list:
            messagebox.showwarning("Advertencia", "Por favor, ingrese comandos SSH.")
            return

        self.log_message("\n--- Iniciando Operaciones SSH ---")
        self.error_log_widget.config(state="normal")
        self.error_log_widget.delete(1.0, tk.END)
        self.error_log_widget.insert(tk.END, "--- Errores Detectados (Sesión Actual) ---\n")
        self.error_log_widget.config(state="disabled")

        for config in selected_configs:
            host, ip, user, password, port = (config.get(k, "") for k in ["hostname", "ip", "user", "password", "port"])
            port = int(port)

            self.log_message(f"\n--- Procesando: {host} ({ip}) ---")

            ssh_client = None
            try:
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(ip, port, username=user, password=password, timeout=10)
                self.log_message(f"Conexión exitosa a {host} ({ip}).")

                for command in commands_list:
                    if command.lower() == 'deploy':
                        local_file = config.get("Cargar (ruta origen)")
                        remote_path = config.get("Subir (ruta absoluta)")
                        self._deploy_file(ssh_client, local_file, remote_path, config['id'], host, ip)
                    else:
                        self._execute_ssh_command(ssh_client, command, config['id'], host, ip)

            except Exception as e:
                msg = f"ID {config.get('id', 'N/A')} - {host} ({ip}) - Error: {e}"
                self.log_message(msg)
                self.error_log_message(msg)
            finally:
                if ssh_client:
                    ssh_client.close()
                    self.log_message(f"Sesión SSH cerrada para {host} ({ip}).")

        self.log_message("\n--- Proceso de Operaciones SSH Finalizado ---")

    def _deploy_file(self, ssh_client, local_file_name, remote_dest_path, record_id, hostname, ip_address):
        if not local_file_name or not remote_dest_path:
            msg = f"ID {record_id} - {hostname}: Falta ruta local o remota para deploy."
            self.log_message(msg)
            self.error_log_message(msg)
            return

        local_full_path = os.path.join(self.deploy_source_folder, local_file_name)

        if not os.path.exists(local_full_path):
            msg = f"ID {record_id} - {hostname}: Archivo local no encontrado en '{local_full_path}'."
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
                self.log_message(f"Log de actividad del día cargado.")
            except Exception as e:
                self.log_message(f"Error al cargar log: {e}")
        else:
            self.log_message(f"No existe log para hoy. Se creará uno nuevo.")

        self.log_text_widget.see(tk.END)
        self.log_text_widget.config(state="disabled")

    def log_message(self, message):
        log_entry = f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n"
        
        self.log_text_widget.config(state="normal")
        self.log_text_widget.insert(tk.END, log_entry)
        self.log_text_widget.see(tk.END)
        self.log_text_widget.config(state="disabled")

        today_log_file = os.path.join(self.log_folder, f"{dt.date.today()}.log")
        try:
            with open(today_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            self.original_stdout.write(f"Error al escribir en log: {e}\n")

    def error_log_message(self, message):
        log_entry = f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n"

        self.error_log_widget.config(state="normal")
        self.error_log_widget.insert(tk.END, log_entry)
        self.error_log_widget.see(tk.END)
        self.error_log_widget.config(state="disabled")

        today_error_log_file = os.path.join(self.error_log_folder, f"error_{dt.date.today()}.log")
        try:
            with open(today_error_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            self.original_stderr.write(f"Error al escribir en log de errores: {e}\n")

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
    root = tk.Tk()
    app = JsonTableApp(root)
    root.mainloop()