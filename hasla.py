#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: sw=3 sts=3

import sys, time, os, datetime, hashlib
import smtplib
import pprint
import getpass
import traceback
import keyring

from ustawienia import slownik
from ustawienia import konta

def pobierz_haslo(service, username):
   if keyring:
      password = keyring.get_password(service, username)
      if password:
         return password

   password = getpass.getpass(prompt='podaj haslo dla %s@%s' % (username,
      service))
   if password and keyring:
      keyring.set_password(service, username, password)
   return password

def haslo(service, username, password):
   if password:
      return password
   return pobierz_haslo(service=service, username=username)
