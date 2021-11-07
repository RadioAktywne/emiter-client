
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import * 

from PyQt5.QtWidgets import QApplication, QDialog, QTableWidget, QTableWidgetItem

import time

#dni tygodnia
wdays = ['Poniedziałek','Wtorek','Środa','Czwartek','Piątek','Sobota','Niedziela']

class Gui_utils:

    def __init__(self,ui_object):
        self.ui = ui_object

    def table_resize(self):
        #resize'y
        # self.ui.playlist_table.setColumnWidth(0,80)
        # self.ui.playlist_table.setColumnWidth(1,80)
        # self.ui.playlist_table.setColumnWidth(2,50)
        # self.ui.playlist_table.setColumnWidth(3,300)
        # self.ui.playlist_table.setColumnWidth(4,300)
        # self.ui.playlist_table.setColumnWidth(5,400)

        # self.ui.schedule_table.setColumnWidth(0,80)
        # self.ui.schedule_table.setColumnWidth(1,80)
        # self.ui.schedule_table.setColumnWidth(2,80)
        # self.ui.schedule_table.setColumnWidth(3,80)
        # self.ui.schedule_table.setColumnWidth(4,200)
        # self.ui.schedule_table.setColumnWidth(5,400)
        pass


    #aktualizuje pojedyńczy wiersz w tabelo
    def set_table_row(self,table,row,data,color):
        #liczba wierszy
        rows = table.rowCount()
        #print("found "+str(rows)+" rows")

        if row < rows:

            #kolor
            color = QtGui.QColor(color[0],color[1],color[2])
            bg = QtGui.QBrush(color)
            bg.setStyle(QtCore.Qt.SolidPattern)

            for c in range(len(data)):
                cell = QTableWidgetItem(data[c])
                cell.setBackground(bg)
                table.setItem(row,c,cell)


    #bindy dla obiektów
    def set_playlist_row(self,row,data,color):
        self.set_table_row(self.ui.playlist_table,row,data,color)
    def set_schedule_row(self,row,data,color):
        self.set_table_row(self.ui.schedule_table,row,data,color)

    def show_playlist(self,datas,colors):
        for i in range(len(datas)):
            self.set_playlist_row(i,datas[i],colors[i])

    def show_schedule(self,datas,colors):
        for i in range(len(datas)):
            self.set_schedule_row(i,datas[i],colors[i])        


    #data
    def set_date(self,wd,d):
        self.ui.current_date.setText(time.strftime("%Y-%m-%d",d))
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
            else:
                #nic nie rób
                pass
        else:
            obj.setText(time.strftime("%H:%M:%S ",time.gmtime(ts)))


    def update_break_downtime(self,t):
        self.ui.current_break_downtime.setText(time.strftime("-%M:%S ",t))

    def update_time(self,tstr):
        self.update_clock(self.ui.current_time,tstr)

    def set_playlist_clock(self,t):
        self.disable_clock(self.ui.studio_uptime)
        self.disable_clock(self.ui.studio_downtime)
        self.disable_clock(self.ui.schedule_downtime)
        self.update_clock_from_timestamp(self.ui.playlist_downtime,t)

    def set_schedule_clock(self,t):
        self.disable_clock(self.ui.studio_uptime)
        self.disable_clock(self.ui.studio_downtime)
        self.disable_clock(self.ui.playlist_downtime)
        self.update_clock_from_timestamp(self.ui.schedule_downtime,t)

    def set_studio_clock(self,tup,tdown,enable_downtime=False):
        self.disable_clock(self.ui.schedule_downtime)
        self.disable_clock(self.ui.playlist_downtime)
        self.update_clock_from_timestamp(self.ui.studio_uptime,tup)
        if enable_downtime:
            self.update_clock_from_timestamp(self.ui.studio_downtime,tdown,negative_time=True)
        else:
            self.disable_clock(self.ui.studio_downtime)

    def status_onair(self,obj):
        obj.setStyleSheet("color: rgb(220, 0, 0)")
        obj.setText("Odtwarzam")

    def status_ready(self,obj):
        obj.setStyleSheet("color: rgb(0, 220, 0)")
        obj.setText("Gotowy")

    def status_suspend(self,obj):
        obj.setStyleSheet("color: rgb(0, 0, 0)")
        obj.setText("Zatrzymany")

    def set_status_playlist(self):
        self.status_onair(self.ui.playlist_status)
        self.status_suspend(self.ui.schedule_status)
        
    def set_status_schedule(self):
        self.status_onair(self.ui.schedule_status)
        self.status_ready(self.ui.playlist_status)

    def set_status_schedule_ready(self):
        self.status_ready(self.ui.schedule_status)

    def set_status_none(self):
        self.status_ready(self.ui.playlist_status)
        self.status_suspend(self.ui.schedule_status)

    def studio_status_start_countdown(self,secs):
        self.ui.studio_label.setStyleSheet("background-color: rgb(252, 233, 79);")
        self.ui.studio_label.setText("Łączę za "+str(secs))

    def studio_status_split_countdown(self,secs):
        self.ui.studio_label.setStyleSheet("background-color: rgb(252, 233, 79);")
        self.ui.studio_label.setText("Dzielę za "+str(secs))

    def studio_status_connected(self):
        self.ui.studio_label.setStyleSheet("background-color: rgb(0, 233, 0);")
        self.ui.studio_label.setText("POŁĄCZONY")
    
    def studio_status_disconnecting(self):
        self.ui.studio_label.setStyleSheet("background-color: rgb(255, 100, 100);")
        self.ui.studio_label.setText("Rozłączanie")

    def studio_status_disconnected(self):
        self.ui.studio_label.setStyleSheet("background-color: rgb(255, 0, 0);")
        self.ui.studio_label.setText("ROZŁĄCZONY")

    def studio_status_wait(self):
        self.ui.studio_label.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.ui.studio_label.setText("...")
    
    def buttons_set_start_cancelling(self):
        self.ui.b_connect_now.setText("")
        self.ui.b_connect_10s.setText("Anuluj")
        self.ui.b_split_now.setText("")
        self.ui.b_split_10s.setText("")
        self.ui.b_disconnect.setText("")
        
    def buttons_set_split_cancelling(self):
        self.ui.b_connect_now.setText("")
        self.ui.b_connect_10s.setText("")
        self.ui.b_split_now.setText("")
        self.ui.b_split_10s.setText("Anuluj")
        self.ui.b_disconnect.setText("")

    def buttons_reset(self):
        self.ui.b_connect_now.setText("Połącz teraz")
        self.ui.b_connect_10s.setText("Połącz za 10 s")
        self.ui.b_split_now.setText("Dziel teraz")
        self.ui.b_split_10s.setText("Dziel za 10 s")
        self.ui.b_disconnect.setText("Rozłącz")

    def rds_to_now(self):
        #przerzut audycja następna -> audycja teraz
        self.ui.current_aud_name.setText(self.ui.next_aud_name.text())
        self.ui.current_aud_host.setText(self.ui.next_aud_host.text())