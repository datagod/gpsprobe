#!/usr/bin/python

#------------------------------------------------------------------------------
#   ____ ____  ____  ____  ____   ___  ____  _____                           --
#  / ___|  _ \/ ___||  _ \|  _ \ / _ \| __ )| ____|                          --
# | |  _| |_) \___ \| |_) | |_) | | | |  _ \|  _|                            --
# | |_| |  __/ ___) |  __/|  _ <| |_| | |_) | |___                           --
#  \____|_|   |____/|_|   |_| \_\\___/|____/|_____|                          --
#                                                                            --
#                                                                            --
#  A passive surveillance tool that tracks wifi enabled devices nearby,      --
#  GPSProbe records the MAC addresses, GPS co-ordinates and other pertinent  --
#  information.  This tool pairs nicely with security cameras to provide     --
#  evidence of who or what was visiting your property uninvited.             --
#                                                                            --
#  Features:                                                                 --
#  - record MAC address, time of day, signal strength, vendor, etc.          -- 
#  - can assign a friendly name to previously recognized MAC addresses       -- 
#  - optional tracking of GPS co-ordinates                                   --
#  - tracks routers as well as mobile devices                                --
#                                                                            --
#  Optional Unicoirn hat HD display                                          --
#  - leverages code from Arcade Retro Clock to display device counts,        --
#    signal counts, and packet counts                                        --
#                                                                            --
#                                                                            --
#  Special Thanks:                                                           --
#  - This project started off as a fork of probemon.  I added the ability    --
#    to capture GPS co-ordinates to the capture file.                        --
#    https://github.com/nikharris0/probemon                                  --
#                                                                            --
#  - Arcade Retro Clock HD has not been released as of July 2019 but I have  --
#    included some functions and objects required to display scrolling       --
#    alphanumerics and strength bars.                                        --
#    https://github.com/datagod/Arcade-Retro-Clock                           --                                           --
#                                                                            --
#  - GPS polling code and thread spawning code was borrowed from another     --
#    project that I have since lost track.  I will certainly give them       --
#    full credit when I track them down                                     --
#                                                                            --
#                                                                            --
#------------------------------------------------------------------------------


# To Do:
#
# Injest raw text files into DB
# Produce spreadsheets from DB to import into google maps
# Produce device name list from database, after marking records
# Send messages to UnicornHat in a thread
# Eliminate flickering when scrolling friendly names




from __future__ import print_function

import datetime
import argparse
import netaddr
import sys
import logging
import string 
from scapy.all import *
from pprint import pprint
from logging.handlers import RotatingFileHandler

from gps import *
from time import *
from datetime import datetime, timedelta
import time
import threading
from threading import Event, Thread

#--------------------------------------
# Variable Declaration               --
#--------------------------------------

NAME = 'GPSProbe'                   
DESCRIPTION = "A passive non visual surveillance tool"
DEBUG = False

ChangeChannelWait = 1
Channel           = 1
UseGPS            = False

OldLat      = ''
OldLon      = ''
OldMAC      = ''
OldLogTime  = datetime.now()
RouterList  = {}
MobileList  = {}
PacketCount = 0

F_bssids   = []    # Found BSSIDs
HatDisplay = False
RouterCount  = 0
MobileCount  = 0
RouterBars   = 0
MobileBars   = 0
NewRouterBar = 0
NewMobileBar = 0
TimeDelay    = 0.2 #Display status bars ever X seconds


parser = argparse.ArgumentParser(description=DESCRIPTION)
parser.add_argument('-i', '--interface', help="capture interface")
parser.add_argument('-t', '--time', default='iso', help="output time format (unix, iso)")
parser.add_argument('-o', '--output', default='probemon.log', help="logging output location")
parser.add_argument('-b', '--max-bytes', default=5000000, help="maximum log size in bytes before rotating")
parser.add_argument('-c', '--max-backups', default=99999, help="maximum number of log files to keep")
parser.add_argument('-d', '--delimiter', default='\t', help="output field delimiter")
parser.add_argument('-f', '--mac-info', action='store_true', help="include MAC address manufacturer")
parser.add_argument('-s', '--ssid',  action='store_true', help="include probe SSID in output")
parser.add_argument('-r', '--rssi',  action='store_true', help="include rssi in output")
parser.add_argument('-D', '--debug', action='store_true', help="enable debug output")
parser.add_argument('-l', '--log',   action='store_true', help="enable scrolling live view of the logfile")
parser.add_argument('-g', '--gps',   action='store_true', help="Enable GPS functions")
parser.add_argument('-u', '--unicornhat', action='store_true', help="use unicorn hat display")
args = parser.parse_args()



if not args.interface:
  print ("error: capture interface not given, try --help")
  sys.exit(-1)

if(args.gps):
  UseGPS = True

if (args.unicornhat):
  import arcadeclock
  HatDisplay = True

DEBUG = args.debug


  
#--------------------------------------
# Functions / Classes                --
#--------------------------------------



class RepeatedTimer:

    """Repeat `function` every `interval` seconds."""

    def __init__(self, interval, function, *args, **kwargs):
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.start = time.time()
        self.event = Event()
        self.thread = Thread(target=self._target)
        self.thread.start()

    def _target(self):
        while not self.event.wait(self._time):
            self.function(*self.args, **self.kwargs)

    @property
    def _time(self):
        return self.interval - ((time.time() - self.start) % self.interval)

    def stop(self):
        self.event.set()
        self.thread.join()




class GpsPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global gpsd #bring it in scope
    gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
    self.current_value = None
    self.running = True #setting the thread running to true

  def run(self):
    global gpsd
    while gpsp.running:
      gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer




def GetFriendlyName(MAC):
  global FriendlyNameList
  
  #for keys,values in FriendlyNameList.items():
  #  print(keys,values)

    
  FriendlyName = ''
  mac = string.upper(MAC)
  FriendlyName = FriendlyNameList.get(MAC,'--')
  
  return FriendlyName;  


def ShowDeviceCount():
  global RouterList
  global MobileList
  
  
  UniqueRouters = len(RouterList)
  UniqueMobile  = len(MobileList)
  RouterDisplay = arcadeclock.CreateBannerSprite(str(UniqueRouters))
  RouterDisplay.r = 200
  RouterDisplay.g = 0
  RouterDisplay.b = 0
  MobileDisplay = arcadeclock.CreateBannerSprite(str(UniqueMobile))
  MobileDisplay.r = 0
  MobileDisplay.g = 0
  MobileDisplay.b = 255
  
  RouterDisplay.DisplayIncludeBlack(-1,0)
  MobileDisplay.DisplayIncludeBlack(-1,6)



def CalculateIntensity(i):
  #this function is used to set the brightness of a pixel based on an input digit
  intensity = 0
  
  if (i == 0):
    intensity = 50
  if (i == 1):
    intensity = 75
  if (i == 2):
    intensity = 100
  if (i == 3):
    intensity = 125
  if (i == 4):
    intensity = 150
  if (i == 5):
    intensity = 175
  if (i == 6):
    intensity = 200
  if (i == 7):
    intensity = 220
  if (i == 8):
    intensity = 240
  if (i == 9):
    intensity = 255
  
  #print ("i",i,"intensity",intensity)
  return intensity;




def DisplayStatusBars():
  global StatusBarRouter
  global StatusBarMobile
  
  global RouterBars
  global MobileBars
  global NewRouterBar
  global NewMobileBar
  global PacketCount
  
  
  #adjust length of bars if new bars detected
  #then flip switch to allow for slow decay of bar strength
  if (NewRouterBar == True):
    StatusBarRouter.BarLength = RouterBars
    NewRouterBar = False
  else:
    StatusBarRouter.BarLength = StatusBarRouter.BarLength -1
    
  
  if (NewMobileBar == True):
    if (MobileBars > StatusBarMobile.BarLength):
      StatusBarMobile.BarLength = MobileBars
    NewMobileBar = False
  else:
    if (RouterBars > StatusBarRouter.BarLength):
      StatusBarMobile.BarLength = StatusBarMobile.BarLength -1
  
  #stop decrementing at 0
  if (StatusBarRouter.BarLength < 0):
    StatusBarRouter.BarLength = 0
  if (StatusBarMobile.BarLength < 0):
    StatusBarMobile.BarLength = 0
  
  
  #update router sprite
  for h in range (0,arcadeclock.HatWidth):
    if (h <= StatusBarRouter.BarLength):
      StatusBarRouter.grid[h] = 1
    else:
      StatusBarRouter.grid[h] = 0

  #update mobile sprite
  for h in range (0,arcadeclock.HatWidth):
    if (h <= StatusBarMobile.BarLength):
      StatusBarMobile.grid[h] = 1
    else:
      StatusBarMobile.grid[h] = 0


  #Draw packet count line
  count =   str(PacketCount)[::-1]
  y = 13
  r = 0
  g = 0
  b = 0
  for x in range (0,len(count)):
    intensity = CalculateIntensity(int(count[x]))
    g = intensity
    arcadeclock.setpixel(x,y,r,g,b)

  #print ("Packet:",count, PacketCount)
  arcadeclock.unicorn.show()

  
  
  StatusBarRouter.DisplayIncludeBlack(0,14)
  StatusBarMobile.DisplayIncludeBlack(0,15)




def EraseStatusArea():
  for h in range (0,16):
    time.sleep(0.10)
    arcadeclock.setpixel(15-h,13,0,0,0)
    arcadeclock.setpixel(15-h,14,0,0,0)
    arcadeclock.setpixel(15-h,15,0,0,0)
  arcadeclock.unicorn.show()




  




def ShowSignalStrength(rssi_val,DeviceType):
  count = 0
  
  if (DeviceType == 'router'):
    v = 14
    r = 200
    g = 0
    b = 0
  else:
    v = 15
    r = 0
    g = 0
    b = 200
  
    
  #try to convert to a number that makes sense to a human (-db is weird to me, sorry folks)
  SmartStrength = 100 - (int(rssi_val) * -1)
  if (SmartStrength < 0):
      SmartStrength = 0
  if (SmartStrength > 100):
    SmartStrength = 100

  MinLineLen = 0
  MaxLineLen = 16

  Chunk = 100 / MaxLineLen
  LineLen = int(SmartStrength / Chunk)
  

  #print (DeviceType, 'rssi',rssi_val, 'SmartStrength',SmartStrength, 'Chunk',Chunk, 'LineLen',LineLen,'rgb',r,g,b)

  #erase the part of the screen with no line
  for h in range (0,15-LineLen):
    arcadeclock.setpixel(15-h,v,0,0,0)
  
  #Draw the line
  for h in range (0,LineLen):
    arcadeclock.setpixel(h,v,r,g,b)

  arcadeclock.unicorn.show()




def UpdateSignalStrength(rssi_val,DeviceType):
  global RouterBars     #counts dots to display for router
  global MobileBars     #counts dots to display for router
  global NewRouterBar   #indicates a new router bar strength has been detected
  global NewMobileBar   #indicates a new router bar strength has been detected
  
  count = 0
    
  #try to convert to a number that makes sense to a human (-db is weird to me, sorry folks)
  SmartStrength = 100 - (int(rssi_val) * -1)
  if (SmartStrength < 0):
      SmartStrength = 0
  if (SmartStrength > 100):
    SmartStrength = 100

  MinLineLen = 0
  MaxLineLen = 16

  Chunk = 100 / MaxLineLen
  LineLen = int(SmartStrength / Chunk)
  
  if(DeviceType == 'router'):
    NewRouterBar = True
    RouterBars   = LineLen
  else:
    NewMobileBar = True
    MobileBars   = LineLen
    
  
  
  







#This function seems to be configured to run by a logger, or a service
#and will run in a separate process
 
def build_packet_callback(time_fmt, logger, delimiter, mac_info, ssid, rssi):


  def StoreMAC(MAC,DeviceType,log_time):
    global RouterList
    global MobileList
    #We keep a list of routers and mobile devices so we can 
    #have a unique count for the past X minutes
    if(DeviceType == 'router'):
      if (MAC not in RouterList):
        RouterList[MAC]=log_time
      
    elif(DeviceType == 'mobile'):
      if (MAC not in MobileList):
        MobileList[MAC]=log_time



  
  def packet_callback(packet):
    #bring in GPS object
    global gpsd
    global OldLat
    global OldLon
    global Channel
    global UseGPS
    global HatDisplay
    global RouterCount
    global MobileCount
    global OldMAC
    global OldLogTime
    global RouterList
    global MobileList
    global PacketCount

    SSID       = ''
    PacketType = ''
    DeviceType = ''
    vendor     = ''
    LastSSID   = ''
    MAC        = ''
    lat        = ''
    lon        = ''
    dst        = ''
    MACDest    = ''
    UniqueRouters = 0
    UniqueMobile  = 0
    
    
    
    #get Lat/lon from gps
    if(UseGPS == True):
      lat = str(gpsd.fix.latitude)
      lon = str(gpsd.fix.longitude)

    # determine preferred time format 
    log_time = str(datetime.now())[0:19]


    # list of output fields
    fields = []

    #Diagnositics
    #print (packet.haslayer)
    #print ("examining")
    #print (packet.show)  


    #Add to packet counter
    PacketCount = PacketCount +1

    #we want to record packet type no matter what
    PacketType = str(packet.type) + '-' + str(packet.subtype)
   
    # check for packets that show SSID of existing networks
    if packet.haslayer(Dot11Beacon):
      SSID = packet.getlayer(Dot11Elt).info
      DeviceType = 'router'
      RouterCount = RouterCount + 1
      
      #print (packet.show)  
      
      if (SSID == '' or packet.getlayer(Dot11Elt).ID != 0):
        SSID = 'HIDDEN'


    
    #Look for management frames with probe subtype
    elif (packet.haslayer(Dot11FCS) or packet.haslayer(Dot11)):

      #probe response as address1 MAC of 'FF-FF-FF-FF-FF-FF-FF-FF'
      #which means the router is sending out a probe response
      
      MACDest = string.upper(str(netaddr.EUI(packet.addr1)))
      if ( MACDest == 'FF-FF-FF-FF-FF-FF-FF-FF') :
        if (HatDisplay):
          arcadeclock.ShowScrollingBanner("ROUTER",200,0,0,.01)
        DeviceType = 'router'


      #exit if not a probe request
      if (packet.type != 0 or packet.subtype != 0x04):
        return

      DeviceType = 'mobile'
      MobileCount = MobileCount + 1
      
      # include the SSID in the probe frame
      SSID = packet.info
      


    #Signal strength
    rssi_val = str(packet.dBm_AntSignal)



   
    # parse mac address and look up the organization from the vendor octets
    try:
      MAC = netaddr.EUI(packet.addr2)
      vendor = MAC.oui.registration().org
    except netaddr.core.NotRegisteredError, e:
      vendor = '?'
        
 
    #Get friendly name for recognized devices
    FriendlyName = GetFriendlyName(str(MAC))
    

    #Assemble fields for output to logfile  
    fields.append(log_time)
    fields.append(lat)
    fields.append(lon)
    fields.append(rssi_val)
    fields.append(str(Channel))
    fields.append(PacketType)
    fields.append(DeviceType)
    fields.append(str(MAC))
    fields.append(FriendlyName)
    fields.append(vendor)
    fields.append(SSID)
    
    

    
    #add all collected fields together, delimited by tab
    #only log if lat long has moved
    #log everything if no GPS in use
    if (((lat <> OldLat or lon <> OldLon) and (DeviceType == 'router')) 
      or (DeviceType == 'mobile') 
      or (UseGPS == False)):
      try:
        
        
        #one log per second is sufficient
        if (OldMAC <> MAC and OldLogTime <> log_time):
          logger.info(delimiter.join(fields))
          OldMAC = MAC
          OldLogTime = log_time
          
          #show friendly name on unicorn hat display
          if (FriendlyName <> '' and FriendlyName <> '--' and DeviceType <> 'router'):
            if(HatDisplay):
              arcadeclock.ShowScrollingBanner(FriendlyName,125,0,125,.02)

      except:
        print ("Unicode error while joining fields")
      OldLat = lat
      OldLon = lon

    StoreMAC(MAC,DeviceType,log_time)

    

    #Display router and mobile counts on unicorn hat
    if (HatDisplay):
      ShowDeviceCount()
      #ShowSignalStrength(rssi_val,DeviceType)
      UpdateSignalStrength(rssi_val,DeviceType)

    
    
  return packet_callback;


#--------------------------------------
# Functions for non prope packets    --
#--------------------------------------


#This function changes the Channel to be monitored
def ChangeChannel(iface):
    global Channel
    Channel = 1
    n = 1
    stop_ChangeChannel = False
    while not stop_ChangeChannel:
        time.sleep(ChangeChannelWait)
        #print ("Changing to Channel: ",Channel)
        os.system('iwconfig %s Channel %d' % (iface, Channel))
        n = random.randint(1,14)
        if(n != Channel):
            Channel = n



def findSSID(pkt):
    if pkt.haslayer(Dot11Beacon):
       if pkt.getlayer(Dot11).addr2 not in F_bssids:
           F_bssids.append(pkt.getlayer(Dot11).addr2)
           ssid = pkt.getlayer(Dot11Elt).info
           if ssid == '' or pkt.getlayer(Dot11Elt).ID != 0:
               print ("Hidden Network Detected")
           print ("Network Detected: %s" % (ssid))
           return ssid





#--------------------------------------
# Create sprites                     --
#--------------------------------------

StatusBarRouter = arcadeclock.Sprite(
  16,
  1,
  100,
  0,
  0,
  [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
)

StatusBarRouter.BarLength = 0


StatusBarMobile = arcadeclock.Sprite(
  16,
  1,
  0,
  0,
  200,
  [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
)
StatusBarMobile.BarLength = 0





#--------------------------------------
# MAIN PROCESSING                    --
#--------------------------------------

#gpsd = None #seting the global variable

os.system('clear') #clear the terminal (optional)
os.system("figlet 'GPS PROBE'")

time.sleep(1)




#Create friendly name list
FriendlyNameList = {
  'AA-BB-CC-DD-EE-FF' : 'MyPhone',
  'AA:DD:CC:DD:FF:FF' : 'BigTV'
}


    



#--------------------
# Start GPS thread --
#--------------------
if(UseGPS == True):
  gpsd = None 
  gpsp = GpsPoller() 
  gpsp.start() 



#-------------------------------
#If unicorn hat is to be used --
#-------------------------------
if(HatDisplay):
  arcadeclock.unicorn.off()
  arcadeclock.ShowScrollingBanner("GPS Probe",0,0,200,.02)
    
  StatusAreaTimer = RepeatedTimer(TimeDelay,DisplayStatusBars)
  #timer2 = RepeatedTimer(1,ShowPacketCount)




#Launch Probe Logger
logger = logging.getLogger(NAME)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(args.output, maxBytes=args.max_bytes, backupCount=args.max_backups)
logger.addHandler(handler)

#If logging specified, open handler and write column headings
if args.log:
  logger.addHandler(logging.StreamHandler(sys.stdout))
  logger.info('DateTime           \tLat\tLon\tSignal\tChannel\tPktType\tDevice\tMACAddress         \tFriendlyName\tVendor\tSSID')
  
  
  
built_packet_cb = build_packet_callback(
  args.time,
  logger,
  args.delimiter,
  args.mac_info,
  args.ssid,
  args.rssi
)

#launch thread to switch Channels
thread = threading.Thread(target=ChangeChannel, args=(args.interface, ), name="ChangeChannel")
thread.daemon = True
thread.start()

#capture packets
sniff(iface=args.interface, prn=built_packet_cb, store=0, monitor=True)




#Stop threads  
print ("\nKilling threads...")
if(UseGPS == True):
  gpsp.running = False

thread.stop_ChangeChannel = False
StatusAreaTimer.stop()
#timer2.stop()

#gpsp.join() # wait for the thread to finish what it's doing
os.system("figlet 'BYE LOSER'")
print ("Done.\nExiting.")


