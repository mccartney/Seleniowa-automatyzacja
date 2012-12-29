#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: sw=3 sts=3

from selenium import selenium
import sys, time, os, datetime, hashlib
import smtplib
import pprint
import getpass
import traceback
import keyring

from email.MIMEText import MIMEText
from email.Charset import Charset

from ustawienia import slownik
from ustawienia import konta
import hasla
from scraper import *

class ScraperMedicover(ScraperLekarzy):
  def __init__(self):
    dzien = 864000000000
    komponentZData = "//input[@name='dtpStartDateTicks']"

    adres="https://online.medicover.pl/WAB3/"

    selenium_conf = slownik['selenium']
    sel = selenium(selenium_conf["host"], selenium_conf["port"],
          selenium_conf.get('browser', '*firefox /usr/bin/firefox'), adres)
    try:
      sel.start()
      sel.open(adres)

      sel.wait_for_page_to_load(10000)  

      sel.type('id=txUserName', slownik["login"])
      sel.type('id=txPassword', hasla.haslo('medicover', slownik['login'], slownik.get('haslo')))
      sel.click('id=btnLogin')
      sel.wait_for_page_to_load(20000)

      sel.click('id=btnNext')
      sel.wait_for_page_to_load(10000)

      sel.click('id=btnBookAppointment')
      sel.wait_for_page_to_load(10000)

      sel.select('id=cboRegion', 'Warszawa')
      time.sleep(2)
      
      if specjalizacja:
       self.wybierz(sel, 'id=cboSpecialty', specjalizacja) 
      if sel.is_element_present('id=chkFollowUpVisit'):	# pojawia się po wyborze "Pediatra"
       sel.click('id=chkFollowUpVisit')
       time.sleep(2)
      if doktor:
       self.wybierz(sel, 'id=cboDoctor', doktor) 
      if centrum:
       self.wybierz(sel, 'id=cboClinic', centrum)

      wynik={}
      
      dzis = datetime.datetime.now()
      poczatkowaWartoscPoczatku = int(sel.get_value(komponentZData))
      max_dni = (przed-dzis).days + 1

      sel.click('id=btnSearch')
      sel.wait_for_page_to_load(10000)
      time.sleep(3)
      while sel.is_element_present('id=lblLoading'):
          time.sleep(3)

      while sel.is_element_present('id=dgGrid'):  
         dataNapis = sel.get_table('dgGrid.0.0').strip().split(" ")[1].__str__()
         data = datetime.datetime.strptime(dataNapis, "%d/%m/%Y")
         
         zaIleDni = (data-dzis).days
         if data > przed:
           print "Wybieglismy juz %d dni w przyszlosc, konczymy" % zaIleDni
           break
           
         wynikiTegoDnia=[]  
         wynik[data.strftime("%Y-%m-%d (%A)")] = wynikiTegoDnia  

         ileWierszy = int(sel.get_xpath_count("//*[@id='dgGrid']/*/*"))
         for wiersz in range(ileWierszy):
            komorki = [self.pozbadzSiePolskichLiter(sel.get_table('dgGrid.%d.%d' % (wiersz,kolumna))) for kolumna in [1,2,3]]
            print data, komorki
            wynikiTegoDnia.append(" ".join(komorki))
            
         nextDay="xpath=//input[@id='btnNextDay'][not(@disabled)]" 
         if sel.is_element_present(nextDay):
             sel.click(nextDay)
             sel.wait_for_page_to_load(10000)
             time.sleep(1)
         else:
             break          

      wynikSformatowany=pprint.pformat(sorted(wynik))

      md5 = hashlib.md5()
      md5.update(wynikSformatowany)
      skrot = 'pamiec/%s' % (md5.hexdigest())
      if not wynik or os.path.exists(skrot):
        print "NIC NOWEGO"
      else:
        print "Cos nowego: ", wynik
        self.mejl(wynik, slownik["email"])
        plik = open(skrot, 'w')
        plik.write(wynikSformatowany)
        plik.close()

    finally:
       try:
          sel.close()
          time.sleep(2)
          sel.stop()
          time.sleep(2)
       except:
          traceback.print_exc()

if __name__ == "__main__":
  parametry = sys.argv[1:4]
  dopisaneRegExp = [{True: "", False: "regexp:"+i}[i==""] for i in parametry]
  specjalizacja, doktor, centrum = tuple([dopisaneRegExp[i] for i in [0,1,2]])

  przed = datetime.datetime.strptime(sys.argv[4], "%Y-%m-%d")

  if len(sys.argv) > 5:
     login = sys.argv[5]
     slownik_konta = konta.get(login, {})
     slownik_konta.setdefault('login', login)
     slownik.update(slownik_konta)

  print "Szukamy dla loginu %s:" % (slownik['login'],)
  print "- specjalizacji "+specjalizacja
  print "- doktora       "+doktor
  print "- centrum       "+centrum
  print "Wizyta przed "+str(przed)
  ScraperMedicover()
  

