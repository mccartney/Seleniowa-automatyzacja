#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: sw=3 sts=3

from selenium import selenium
import sys, time, os, datetime

from ustawienia import slownik
from ustawienia import konta
import hasla
from scraper import *

class ScraperMedicover(ScraperLekarzy):
  def __init__(self, parametry):
    ScraperLekarzy.__init__(self, adresStartowy="https://online.medicover.pl/WAB3/",
                                  naglowekWMejlu="MEDICOVER", parametryWejsciowe=parametry)
  def odwiedzIZbierzWyniki(self, sel):
    dzien = 864000000000
    komponentZData = "//input[@name='dtpStartDateTicks']"

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
    
    if self.specjalizacja:
     self.wybierz(sel, 'id=cboSpecialty', self.specjalizacja) 
    if sel.is_element_present('id=chkFollowUpVisit'):	# pojawia się po wyborze "Pediatra"
     sel.click('id=chkFollowUpVisit')
     time.sleep(2)
    if self.doktor:
     self.wybierz(sel, 'id=cboDoctor', self.doktor) 
    if self.centrum:
     self.wybierz(sel, 'id=cboClinic', self.centrum)

    wynik={}
    
    dzis = datetime.datetime.now()
    poczatkowaWartoscPoczatku = int(sel.get_value(komponentZData))
    max_dni = (self.przed-dzis).days + 1

    sel.click('id=btnSearch')
    sel.wait_for_page_to_load(10000)
    time.sleep(3)
    while sel.is_element_present('id=lblLoading'):
        time.sleep(3)

    while sel.is_element_present('id=dgGrid'):  
       dataNapis = sel.get_table('dgGrid.0.0').strip().split(" ")[1].__str__()
       data = datetime.datetime.strptime(dataNapis, "%d/%m/%Y")
       
       zaIleDni = (data-dzis).days
       if data > self.przed:
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
    return wynik


if __name__ == "__main__":
  ScraperMedicover(sys.argv).scrapuj()
  

