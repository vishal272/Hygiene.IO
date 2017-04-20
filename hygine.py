
import pexpect
import sys
import time
import json
import select
import datetime
import time
import os, json
import ibmiotf.application
import uuid

try:
  options = ibmiotf.application.ParseConfigFile("/home/pi/device.cfg")
  options["deviceId"] = options["id"]
  options["id"] = "aaa" + options["id"]
  client = ibmiotf.application.Client(options)
  client.connect()
except ibmiotf.ConnectionException  as e:
  print e


def sendData(index,array):
  try:
    myData = {'id':index,'data':array}
    client.publishEvent("raspberrypi", options["deviceId"], "input", "json", myData)
    time.sleep(0.2)
    print 33
  except ibmiotf.ConnectionException  as e:
    print e
    
def floatfromhex(h):
   t = float.fromhex(h)
   if t > float.fromhex('7FFF'):
       t = -(float.fromhex('FFFF') - t)
       pass
   return t

class SensorTag:

   def __init__( self, bluetooth_adr):
       self.con = pexpect.spawn('gatttool -b ' + bluetooth_adr + ' --interactive')
       self.con.expect('\[LE\]>', timeout=600)
       print "Preparing to connect. You might need to press the side button..."
       self.con.sendline('connect')
       self.con.expect('Connection successful.*\[LE\]>')
       print " Connected "
       self.cb = {}
       return
       self.con.expect('\[CON\].*>')
       self.cb = {}
       return

   def char_write_cmd( self, handle, value):
       cmd = 'char-write-cmd 0x%02x 0%x' % (handle, value)
       print cmd
       self.con.sendline( cmd )
       return
   
   def char_read_hnd1( self, handle):
       self.con.sendline('char-read-hnd 0x%02x' % handle)
       self.con.expect('descriptor: .*? \r')
       after = self.con.after
       rval = after.split()[1:]
       result = []
       for x in range(0,11):
          a = rval[2*x]
          b = rval[2*x + 1]
	  c = long(float.fromhex(a + b))
	  result.append(c)
       return result
    
   def char_read_hnd( self, handle ):
       self.con.sendline('char-read-hnd 0x%02x' % handle)
       self.con.expect('descriptor: .*? \r')
       after = self.con.after
       rval = after.split()[1:]
       print rval
       return [int(floatfromhex(n)) for n in rval]

   def register_cb( self, handle, fn):
       self.cb[handle]=fn;
       return


def readSensor(addr,index):
   try:
       array = []
       var = 1
       array.insert(0,index)
       tag1 = SensorTag(addr)
       array.insert(1,tag1.char_read_hnd(0x1e))
       tag1.char_write_cmd(0x24,01)# froce write current time
       if index == 1 :
          var =2
       while var == 1 :
          reset = tag1.char_read_hnd(0x21)
          print "no reset"
          if reset == [1]:
            print 2
            var = 2
       TempArray = tag1.char_read_hnd1(0x2b)# read time array
       tag1.char_write_cmd(0x1e,11)#reset
       #print TempArray
       for x in range(0,9):
          sec = TempArray[10]-TempArray[x]
          s = datetime.datetime.now() - datetime.timedelta(seconds=sec)
          string = s.strftime("%d-%m-%Y %H:%M:%S")
          array.insert((x+2),string)
       sendData(index,array)
       print array
   except:
       pass
   
def main():
   bluetooth_adr1 = "B0:B4:48:BD:6F:03"
   bluetooth_adr2 = "B0:B4:48:BC:6A:81"
   while True:
       readSensor(bluetooth_adr1,1)
       time.sleep(5)
       readSensor(bluetooth_adr2,2)
       time.sleep(300)

if __name__ == "__main__":
   main()
