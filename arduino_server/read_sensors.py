#!/usr/bin/python
from re import compile, sub
from time import sleep, time
from serial import Serial
from optparse import OptionParser
from datetime import datetime
from sys import stdout, path
import os

criticalTemp=42.0            #in degrees Celsius
notificationInterval=300    #in seconds
lockFile="/root/.CriticalTemp"
snmpDir="/root/SNMP"
snmpRelays=[ 'mastercr1.inv.usc.es', 'nodo041.inv.usc.es',
             'nodo068.inv.usc.es', 'nodo086.inv.usc.es',
             'nodo110.inv.usc.es', 'nodo156.inv.usc.es' ]


path.insert(1,snmpDir)
from Send_Trap import SendTrap

ser=Serial(port='/dev/ttyACM0',baudrate=115200,timeout=1.5)

extraWrite=False

temp_regex=compile(r'Temperature=\s*([0-9.-]*)\r*\n*')
pressure_regex=compile(r'Pressure:\s*([0-9.-]*)\s*hPa\n*')
humidity_regex=compile(r'Humidity:\s*([0-9.-]*)\s*\%,\s*Dew Point:\s*'+ \
                       r'([0-9.-]*)\s*C,\s*Temperature:')
temperatureLine_regex=compile(r'Temperature Rack (\d):\s*'+\
                              r'\s*(([0-9.-]+,\s*){5}[0-9.-]+)')

usage='read_data.py [-TPHcsh]'
parser=OptionParser(usage)
parser.set_defaults(printall=False,getfile=False,nodeclass='all')
parser.add_option("-T", "--temperature", action='store_true',
                  default=False, dest='temperature')
parser.add_option("-P", "--pressure", action='store_true', default=False,
                  dest='pressure')
parser.add_option("-H", "--humidity", action='store_true', default=False,
                  dest='humidity')
parser.add_option("-A", "--all-types", action='store_true', default=False,
                  dest='all')
parser.add_option("-c", "--cable", action='store', default='1', dest="cable")
parser.add_option("-s", "--sensor", action='store', default='1', dest="sensor")
parser.add_option("-a", "--all-sensors", action='store_true', default=False,
                  dest="allsensor")
(options,args)=parser.parse_args()

ser.readline()

if options.cable=='1':
  file=open('/root/dataTemp3.dat','a')
  extraWrite=True

if options.temperature:
  if options.allsensor:
    string=''
    join=''
    for i in range(1,7):
      ser.write('T%s%s' % (options.cable,i))
      line=None
      while not line:
        line=ser.readline()
      string+=join+'Sensor %i: %s' % (i, temperature_regex.sub(r'\1',line[0:-1]))
      join='|'
      if extraWrite and i==3:
        file.write('%s\t%s\n' % (datetime.today().strftime("%s"),
                                 temperature_regex.sub(r'\1',line[0:-1])))
    print string
  else:
    ser.write('T'+options.cable+options.sensor)
    line=None
    while not line:
      line=ser.readline()
      print temp_regex.sub(r'\1',line[0:-1])
      if extraWrite:
        file.write('%s\t%s\n' % (datetime.today().strftime("%s"),
                                 temp_regex.sub(r'\1',line[0:-1])))
elif options.humidity:
  ser.write('Hh')
  line=None
  while not line:
    line=ser.readline()
  print line
elif options.all:
  from copy import copy
  string=''
  ser.write('A')
  tempArray=[]
  line=''
  while line[0:3].lower()!="end":
    line=''
    while not line:
      line=ser.readline()
    if temperatureLine_regex.search(line):
      temperatureData=temperatureLine_regex.search(line)
      [tempArray.append(float(x)) for x in
       temperatureData.group(2).split(', ')[0:3]]
      if extraWrite and temperatureData.group(1)=='1':
        file.write('%s\t%s\n' % (datetime.today().strftime("%s"),
                                 tempArray[-1]))
      if sum(tempArray[-3:])==0.0:
        tempArray=tempArray[:-3]
      else:
        print line[:-2]
    elif pressure_regex.search(line) or humidity_regex.search(line):
      print line[:-2]
  averageTemp=sum(tempArray)/float(len(tempArray))
  if averageTemp>=criticalTemp:
    sendTrap=False
    if os.path.isfile(lockFile):
      if int(datetime.now().strftime("%s"))-os.stat(lockFile).st_mtime > notificationInterval:
        sendTrap=True
        os.utime(lockFile,None)
    else:
      criticalStatus=open(lockFile,"w")
      sendTrap=True
    if sendTrap:
      trap=SendTrap(snmpDir, averageTemp, ','.join(snmpRelays))
      trap.dispatch()
  else:
    if os.path.isfile(lockFile):
      trap=SendTrap(snmpDir, averageTemp, ','.join(snmpRelays),False)
      trap.dispatch()
      os.remove(lockFile)
else:
  from copy import copy
  string=''
  ser.write('Pp')
  line=None
  while not line:
    line=ser.readline()
  string=copy(line[0:-2])
  sleep(4)
  ser.write('Pt')
  line=None
  while not line:
    line=ser.readline()
  print string+sub(r'BMP085', r',', line)
if extraWrite:
  file.close()

#ser.close()
#print a.subs('',line)
#sleep(1000)
