#!/usr/bin/python

from fofum import Fofum

def ev(msg):
  print msg

f = Fofum(user='pl')
f.listen_on_event('test',ev)
