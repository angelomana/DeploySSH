import paramiko
import time
import os
import datetime as dt

class Conectar():
    
    def log(self,mensaje):
        hoy = dt.date.today()
        carga = "f{hoy}.txt"
        with open(carga, "a", encoding='utf-8') as archivo:
            archivo.write(mensaje+ "\n")
    
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
        
                

        
                #sudo find / -type d -name "monagent"
                #service site24x7monagent restart
                
                if lo:
                    try:
                        TIMEOUT = 10
                        ssh = paramiko.SSHClient()
                        ssh.load_system_host_keys()
                        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        ssh.connect(ip, port,username=user, password=password,timeout=TIMEOUT)
                        start_time = time.time()
                        subi = '\n'
                        print(subi)
                        self.log(subi)
                        
                        directi = os.getcwd()
                        coma = f"{directi}\commands.txt"
                        with open(coma, "r") as file:
                            for ml in file:
                                if ml.strip() == 'deploy':
                                    try:
                                        origen = 'respaldo_rutas.py'
                                        destino = '/tmp/monitoreo/respaldo_rutas.py'
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

                                    try:
                                        stdin, stdout, stderr = ssh.exec_command(ml)
                                        output = stdout.read().decode('utf-8')
                                        error = stderr.read().decode('utf-8')
                                        if time.time() - start_time > TIMEOUT:
                                            
                                            while not stdout.channel.exit_status_ready():
                                                print(subi+" El comando ha tardado demasiado")
                                                me = str(num)+' '+str(tod)+' '+str(host)+' '+str(ip)+' '+'No se ejecuto el comando, tardo la sesión\n'
                                                self.log(me)
                                                stdout.channel.send("\x03")
                                                #ssh.close()
                                            
                                                if ssh.get_transport() and ssh.get_transport().is_active():
                                                    m = str(num)+' '+str(tod)+' '+str(host)+' '+str(ip)+' '+'No se ejecuto el comando, cerrando la sesión\n'
                                                    self.log(m)
                                                    ssh.close()
                                                break

                                        if error:
                                            print(f"Error al ejecutar el comando: {error}")
                                        else:
                                            print(output)
                                            

                                    except Exception as e:
                                        print(e)
                                    finally:
                                        #ssh.close()
                                        pass
                                """
                                else:
                                    print('ya no revalide deploy')
                                    
                                    while not stdout.channel.exit_status_ready():
                                        if time.time() - start_time > TIMEOUT:
                                            print(subi+" El comando ha tardado demasiado")
                                            me = str(num)+' '+str(tod)+' '+str(host)+' '+str(ip)+' '+'No se ejecuto el comando, tardo la sesión\n'
                                            self.log(me)
                                            stdout.channel.send("\x03")
                                            #ssh.close()
                                        
                                            if ssh.get_transport() and ssh.get_transport().is_active():
                                                m = str(num)+' '+str(tod)+' '+str(host)+' '+str(ip)+' '+'No se ejecuto el comando, cerrando la sesión\n'
                                                self.log(m)
                                                ssh.close()
                                            break
                                            
                                    
                                    #st=stdout.readlines()
                                    
                                    st = stdout.read().decode('utf-8')
                                    error = stderr.read().decode('utf-8')
                                    
                                    
                                    if st:
                                        aplicado = str(num)+' '+str(tod)+' '+str(host)+' '+str(ip)+' '+str(st)+'\n'
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
                                """
                                        
                                
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
                            sesion = "Cerrando \n"
                            print(sesion)
                            self.log(sesion)
                            ssh.close()
            else:
                calor = str(num)+' '+str(lo)+'No tiene valores, o no se puede realizar la acción\n'
                print(calor)
                self.log(calor)
        except IndexError:
            er = str(num)+' '+str(lo)+' '+"La lista no tiene todos los elementos (hostname, ip, user, password, port)\n"
            print(er)
            self.log(er)
    
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

    





