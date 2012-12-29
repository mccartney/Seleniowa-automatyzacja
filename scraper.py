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

class ScraperLekarzy: 
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
       tekst = u"<h2>Wyniki</h2>" +"<ul>"
       
       for dzien in tabelka.keys():
          tekst=tekst + "<li>"+self.uni(dzien) + "<ol>"
          for wynikDnia in tabelka[dzien]:
             tekst=tekst + "<li>"+self.uni(wynikDnia)+"</li>"
          tekst=tekst+"</ol></li>"   
       
       tekst = tekst + ("</ul>" +"<br/>\r-- " +"<br/>\r %s") \
         % datetime.datetime.now().__str__()
       
       
       temat="[MEDICOVER] %s" % (datetime.datetime.now())

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
       

