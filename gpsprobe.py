#!/usr/bin/python3

#------------------------------------------------------------------------------
#   ____ ____  ____  ____  ____   ___  ____  _____                           --
#  / ___|  _ \/ ___||  _ \|  _ \ / _ \| __ )| ____|                          --
# | |  _| |_) \___ \| |_) | |_) | | | |  _ \|  _|                            --
# | |_| |  __/ ___) |  __/|  _ <| |_| | |_) | |___                           --
#  \____|_|   |____/|_|   |_| \_\\___/|____/|_____|                          --
#                                                                            --
#------------------------------------------------------------------------------
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
#  Optional Unicorn hat HD display                                           --
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
#    https://github.com/datagod/Arcade-Retro-Clock                           --
#                                                                            --
#  - Portions of ProbeQuest were used to get the MAC organization            --
#    https://github.com/SkypLabs/probequest                                  --
#                                                                            --
#  - GPS polling code and thread spawning code was borrowed from another     --
#    project that I have since lost track.  I will certainly give them       --
#    full credit when I track them down                                      --
#                                                                            --
#------------------------------------------------------------------------------
#  February 3, 2020                                                          --
#   - changed display to show current activity / heartbeat                   --
#   - added ability to dim the HD display                                    --
#   - we now parse time from GPS, if available                               --
#                                                                            --
#------------------------------------------------------------------------------
#  April 3, 2020                                                             --
#   - added more reports                                                     --
#   - added pandas dataframes                                                --
#------------------------------------------------------------------------------
#  April 4, 2020                                                             --
#   - added curses                                                           --
#------------------------------------------------------------------------------
#  April 23, 2020                                                            --
#   - added windows for text display                                         --
#------------------------------------------------------------------------------
#  May 4, 2020                                                               --
#   - migrated to python 3                                                   --
#------------------------------------------------------------------------------
#  May 14, 2020                                                              --
#   - added new record count, total database records, etc.                   --
#   - added ability to scroll through recent non-friendly records            --
#------------------------------------------------------------------------------
#  Oct 19, 2024                                                              --
#   - adapting for dual wifi                                                 --
#------------------------------------------------------------------------------


# To Do:
#
# Produce spreadsheets from DB to import into google maps
# Produce device name list from database, after marking records
# Send messages to UnicornHat in a thread
# don't log friendly routers to the database (change this to a flag later)
# update Netaddr information
# limit logging of routers to ince every X seconds by maintaining a list of recent devices and a timestamp
# go through all variables and remove unnecessary ones -- especially ones marked global


from __future__ import print_function

from datetime import datetime, timedelta 
import argparse
import netaddr
import sys
import logging
import traceback
import string 
from scapy.all import *
from pprint import pprint
from logging.handlers import RotatingFileHandler
from FriendlyNameList import FriendlyNameList

from gps import *
from time import *
from datetime import datetime, timedelta
import time
import threading
from threading import Event, Thread
from configparser import SafeConfigParser

#Database support
import sqlite3
from sqlite3 import Error
import pandas 
 
#For capturing keypresses and drawing text boxes
import curses
from curses import wrapper
from curses.textpad import Textbox, rectangle

#to help with debugging
import inspect




#For sorting dictionary (we sort FriendlyNameList)
from collections import OrderedDict 

#--------------------------------------
# Variable Declaration               --
#--------------------------------------

NAME = 'GPSProbe'                   
DESCRIPTION = "A passive non visual surveillance tool"
DEBUG = False

ChangeChannelWait = 0.2
Channel           = 1
UseGPS            = False
MobileOnly        = False

OldLat      = '0'
OldLon      = '0'
OldMAC      = '0'
OldLogTime  = datetime.today() - timedelta(minutes=1)
OldLogTimeString = str(OldLogTime)[0:19]
RouterList  = {}
MobileList  = {}
PacketCount = 0

F_bssids      = []    # Found BSSIDs
HatDisplay    = False
RouterCount   = 0
MobileCount   = 0
UniqueRouters = 0
UniqueMobile  = 0
RouterBars    = 0
MobileBars    = 0
NewRouterBar  = 0
NewMobileBar  = 0
TimeDelay     = 0.05 #Display status bars ever X seconds
DisplayBars   = True
ScrollSpeed   = 0.001
Filter        = "NoFriendly"   # none, NoFriendlyRouter, NoFriendly
GPSLogRecordCount = 0
PauseOutput   = False

FriendlyCount = 0
RecordCount   = 0


#Config file for storing datetime during power outages
ConfigFileName     = "ProbeConfig.ini"

#Timers
ConfigFileStartTime   = time.time()  #number of seconds since epoch
HeartBeatStartTime    = time.time()  #number of seconds since epoch
SaveConfigSeconds = 100
HeartBeatSeconds = 2


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
parser.add_argument('-m', '--mobileonly', action='store_true', help="mobile only")
args = parser.parse_args()

#Report pagination
StartRow   = 0



#Text windows
global TitleWindow
global StatusWindow
global Window1
global Window2
global Window3
global Window4
global stdscr
global IPAddress
stdscr = curses.initscr()

#hide the cursor
curses.curs_set(0)


if not args.interface:
  print ("error: capture interface not given, try --help")
  sys.exit(-1)

if(args.gps):
  UseGPS = True

if(args.mobileonly):
  MobileOnly = True
else:
  MobileOnly = False

if (args.unicornhat):
  import arcaderetroclock
  HatDisplay = True

DEBUG = args.debug


  
#--------------------------------------
# Functions / Classes                --
#--------------------------------------


class ProbeWindow(object):
  def __init__(self,name, rows,columns,y1,x1,y2,x2,ShowBorder,BorderColor):
    self.name              = name
    self.rows              = rows
    self.columns           = columns
    self.y1                = y1
    self.x1                = x1
    self.y2                = y2
    self.x2                = x2
    self.ShowBorder        = ShowBorder
    self.BorderColor       = BorderColor #pre defined text colors 1-7
    self.TextWindow        = curses.newwin(self.rows,self.columns,self.y1,self.x1)
    self.CurrentRow        = 1
    self.StartColumn       = 1
    self.DisplayRows       = self.rows    #we will modify this later, based on if we show borders or not
    self.DisplayColumns    = self.columns #we will modify this later, based on if we show borders or not
    self.PreviousLineText  = ""
    self.PreviousLineRow   = 0
    self.PreviousLineColor = 2
    self.Title             = ""
    self.TitleColor        = 2

    #If we are showing border, we only print inside the lines
    if (self.ShowBorder  == 'Y'):
      self.CurrentRow     = 1
      self.StartColumn    = 1
      self.DisplayRows    = self.rows -2 #we don't want to print over the border
      self.DisplayColumns = self.columns -2 #we don't want to print over the border
      self.TextWindow.attron(curses.color_pair(BorderColor))
      self.TextWindow.border()
      self.TextWindow.attroff(curses.color_pair(BorderColor))
      self.TextWindow.refresh()

    else:
      self.CurrentRow   = 0
      self.StartColumn  = 0



  def ScrollPrint(self,PrintLine,Color): 
    #for now the string is printed in the window and the current row is incremented
    #when the counter reaches the end of the window, we will wrap around to the top
    #we don't print on the window border

    try:
      
      

      #expand tabs to X spaces, pad the string with space then truncate
      PrintLine = PrintLine.expandtabs(4)
      PrintLine = PrintLine.ljust(self.DisplayColumns -1,' ')
      PrintLine = PrintLine[0:self.DisplayColumns]

      self.TextWindow.attron(curses.color_pair(Color))
      if (self.rows == 1):
        #if you print on the last character of a window you get an error
        PrintLine = PrintLine[0:self.DisplayColumns-1]
        self.TextWindow.addstr(0,0,PrintLine)
      else:

        #unbold current line  (bold seems to stick, so I am changing)
        self.TextWindow.attron(curses.color_pair(self.PreviousLineColor))
        self.TextWindow.addstr(self.PreviousLineRow,self.StartColumn,self.PreviousLineText)
        #print new line in bold        
        self.TextWindow.addstr(self.CurrentRow,self.StartColumn,PrintLine,curses.A_BOLD)
      self.TextWindow.attroff(curses.color_pair(Color))



      self.PreviousLineText  = PrintLine
      self.PreviousLineColor = Color
      self.PreviousLineRow   = self.CurrentRow
      self.CurrentRow        = self.CurrentRow + 1

        
      if (self.CurrentRow > (self.DisplayRows)):
        if (self.ShowBorder == 'Y'):
          self.CurrentRow = 1
        else:
          self.CurrentRow = 0
        
      
      #erase to end of line
      #self.TextWindow.clrtoeol()
      self.TextWindow.refresh()



    except Exception as ErrorMessage:
      TraceMessage = traceback.format_exc()
      AdditionalInfo = "PrintLine: " + PrintLine 
      ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)
      
      


        
  def WindowPrint(self,y,x,PrintLine,Color): 
    #print at a specific coordinate within the window
    try:
     
      #expand tabs to X spaces, pad the string with space then truncate
      PrintLine = PrintLine.expandtabs(4)
      PrintLine = PrintLine.ljust(self.DisplayColumns -1,' ')
      PrintLine = PrintLine[0:self.DisplayColumns]

      self.TextWindow.attron(curses.color_pair(Color))
      self.TextWindow.addstr(y,x,PrintLine)
      self.TextWindow.attroff(curses.color_pair(Color))

      #We will refresh afer a series of calls instead of every update
      #self.TextWindow.refresh()

    except Exception as ErrorMessage:
      TraceMessage = traceback.format_exc()
      AdditionalInfo = "PrintLine: " + PrintLine
      ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)
        
      


  def DisplayTitle(self,Title, Color): 
    #display the window title 
    if(Title == ""):
      Title = self.Title
    try:
      #expand tabs to X spaces, pad the string with space then truncate
      Title = Title[0:self.DisplayColumns-3]

      self.TextWindow.attron(curses.color_pair(Color))
      if (self.rows > 2):
        #print new line in bold        
        self.TextWindow.addstr(0,2,Title)
        self.TextWindow.refresh()

      else:
        print ("ERROR - You cannot display title on a window smaller than 3 rows")

    except Exception as ErrorMessage:
      TraceMessage = traceback.format_exc()
      AdditionalInfo = "Title: " + Title
      ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)


  def Clear(self):
    self.TextWindow.clear()
    self.TextWindow.attron(curses.color_pair(self.BorderColor))
    self.TextWindow.border()
    self.TextWindow.attroff(curses.color_pair(self.BorderColor))
    self.DisplayTitle(self.Title,self.TitleColor)
    self.TextWindow.refresh()
    if (self.ShowBorder  == 'Y'):
      self.CurrentRow    = 1
      self.StartColumn   = 1
    else:
      self.CurrentRow   = 0
      self.StartColumn  = 0

      











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
    global GPSReport
    while gpsp.running:
      GPSReport = gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer

      #Parse GPS Objects (this is a new method I discovered, different from the ones below)   
      #Look for TPV (Time Position Velocity class)
      #if GPSReport['class'] == 'TPV':
             
        #print  (getattr(GPSReport,'lat',0.0),"\t")
        #print  (getattr(GPSReport,'lon',0.0),"\t")
        #print  (getattr(GPSReport,'time',''),"\t")
        #print  (getattr(GPSReport,'alt','nan'),"\t\t")
        #print  (getattr(GPSReport,'epv','nan'),"\t")
        #print  (getattr(GPSReport,'ept','nan'),"\t")
        #print  (getattr(gpsd,'speed','nan'),"\t")
        #print  (getattr(GPSReport,'climb','nan'),"\t")
 
 


def ShowIPAddress():
  global stdscr
  global StatusWindow
  IPAddress = ""
  
  #Debug info
  Name = inspect.currentframe().f_code.co_name

  #with python3 the IPAddress was coming back as b'xxx.xxx.xxx.xxx, so now we decode to UTF-8
  IPAddress = (subprocess.check_output("hostname -I", shell=True)[:-1])[0:15].decode('UTF-8')
  Window2.ScrollPrint (Name + ": " + IPAddress,2)
  #arcaderetroclock.ShowScrollingBannerV(IPAddress,0,225,0,3,0.03)

  return IPAddress
 


def GetFriendlyName(MAC):
  global FriendlyNameList
  global stdscr
  global StatusWindow
  global Window2
  global Window3

  #Debug info
  #Name = inspect.currentframe().f_code.co_name
  #Window2.ScrollPrint ("Function: " + Name,2)
  
  #for keys,values in FriendlyNameList.items():
  #  print(keys,values)

    
  FriendlyName = ''
  #mac = string.upper(MAC)
  mac = MAC.upper()
  FriendlyName = FriendlyNameList.get(MAC,'--')
  
  return FriendlyName  


def ShowDeviceCount():
  global RouterList
  global MobileList
  global UniqueRouters
  global UniqueMobile
  global stdscr
  global Window1
  global Window2

  #Window2.ScrollPrint("Settingup banner sprite for device count",1)
  #Debug info
  #Name = inspect.currentframe().f_code.co_name
  #Window2.ScrollPrint ("Function: " + Name,2)

  
  UniqueRouters = len(RouterList)
  UniqueMobile  = len(MobileList)
  RouterDisplay = arcaderetroclock.CreateBannerSprite(str(UniqueRouters))
  RouterDisplay.r = 200
  RouterDisplay.g = 0
  RouterDisplay.b = 0
  MobileDisplay = arcaderetroclock.CreateBannerSprite(str(UniqueMobile))
  MobileDisplay.r = 0
  MobileDisplay.g = 0
  MobileDisplay.b = 200


  RouterDisplay.DisplayIncludeBlack(-1,0)
  MobileDisplay.DisplayIncludeBlack(-1,6)

  #Window2.ScrollPrint("counts displayed",1)
  
  
  #OutputLine = "Routers: " + str(UniqueRouters)
  #Window1.ScrollPrint(OutputLine,2)
  #OutputLine = "Mobile:  " + str(UniqueMobile)
  #Window1.ScrollPrint(OutputLine,2)
  


def CalculateIntensity(i):
  #this function is used to set the brightness of a pixel based on an input digit
  intensity = 0
  
  if (i == 0):
    intensity = 0
  if (i == 1):
    intensity = 50
  if (i == 2):
    intensity = 75
  if (i == 3):
    intensity = 100
  if (i == 4):
    intensity = 125
  if (i == 5):
    intensity = 150
  if (i == 6):
    intensity = 175
  if (i == 7):
    intensity = 200
  if (i == 8):
    intensity = 225
  if (i == 9):
    intensity = 255
#  else:
#    intensity = 255
    

  return intensity




def DisplayStatusBars():
  global StatusBarRouter
  global StatusBarMobile
  
  global RouterBars
  global MobileBars
  global NewRouterBar
  global NewMobileBar
  global PacketCount
  global DisplayBars

 

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
  for h in range (0,arcaderetroclock.HatWidth):
    if (h <= StatusBarRouter.BarLength):
      StatusBarRouter.grid[h] = 1
    else:
      StatusBarRouter.grid[h] = 0
  
  
  #update mobile sprite
  for h in range (0,arcaderetroclock.HatWidth):
    if (h <= StatusBarMobile.BarLength):
      StatusBarMobile.grid[h] = 1
    else:
      StatusBarMobile.grid[h] = 0

  

  if (DisplayBars == True):

    #Draw packet count line
    count =   str(PacketCount)[::-1]
    y = 13
    r = 0
    g = 0
    b = 0
    for x in range (0,len(count)):
      intensity = CalculateIntensity(int(count[x]))
      g = intensity
      arcaderetroclock.setpixel(x,y,r,g,b)

  

    arcaderetroclock.unicorn.show()
    StatusBarRouter.DisplayIncludeBlack(0,14)
    StatusBarMobile.DisplayIncludeBlack(0,15)




def EraseStatusArea():
  for h in range (0,16):
    arcaderetroclock.setpixel(15-h,13,0,0,0)
    arcaderetroclock.setpixel(15-h,14,0,0,0)
    arcaderetroclock.setpixel(15-h,15,0,0,0)
  arcaderetroclock.unicorn.show()




  




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
    arcaderetroclock.setpixel(15-h,v,0,0,0)
  
  #Draw the line
  for h in range (0,LineLen):
    arcaderetroclock.setpixel(h,v,r,g,b)

  arcaderetroclock.unicorn.show()




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
    
  


#--------------------------------------
# Initialize Text window / curses    --
#--------------------------------------
  
def CreateTextWindows():

  global stdscr
  global StatusWindow
  global TitleWindow
  global Window1
  global Window2
  global Window3
  global Window4
  


  #Colors are numbered, and start_color() initializes 8 
  #basic colors when it activates color mode. 
  #They are: 0:black, 1:red, 2:green, 3:yellow, 4:blue, 5:magenta, 6:cyan, and 7:white.
  #The curses module defines named constants for each of these colors: curses.COLOR_BLACK, curses.COLOR_RED, and so forth.
  #Future Note for pads:  call noutrefresh() on a number of windows to update the data structure, and then call doupdate() to update the screen.

  #Text windows

  stdscr.nodelay (1) # doesn't keep waiting for a key press
  curses.start_color()
  curses.noecho()

  
  #We do a quick check to prevent the screen boxes from being erased.  Weird, I know.  Could not find
  #a solution.  Am happy with this work around.
  c = str(stdscr.getch())


  #Window1 Coordinates
  Window1Height = 12
  Window1Length = 40
  Window1x1 = 0
  Window1y1 = 1
  Window1x2 = Window1x1 + Window1Length
  Window1y2 = Window1y1 + Window1Height

  #Window2 Coordinates
  Window2Height = 12
  Window2Length = 40
  Window2x1 = Window1x2 + 1
  Window2y1 = 1
  Window2x2 = Window2x1 + Window2Length
  Window2y2 = Window2y1 + Window2Height

  #Window3 Coordinates
  Window3Height = 12
  Window3Length = 70
  Window3x1 = Window2x2 + 1
  Window3y1 = 1
  Window3x2 = Window3x1 + Window3Length
  Window3y2 = Window3y1 + Window3Height

  #Window4 Coordinates
  Window4Height = 32
  Window4Length = 152
  Window4x1 = 0
  Window4y1 = Window1y2 
  Window4x2 = Window4x1 + Window4Length
  Window4y2 = Window4y1 + Window4Height



  try:


    #stdscr.clear()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)



    #--------------------------------------
    # Draw Screen                        --
    #--------------------------------------

    # Create windows
    TitleWindow   = ProbeWindow('TitleWindow',1,50,0,0,0,50,'N',0) 
    StatusWindow  = ProbeWindow('StatusWindow',1,50,0,51,0,100,'N',0) 
    StatusWindow2 = ProbeWindow('StatusWindow2',1,30,0,101,0,130,'N',0) 
    Window1       = ProbeWindow('Window1',Window1Height,Window1Length,Window1y1,Window1x1,Window1y2,Window1x2,'Y',2)
    Window2       = ProbeWindow('Window2',Window2Height,Window2Length,Window2y1,Window2x1,Window2y2,Window2x2,'Y',3)
    Window3       = ProbeWindow('Window3',Window3Height,Window3Length,Window3y1,Window3x1,Window3y2,Window3x2,'Y',4)
    Window4       = ProbeWindow('Window4',Window4Height,Window4Length,Window4y1,Window4x1,Window4y2,Window4x2,'Y',6)
   
  
    # Display the title  
    TitleWindow.ScrollPrint("──GPSProbe 2020──",2)
    #StatusWindow.ScrollPrint("Preparing devices",6)
    #Window1.ScrollPrint("Channel Info",2)
    #Window2.ScrollPrint("Debug Info",2)
    #Window3.ScrollPrint("Alerts",2)
    #Window4.ScrollPrint("Details",2)
    
    Window1.DisplayTitle("Info",2)
    Window2.DisplayTitle("Debug",3)
    Window3.DisplayTitle("Alerts",5)

    #We will overwrite the title with page information during a report, so we store the original first
    Window4.Title = "Date───────────────Coordinates────────Sig─Chan──Type────MAC─────────────────Details"
    Window4.DisplayTitle("",6)



  except Exception as ErrorMessage:
    TheTrace = traceback.format_exc()
    FinalCleanup(stdscr)
    print("")
    print("")
    print("--------------------------------------------------------------")
    print("ERROR - Creating text windows")
    print(ErrorMessage)
    print("")
    #print("EXCEPTION")
    #print(sys.exc_info())
    print("")
    print ("TRACE")
    print (TheTrace)

    print("--------------------------------------------------------------")
    print("")
    print("")
    time.sleep(5)








#--------------------------------------
# Packet Capture functions           --
#--------------------------------------


#This function is run in a separate process
 
def build_packet_callback(time_fmt, logger, delimiter, mac_info, ssid, rssi):

  global stdscr
  global TitleWindow
  global StatusWindow
  global Window1
  global Window2
  global Window3
  global Window4
  global UniqueRouters
  global UniqueMobile
  global FriendlyNameList
  global PauseOutput
  IPAddress = ""
  

  #create text window interface within this thread
  #only processes in this thread can write to the windows
  CreateTextWindows()

  def StoreMAC(MAC,DeviceType,LogTimeString):
    global RouterList
    global MobileList
    global DisplayBars 
    
    global Window1
    #Window2.ScrollPrint("store mac",4)

    #We keep a list of routers and mobile devices so we can 
    #have a unique count for the past X minutes
    if(DeviceType == 'router'):
      if (MAC not in RouterList):
        RouterList[MAC]=LogTimeString
        #print (*RouterList, sep = " # ")

    elif(DeviceType == 'mobile'):
      if (MAC not in MobileList):
        MobileList[MAC]=LogTimeString
        #print (*MobileList, sep = "\n")



  
  def packet_callback(packet):
    #bring in GPS object
    global gpsd
    global GPSReport #a copy so we can view attritbutes
    global OldLat
    global OldLon
    global Channel
    global UseGPS
    global HatDisplay
    global RouterCount
    global MobileCount
    global OldMAC
    global OldLogTime
    global OldLogTimeString
    global RouterList
    global MobileList
    global UniqueRouters
    global UniqueMobile
    global PacketCount
    global DisplayBars
    global MobileOnly
    global ConfigFileStartTime
    global HeartBeatStartTime
    global stdscr
    global TitleWindow
    global StatusWindow
    global Window1
    global Window2
    global Window3
    global Window4
    global IPAddress
    global Filter
    global FriendlyNameList

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
    DidTimeElapse = 0
    Key           = ''
    GPSTime = datetime.today()

    stdscr.refresh()


    try:


      #--------------------------------
      #Check for keyboard input      --
      #--------------------------------
      Key = PollKeyboard()
      if (Key == 'q'):
        LevelFinished = 'Y'
        Finished      = 'Y'
        return

      #Debug info
      Name = inspect.currentframe().f_code.co_name
      #Window2.ScrollPrint ("Function: " + Name,2)
      
      #save config info every X seconds
      if (CheckElapsedTime(ConfigFileStartTime, SaveConfigSeconds) == 1):
        SaveConfigData()
        ConfigFileStartTime = time.time() + SaveConfigSeconds
      
      
       
      #Get time from GPS
      #if ((UseGPS == True) and (GPSReport['class'] == 'TPV')):
        #print  (getattr(GPSReport,'lat',0.0),"\t")
        #print  (getattr(GPSReport,'lon',0.0),"\t")
        #print  (getattr(GPSReport,'time',''),"\t")
        #GPSTime = getattr(GPSReport,'time','')
     

      
      #get Lat/lon from gps
      if(UseGPS == True):
        lat = str(gpsd.fix.latitude)[0:9]
        lon = str(gpsd.fix.longitude)[0:9]
        
        
      # determine preferred time format 
      LogTime       = datetime.today()
      LogTimeString = str(LogTime)[0:19]
      GPSTimeString = str(GPSTime)[0:19]
      GPSTimeString = GPSTimeString.replace("T"," ")  # remove T from date time string

      #Use GPS time if available
      if (GPSTimeString != ''):
        LogTimeString = GPSTimeString


      # list of output fields
      fields = []

      #Diagnositics
      #print (packet.haslayer)
      #print ("examining")
      #print (packet.show)  
      #time.sleep(1)


      #Add to packet counter
      PacketCount = PacketCount +1
      Window1.WindowPrint(6,1,("Packets:    " + str(PacketCount)),2)
      Window1.TextWindow.refresh()

      #we want to record packet type no matter what
      PacketType = str(packet.type) + '-' + str(packet.subtype)
      #Window3.ScrollPrint(("PacketType:" + str(packet.type) + '-' + str(packet.subtype)),2)

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
        
        MACDest = str(netaddr.EUI(packet.addr1)).upper()
        if ( MACDest == 'FF-FF-FF-FF-FF-FF-FF-FF') :
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
      except netaddr.core.NotRegisteredError:
        vendor = '--'
          
   
      #Get friendly name for recognized devices
      FriendlyName = GetFriendlyName(str(MAC))
      

      #Assemble fields for output to logfile  
      fields.append(LogTimeString)
      fields.append(lat)
      fields.append(lon)
      fields.append(rssi_val)
      fields.append(str(Channel))
      fields.append(PacketType)
      fields.append(DeviceType)
      fields.append(str(MAC))
      fields.append(FriendlyName)
      fields.append(vendor)
      fields.append(SSID.decode('UTF-8'))
      
      
      #--------------------------------------
      # Limit logging                      --
      #--------------------------------------

      #only log if lat long has moved or time is significantly different

      #add all collected fields together, delimited by tab
      #log everything if no GPS in use

      if ((FriendlyName == '--' and DeviceType == 'router') or
          (DeviceType == 'mobile')):

        try:
          #Log to the database
          with conn:
            InsertGPSLog(conn, (GPSTimeString, lat, lon, rssi_val, str(Channel), PacketType, DeviceType, str(MAC), FriendlyName, vendor, SSID))
        


        except Exception as ErrorMessage:
          TheTrace = traceback.format_exc()
          FinalCleanup(stdscr)
          print("")
          print("")
          print("--------------------------------------------------------------")
          print("ERROR - InsertGPSLog()")
          print(ErrorMessage)
          print("")
          #print("EXCEPTION")
          #print(sys.exc_info())
          print("")
          print ("TRACE")
          print (TheTrace)

          print("--------------------------------------------------------------")
          print("")
          print("")

      StoreMAC(MAC,DeviceType,LogTimeString)

    except Exception as ErrorMessage:
      TraceMessage = traceback.format_exc()
      AdditionalInfo = "Capturing and processing a packet"
      ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)


    #------------------------------------------------------
    #-- UPDATE TEXT WINDOWS                              --
    #------------------------------------------------------



    #Update Text windows
    try:
      #OutputLine = str(GPSTimeString) + "\t" +  lat+ lon + "\t"  + str(rssi_val)+ "\t"  +  str(Channel)+ "\t"  + DeviceType+ "\t" + str(MAC)+ "\t"  + FriendlyName + "\t" + vendor+ "\t" + SSID.decode('UTF-8')

      #assemble the pieces up until we get an error
      try:
        OutputLine = ""
        OutputLine = OutputLine + str(GPSTimeString)+ "\t"
        OutputLine = OutputLine + str(lat)          + " "
        OutputLine = OutputLine + str(lon)          + "\t" 
        OutputLine = OutputLine + str(rssi_val)     + "\t" 
        OutputLine = OutputLine + str(Channel)      + "\t" 
        OutputLine = OutputLine + str(DeviceType)   + "\t"
        OutputLine = OutputLine + str(MAC)          + "\t" 
        OutputLine = OutputLine + FriendlyName      + "\t" 
        OutputLine = OutputLine + vendor            + "\t" 
        OutputLine = OutputLine + SSID.decode('UTF-8')
      except Exception as ErrorMessage:
        #Print as much as we got so far
        
        OutputLine = str(GPSTimeString) + "\t" +  lat+ lon + "\t"  + str(rssi_val)+ "\t"  +  str(Channel)+ "\t"  + DeviceType+ "\t" + str(MAC)+ "\t"  + FriendlyName + "\t" + vendor+ "\t" + SSID.decode('UTF-8')
        OutputLine = OutputLine + "*error*"
      
      # "NoFriendlyRouter" can be any of the following:
      #   no friendly routers
      #   unknown routers
      #   all mobile

      
      if ((Filter == 'none') or
          (Filter == 'NoFriendlyRouter' and DeviceType   == 'router' and FriendlyName == '--') or
          (Filter == 'NoFriendlyRouter' and FriendlyName == '--')     or
          (Filter == 'NoFriendlyRouter' and DeviceType   == 'mobile') or
          (Filter == 'NoFriendly'       and FriendlyName == '--')):

        if (PauseOutput == False):
          Window4.ScrollPrint(OutputLine,2)


    except Exception as ErrorMessage:
      TraceMessage = traceback.format_exc()
      AdditionalInfo = "Updating text window - OutputLine: " + PrintLine 
      ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)

    
    
    #show alert if non friendly device detected
    try:
      if (FriendlyName == "--"):
        OutputLine = GPSTimeString[-8:] + " " + str(MAC) + " " + vendor+ " " + SSID.decode('UTF-8')  
        Window3.ScrollPrint(OutputLine,2)
    except Exception as ErrorMessage:
      TraceMessage = traceback.format_exc()
      AdditionalInfo = "Showing alert - OutputLine: " + PrintLine 
      ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)


    #show cool info
    Window1.WindowPrint(1,1, "Datetime:   " + GPSTimeString,2)
    Window1.WindowPrint(2,1, "IPAddress:  " + IPAddress,2)
    Window1.WindowPrint(3,1,("Routers:    " + str(UniqueRouters)),2)
    Window1.WindowPrint(4,1,("Mobile:     " + str(UniqueMobile)),2)
    Window1.WindowPrint(5,1,("Channel:    " + str(Channel)),2)
    Window1.WindowPrint(7,1,("Filter:     " + Filter),2)
    Window1.WindowPrint(8,1,("Known Devices: " + str(FriendlyCount)),2)
    Window1.WindowPrint(9,1,("New Records:   " + str(RecordCount)),2)
    Window1.WindowPrint(10,1,("Record Count:  " + str(GPSLogRecordCount)),2)
    

    Window1.TextWindow.refresh()


    #Display router and mobile counts on unicorn  hat
    if (HatDisplay):
      ShowDeviceCount()
      ShowSignalStrength(rssi_val,DeviceType)
      UpdateSignalStrength(rssi_val,DeviceType)
       

  
    
  return packet_callback


#--------------------------------------
# Functions for non probe packets    --
#--------------------------------------


#This function changes the Channel to be monitored
def ChangeChannel(iface):
    global Channel
    global Window2
    OutputLine = ""

    #Debug info
    Name = inspect.currentframe().f_code.co_name
    #Window2.ScrollPrint ("Function: " + Name,2)

    Channel = 1
    n = 1
    stop_ChangeChannel = False
    
    while not stop_ChangeChannel:
        time.sleep(ChangeChannelWait)



        #might need to clean special characters

        #OutputLine = "Changing to Channel: " + (str(Channel))
        #Window1.ScrollPrint(OutputLine,5)
        #OutputLine = ""    
        
        #Window1.WindowPrint(5,1,("Channel:    " + str(Channel)[0:1]),2)
        #Window1.TextWindow.refresh()
    

        
        try:

          os.system('iwconfig %s Channel %d >/dev/null 2>&1' % (iface, Channel))
          n = random.randint(1,14)
          if(n != Channel):
              Channel = n

        except Exception as ErrorMessage:
            TheTrace = traceback.format_exc()
            FinalCleanup(stdscr)
            print("")
            print("")
            print("--------------------------------------------------------------")
            print("ERROR - ChangeChannel")
            print(ErrorMessage)
            print("")
            #print("EXCEPTION")
            #print(sys.exc_info())
            print("")
            print ("TRACE")
            print (TheTrace)
        
            print("--------------------------------------------------------------")
            print("")
            print("")



        

      #Display heartbeat every channel change
      #if (CheckElapsedTime(HeartBeatStartTime, HeartBeatSeconds +1) == 1):
        r,g,b = arcaderetroclock.getpixel(15,0)
    
        #if yellow, make black.  Else make yellow (yes, I said that!)
        if (r == 120 and g == 120 and b == 0):
          arcaderetroclock.setpixel(15,0,0,0,0)
        else:
          arcaderetroclock.setpixel(15,0,120,120,0)
          
      #HeartBeatStartTime = time.time() + HeartBeatSeconds    





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

StatusBarRouter = arcaderetroclock.Sprite(
  16,
  1,
  100,
  0,
  0,
  [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
)

StatusBarRouter.BarLength = 0


StatusBarMobile = arcaderetroclock.Sprite(
  16,
  1,
  0,
  0,
  200,
  [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
)
StatusBarMobile.BarLength = 0





#--------------------------------------
# Config Data                        --
#--------------------------------------


def SaveConfigData():

  global stdscr
  global Window2
  
  #print (" ")
  #print ("--Save Config Data------------")
  #we save the time to file as 5 minutes in future, which allows us to unplug the device temporarily
  #the time might be off, but it might be good enough
  
  AdjustedTime = (datetime.today() + timedelta(minutes=5)).strftime('%k:%M:%S')


  #Debug info
  Name = inspect.currentframe().f_code.co_name
  Window2.ScrollPrint ("Function: " + Name,2)


  
  if (os.path.exists(ConfigFileName)):
    ConfigFile = SafeConfigParser()
    ConfigFile.read(ConfigFileName)
  else:
    #print ("Config file not found.  Creating new one.")
    ConfigFile = SafeConfigParser()
    ConfigFile.read(ConfigFileName)
    ConfigFile.add_section('main')
    ConfigFile.add_section('pacdot')

    
  ConfigFile.set('main', 'CurrentTime', AdjustedTime)
  #print ("Time to save: ",AdjustedTime)


  #print ("Writing configuration file")
  with open(ConfigFileName, 'w') as f:
    ConfigFile.write(f)
  #print ("------------------------------")


def LoadConfigData():


  #print ("--Load Config Data------------")
    
  if (os.path.exists(ConfigFileName)):
    ConfigFile = SafeConfigParser()
    ConfigFile.read(ConfigFileName)

    #Get and set time    
    TheTime = ConfigFile.get("main","CurrentTime")
    #print ("Setting time: ",TheTime)
    CMD = "sudo date --set \"" + TheTime + "\">/dev/null 2>&1"
    os.system(CMD)
   
    
  else:
    print ("Config file not found! Running with default values.")

  start_time   = time.time()

    
  print ("------------------------------")
  print (" ")
  


  
def CheckElapsedTime(start_time, seconds):
  
  elapsed_time = time.time() - start_time
  elapsed_hours   = elapsed_time / 3600
  elapsed_minutes = elapsed_time / 60
  elapsed_seconds = int(elapsed_time) 
  #print ("StartTime:",starttime,"Seconds:",seconds)
  #print("Clock Timer: {:0>2}:{:0>2}:{:05.2f}".format(int(elapsed_hours),int(elapsed_minutes),elapsed_seconds),"Elapsed seconds:",elapsed_seconds, "Check seconds:",seconds)
  
  
  d,r = divmod(elapsed_seconds, seconds)
  
  #print("CheckElapsedTime:",seconds, "StartTime:",start_time," Elapsed:",elapsed_time,"Remainder:",r)
  
  
#  if (elapsed_seconds >= seconds):
#    start_time = time.time()

  if (r == 0):
    return 1
  else:
    return 0


  




#--------------------------------------------------------------------
#  ____        _        _                                          --
# |  _ \  __ _| |_ __ _| |__   __ _ ___  ___                       --
# | | | |/ _` | __/ _` | '_ \ / _` / __|/ _ \                      --  
# | |_| | (_| | || (_| | |_) | (_| \__ \  __/                      --
# |____/ \__,_|\__\__,_|_.__/ \__,_|___/\___|                      --
#                                                                  --
#--------------------------------------------------------------------


 
 
def create_connection(db_file):
  """ create a database connection to the SQLite database
      specified by db_file
  :param db_file: database file
  :return: Connection object or None
  """
  conn = None
  try:
      conn = sqlite3.connect(db_file)
  except Error as e:
      FinalCleanup(stdscr)
      print(e)
 
  return conn
    
    
 
def InsertGPSLog(conn, fields):
  #Text windows
  global stdscr
  global StatusWindow
  global Window4
  global Window2
  global RecordCount 
  global GPSLogRecordCount

  #Debug info
  Name = inspect.currentframe().f_code.co_name
  Window2.ScrollPrint ("Function: " + Name,2)

  try:
    SQLQuery = ''' INSERT INTO GPSLog values (?,?,?,?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(SQLQuery, fields)
    conn.commit()
    RecordCount = RecordCount + 1
    GPSLogRecordCount = GPSLogRecordCount + 1

  except Exception as ErrorMessage:
    TraceMessage = traceback.format_exc()
    AdditionalInfo = "SQLQuery: " + SQLQuery
    ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)


  return cur.lastrowid    






def PopulateFriendlyName(FriendlyNameList):
  
  # Take the values from the FriendlyNameList (imported from file) and insert into
  # the SQLite database
  # We wil first sort the values to make sure the values are entered in key order
  # this will improve performance of lookups
  # the table will also have an index 


  cur = conn.cursor()

  try:
    #truncate table 
    SQLQuery = ''' delete from FriendlyName; '''
    cur.execute(SQLQuery)
  
    SQLQuery = ''' INSERT INTO FriendlyName values (NULL,?,?) '''
  
    for key,value in FriendlyNameList.items():
      cur.execute(SQLQuery, (key,value))


  except Exception as ErrorMessage:
    TraceMessage = traceback.format_exc()
    AdditionalInfo = "SQLQuery: " + SQLQuery
    ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)


  return cur.lastrowid    





def ShowDistinctDevices(conn):

  global stdscr
  global Window2

  #Debug info
  Name = inspect.currentframe().f_code.co_name
  Window2.ScrollPrint ("Function: " + Name,2)

  try:
    cursor = conn.cursor()
    SQLQuery = """SELECT count(*),  
                         FriendlyName,
                         Vendor, 
                         SSID 
                    from GPSLog 
                   where DateTime >= datetime('now','localtime','-24 Hour')
                   group by FriendlyName,
                            Vendor, 
                            SSID
                   order by FriendlyName ;
    """

    Results = pandas.read_sql_query(SQLQuery, conn)
    print(Results)
    

  except Exception as ErrorMessage:
    TraceMessage = traceback.format_exc()
    AdditionalInfo = "SQLQuery: " + SQLQuery
    ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)
 





def ShowRecentCaptures(conn):

  global stdscr
  global Window2
  global Window4
  global StartRow 
  global Filter
  Output = ""
  AndClause = ""

  
  #Pagination
  RowsToShow = Window4.DisplayRows
  Window4.DisplayTitle(Window4.Title + "──────Rows: " + str(StartRow) + " - " + str(StartRow + RowsToShow) + " ───",6)

  #Debug info
  Name = inspect.currentframe().f_code.co_name
  #Window2.ScrollPrint ("Start:" + str(StartRow) + " Rows:" + str(RowsToShow),2)


  #I had to recast everything as string because of conversion errors (float or unicode)
  try:
    cursor = conn.cursor()

    #Build the AND clause for the filter
    if (Filter == "NoFriendly"):
      AndClause = "and FriendlyName = '--'"
    elif (Filter == 'NoFriendlyRouter'):
      AndClause = "and (Device = 'mobile' or (Device = 'router' and FriendlyName <> '--'))"
    else:
      AndClause = ""

    SQLQuery = """SELECT DateTime    ,
                         Device      ,
                         MACAddress  ,
                         Lat         ,
                         Lon         ,
                         Signal      ,
                         Channel     ,
                         PktType     ,
                         FriendlyName,
                         Vendor      , 
                         SSID       
                    from GPSLog 
                   where DateTime >= datetime('now','localtime','-72 Hour')
                   """ + AndClause + """                    
                   order by DateTime desc
                   limit """ + str(StartRow) + "," + str(RowsToShow) + """ ;
    """
    Results = pandas.read_sql_query(SQLQuery, conn)

    for index, row in Results.iterrows():

      try:
        Output = ""
        Output = Output + row['DateTime']         + "\t"
        Output = Output + str(row['Lat'])         + " "
        Output = Output + str(row['Lon'])         + "\t" 
        Output = Output + str(row['Signal'])      + "\t" 
        Output = Output + str(row['Channel'])     + "\t" 
        Output = Output + str(row['Device'])      + "\t"
        Output = Output + str(row['MACAddress'])  + "\t" 
        Output = Output + str(row['FriendlyName'])+ "\t" 
        Output = Output + str(row['Vendor'])      + "\t" 
        Output = Output + row['SSID'].decode('UTF-8')
        Window4.ScrollPrint(Output,2)
      except Exception as ErrorMessage:
        #TraceMessage = traceback.format_exc()
        #ErrorHandler(ErrorMessage,TraceMessage,'')

        #Print as much as we got so far
        Output =  Output + "**PACKET ERROR**"
        Window4.ScrollPrint(Output,1)


  except Exception as ErrorMessage:
    TraceMessage = traceback.format_exc()
    AdditionalInfo = "SQLQuery: " + SQLQuery
    ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)
 


 
  

def ShowUnknownDevices(conn):

  global stdscr
  global Window2

  #Debug info
  Name = inspect.currentframe().f_code.co_name
  Window2.ScrollPrint ("Function: " + Name,2)

  try:
    cursor   = conn.cursor()
    SQLQuery = """
    
      select count(*) as Hits,
             max(DateTime) as LastSeen,
             Device, MACAddress, FriendlyName, Vendor, SSID  
        from GPSLog               
       where FriendlyName = '--'
       group by Device, MACAddress, FriendlyName, Vendor, SSID  
       order by DateTime;
    """
 
    
    Results = pandas.read_sql_query(SQLQuery, conn)
    print(Results)

  except Exception as ErrorMessage:
    TraceMessage = traceback.format_exc()
    AdditionalInfo = "SQLQuery: " + SQLQuery
    ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)
  



def ShowRecentDevices(conn):

  global stdscr
  global Window2

  #Debug info
  Name = inspect.currentframe().f_code.co_name
  Window2.ScrollPrint ("Function: " + Name,2)

  try:
    cursor = conn.cursor()
    
    SQLQuery = """
    
      select DateTime, PktType, Device, MACAddress, FriendlyName, Vendor, SSID  
        from GPSLog               
      order by DateTime desc
      limit 30;"""

    
    Results = pandas.read_sql_query(SQLQuery, conn)
    print(Results)
    

    #print('Total Row(s):', cursor.rowcount)
    #for row in rows:
    #  print(row)
  except Exception as ErrorMessage:
    TraceMessage = traceback.format_exc()
    AdditionalInfo = "SQLQuery: " + SQLQuery
    ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)
  


def GetDatabaseRecordCount(conn):

  try:
    cursor = conn.cursor()
    
    SQLQuery = """
      select count(*) as RecordCount from GPSLog;
      """
   
    Results = pandas.read_sql_query(SQLQuery, conn)
    RecordCount = Results['RecordCount'].values[0]

  except Exception as ErrorMessage:
    TraceMessage = traceback.format_exc()
    AdditionalInfo = "SQLQuery: " + SQLQuery
    ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)

  return RecordCount



def ListFriendlyNames(conn):

  global stdscr
  global Window2

  #Debug info
  Name = inspect.currentframe().f_code.co_name
  Window2.ScrollPrint ("Function: " + Name,2)

  try:
    cursor = conn.cursor()
    
    SQLQuery = """
    
      select *
        from FriendlyName
      order by 2;
      """

    
    Results = pandas.read_sql_query(SQLQuery, conn)
    #print(Results)

  except Exception as ErrorMessage:
    TraceMessage = traceback.format_exc()
    AdditionalInfo = "SQLQuery: " + SQLQuery
    ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)



 

#--------------------------------------------------------------------
#                                                                  --
#  | |/ /___ _   _ _ __  _ __ ___  ___ ___  ___  ___               --
#  | ' // _ \ | | | '_ \| '__/ _ \/ __/ __|/ _ \/ __|              --
#  | . \  __/ |_| | |_) | | |  __/\__ \__ \  __/\__ \              --
#  |_|\_\___|\__, | .__/|_|  \___||___/___/\___||___/              --
#            |___/|_|                                              --
#                                                                  --
#--------------------------------------------------------------------


#--------------------------------------
# Handle Kepresses                   --
#--------------------------------------

  
def ProcessKeypress(Key):
  global stdscr
  global StatusWindow
  global Window2
  global Window4
  global Filter
  global FriendlyCount
  global IPAddress
  global StartRow
  global PauseOutput

  count  = 0

  OutputLine = "** KEYPRESS: " + str(Key) + " **"
  Window2.ScrollPrint (OutputLine,5)
  # p = pause
  # q = quit
  # r = reboot
    
  if (Key == "p" or Key == " "):
    PauseOutput = not (PauseOutput)
    if (PauseOutput == True):
      Window2.ScrollPrint("Pausing output",2)
      StatusWindow.ScrollPrint("** Output Paused - press SPACE to resume **",3)
    else:
      Window2.ScrollPrint("Resuming output",2)
      StatusWindow.ScrollPrint("",2)

  elif (Key == "i"):
    IPAddress = ShowIPAddress()
    arcaderetroclock.ShowScrollingBannerV(IPAddress,0,225,0,3,0.03)

  elif (Key == "q"):
    arcaderetroclock.ShowScrollingBannerV("Quit!",200,0,0,3,0.02)
    FinalCleanup(stdscr)

    os._exit(1)

  elif (Key == "c"):
      Window2.Clear()
      Window4.Clear()
      Window4.DisplayTitle(Window4.Title,6)

      Window2.ScrollPrint("Clear screen",2)
      StartRow = 0
  elif (Key == "f"):
    #FriendlyNameList(conn)
    #arcaderetroclock.ShowScrollingBannerV("Friend Filter",200,0,0,3,0.01)
    if (Filter == "none"):
      Filter = "NoFriendlyRouter"
    elif (Filter == "NoFriendlyRouter"):
      Filter = "NoFriendly"
    else:
      Filter = "none"
    Window2.ScrollPrint(("Filter: " + Filter),5)
    #repopulate the friendlyname table to incorporate changes
    #FriendlyCount = PopulateFriendlyName(FriendlyNameList)
  elif (Key == "r"):
    arcaderetroclock.ShowScrollingBannerV("Reboot!",100,0,0,3,0.01)
    FinalCleanup(stdscr)
    os.execl(sys.executable, sys.executable, *sys.argv)
  elif (Key == "1"):
    print ("Setting brightness 100%")
    arcaderetroclock.unicorn.brightness(1)
  elif (Key == "2"):
    print ("Setting brightness 75%")
    arcaderetroclock.unicorn.brightness(0.75)
  elif (Key == "3"):
    print ("Setting brightness 50%")
    arcaderetroclock.unicorn.brightness(0.5)
  elif (Key == "4"):
    print ("Setting brightness 25%")
    arcaderetroclock.unicorn.brightness(0.25)
  elif (Key == "5"):
    print ("Setting brightness 0%")
    arcaderetroclock.unicorn.brightness(0)
  elif (Key == "6"):
    print ("--Report 6: distinct devices ")
    ShowDistinctDevices(conn)
    arcaderetroclock.ShowScrollingBannerV("Distinct Devices",200,0,0,3,0.01)

  elif (Key == "7"):
    print ("--Report 7: All unknown devices")
    ShowUnknownDevices(conn)
    arcaderetroclock.ShowScrollingBannerV("unknown devices",200,0,0,3,0.01)

  elif (Key == "8"):
    print ("--Report 8: 30 recent devices")
    ShowRecentDevices(conn)
    arcaderetroclock.ShowScrollingBannerV("Recent devices",200,0,0,3,0.01)

  elif (Key == "9"):
    
    Window2.ScrollPrint("--Report 9: Recent Intruders",2)
    ShowRecentCaptures(conn)
    StartRow = StartRow + Window4.DisplayRows

  elif (Key == "0"):
    
    StartRow = StartRow - Window4.DisplayRows
    Window2.ScrollPrint("--Report 9: Recent Intruders",2)
    ShowRecentCaptures(conn)


    
  
 





def PollKeyboard():
  global stdscr
  global Window2
  ReturnChar = ""
  c = ""

  #curses.filter()
  curses.noecho()


  

  try:
    c = chr(stdscr.getch())

  except Exception as ErrorMessage:
    c=""

  
  #Look for specific characters
  if  (c == " " 
    or c == "+"
    or c == "-"
    or c == "c"
    or c == "f"
    or c == "i"
    or c == "p"
    or c == "q"
    or c == "r"
    or c == "t"):
    ReturnChar = c       

  #Look for digits (ascii 48-57 == digits 0-9)
  elif (c >= '0' and c <= '9'):
    #print ("Digit detected")
    #StatusWindow.ScrollPrint("Digit Detected",2)
    ReturnChar = (c)    

  if (c != ""):
    #print ("----------------")
    #print ("Key Pressed: ",Key)
    #print ("----------------")
    OutputLine = "Key Pressed: " + c
    #Window2.ScrollPrint(OutputLine,4)
    ProcessKeypress(c)
  return ReturnChar




def ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo):
  CallingFunction =  inspect.stack()[1][3]
  FinalCleanup(stdscr)
  print("")
  print("")
  print("--------------------------------------------------------------")
  print("ERROR - Function (",CallingFunction, ") has encountered an error. ")
  print(ErrorMessage)
  print("")
  print("")
  print("TRACE")
  print(TraceMessage)
  print("")
  print("")
  if (AdditionalInfo != ""):
    print("Additonal info:",AdditionalInfo)
    print("")
    print("")
  print("--------------------------------------------------------------")
  print("")
  print("")
  arcaderetroclock.ShowScrollingBannerV("ERROR DETECTED!",255,0,0,3,0.03)




def FinalCleanup(stdscr):
  stdscr.keypad(0)
  curses.echo()
  curses.nocbreak()
  curses.curs_set(1)
  curses.endwin()
  


#--------------------------------------------------------------------
#   __  __    _    ___ _   _                                       --
#  |  \/  |  / \  |_ _| \ | |                                      --
#  | |\/| | / _ \  | ||  \| |                                      --
#  | |  | |/ ___ \ | || |\  |                                      --
#  |_|  |_/_/   \_\___|_| \_|                                      --
#                                                                  --
#  ____  ____   ___   ____ _____ ____ ____ ___ _   _  ____         --
# |  _ \|  _ \ / _ \ / ___| ____/ ___/ ___|_ _| \ | |/ ___|        --
# | |_) | |_) | | | | |   |  _| \___ \___ \| ||  \| | |  _         --
# |  __/|  _ <| |_| | |___| |___ ___) |__) | || |\  | |_| |        --
# |_|   |_| \_\\___/ \____|_____|____/____/___|_| \_|\____|        --
#                                                                  --
#--------------------------------------------------------------------
 
  
#def main(stdscr):



#gpsd = None #setting the global variable

os.system('clear') #clear the terminal (optional)
os.system("figlet 'GPS PROBE'")


LoadConfigData()



#--------------------
# Setup Database   --
#--------------------
database = "/home/pi/sqlite/GPSProbe"  
conn = create_connection(database)
 

#-------------------------------
# Populate FriendlyName table --
#-------------------------------

try:
  #Sort the list before entering into database
  FriendlyNameList =  OrderedDict(sorted(FriendlyNameList.items())) 
  FriendlyCount = PopulateFriendlyName(FriendlyNameList)

except Exception as ErrorMessage:
  TraceMessage = traceback.format_exc()
  AdditionalInfo = "Populating FriendlyName"
  ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)


#Get count of records in GPSLog table
GPSLogRecordCount = GetDatabaseRecordCount(conn)







    



#--------------------
# Start GPS thread --
#--------------------
if(UseGPS == True):
  gpsd = None 
  gpsp = GpsPoller() 
  gpsp.start() 



#Launch Probe Logger
logger = logging.getLogger(NAME)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(args.output, maxBytes=args.max_bytes, backupCount=args.max_backups)
logger.addHandler(handler)

#If logging specified, open handler and write column headings
if args.log:
  logger.addHandler(logging.StreamHandler(sys.stdout))
  #Column Headers
  logger.info('DateTime         \tLat\t\tLon\tSignal\tChannel\tPktType\tDevice\tMACAddress\t\t\tFriendlyName  \tVendor  \tSSID')
  
  

#Assemble captured packets   
built_packet_cb = build_packet_callback(
  args.time,
  logger,
  args.delimiter,
  args.mac_info,
  args.ssid,
  args.rssi
)

IPAddress = ShowIPAddress()




#launch thread to switch Channels
thread = threading.Thread(target=ChangeChannel, args=(args.interface, ), name="ChangeChannel")
thread.daemon = True
thread.start()


#-------------------------------
#If unicorn hat is to be used --
#-------------------------------
if(HatDisplay):
  arcaderetroclock.unicorn.rotation(90)
  arcaderetroclock.unicorn.off()
  arcaderetroclock.ShowScrollingBanner("GPS Probe",0,0,200,ScrollSpeed * 3)
    
  StatusAreaTimer = RepeatedTimer(TimeDelay,DisplayStatusBars)
  #timer2 = RepeatedTimer(1,ShowPacketCount)


while True:
  try:
    #capture packets
    sniff(iface=args.interface, prn=built_packet_cb, store=0, monitor=True)
    break #exit loop if sniff exits successfully (user quit)
  except Exception as ErrorMessage:
    TraceMessage = traceback.format_exc()
    AdditionalInfo = "An error occurred while running SNIFF"
    ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)






#Stop threads  
print ("\nKilling threads...")
if(UseGPS == True):
  gpsp.running = False

time.sleep(5)


thread.stop_ChangeChannel = False
StatusAreaTimer.stop()
#timer2.stop()

#gpsp.join() # wait for the thread to finish what it's doing
os.system("figlet 'BYE LOSER'")
print ("Done.\nExiting.")







#wrapper(main)






