#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5 import QtWidgets
from PyQt5.QtCore import * 

from PyQt5.QtWidgets import QMessageBox, QInputDialog

import logging
import time
from datetime import datetime
import signal
import threading

import gui_utils
import emiterui
import liquidsoap
import program  
import subprocess
import os

#### CONFIG START ####

#API path
api_path="https://cloud.radioaktywne.pl/api"

#loglevel
loglevel = logging.INFO

#### CONFIG END ####

#get real path of file
path = os.path.dirname(os.path.realpath(__file__))

#set logging to stdout and file
logging.basicConfig(handlers=[logging.FileHandler(path+'/client.log'),logging.StreamHandler()], level=loglevel,format='%(asctime)s %(levelname)s: %(message)s')

class View(QtWidgets.QMainWindow):


    def __init__(self):
        super().__init__()

        #self.ui = ui_object
        self.ui = emiterui.Ui_EmiterClient()
        self.ui.setupUi(self)
        self.util = gui_utils.Gui_utils(self.ui)

        #bindy
        self.ui.b_connect_now.clicked.connect(core.connect)
        self.ui.b_disconnect.clicked.connect(core.disconnect)
        self.ui.next_aud_preset.currentTextChanged.connect(core.change_program)
        self.ui.next_aud_nearest.clicked.connect(core.set_next_program)
        self.ui.b_rds_update.clicked.connect(core.update_rds)

        self.ui.statusbar.showMessage("Emiter - system emisyjny Radia Aktywnego")

        self.util.studio_status_disconnected()

    def errorBox(self,title,text):
        box = QMessageBox.about(self,title,text)

    def status(self,text):
        self.ui.statusbar.showMessage(time.strftime("%H:%M:%S ")+text)

    def question(self,header,text):
        resp = QMessageBox.question(self,header,text, QMessageBox.Yes | QMessageBox.No )
        return resp == QMessageBox.Yes

    def rds_textbox(self,default=""):
        #TODO default
        rds,done = QInputDialog.getText(self,"Podaj RDS","Nowy RDS:",text=default)
        
        if not done:
            return None
        else:
            return rds

    def closeEvent(self,event):
        #message
        msg = "Czy jesteś pewien że chcesz zamknąć?\nPamiętaj, że jeśli program uruchomiony jest z poziomu Claudii, powinien być zamknięty przyciskiem 'Stop studio'."
        
        #if live show, add info about it
        if core.live:
            msg = "TRWA AUDYCJA NA ŻYWO!\nAktualnie jesteś połączony z serwerem emisji.\nZamkniecie spowoduje zakończenie transmisji.\n\n"+msg
            
        reply = QMessageBox.question(self, 'Zamykanie', msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            event.accept()
            logging.info('Window closed')
        else:
            event.ignore()

class Core:

    init = True

    break_interval = 30*60

    program = program.Program()

    program_index_now = 0
    program_index_next = 0

    program_list = [
        {"slug":"", "listname":"- Brak audycji - ", "rds":"", "anytime":False},
        {"slug":"custom", "listname":"<custom> Inna audycja", "rds":"", "anytime":True}
    ]

    rds = ""

    live = False
    connection_error = 0
    #studio_counter = 0

    studio_start_timer = 0
    studio_endtime_flag = False
    studio_end_timer = 0

    def __init__(self):

        #timer
        self.sec_timestamp = -1
        self.day_timestamp = -1
        self.timer = QTimer()
        self.timer.timeout.connect(self.masterTimer)
        self.timer.start(100)

    def masterTimer(self):
        now = time.localtime()

        if self.sec_timestamp != now.tm_sec:
            #nowa sekunda
            self.secondant(now)
            self.sec_timestamp = now.tm_sec

            if self.day_timestamp != now.tm_mday:
                #nowy dzień
                view.util.set_date(now.tm_wday,now)
                self.day_timestamp = now.tm_mday

        #connection tracker
        if self.live:
            if not liquidsoap_instance.connected_flag:
                #disconnected now
                self.live = False
                
                view.ui.aud_rds.setText("")
                view.ui.current_aud_preset.setText("")
                view.util.studio_status_disconnected()
                view.status("Rozłączono z serwerem emisji")
                self.connection_error = 0

                self.studio_endtime_flag = False

                #disable all clocks
                view.util.disable_clock(view.ui.studio_uptime)
                view.util.disable_clock(view.ui.studio_downtime)
        else:
            if liquidsoap_instance.connected_flag:
                #connected right now
                self.live = True
                view.util.studio_status_connected()
                view.status("Połączono z serwerem emisji")

        if liquidsoap_instance.errorcode != self.connection_error:
            if liquidsoap_instance.errorcode >= 0:
                #when errorcode set to 0 (successful connection after error occured)
                view.errorBox("Informacja","Ponownie połączono z serwerem")
            else:
                #non-zero code - error occured
                view.errorBox("Błąd połączenia",liquidsoap_instance.error_text(liquidsoap_instance.errorcode))
                view.util.studio_status_reconnecting()
                view.status("Błąd połączenia: "+liquidsoap_instance.error_text(liquidsoap_instance.errorcode))
            #self.disconnect()
            self.connection_error = liquidsoap_instance.errorcode
            

    def secondant(self,now):
        #funkcja wywoływane w każdej nowej sekundzie

        #zegar główny
        view.util.update_time(now)

        #sekundy do pełnej
        break_sec = self.break_interval - (time.time() % self.break_interval) +1
        view.util.update_break_downtime(time.gmtime(break_sec))

        #studio uptime clock
        if self.live:
            view.util.update_clock(view.ui.studio_uptime,time.gmtime(time.time()-self.studio_start_timer))

        #studio downtime clock
        if self.studio_endtime_flag:
            overtime = view.util.update_clock_from_timestamp(view.ui.studio_downtime,self.studio_end_timer-time.time()+1,negative_time=True)
            if overtime:
                #Blink-in
                view.ui.studio_downtime.setStyleSheet("color: rgb(0, 0, 0); background-color: rgb(255, 0, 0)")
                #Set thread to blink-out after 0.5 s
                threading.Thread(target=self.blink_reset_after,args=(0.5,)).start()
        else:
            view.util.disable_clock(view.ui.studio_downtime)


                
    #Reset studio downtime flag to normal
    def blink_reset_after(self,t):
        time.sleep(t)
        view.ui.studio_downtime.setStyleSheet("color: rgb(255, 0, 0); background-color: rgb(0, 0, 0)")

    def rewrite_rds(self,t):
        time.sleep(t)
        logging.info("Rewriting RDS...")
        liquidsoap_instance.insert_rds(self.program_list[self.program_index_now]["slug"],self.rds)
                
    def disconnect(self):
        logging.info("Disconnect button pressed")
        if not self.live:
            view.errorBox("Błąd","Już rozłączono!")
            return
        view.util.studio_status_disconnecting()
        liquidsoap_instance.stop_studio()
        self.program_index_now = 0

    def connect(self):
        logging.info("Program start button pressed")

        #TODO disable downtime clock
        view.util.disable_clock(view.ui.studio_downtime)
    
        if self.program_list[self.program_index_next]["slug"] == "":
            view.errorBox("Błąd","Nie wybrano audycji")
            return

        if self.program_index_next == self.program_index_now:
            view.errorBox("Błąd","Nie zmieniono audycji")
            return

        #check if program starts today
        if self.program_list[self.program_index_next]["anytime"]:
            logging.info("Program %s can be started anytime" % self.program_list[self.program_index_next]["slug"])
            self.studio_endtime_flag = False
        else:
            #check if it starts today
            now = time.localtime()
            wd = now.tm_wday+1
            #get programs today
            pgms_today = self.program.list_programs(wd,0,0,0)
            pgm_today = None
            for pgm in pgms_today:
                if not pgm["replay"]:
                    if pgm["program"]["slug"] == self.program_list[self.program_index_next]["slug"]:
                        pgm_today = pgm
                        break
            #if program found
            if pgm_today is not None:
                logging.info("Program %s is today" % pgm_today["program"]["slug"])
                self.studio_endtime_flag = True
                #create endtime based on today and program time
                dt_start = datetime(now.tm_year,now.tm_mon,now.tm_mday,pgm_today["begin_h"],pgm_today["begin_m"],0)
                ts_start = dt_start.timestamp()
                self.studio_end_timer = ts_start + pgm_today["duration"]*60
            else:
                logging.info("Program %s is NOT today" % self.program_list[self.program_index_next]["slug"])
                resp = view.question("Błąd wyboru audycji","Audycja '"+self.program_list[self.program_index_next]["slug"]+"' nie odbywa się dziś!\n"+
                    "- Sprawdź, czy wybrałeś prawidłową audycję\n"+
                    "- Jeśli chcesz prowadzić audycję poza standardowymi godzinami, potrzebujesz zgody RedProga,\n"+
                    "- W przypadku niestandardowej audycji (bez powtórki) poza godzinami nadawania, wybierz z listy 'inna audycja'.\n\n"+
                    "Czy mimo to chcesz kontynuować?")
                if resp:
                    #set program but endtime flag is false
                    self.studio_endtime_flag = False
                else:
                    #abort
                    logging.info("Aborted")
                    return
        if self.live:
            view.status("Zmiana audycji")
        else:
            view.status("Łączenie")
            view.util.studio_status_wait()
            liquidsoap_instance.start_studio()
        #push RDS here
        liquidsoap_instance.insert_rds(self.program_list[self.program_index_next]["slug"],self.rds)
        view.ui.aud_rds.setText(self.rds)
        #przerzut
        self.program_index_now = self.program_index_next
        view.ui.current_aud_preset.setText(self.program_list[self.program_index_now]["listname"])
        #set start time
        self.studio_start_timer = time.time()
        #due to bug in emiter-server
        #rewrite RDS after a few seconds
        threading.Thread(target=self.rewrite_rds,args=(2,)).start()

    def update_rds(self):
        logging.info("Update RDS button presed")
        rds = None

        change_rds = False

        if self.program_index_next == 0:
            view.errorBox("Błąd","Nie wybrano żadnej audycji")
        elif self.program_index_next != self.program_index_now:
            view.errorBox("Nowa audycja?","Ustawiono nową audycję \"%s\", ale jej nie zaczęto.\nRDS zostanie zaktualizowany po wciśnięciu \"Start nowej audycji\"." % self.program_list[self.program_index_next]["slug"])
            rds = view.rds_textbox(default=self.program_list[self.program_index_next]["rds"])
        else:
            view.status("aktualizowanie RDS")
            #okienko
            rds = view.rds_textbox(default=self.rds)
            #aktualizuj
            change_rds = True
            pass

        if rds is not None:
            logging.info("New rds is "+rds)
            self.rds = rds
            view.ui.aud_rds.setText(rds)

            if change_rds:
                #ustaw nowy RDS
                liquidsoap_instance.insert_rds(self.program_list[self.program_index_now]["slug"],self.rds)
                view.status("Zaktualizowano RDS")

    def change_program(self):
        #zmiana audycji
        self.program_index_next = view.ui.next_aud_preset.currentIndex()

        pgm = self.program_list[self.program_index_next]
        view.ui.aud_rds.setText(pgm["rds"])
        self.rds = pgm["rds"]
        
    #set program incoming
    def set_next_program(self):
        #get program starting in next 15 minutes
        pgm_now = self.program.get_program_now(False,True,time_margin=15)

        #find program by slug (0 by default)
        index_now = 0 

        #gdy znaleziono program
        if pgm_now["found"]:
            if not pgm_now["replay"]:
                for i in range(len(self.program_list)):
                    if self.program_list[i]["slug"] == pgm_now["slug"]:
                        index_now = i
                        break

        view.ui.next_aud_preset.setCurrentIndex(index_now)
        

    def update_pgm_list(self):
        #load api
        view.status("Pobieranie danych z API...")
        
        for i in range(5):
            
            if i > 0:
                view.status("Ponowna próba pobrania audycji z API (%d)..." % i)
            # try to get data from api
            if self.program.update_from_api(api_path):
                break

            if i == 4:
                view.errorBox("Błąd","Nie udało się wczytać listy audycji.\n\n- Sprawdź, czy komputer jest połączony z internetem,\n- Być może to awaria serwera emisji. Skontaktuj się z działem IT.")
                return
            time.sleep(5)

        programs = self.program.list_all_programs()
    
        view.status("Wczytano %d audycji z API" % len(programs))
        
        for p in programs:
            self.program_list.append({
                "slug":p["slug"], 
                "listname":"<%s> %s " % (p["slug"], p["name"]),
                "rds": p["rds"],
                "anytime":False
            })

        #refresh list
        view.ui.next_aud_preset.clear()
        for i in range(len(self.program_list)):
            view.ui.next_aud_preset.addItem("")
            view.ui.next_aud_preset.setItemText(i,self.program_list[i]["listname"])

        #set to 0
        view.ui.next_aud_preset.setCurrentIndex(0)


logging.info("---- CLIENT START")
app = QtWidgets.QApplication(sys.argv)

def ensure_pulse_source():
    try:
        result = subprocess.run(['pactl', 'list', 'sources', 'short'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if 'emiter-virtual-source.monitor' in line:
                print(f"[INFO] Found existing emiter-virtual-source.monitor")
                return 'emiter-virtual-source.monitor'
    except Exception as e:
        print(f"[WARN] pactl failed: {e}")
    def try_create_pwloopback():
        print(f"[DEBUG] Attempting to create emiter-virtual-source with pactl...")
        proc = subprocess.Popen(['pactl', 'load-module', 'module-null-sink', 'sink_name=emiter-virtual-source'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.wait()
        if proc.returncode == 0:
            print(f"[INFO] Created emiter-virtual-source with pactl")
            return 'emiter-virtual-source.monitor'
        else:
            print(f"[ERROR] Failed to create with pactl")
            return None
    try:
        name = try_create_pwloopback()
        if name:
            return name
    except Exception as e:
        print(f"[EXCEPTION] Exception during ensure_pulse_source: {e}")
        try:
            result = subprocess.run(['pactl', 'list', 'sources', 'short'], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if 'monitor' in line:
                    name = line.split()[1]
                    print(f"[INFO] Using fallback monitor source: {name}")
                    return name
        except Exception as e2:
            print(f"[FATAL] Could not find any monitor source: {e2}")
        raise RuntimeError('PulseAudio error: {}. No suitable source found.'.format(e))

try:
    pulse_source_name = ensure_pulse_source()
    if not pulse_source_name or not isinstance(pulse_source_name, str):
        raise RuntimeError(f"Pulse source name is invalid: {pulse_source_name}")
    os.environ['PULSE_SOURCE'] = pulse_source_name
    print(f"[DEBUG] Set PULSE_SOURCE={pulse_source_name}")
    subprocess.run(['pactl', 'set-default-source', pulse_source_name], check=True)
    print(f"[DEBUG] Set default source to {pulse_source_name}")
    liquidsoap_instance = liquidsoap.Liquidsoap()
    if liquidsoap_instance.fetch_error() < 0:
        raise RuntimeError("Nie udało się uruchomić klienta systemu emisji")
except Exception as e:
    print(f"[FATAL] PulseAudio/Liquidsoap error: {e}")
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Critical)
    msg.setText("PulseAudio/Liquidsoap error: {}".format(str(e)))
    msg.setWindowTitle("Emiter - Krytyczny błąd")
    msg.exec_()
    sys.exit(-1)

core = Core()
view = View()
view.show()


def sig_handle(signo,stack_frame):
    logging.info("SIGTERM handled. Closing...")
    liquidsoap_instance.stop()
    sys.exit(0)

signal.signal(signal.SIGTERM, sig_handle)

#update program list
threading.Thread(target=core.update_pgm_list).start()

#run GUI
appout = app.exec()

#when closed:
liquidsoap_instance.stop()
logging.info("---- CLIENT STOP")
sys.exit(appout)
