import os
import subprocess
import time
import threading
import logging

from PyQt5.QtCore import * 


errors = {
    0:"All right!",
    -1:"Liquidsoap process stopped",
    -2:"Server not found. Check network connection",
    -3:"Connection refused by server",
    -4:"Unknown",
    -5:"Stream timeout",
    -6:"Connection timeout",
    -10:"Nie udało się zamknąć procesu. Sprawdź, czy emiter nie jest już uruchomiony lub spróbuj zamknąć proces ręcznie.",
    -11:"Nie udało się uruchomić procesu."
}


class Liquidsoap:
    proc = None
    
    comm = "docker"
    liq_file = "client.liq"
    docker_image = "savonet/liquidsoap:v1.4.3"
    docker_name = "emiter-liquidsoap"
    
    connected_flag = False
    errorcode = 0
    
    running = False
    #live = False

    interval = 0.1
    timeout = 3.0

    def __init__(self):
        #ścieżka w której jest skrypt
        self.path = os.path.dirname(os.path.realpath(__file__))

        #ścieżka do procesu
        liq_path = self.path+"/"+self.liq_file
        pulse_socket = os.environ.get("PULSE_SERVER", "unix:/run/user/1000/pulse/native")
        pulse_dir = "/run/user/1000/pulse"
        pipewire_socket = "/run/user/1000/pipewire-0"
        user_id = str(os.getuid())
        group_id = str(os.getgid())
        pulse_source = os.environ.get("PULSE_SOURCE", "")
        docker_cmd = [
            "docker", "run", "--name", self.docker_name, "--rm", "--interactive", "--network", "host", "--tty",
            "--user", f"{user_id}:{group_id}",
            "--volume", f"{pulse_dir}:{pulse_dir}",
            "--volume", f"{pipewire_socket}:{pipewire_socket}",
            "--volume", f"{self.path}:/workspace",
            "--workdir", "/workspace",
            "--env", f"PULSE_SERVER={pulse_socket}",
            "--env", f"PIPEWIRE_REMOTE=unix:{pipewire_socket}",
            "--env", f"PULSE_SOURCE={pulse_source}",
            self.docker_image,
            "liquidsoap",
            self.liq_file
        ]
        
        #sprawdź czy proces liquidsoapa nie pracuje już na kompie
        if self.external_proc_running():
            logging.info("Found not properly closed liquidsoap thread. Killing attempt...")
            #próba zabicia
            self.send("sudoku")
            time.sleep(10)

            if self.external_proc_running():
                logging.info("Trying to kill Docker container...")
                try:
                    subprocess.run(["docker", "kill", self.docker_name], check=False)
                    time.sleep(2)
                    subprocess.run(["docker", "rm", self.docker_name], check=False)
                except Exception as e:
                    logging.error(f"Failed to kill/rm Docker container: {e}")
                
                if self.external_proc_running():
                    #teraz to już serio coś się zjebało
                    self.set_error(-10)
                    print(self.error_text(self.errorcode))
                    
                    return
        
        self.running = False
        attempt = 1

        while not self.running:
            logging.info("starting liquidsoap process attempt #"+str(attempt))
            self.proc = subprocess.Popen(docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            time.sleep(1)

            self.running = self.proc.poll() is None

            attempt += 1
            if attempt >= 3:
                #nieudane uruchomienie
                self.set_error(-11)
                logging.error(self.error_text(self.errorcode))
                return
        logging.info("Liquidsoap (Docker) started")
        #run STDOUT tracking
        self.tracker = threading.Thread(target=self.trace_stdout)
        self.tracker.start()


    def trace_stdout(self):
        #proces odczytu linii w tle
        #print("thread")
        while self.proc.poll() is None:
            proc_line = self.proc.stdout.readline()
            #print(proc_line)

            #wiadomości dobre
            if 'Connection setup was successful' in proc_line:
                self.connected_flag = True
                self.set_error(0)
            elif 'Closing connection...' in proc_line:
                self.connected_flag = False

            #wiadomości hiobowe
            elif 'Connection failed: Not_found' in proc_line or 'Connection failed: could not connect' in proc_line:
                self.set_error(-2)
            elif 'Connection refused' in proc_line:
                self.set_error(-3)
            elif "connection timeout" in proc_line:
                self.get_error(-5)

        #jeśli tu jesteś, znaczy że proces umar
        self.set_error(-1)


    # def __del__(self):
    #     self.stop()

    def stop(self):
        logging.info("stopping liquidsoap process")
        try:
            self.proc.kill()
        except AttributeError:
            logging.info("Nothing to close!")
        
        finally:
            self.running = False
            # Clean up socket file
            socket_path = self.path + "/client.sock"
            try:
                if os.path.exists(socket_path):
                    os.unlink(socket_path)
                    logging.info("Cleaned up socket file")
            except Exception as e:
                logging.error(f"Failed to clean up socket: {e}")

    def external_proc_running(self):
        #sprawdza, czy proces aktywny
        proc_list = os.popen("ps aux").read().splitlines()

        found = False
        for proc in proc_list:
            #szukaj w liście procesów nazwy skryptu lub dockera
            if self.liq_file in proc or ("docker" in proc and self.docker_name in proc):
                logging.debug("found:")
                logging.debug(proc)

                found = True
                break

        # Also check for running Docker containers
        if not found:
            try:
                result = subprocess.run(["docker", "ps", "--filter", f"name={self.docker_name}", "--format", "{{.Names}}"], capture_output=True, text=True)
                if self.docker_name in result.stdout:
                    logging.debug(f"Found running Docker container: {self.docker_name}")
                    found = True
            except Exception as e:
                logging.debug(f"Failed to check Docker containers: {e}")

        return found

    def set_error(self,code):
        self.errorcode = code
        logging.info(self.error_text(self.errorcode))

    def error_text(self,code):
        return errors.get(code,"Unknown error(%d)"%code)

    def start_with_ack(self):
        wait_time = 0.0

        #start studia
        self.start_studio()

        while not self.connected_flag:
            time.sleep(self.interval)
            wait_time += self.interval

            if wait_time >= self.timeout:
                #timeout
                logging.error("Connection timeout...")
                self.errorcode = -6
                return False

            if self.errorcode != 0:
                logging.error(self.error_text(self.errorcode))
                return False

        #self.live = True
        return True

    def stop_with_ack(self):
        wait_time = 0.0

        #koniec studia
        self.stop_studio()

        while self.connected_flag:
            time.sleep(self.interval)
            wait_time += self.interval

            if wait_time >= self.timeout:
                #timeout
                logging.error("Disonnection timeout...")
                self.errorcode = -6
                return False

            if self.errorcode != 0:
                logging.error(self.error_text(self.errorcode))
                return False

        #self.live = False
        return True

    def fetch_error(self):
        #pobiera kod błędu
        return self.errorcode

    def send(self,command):
        logging.info("sending command: "+command)
        socket_path = self.path+'/client.sock'
        if not os.path.exists(socket_path):
            logging.warning("Socket file does not exist")
            return ""
        #print(socket_path)
        result = os.popen('( echo "'+command+'"; echo exit ) | socat '+socket_path+' -').read()
        return result

    def start_studio(self):
        self.send("studio.start")
        #self.statuscode = 2 #łączenie

    def stop_studio(self):
        self.send("studio.stop")
        #self.statuscode = 4 #rozłączanie

    def connected(self):
        #sprawdza czy połączony
        return "on" in self.send("studio.status")

    def insert_rds(self,code,rds):
        self.send('S4.insert album=\\"'+code+'\\", title=\\"'+rds+'\\"')