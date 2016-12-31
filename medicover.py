#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: sw=3 sts=3

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import sys, time, os, datetime, re

from ustawienia import slownik
from ustawienia import konta
import hasla
from scraper import *

class ScraperMedicover(ScraperLekarzy):
  def __init__(self, parametry):
    ScraperLekarzy.__init__(self, adresStartowy="https://mol.medicover.pl",
                                  naglowekWMejlu="MEDICOVER", parametryWejsciowe=parametry)
  def odwiedzIZbierzWyniki(self, sel):
    dzien = 864000000000

    sel.find_element_by_id('oidc-submit').click()
    glowneOkno = sel.window_handles[0]
    sel.switch_to_window(sel.window_handles[1])
    self.czekajAzSiePojawi(sel, (By.ID, 'username-email'))
    sel.find_element_by_id('username-email').send_keys(slownik['login'])
    sel.find_element_by_id('password').send_keys(hasla.haslo('medicover', slownik['login'], slownik.get('haslo')))
    time.sleep(2)
    sel.find_element_by_id('password').send_keys(Keys.RETURN)
    time.sleep(3)
    sel.switch_to_window(glowneOkno)
    
    # ============ po logowaniu
    
    self.czekajAzSiePojawi(sel, (By.ID, "myCarousel"))
    sel.get("https://mol.medicover.pl/MyVisits")
    sel.get("https://mol.medicover.pl/MyVisits?bookingTypeId=2&mex=True&pfm=1")
    self.czekajAzSiePojawi(sel, (By.CSS_SELECTOR, '.search-button'))
    
    time.sleep(2)    
    
    Select(sel.find_element_by_id('RegionId')).select_by_value('204')	# 204 = Warszawa

    self.czekajAzSiePojawi(sel, (By.ID, "SpecializationId"))
    time.sleep(2)

    print "Szukam %s" % self.specjalizacja    
    spec = Select(sel.find_element_by_id('SpecializationId'))
    for option in spec.options:
       if re.findall(self.specjalizacja, option.text):
          spec.select_by_value(option.get_attribute('value'))
          break

    time.sleep(3)
    sel.find_element_by_css_selector('#advancedSearchForm .panel.panel-default .panel-body .search-button button').click()
    self.czekajAzSiePojawi(sel, (By.CSS_SELECTOR, '.results'))

    time.sleep(3)

    for i in range(5):
      self.czekajAzSiePojawi(sel, (By.CSS_SELECTOR,'.btn.default.col-lg-4'))
      try:
       sel.find_element_by_css_selector('.btn.default.col-lg-4').click()
      except Exception as e:
       print "Failed to click next: %s" % e
      time.sleep(3)


    terminy = sel.find_elements_by_css_selector('.freeSlots-container')
    
    wyniki=[]
    
    for termin in terminy:
      dane = [element.text for element in termin.find_elements_by_css_selector('h5,p,span')]
      dane[0] = datetime.datetime.strptime(dane[0], "%d/%m/%Y")

      if (not self.przed) or (dane[0] < self.przed):
        wyniki.append(dane)
    return wyniki


if __name__ == "__main__":
  ScraperMedicover(sys.argv).scrapuj()
  

