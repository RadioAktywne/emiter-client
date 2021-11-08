#program.py - zardządzanie ramówką

from json.decoder import JSONDecodeError
#from emiter_core import cfg

import requests
#import datetime
import time
import json

import logging

class Program:
    #deprecated
    #margin = 5 # 5 minut
    program_table = []

    schedule = []
    programs = []

    #init - pobiera program
    def __init__(self,url,sufix="default"):
        
        #pobierz listę slotów
        rq = requests.get(url+"/timeslots")

        #jeśli odpowiada JSONem
        try:
            timeslots = rq.json()
            
            #zapisz kopię do json-ów
            # with open(cfg.cfg['path_schedules']+"timeslots_"+sufix,mode='w') as f:
            #     f.write(rq.text)
            #     f.close()

        except JSONDecodeError:
            
            logging.warning("API response /timeslots decoding error (status %d)"% rq.status_code)
            #jeśli nie:
            #importowanie dane z json-a
            # with open(cfg.cfg['path_schedules']+"timeslots_"+sufix) as f:
            #     timeslots = json.load(f)
            #     f.close()

        #pobierz listę programów
        rq = requests.get(url+"/programs")

        #jeśli odpowiada JSONem
        try:
            programs = rq.json()
            
            #zapisz kopię do json-ów
            # with open(cfg.cfg['path_schedules']+"programs_"+sufix,mode='w') as f:
            #     f.write(rq.text)
            #     f.close()

        except JSONDecodeError:
            
            logging.warning("API response /programs decoding error (status %d)"% rq.status_code)
            
            #jeśli nie:
            #importowanie dane z json-a
            with open(cfg.cfg['path_schedules']+"programs_"+sufix) as f:
                programs = json.load(f)
                f.close()
        
        #przerzut do listy jeśli audycja ma być widoczna przez system
        for uuid in timeslots:
            if timeslots[uuid]["program"]["broadcast_visible"]:
                self.schedule.append(timeslots[uuid])

        #sortowanie slotów po czasie
        self.schedule.sort(key=self.slot_minute_of_week)


        #lista wszystkich występujących slugów w timeslotach
        slugs = []
        for slot in self.schedule:
            slug = slot["program"]["slug"]
            if slug not in slugs:
                slugs.append(slug)

        for slug in slugs:
            #przeszukaj wśród zaimportowanych programów

            found = False
            for uuid in programs:
                #gdy znaleziono pasujący program
                if programs[uuid]["slug"] == slug:
                    self.programs.append(programs[uuid].copy())
                    found = True
                    break
            
            #jeśli nie znaleziono
            if not found:
                stub_program = {
                    "slug": slug,
                    "name": slug,
                    "rds": "",
                    "people": []
                }
                self.programs.append(stub_program)
        

    #funkcja do sortowania timeslotów
    def slot_minute_of_week(self,slot):
        return self.minute_of_week(slot["weekday"],slot["begin_h"],slot["begin_m"])

    #minuta w tygodniu
    def minute_of_week(self,wd,h,m):
        return (wd-1)*60*24 + h*60 + m

    #uwzględnia margines czasu do przodu lub do tyłu
    def time_margin(self,weekday,hour,min,margin):
        
        m = min + margin
        h = hour
        wd = weekday

        #carry
        if m >= 60:
            m -= 60
            h += 1
            if h >= 24:
                h -= 24
                wd +=1
                if wd > 7:
                    wd -= 7

        #borrow
        if m < 0:
            m += 60
            h -= 1
            if h < 0:
                h += 24
                wd -= 1
                if wd < 1:
                    wd += 7
        
        return wd, h, m

    #szukaj rekordu danego dnia tygodnia o danej godzinie
    def get_program(self,prev,next,wd,h,m,time_margin=5):

        #przesuwanie czasu do przodu/tyłu
        if(prev):
            weekday, hour, min = self.time_margin(wd,h,m,-time_margin)
        elif(next):
            weekday, hour, min = self.time_margin(wd,h,m,time_margin)
        else:
            weekday = wd
            hour = h
            min = m

        #minuta w tygodniu
        now_min_of_week = self.minute_of_week(weekday,hour,min)

        found = False
        target_program = {}
        for slot in self.schedule:

            #minuta tygodnia, gdy slot się zaczyna i kończy
            slot_min_of_week = self.slot_minute_of_week(slot)
            end_min_of_week = slot_min_of_week + slot["duration"]

            #jeśli audycja przechodzi przez koniec tygodnia (zaczyna się w niedzielę, kończy w poniedziałek)
            if end_min_of_week > self.minute_of_week(8,0,0):
                end_min_of_week -= self.minute_of_week(8,0,0)
                found = now_min_of_week >= slot_min_of_week or now_min_of_week < end_min_of_week
            else:
                #jeśli nie
                #czy czas mieści się w granicach?
                found = now_min_of_week >= slot_min_of_week and now_min_of_week < end_min_of_week


            #czy znaleziono audycję?
            if found:
                #wpisz dane
                target_program = {
                    "slug": slot["program"]["slug"],
                    "weekday":slot["weekday"],
                    "duration":slot["duration"],
                    "start_h":slot["begin_h"],
                    "start_m":slot["begin_m"],
                    "replay":slot["replay"]
                }

                #wydź z pętli
                break
        
        #dodaj flagę found i zwróć program
        target_program["found"] = found
        return target_program

    #wyszukuje n audycje/powtórek od danego punktu 
    #jeśli num = 0, wyszukuje wszystkie pozostałe danego dnia
    def list_programs(self,wd,h,m,num):
        
        #minuta w tygodniu
        now_min_of_week = self.minute_of_week(wd,h,m)

        i = 0
        last_program_end = 0
        while True:

            slot = self.schedule[i]
            #minuta tygodnia, gdy slot się zaczyna i kończy
            slot_min_of_week = self.slot_minute_of_week(slot)

            #czy audycja zaczyna się po timestampie
            if slot_min_of_week > now_min_of_week:
                #wyjdź
                break
            else:
                #nastepny
                i+=1
        
        auds = []

        #dzień tygodnia
        dow = slot["weekday"]
        while True:
            slot = self.schedule[i]

            if num == 0 and slot["weekday"] != dow:
                break

            if num > 0 and len(auds) >= num:
                break

            #dodaj audycję
            auds.append(slot)
            i+=1

            #gdy poza ostatnim rekordem?
            if i >= len(self.schedule):
                #wróć do początku
                i = 0

        return auds


    def get_program_with_split(self,next,wd,h,m,time_margin=5):

        #pobierz audycję przed/po
        aud = self.get_program(not next,next,wd,h,m,time_margin=time_margin)

        #pobierz audycję teraz
        now = self.get_program(False,False,wd,h,m)

        #czy przejście między audycjami?
        if aud["found"] and now["found"]:
            #Czy audycja się zmieniła?
            changed = (aud['slug'] != now['slug'])
        else:
            #przejście z/do playlisty
            changed = (aud["found"] != now["found"])

        #dopisz do listy informację o zmianie audycji
        aud['changed'] = changed

        #zwróć
        return aud

    #zwróć wszystkie sloty
    def list_all_slots(self):
        return self.list_programs(1,0,0,len(self.schedule))

    #zwróć wszystkie audycje
    def list_all_programs(self):
        return self.programs

    #lista slugów
    def list_all_slugs(self):
        slugs = []
        for program in self.programs:
            slugs.append(program["slug"])
        
        return slugs

    #bindy dla czasu teraz
    def get_program_now(self,prev,next,time_margin=5):
        t = time.localtime()
        wd = t.tm_wday+1
        h = t.tm_hour
        m = t.tm_min 

        return self.get_program(prev,next,wd,h,m,time_margin=time_margin)

    def get_program_with_split_now(self,next,time_margin=5):
        t = time.localtime()
        wd = t.tm_wday+1
        h = t.tm_hour
        m = t.tm_min 

        return self.get_program_with_split(next,wd,h,m,time_margin=time_margin)

    def list_programs_now(self,num):
        t = time.localtime()
        wd = t.tm_wday+1
        h = t.tm_hour
        m = t.tm_min 

        return self.list_programs(wd,h,m,num)

    def list_programs_today(self):
        t = time.localtime()
        wd = t.tm_wday+1
        h = t.tm_hour
        m = t.tm_min 

        return self.list_programs(wd,h,m,0)
    