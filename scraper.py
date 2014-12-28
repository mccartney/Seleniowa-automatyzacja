#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: sw=3 sts=3

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time, os, datetime, hashlib
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

class ScraperLekarzy: 
    def __init__(self, adresStartowy, naglowekWMejlu, parametryWejsciowe):
      self.adresStartowy = adresStartowy
      self.naglowekWMejlu = naglowekWMejlu
      
      parametryWejsciowe = parametryWejsciowe[1:4]+['','','','','','']
      self.specjalizacja = parametryWejsciowe[0]
      self.przed=None
      if parametryWejsciowe[1]:
       self.przed = datetime.datetime.strptime(parametryWejsciowe[1], "%Y-%m-%d")

      #TODO to jest przecież specyficzne dla Medicoveru, przenieść do medicover.py
      if parametryWejsciowe[2]:
         login = parametryWejsciowe[2]
         slownik_konta = konta.get(login, {})
         slownik_konta.setdefault('login', login)
         slownik.update(slownik_konta)

      print "Szukamy dla loginu %s:" % (slownik['login'],)
      print "- specjalizacji "+self.specjalizacja
      print "- przed "+str(self.przed)


    def scrapuj(self):
      try:
       selenium = self.wystartujSelenium()
       wynik = self.odwiedzIZbierzWyniki(selenium)
       self.sprawdzCzyWynikNowyIEwentualnieZakomunikuj(wynik)
      finally:
         try: 
            selenium.close()
            time.sleep(2)
         except:
            traceback.print_exc()

    def wystartujSelenium(self):
     selenium_conf = slownik['selenium']

     driver = webdriver.Remote(
        command_executor='http://%s:%s/wd/hub' % (selenium_conf["host"], selenium_conf["port"]),    
         desired_capabilities=DesiredCapabilities.FIREFOX)
     driver.get(self.adresStartowy)
     return driver
     
    def czekajAzSiePojawi(self, driver, co):
     return WebDriverWait(driver, timeout=30).until(EC.presence_of_element_located(co))

    # TODO te dwie metody trzeba by obiektowo zrobic, wydzielic klase - Zapisywacz albo Pamiec
    def sprawdzCzyJuzSpotkalismy(self, co):
        md5 = hashlib.md5()
        md5.update(co)
        skrot = 'pamiec/%s' % (md5.hexdigest())
        print "Skrót wyszedł: "+ skrot
        ret = os.path.exists(skrot) 
        plik = open(skrot, 'w')
        plik.write(co)
        plik.close()
        return ret

    def sprawdzCzyWynikNowyIEwentualnieZakomunikuj(self, wynik):
        if not wynik:
           print "Brak wynikow"
           return

        wynikSformatowany=pprint.pformat(wynik)

        print "Wynik: "+wynikSformatowany
        
        if self.sprawdzCzyJuzSpotkalismy(wynikSformatowany):
          print "NIC NOWEGO"
        else: 
          print "Cos nowego: ", wynik
          self.mejl(wynik, slownik["email"])

    def pozbadzSiePolskichLiter(self, text):
       dic = {u'ą':'a', u'ć':'c', u'ę':'e', u'ł':'l', u'ń':'n', u'ó':'o', u'ś':'s', u'ź':'z', u'ż':'z', 
              u'Ą':'A', u'Ć':'C', u'Ę':'E', u'Ł':'L', u'Ń':'N', u'Ó':'O', u'Ś':'S', u'Ź':'Z', u'Ż':'Z', 
             } 
       for org, nowa in dic.iteritems():
           text = text.replace(org, nowa)
       return text

    def uni(self, str_or_unicode):
       if isinstance(str_or_unicode, unicode):
          return str_or_unicode
       else:
          return str_or_unicode.decode('utf-8')

    def mejl(self, tabelka, ustawieniaMejla):
       od, do, smtp = tuple([ustawieniaMejla[x] for x in ["od", "do", "smtp"]])
       tekst = u"<h2>Wyniki</h2><ul>"
       
       poprzedniDzien=""
       for wiersz in tabelka:
          if wiersz[0] != poprzedniDzien:
             tekst= tekst + "</ul><h4>%s<h4><ul>" % wiersz[0].strftime("%A, %Y-%m-%d")
          reprezentacja = "%s" % (", ".join(wiersz[1:]))   
          style=""
          if !self.sprawdzCzyJuzSpotkalismy(reprezentacja):
            style=" style='color: green'"
          tekst=tekst + "<li%s>%s</li>" % (style, reprezentacja)
       
       tekst=tekst+"</ul><br/><br/>"
       
       tekst = tekst + ("<br/>\r-- " +"<br/>\r %s")   % datetime.datetime.now().__str__()
       
       
       temat="[%s] %s" % (self.naglowekWMejlu, datetime.datetime.now())

       charset=Charset('utf-8')
       tresc=MIMEText(tekst.encode('utf-8'), 'html')
       tresc.set_charset(charset)
       tresc['From'] = od
       tresc['To'] = ", ".join(do)
       tresc['Subject'] = temat

       if ustawieniaMejla.get('smtp_tls'):
          smtp_pass = hasla.haslo(smtp, od, ustawieniaMejla.get('smtp_password'))
          serwer=smtplib.SMTP(smtp, 587)
          serwer.starttls()
          serwer.login(od, smtp_pass)
       else:
          serwer=smtplib.SMTP(smtp)
       serwer.sendmail(od,do,tresc.as_string())
       serwer.quit()

    def wybierz(self, selenium, id, wartosc):
       selenium.select(id, wartosc)
       selenium.fire_event(id, 'change')
       time.sleep(2)
       

