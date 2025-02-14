import paramiko
import time
import os
import sys
import datetime as dt

class Conectar():

    def log(self,mensaje):
        hoy = dt.date.today()
        carga = str(hoy)+".txt"
        with open(carga, "a") as archivo:
            archivo.write(mensaje+ "\n")
   
    def Lanza(self, lo, num):
        try:
            if lo[0] and lo[1] and lo[2] and lo[3] and lo[4]:
                host = lo[0]
                ip = lo[1]
                user = lo[2]
                password = lo[3]
                port = lo[4]
        
            codigo = '''#!/bin/python
# -*- coding: utf-8 -*-
import json
import argparse
import subprocess

# Configuración del plugin
PLUGIN_VERSION = 1
HEARTBEAT = '"true"'
METRIC_UNITS = {'"Backup status"': '"count"'}

# Ruta del archivo de respaldo
#backup_file = '"/opt/site24x7/monagent/plugins/respaldo_rutas/backup_rutas.txt"'
backup_file = '"/home/site24x7/site24x7/monagent/plugins/respaldo_rutas/backup_rutas.txt"'

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
                subprocess.call(['"ip"', '"route"', '"show"'], stdout=file, universal_newlines=True)

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


        
        
            ########110_opt 
            #command = 'sudo mkdir /opt/site24x7/monagent/plugins/respaldo_rutas'
            #command = 'sudo chmod 777 /opt/site24x7/monagent/plugins/respaldo_rutas/'
            #command = 'sudo touch /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py'
            #command = 'sudo chmod 777 /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py'
            #command = f"echo \"{codigo}\" | sudo tee /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py > /dev/null"
            #command = 'sudo chown -R site24x7-agent:site24x7-group /opt/site24x7/monagent/plugins/respaldo_rutas'
            #command = 'sudo python /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py'
            #command = 'sudo ls -l /opt/site24x7/monagent/plugins'
            command = 'hostname'
            ########110_opt
            
            ######142_opt  /opt/site24x7/monagent/plugins/
            #command = 'hostname'
            #command = 'sudo ls /opt/site24x7/monagent/plugins'
            #command = 'sudo mkdir /opt/site24x7/monagent/plugins/respaldo_rutas'
            #command = 'sudo chmod 700 /opt/site24x7/monagent/plugins/respaldo_rutas/'
            #command = 'sudo touch /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py'
            #command = 'sudo chmod 777 /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py'
            #command = 'sudo touch /opt/site24x7/monagent/plugins/respaldo_rutas/backup_rutas.txt'
            #command = 'sudo chmod 722 /opt/site24x7/monagent/plugins/respaldo_rutas/backup_rutas.txt'
            #command = f"echo \"{codigo}\" | sudo tee /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py > /dev/null"
            #command = 'sudo chown -R site24x7-agent:site24x7-group /opt/site24x7/monagent/plugins/respaldo_rutas'
            #command = 'sudo python /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py'
            #command = 'sudo ls -l /opt/site24x7/monagent/plugins/'
            #command = 'sudo cat /opt/site24x7/monagent/plugins/respaldo_rutas/backup_rutas.txt'
            ######142_opt
            
            
            ######142_home /home/site24x7/site24x7/monagent/plugins
            #command = 'hostname'
            #command = 'ls /home/site24x7/site24x7/monagent/plugins'
            #command = 'mkdir /home/site24x7/site24x7/monagent/plugins/respaldo_rutas'
            #command = 'sudo chmod 777 /home/site24x7/site24x7/monagent/plugins/respaldo_rutas'
            #command = 'touch /home/site24x7/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py'
            #command = 'chmod 777 /home/site24x7/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py'
            #command = 'touch /home/site24x7/site24x7/monagent/plugins/respaldo_rutas/backup_rutas.txt'
            #command = 'sudo chmod 722 /home/site24x7/site24x7/monagent/plugins/respaldo_rutas/backup_rutas.txt'
            #command = f"echo \"{codigo}\" | sudo tee /home/site24x7/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py > /dev/null"
            #command = 'chown -R site24x7-agent:site24x7-group /home/site24x7/site24x7/monagent/plugins/respaldo_rutas'
            #command = 'python /home/site24x7/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py'
            #command = 'ls -l /home/site24x7/site24x7/monagent/plugins/respaldo_rutas/backup_rutas.txt'
            #command = 'ls -l /home/site24x7/site24x7/monagent/plugins/'
            ######142_home
            
            #command = 'sudo cat /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py'
            #command = 'sudo ls /'
            #command = 'find / -name /site24x7/monagent/plugins'
            #command = 'find / -name '"'/site24x7/monagent/plugins'"''
            #command = 'sudo bfind / -type d -path '"'/site24x7/monagent/plugins'"''
            #command = 'sudo ls /'
            if lo:
                
                try:
                    TIMEOUT = 10
                    ssh = paramiko.SSHClient()
                    ssh.load_system_host_keys()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(ip, port,username=user, password=password,timeout=TIMEOUT)
                    print("Conexión establecida...")
                    
                    #######envia comando
                    start_time = time.time()
                    stdin, stdout, stderr = ssh.exec_command(command, bufsize =-1, timeout = None, get_pty=True,environment = None)
                    
                    while not stdout.channel.exit_status_ready():
                        if time.time() - start_time > TIMEOUT:
                            print("El comando ha tardado demasiado, cerrando sesión...")
                            me = str(num)+' '+str(host)+' '+str(ip)+' '+'No se ejecuto el comando, tardo la sesión'
                            self.log(me)
                            ssh.close()
                            if ssh.get_transport() and ssh.get_transport().is_active():
                                m = str(num)+' '+str(host)+' '+str(ip)+' '+'No se ejecuto el comando, cerrando la sesión'
                                self.log(m)
                                ssh.close()
                            break
                    
                    st=stdout.readlines()
                    error = stderr.read().decode()

                    if st:
                        aplicado = str(num)+' '+str(host)+' '+str(ip)+' | '+str(st)
                        if aplicado:
                            print(aplicado)
                            self.log(aplicado)
                        else:
                            correcto = aplicado+' Valor Vacio /Comando aplicado correctamente'
                            print(correcto)
                            self.log(correcto)
                    ssh.close()
                    print('cerrando sesion satisfactoria')
                    if error:
                        print(error)
                        er = str(num)+' '+' '+str(host)+' '+str(ip)+' '+str(command)+' '+str(error)
                        self.log(er)
                    
                except paramiko.AuthenticationException:
                    print("Error de autenticación, revisa las credenciales")
                    error1 = str(num)+' '+str(host)+' '+str(ip)+' '+str(command)+' '+'Error autenticacion'
                    self.log(error1)
                except paramiko.SSHException as e:
                    print(f"Error de conexión SSH: {e}")
                    error2 = str(num)+' '+str(host)+' '+str(ip)+' '+str(command)+' '+f"Error conexion ssh {e}"
                    self.log(error2)
                except Exception as e:
                    print(f"Error: {e}")
                    error3 = str(num)+' '+str(host)+' '+str(ip)+' '+str(command)+' '+f"Error{e}"
                    self.log(error3)
                finally:
                    transport = ssh.get_transport()
                    if transport and transport.is_active():
                        sesion = str(num)+"Cerrando sesion ssh ... \n"+' '+str(host)+' '+str(ip)+' '+str(command)
                        self.log(sesion)
                        ssh.close()

            else:
                calor = 'No se puede realizar la acción'
                print(calor)
                self.log(calor)
        except IndexError:
            print("La lista no tiene todos los elementos (hostname, ip, user, password, port)")
    
    def Ejecutar(self):
        num = 0
        arc = input("Nombre del archivo: ")
        direc = os.getcwd()
        path = f'{direc}\{arc}.txt'
        if path:
            with open(path, "r") as file:
                for ml in file:
                    num = num+1
                    li = ml.split()
                    self.Lanza(li, num)
        else:
            no = 'No encontre el path termine'
            self.log(no)

if __name__ == '__main__':
    iniciar = Conectar()
    iniciar.Ejecutar()

    




