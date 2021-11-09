#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import * 

from PyQt5.QtWidgets import QApplication, QDialog, QTableWidget, QTableWidgetItem, QMessageBox, QInputDialog

import time
import json
import signal
import threading

import gui_utils
import emiterui
import liquidsoap
import program  

#import danych z client.cfg
path = os.path.dirname(os.path.realpath(__file__))
with open(path+'/client.cfg') as cfgfile:
    #wykonaj zawartość pliku by pobrać zmienne z konfiguracji
    exec(cfgfile.read())

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

    def errorBox(self,title,text):
        box = QMessageBox.about(self,title,text)

    def status(self,text):
        self.ui.statusbar.showMessage(time.strftime("%H:%M:%S ")+text)

    def rds_textbox(self,default=""):
        #TODO default
        rds,done = QInputDialog.getText(self,"Podaj RDS","Nowy RDS:",text=default)
        
        if not done:
            return None
        else:
            return rds

    def closeEvent(self,event):
    #     reply = QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
    #     if reply == QMessageBox.Yes:
    #         event.accept()
    #         print('Window closed')
    #     else:
    #         event.ignore()
        event.accept()
        

class Core:

    init = True

    break_interval = 30*60

    program_index_now = 0
    program_index_next = 0

    program_list = [
        {"slug":"", "listname":"- Brak audycji - ", "rds":"", "anytime":False},
        {"slug":"custom", "listname":"<custom> Inna audycja", "rds":"", "anytime":True}
    ]

    live = False
    connection_error = 0
    studio_counter = 0

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
            if not liquidsoap.connected_flag:
                #disconnected now
                self.live = False
                view.util.studio_status_disconnected()
                view.status("Rozłączono z serwerem emisji")
        else:
            if liquidsoap.connected_flag:
                #connected right now
                self.live = True
                view.util.studio_status_connected()
                view.status("Połączono z serwerem emisji")

        if liquidsoap.errorcode != self.connection_error:
            view.errorBox("Błąd połączenia",liquidsoap.error_text(liquidsoap.errorcode))
            self.disconnect()
            self.connection_error = liquidsoap.errorcode
            

    def secondant(self,now):
        #funkcja wywoływane w każdej nowej sekundzie

        #zegar główny
        view.util.update_time(now)

        #sekundy do pełnej
        break_sec = self.break_interval - (time.time() % self.break_interval) +1
        view.util.update_break_downtime(time.gmtime(break_sec))

        #TODO zegar studia

    def disconnect(self):
        print("przycisk rozłącz")
        view.util.studio_status_disconnecting()
        liquidsoap.stop_studio()
        self.program_index_now = 0

    def connect(self):
        print("przycisk łącze teraz")
    
        if self.program_list[self.program_index_next]["slug"] == "":
            view.errorBox("Błąd","Nie wybrano audycji")
            return

        if self.program_index_next == self.program_index_now:
            view.errorBox("Błąd","Nie zmieniono audycji")
            return

        #push RDS here - TODO rds
        liquidsoap.insert_rds(self.program_list[self.program_index_next]["slug"],"")

        if self.live:
            view.status("Zmiana audycji")
        else:
            view.status("Łączenie")
            view.util.studio_status_wait()
            liquidsoap.start_studio()

        #przerzut
        self.program_index_now = self.program_index_next
        view.ui.current_aud_preset.setText(self.program_list[self.program_index_now]["listname"])


    def update_rds(self):
        print("przycisk aktualizuj")
        #split = Comm(['record.split czwartek'])
        #self.threadpool.start(split)
        rds = None

        if self.program_index_next == 0:
            view.errorBox("Błąd","Nie wybrano żadnej audycji")
        elif self.program_index_next != self.program_index_now:
            view.errorBox("Nowa audycja?","Ustawiono nową audycję \"%s\", ale jej nie zaczęto.\nRDS zostanie zaktualizowany po wciśnięciu \"Start nowej audycji\"." % self.program_list[self.program_index_next]["slug"])
            rds = view.rds_textbox(default=self.program_list[self.program_index_next]["rds"])
        else:
            view.status("aktualizowanie RDS")
            #okienko
            rds = view.rds_textbox(default=self.program_list[self.program_index_now]["rds"])
            #aktualizuj
            pass

        if rds is not None:
            print("New rds is "+rds)
            view.ui.aud_rds.setText(rds)

    def change_program(self):
        #zmiana audycji
        print("zmiana na pasku")
        self.program_index_next = view.ui.next_aud_preset.currentIndex()

        pgm = self.program_list[self.program_index_next]
        view.ui.aud_rds.setText(pgm["rds"])
        
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
        self.program = program.Program("https://cloud.radioaktywne.pl/api/dev")
        
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


app = QtWidgets.QApplication(sys.argv)

core = Core()
view = View()

#run liquidsoap subprocess
liquidsoap = liquidsoap.Liquidsoap()
if liquidsoap.fetch_error() < 0:
    #błąd
    view.errorBox("Emiter - Krytyczny błąd",liquidsoap.error)
    sys.exit(-1)

view.show()


#handle SIGTERM signal generated by Claudia (stop liquidsoap proc and exit)
def sig_handle(signo,stack_frame):
    print("signal handled")
    liquidsoap.stop()
    sys.exit(0)

signal.signal(signal.SIGTERM, sig_handle)

#update program list
threading.Thread(target=core.update_pgm_list).start()

#run GUI
appout = app.exec()

#when closed:
liquidsoap.stop()
sys.exit(appout)
