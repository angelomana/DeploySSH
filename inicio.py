import paramiko
import time
import os
import datetime as dt

class Conectar():

    def log(self,mensaje):
        hoy = dt.date.today()
        carga = str(hoy)+".txt"
        with open(carga, "a") as archivo:
            archivo.write(mensaje+ "\n")
   
    def Lanza(self, lo, num):
        host = lo[0]
        user = lo[1]
        password = lo[2]
        port = lo[3]
        codigo = '''#!/usr/bin/python3
import json
import argparse
import subprocess

# Configuración del plugin
PLUGIN_VERSION = 1
HEARTBEAT = '"true"'
METRIC_UNITS = {'"Backup status"': '"count"'}

# Ruta del archivo de respaldo
backup_file = '"/opt/site24x7/monagent/plugins/respaldo_rutas/backup_rutas.txt"'

class Plugin:
    def __init__(self):
        self.data = {
            '"plugin_version"': PLUGIN_VERSION,
            '"heartbeat_required"': HEARTBEAT,
            '"units"': METRIC_UNITS
        }

    def getData(self):
        try:
            # Ejecutar el comando y guardar la salida
            with open(backup_file, '"w"') as file:
                subprocess.run(['"ip"', '"route"', '"show"'], stdout=file, universal_newlines=True)

            # Si la ejecución fue exitosa, marcar el backup como correcto
            self.data['"Backup status"'] = 1
            #self.data['"Backup file"'] = backup_file

        except Exception as e:
            self.data['"status"'] = 0
            self.data['"msg"'] = str(e)  # Mensaje de error
            self.data['"Backup status"'] = 0  # Indicar que el respaldo falló

        return self.data

if __name__ == '"__main__"':
    plugin = Plugin()
    data = plugin.getData()
    parser = argparse.ArgumentParser()
    parser.add_argument('"param"', nargs='"?"', default='"dummy"')
    args = parser.parse_args()
    print(json.dumps(data, indent=4, sort_keys=True))  # Salida en formato JSON
                    '''
        #command = 'sudo mkdir /opt/site24x7/monagent/plugins/respaldo_rutas'
        #command = 'sudo chmod 777 /opt/site24x7/monagent/plugins/respaldo_rutas/'
        #command = 'sudo touch /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py'
        #command = 'sudo chmod 777 /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py'
        #command = 'sudo chmod o+w /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py'
        #command = f"sudo echo '''{codigo}''' > /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py"
        #command = "sudo echo 'hola desde acá' > /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py"
        #command = f"echo \"{codigo}\" | sudo tee /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py > /dev/null"
        command = f"echo \"{codigo}\" | sudo tee /prueba/respaldo_rutas.py > /dev/null"
        #command = 'sudo cat /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py'
        #command = 'sudo chmod 777 /prueba/'
        #command = 'touch /prueba/respaldo_rutas.py'
        #command = f"echo '''{codigo}''' > /prueba/respaldo_rutas.py"
        #command = 'cat /prueba/respaldo_rutas.py'
        #command = 'sudo ls /'
        if lo:
            
            try:
                TIMEOUT = 10
                ssh = paramiko.SSHClient()
                ssh.load_system_host_keys()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host, port,username=user, password=password,timeout=TIMEOUT)
                print("Conexión Yes")
                
                #######envia comando
                start_time = time.time()
                stdin, stdout, stderr = ssh.exec_command(command, bufsize =-1, timeout = None, get_pty=True,environment = None)
                
                while not stdout.channel.exit_status_ready():
                    if time.time() - start_time > TIMEOUT:
                        print("El comando ha tardado demasiado, cerrando sesión...")
                        if ssh.get_transport() and ssh.get_transport().is_active():
                            ssh.close()
                        break
                
                st=stdout.readlines()
                error = stderr.read().decode()

                if st:
                    print(st)
                    ma = str(num)+' '+str(command)+' '+' '+str(host)+' '+str(st)
                    self.log(ma)
                    ssh.close()
                if error:
                    print(error)
                    er = str(num)+' '+str(command)+' '+' '+str(host)+' '+str(error)
                    self.log(er)
                
            except paramiko.AuthenticationException:
                print("Error de autenticación, revisa las credenciales")
                error = str(num)+' '+str(command)+' '+str(host)+' '+'Error autenticacion'
                self.log(error)
            except paramiko.SSHException as e:
                print(f"Error de conexión SSH: {e}")
                error = str(num)+' '+str(command)+' '+str(host)+' '+f"Error conexion ssh {e}"
                self.log(error)
            except Exception as e:
                print(f"Error: {e}")
                error = str(num)+' '+str(command)+' '+str(host)+' '+f"Error{e}"
                self.log(error)
            finally:
                transport = ssh.get_transport()
                if transport and transport.is_active():
                    print("Cerrando sesión SSH...")
                    ssh.close()
                #######envia comando
                
                #######envia archivo
                """
                try:
                    sftp = ssh.open_sftp()
                    sftp.put(local, remote)
                    print(f"Archivo {local} transferido correctamente a {remote}")
                    ssh.close()
                except Exception as e:
                    print('conecte pero no logre poner el archivo'+str(e))
                """
                #######envia archivo
                #ssh.close()
                
                #for line in iter(stdout.readline,""):
                    #print(line, end="")
                    #ssh.close()
                #print(stdout)
        else:
            print('Algo fallo')
    
    def Ejecutar(self):
        num = 0
        directory = os.getcwd()
        PATH_PROPERTIES = f"{directory}\local.txt"
        with open(PATH_PROPERTIES, "r") as file:
            for ml in file:
                num = num+1
                li = ml.split()
                self.Lanza(li, num)


if __name__ == '__main__':
    iniciar = Conectar()
    iniciar.Ejecutar()

    



