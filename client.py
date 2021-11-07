#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import * 

from PyQt5.QtWidgets import QApplication, QDialog, QTableWidget, QTableWidgetItem, QMessageBox

import time
import json
import re
import signal

import gui_utils
import emiterui
import liquidsoap

#import danych z client.cfg
path = os.path.dirname(os.path.realpath(__file__))
with open(path+'/client.cfg') as cfgfile:
    #wykonaj zawartość pliku by pobrać zmienne z konfiguracji
    exec(cfgfile.read())
    #buduj zmienną cfg zawierającą konfigurację
    cfg = {'server_host': cfg_broadcast_host, 'telnet_port':telnet_port}


class View(QtWidgets.QMainWindow):


    def __init__(self):
        super().__init__()

        #self.ui = ui_object
        self.ui = emiterui.Ui_EmiterClient()
        self.ui.setupUi(self)
        self.util = gui_utils.Gui_utils(self.ui)

        #resize'y
        self.util.table_resize()

        #bindy
        self.ui.b_connect_now.clicked.connect(core.connect)
        self.ui.b_disconnect.clicked.connect(core.disconnect)
        self.ui.next_aud_preset.currentTextChanged.connect(core.change_aud)
        self.ui.next_aud_nearest.clicked.connect(core.set_next_aud)

        self.ui.statusbar.showMessage("Emiter - system emisyjny Radia Aktywnego")

    def errorBox(self,title,text):
        box = QMessageBox.about(self,title,text)

    def status(self,text):
        self.ui.statusbar.showMessage(time.strftime("%H:%M:%S ")+text)

    def closeEvent(self,event):
    #     reply = QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
    #     if reply == QMessageBox.Yes:
    #         event.accept()
    #         print('Window closed')
    #     else:
    #         event.ignore()
        event.accept()
        #liquidsoap.stop()
        

class Core:

    init = True

    break_interval = 30*60

    program_index_now = 0
    program_index_next = 0

    track_rem = 0
    track_end_stamp = 0
    status_update_refresh = 30
    status_update_timer = 30

    studio_start_flag = False
    studio_split_flag = False
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

    def reinit(self):
        print("reinit")
        view.status("ponowne pobieranie danych...")
        self.init = True

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
        #self.broadcast_stop()

    def connect(self):
        print("przycisk łącze teraz")
        #self.broadcast_start()
    
    def update_rds(self):
        print("przycisk aktualizuj")
        #split = Comm(['record.split czwartek'])
        #self.threadpool.start(split)

    def change_aud(self):
        #zmiana audycji TODO
        pass
        # self.program_index_next = view.ui.next_aud_preset.currentIndex()
        # aud = self.program.get_program(self.program_index_next)
        # view.ui.next_aud_name.setText(aud["name"])
        # view.ui.next_aud_host.setText(aud["host"])
        #self.slur_next = aud["slur"]
        #i inne kwestie....

    def set_next_aud(self):
        view.ui.next_aud_preset.setCurrentIndex(self.program.get_next_program_index())

app = QtWidgets.QApplication(sys.argv)

core = Core()
view = View()

#TODO rozwiązać problem zamykania liquidsoapa
liquidsoap = liquidsoap.Liquidsoap()
if liquidsoap.fetch_error() < 0:
    #błąd
    view.errorBox("Emiter - Krytyczny błąd",liquidsoap.error)
    sys.exit(-1)

view.show()

#handle SIGTERM signal (stop liquidsoap proc and exit)
def sig_handle(signo,stack_frame):
    print("signal handled")
    liquidsoap.stop()
    sys.exit(0)

signal.signal(signal.SIGTERM, sig_handle)

#run GUI
appout = app.exec()

#when closed:
liquidsoap.stop()
sys.exit(appout)
