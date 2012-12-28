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

def pozbadzSiePolskichLiter(text):
   dic = {u'ą':'a', u'ć':'c', u'ę':'e', u'ł':'l', u'ń':'n', u'ó':'o', u'ś':'s', u'ź':'z', u'ż':'z', 
          u'Ą':'A', u'Ć':'C', u'Ę':'E', u'Ł':'L', u'Ń':'N', u'Ó':'O', u'Ś':'S', u'Ź':'Z', u'Ż':'Z', 
	 } 
   for org, nowa in dic.iteritems():
       text = text.replace(org, nowa)
   return text

def uni(str_or_unicode):
   if isinstance(str_or_unicode, unicode):
      return str_or_unicode
   else:
      return str_or_unicode.decode('utf-8')

def mejl(tabelka, ustawieniaMejla):
   od, do, smtp = tuple([ustawieniaMejla[x] for x in ["od", "do", "smtp"]])
   tekst = u"<h2>Wyniki</h2>" +"<ul>"
   
   for dzien in tabelka.keys():
      tekst=tekst + "<li>"+uni(dzien) + "<ol>"
      for wynikDnia in tabelka[dzien]:
         tekst=tekst + "<li>"+uni(wynikDnia)+"</li>"
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

def wybierz(selenium, id, wartosc):
   selenium.select(id, wartosc)
   selenium.fire_event(id, 'change')
   time.sleep(2)
   

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
   wybierz(sel, 'id=cboSpecialty', specjalizacja) 
  if sel.is_element_present('id=chkFollowUpVisit'):	# pojawia się po wyborze "Pediatra"
   sel.click('id=chkFollowUpVisit')
   time.sleep(2)
  if doktor:
   wybierz(sel, 'id=cboDoctor', doktor) 
  if centrum:
   wybierz(sel, 'id=cboClinic', centrum)

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
        komorki = [pozbadzSiePolskichLiter(sel.get_table('dgGrid.%d.%d' % (wiersz,kolumna))) for kolumna in [1,2,3]]
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
    mejl(wynik, slownik["email"])
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
