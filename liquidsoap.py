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
    
    comm = "liquidsoap"
    liq_file = "client.liq"
    
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
        
        logging.info(f"Liquidsoap script path: {liq_path}")
        
        try:
            import shutil
            liquidsoap_binary = shutil.which(self.comm)
            if liquidsoap_binary:
                logging.info(f"Liquidsoap binary found at: {liquidsoap_binary}")
            else:
                logging.error(f"Liquidsoap binary '{self.comm}' not found in PATH")
                self.set_error(-11)
                return
        except Exception as e:
            logging.error(f"Error checking liquidsoap binary: {e}")
        
        if not os.path.exists(liq_path):
            logging.error(f"Liquidsoap script not found: {liq_path}")
            self.set_error(-11)
            return
            
        cfg_path = self.path + "/client.cfg"
        if not os.path.exists(cfg_path):
            logging.error(f"Config file not found: {cfg_path}")
            logging.error("Please copy client.cfg.example to client.cfg and configure it")
            self.set_error(-11)
            return
        
        if self.external_proc_running():
            logging.info("Found not properly closed liquidsoap thread. Killing attempt...")
            #próba zabicia
            self.send("sudoku")
            time.sleep(5)

            if self.external_proc_running():
                #teraz to już serio coś się zjebało
                self.set_error(-10)
                print(self.error_text(self.errorcode))
                
                return
        
        self.running = False
        attempt = 1

        while not self.running:
            logging.info("starting liquidsoap process attempt #"+str(attempt))
            
            try:
                logging.info(f"Running command: {self.comm} {liq_path}")
                self.proc = subprocess.Popen([self.comm, liq_path], 
                                           stdout=subprocess.PIPE, 
                                           stderr=subprocess.STDOUT, 
                                           universal_newlines=True,
                                           cwd=self.path)
                time.sleep(2)

                self.running = self.proc.poll() == None
                
                if self.running:
                    logging.info(f"Liquidsoap process started with PID: {self.proc.pid}")
                else:
                    try:
                        output, _ = self.proc.communicate(timeout=1)
                        logging.error(f"Liquidsoap failed to start. Output: {output}")
                    except subprocess.TimeoutExpired:
                        logging.error("Liquidsoap process terminated immediately")
                        
            except Exception as e:
                logging.error(f"Exception starting liquidsoap: {e}")
                self.running = False

            attempt += 1
            if attempt >= 3:
                #nieudane uruchomienie
                self.set_error(-11)
                logging.error(self.error_text(self.errorcode))
                return
            
        logging.info("Liquidsoap started successfully")

        self.tracker = threading.Thread(target=self.trace_stdout)
        self.tracker.daemon = True 
        self.tracker.start()


    def trace_stdout(self):
        #proces odczytu linii w tle
        logging.info("Starting stdout trace thread")
        line_count = 0
        
        while self.proc.poll() is None:
            try:
                proc_line = self.proc.stdout.readline()
                if proc_line:
                    line_count += 1
                    logging.debug(f"Liquidsoap output [{line_count}]: {proc_line.strip()}")
                    
                    #wiadomości dobre
                    if 'Connection setup was successful' in proc_line:
                        self.connected_flag = True
                        self.set_error(0)
                        logging.info("Studio connection established")
                    elif 'Closing connection...' in proc_line:
                        self.connected_flag = False
                        logging.info("Studio connection closed")
                    elif 'Studio started' in proc_line:
                        logging.info("Studio output started")
                    elif 'Studio stopped' in proc_line:
                        logging.info("Studio output stopped")

                    #wiadomości hiobowe
                    elif 'Connection failed: Not_found' in proc_line or 'Connection failed: could not connect' in proc_line:
                        logging.error(f"Connection failed: {proc_line.strip()}")
                        self.set_error(-2)
                    elif 'Connection refused' in proc_line:
                        logging.error(f"Connection refused: {proc_line.strip()}")
                        self.set_error(-3)
                    elif "connection timeout" in proc_line:
                        logging.error(f"Connection timeout: {proc_line.strip()}")
                        self.set_error(-5)
                    elif 'Error' in proc_line or 'error' in proc_line:
                        logging.warning(f"Liquidsoap error: {proc_line.strip()}")
                    elif 'Exception' in proc_line or 'exception' in proc_line:
                        logging.error(f"Liquidsoap exception: {proc_line.strip()}")
                    elif proc_line.strip().startswith('At line'):
                        logging.error(f"Liquidsoap syntax error: {proc_line.strip()}")
                        
            except Exception as e:
                logging.error(f"Error reading liquidsoap output: {e}")
                break

        exit_code = self.proc.poll()
        logging.error(f"Liquidsoap process ended with exit code: {exit_code}")
        
        try:
            remaining_output = self.proc.stdout.read()
            if remaining_output:
                logging.error(f"Final liquidsoap output: {remaining_output}")
        except Exception as e:
            logging.error(f"Error reading final output: {e}")
            
        #jeśli tu jesteś, znaczy że proces umar
        self.running = False
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

    def external_proc_running(self):
        #sprawdza, czy proces aktywny
        proc_list = os.popen("ps aux").read().splitlines()

        found = False
        for proc in proc_list:
            #szukaj w liście procesów nazwy skryptu
            if self.liq_file in proc:
                logging.debug("found:")
                logging.debug(proc)

                found = True
                break

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
            logging.error(f"Socket file does not exist: {socket_path}")
            return "ERROR: Socket not found"
        
        try:
            result = os.popen('( echo "'+command+'"; echo exit ) | socat '+socket_path+' -').read()
            logging.debug(f"Command result: {result.strip()}")
            return result
        except Exception as e:
            logging.error(f"Error sending command '{command}': {e}")
            return "ERROR: Command failed"

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
        self.send('S4.insert artist="'+code+'", title="'+rds+'"')