import os
import subprocess
import time
import threading

from PyQt5.QtCore import * 

# class Tracker_signals(QObject):
#     error = pyqtSignal(int)
#     connected = pyqtSignal()
#     disconnected = pyqtSignal()

errors = {
    0:"All right!",
    -1:"Liquidsoap process stopped",
    -2:"Server not found. Check network connection",
    -3:"Connection refused by server",
    -4:"Unknown",
    -5:"Stream timeout",
    -6:"Connection timeout"

}


class Liquidsoap:
    proc = None
    #threadpool = QThreadPool()

    comm = "liquidsoap"
    liq_file = "client.liq"
    
    connected_flag = False
    errorcode = 0
    error = ""

    running = False
    live = False

    interval = 0.1
    timeout = 3.0

    def __init__(self):
        #ścieżka w której jest skrypt
        self.path = os.path.dirname(os.path.realpath(__file__))

        #ścieżka do procesu
        liq_path = self.path+"/"+self.liq_file
        
        #sprawdź czy proces liquidsoapa nie pracuje już na kompie
        if self.external_proc_running():
            print("Found not properly closed liquidsoap thread. Killing attempt...")
            #próba zabicia
            self.send("sudoku")
            time.sleep(5)

            if self.external_proc_running():
                #teraz to już serio coś się zjebało
                self.error = "Nie udało się zamknąć procesu. Sprawdź, czy emiter nie jest już uruchomiony lub spróbuj zamknąć proces ręcznie."
                self.statuscode = -10
                print("Error: "+self.error)
                return
        
        self.running = False
        attempt = 1

        while not self.running:
            print("starting liquidsoap process attempt #"+str(attempt))
            self.proc = subprocess.Popen([self.comm, liq_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            time.sleep(1)

            self.running = self.proc.poll() == None

            attempt += 1
            if attempt >= 3:
                #nieudane uruchomienie
                self.error = "Nie udało się uruchomić procesu."
                self.statuscode = -11
                print("Error: "+self.error)
                return
            
        print("Liquidsoap started")

        #run STODUT tracking
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
            elif 'Connection failed: Not_found' in proc_line:
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
        print("stopping liquidsoap process")
        try:
            self.proc.kill()
        except AttributeError:
            print("nic do zamknięcia!")
        
        finally:
            self.running = False

    def external_proc_running(self):
        #sprawdza, czy proces aktywny
        proc_list = os.popen("ps aux").read().splitlines()

        found = False
        for proc in proc_list:
            #szukaj w liście procesów nazwy skryptu
            if self.liq_file in proc:
                print("found:")
                print(proc)

                found = True
                break

        return found

    def set_error(self,code):
        self.errorcode = code

        self.error = errors.get(code,"Unknown error(%d)"%code)
        print(self.error)

    def start_with_ack(self):
        wait_time = 0.0

        #start studia
        self.start_studio()

        while not self.connected_flag:
            time.sleep(self.interval)
            wait_time += self.interval

            if wait_time >= self.timeout:
                #timeout
                print("Connection timeout...")
                self.errorcode = -6
                return False

            if self.errorcode != 0:
                print(self.error)
                return False

        self.live = True
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
                print("Disonnection timeout...")
                self.errorcode = -6
                return False

            if self.errorcode != 0:
                print(self.error)
                return False

        self.live = False
        return True

    def fetch_error(self):
        #pobiera kod błędu
        return self.errorcode

    def send(self,command):
        socket_path = self.path+'/client.sock'
        #print(socket_path)
        result = os.popen("( echo '"+command+"'; echo exit ) | socat "+socket_path+' -').read()
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