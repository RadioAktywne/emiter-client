
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import * 

from PyQt5.QtWidgets import QApplication, QDialog, QTableWidget, QTableWidgetItem

import time

#dni tygodnia
wdays = ['Poniedziałek','Wtorek','Środa','Czwartek','Piątek','Sobota','Niedziela']
class Gui_utils:

    def __init__(self,ui_object):
        self.ui = ui_object


    #data
    def set_date(self,wd,d):
        self.ui.current_date.setText(time.strftime("%d %B",d))
        self.ui.current_wd.setText(wdays[wd])

    #zegary

    #uniwersalny dezaktywator
    def disable_clock(self,obj):
        obj.setText("- -:- -:- - ")

    #uniwersalny updater
    def update_clock(self,obj,t):
        obj.setText(time.strftime("%H:%M:%S ",t))

    def update_clock_from_timestamp(self,obj,ts,negative_time=False):
        if ts < 0:
            if negative_time:
                obj.setText(time.strftime("-%H:%M:%S ",time.gmtime(abs(ts))))
                return True
            else:
                #nic nie rób
                pass
        else:
            obj.setText(time.strftime("%H:%M:%S ",time.gmtime(ts)))
            return False


    def update_break_downtime(self,t):
        self.ui.current_break_downtime.setText(time.strftime("-%M:%S ",t))

    def update_time(self,tstr):
        self.update_clock(self.ui.current_time,tstr)

    def studio_status_connected(self):
        self.ui.studio_label.setStyleSheet("background-color: rgb(0, 233, 0);")
        self.ui.studio_label.setText("POŁĄCZONY")
    
    def studio_status_disconnecting(self):
        self.ui.studio_label.setStyleSheet("background-color: rgb(255, 100, 100);")
        self.ui.studio_label.setText("Rozłączanie")

    def studio_status_reconnecting(self):
        self.ui.studio_label.setStyleSheet("background-color: rgb(255, 100, 100);")
        self.ui.studio_label.setText("Ponowne łączenie...")

    def studio_status_disconnected(self):
        self.ui.studio_label.setStyleSheet("background-color: rgb(255, 0, 0);")
        self.ui.studio_label.setText("ROZŁĄCZONY")

    def studio_status_wait(self):
        self.ui.studio_label.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.ui.studio_label.setText("...")
    