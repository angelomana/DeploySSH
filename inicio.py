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
    
    def Subir(self):
        pass

    
    def Comandos(self):
        direct = os.getcwd()
        coma = f"{direct}\commands.txt"
        with open(coma, "r") as file:
            for ml in file:
                if ml:
                    if ml == 'deploy':
                        print('es:' +ml)
                    else:
                        print('es:'+ml)
   
    def Lanza(self, lo, num):
        now = dt.datetime.now()
        tod = now.strftime("%Y-%m-%d %H:%M:%S")
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
            #command = f"echo \"{codigo}\" | sudo tee /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py > /dev/null"
            ########110_opt
            
            
            ######142_opt  /opt/site24x7/monagent/plugins/
            #command = f"echo \"{codigo}\" | sudo tee /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py > /dev/null"
            ######142_opt
            
            
            ######142_home /home/site24x7/site24x7/monagent/plugins
            #command = f"echo \"{codigo}\" | sudo tee /home/site24x7/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py > /dev/null"
            ######142_home
            
                '''
                sudo find / -type d -name "monagent"
                sudo mkdir /opt/site24x7/monagent/plugins/respaldo_rutas /tmp/monitoreo
                sudo chmod 777 /opt/site24x7/monagent/plugins/respaldo_rutas/ /tmp/monitoreo
                sudo touch /opt/site24x7/monagent/plugins/respaldo_rutas/backup_rutas.txt
                sudo chmod 722 /opt/site24x7/monagent/plugins/respaldo_rutas/backup_rutas.txt
                sudo chown -R site24x7-agent:site24x7-group /opt/site24x7/monagent/plugins/respaldo_rutas
                sudo ls -l /opt/site24x7/monagent/plugins/respaldo_rutas
                sudo chmod 777 /opt/site24x7/monagent/plugins/respaldo_rutas /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py
                sudo python /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py
                sudo ls -la /opt/site24x7/monagent/plugins/respaldo_rutas/backup_rutas.txt
                
                deploy

                sudo mv /tmp/monitoreo/respaldo_rutas.py /opt/site24x7/monagent/plugins/respaldo_rutas/
                sudo chown -R site24x7-agent:site24x7-group /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py
                sudo python /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py
                
                sudo ls -la /opt/site24x7/monagent/plugins/respaldo_rutas/
                sudo cat /opt/site24x7/monagent/plugins/respaldo_rutas/backup_rutas.txt
                '''
                
                #subir = f"echo \"{codigo}\" | tee /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py > /dev/null"
                
                
                '''
                sudo find / -type d -name "monagent"
                sudo mkdir /home/site24x7/site24x7/monagent/plugins/respaldo_rutas /tmp/monitoreo
                sudo chmod 777 /home/site24x7/site24x7/monagent/plugins/respaldo_rutas/ /tmp/monitoreo
                sudo touch /home/site24x7/site24x7/monagent/plugins/respaldo_rutas/backup_rutas.txt
                sudo chmod 722 /home/site24x7/site24x7/monagent/plugins/respaldo_rutas/backup_rutas.txt
                sudo chown -R site24x7:site24x7 /home/site24x7/site24x7/monagent/plugins/respaldo_rutas
                
                deploy
                
                sudo mv /tmp/monitoreo/respaldo_rutas.py /home/site24x7/site24x7/monagent/plugins/respaldo_rutas/
                sudo chown -R site24x7:site24x7 /home/site24x7/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py
                sudo chmod 777 /opt/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py
                sudo python /home/site24x7/site24x7/monagent/plugins/respaldo_rutas/respaldo_rutas.py
                
                sudo ls -l /home/site24x7/site24x7/monagent/plugins/respaldo_rutas
                sudo ls -la /home/site24x7/site24x7/monagent/plugins/respaldo_rutas/backup_rutas.txt
                sudo ls -la /home/site24x7/site24x7/monagent/plugins/respaldo_rutas/
                sudo cat /home/site24x7/site24x7/monagent/plugins/respaldo_rutas/backup_rutas.txt
                '''
                
                
                
                if lo:
                    try:
                        TIMEOUT = 10
                        ssh = paramiko.SSHClient()
                        ssh.load_system_host_keys()
                        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        ssh.connect(ip, port,username=user, password=password,timeout=TIMEOUT)
                        start_time = time.time()
                        subi = str(num)+' '+str(tod)+' '+str(host)+' '+str(ip)+' Conectando ...'
                        print(subi)
                        self.log(subi)
                        
                        directi = os.getcwd()
                        coma = f"{directi}\commands.txt"
                        with open(coma, "r") as file:
                            for ml in file:
                                if ml.strip() == 'deploy':
                                    try:
                                        origen = 'hola.txt'
                                        destino = '/tmp/monitoreo/hola.txt'
                                        sftp = ssh.open_sftp()
                                        sftp.put(origen, destino)
                                        print(f"Archivo {origen} subido exitosamente a {destino}")
                                        sftp.close()
                                        subi = str(num)+' '+str(tod)+' '+str(host)+' '+str(ip)+' Subiendo'
                                        print(subi)
                                        self.log(subi)
                                    except Exception as e:
                                        print(e)
                                    finally:
                                        #ssh.close()
                                        pass
                                    
                                else:                        
                                    stdin, stdout, stderr = ssh.exec_command(ml, bufsize =-1, timeout = None, get_pty=True,environment = None)
                                    while not stdout.channel.exit_status_ready():
                                        if time.time() - start_time > TIMEOUT:
                                            print(subi+" El comando ha tardado demasiado")
                                            me = str(num)+' '+str(tod)+' '+str(host)+' '+str(ip)+' '+'No se ejecuto el comando, tardo la sesión\n'
                                            self.log(me)
                                            #stdout.channel.send("\x03")
                                            ssh.close()
                                        
                                            if ssh.get_transport() and ssh.get_transport().is_active():
                                                m = str(num)+' '+str(tod)+' '+str(host)+' '+str(ip)+' '+'No se ejecuto el comando, cerrando la sesión\n'
                                                self.log(m)
                                                ssh.close()
                                            break
                                            
                                    
                                    st=stdout.readlines()
                                    error = stderr.read().decode()

                                    if st:
                                        aplicado = str(num)+' '+str(tod)+' '+str(host)+' '+str(ip)+' '+str(st)
                                        if aplicado:
                                            print(aplicado)
                                            self.log(aplicado)
                                        else:
                                            correcto = aplicado+' Valor Vacio /Comando aplicado correctamente\n'
                                            print(correcto)
                                            self.log(correcto)
                                    
                                    #print('cerrando sesion satisfactoria')
                                    if error:
                                        noj = str(num)+' '+str(tod)+' '+str(host)+' '+str(ip)+' '+str(command)+' '+str(error)+'\n'
                                        print(noj)
                                        self.log(noj)
                                #else:
                                 #   print(str(num)+'No hay comando\n')
                                
                    except paramiko.AuthenticationException:
                        error1 = str(num)+' '+str(tod)+' '+str(host)+' '+str(ip)+' '+'Error autenticacion ...\n'
                        print(error1)
                        self.log(error1)
                    except paramiko.SSHException as e:
                        error2 = str(num)+' '+str(tod)+' '+str(host)+' '+str(ip)+' '+f"Error conexion ssh {e} ...\n"
                        print(error2)
                        self.log(error2)
                    except Exception as e:
                        error3 = str(num)+' '+str(tod)+' '+str(host)+' '+str(ip)+' '+f"Error{e} ... revisar disponibilidad del servidor\n"
                        print(error3)
                        self.log(error3)
                    finally:
                        transport = ssh.get_transport()
                        if transport and transport.is_active():
                            sesion = str(num)+' '+str(tod)+' '+str(host)+' '+str(ip)+" ... Cerrando sesion\n"
                            print(sesion)
                            self.log(sesion)
                            ssh.close()
            else:
                calor = str(num)+'No tiene valores, o no se puede realizar la acción\n'
                print(calor)
                self.log(calor)
        except IndexError:
            print(str(num)+' '+"La lista no tiene todos los elementos (hostname, ip, user, password, port)\n")
    
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
