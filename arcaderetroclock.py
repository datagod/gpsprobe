#------------------------------------------------------------------------------
#                                                                            --
#      _    ____   ____    _    ____  _____    ____ _     ___   ____ _  __   --
#     / \  |  _ \ / ___|  / \  |  _ \| ____|  / ___| |   / _ \ / ___| |/ /   --
#    / _ \ | |_) | |     / _ \ | | | |  _|   | |   | |  | | | | |   | ' /    --
#   / ___ \|  _ <| |___ / ___ \| |_| | |___  | |___| |__| |_| | |___| . \    --
#  /_/   \_\_| \_\\____/_/   \_\____/|_____|  \____|_____\___/ \____|_|\_\   --
#                                                                            --
#                                                                            --
#   This is a partial collection of classes and functions from my            --
#   Arcade Retro Clock project.                                              --
#                                                                            --
#   Copyright 2019 William McEvoy                                            --
#                                                                            --
#                                                                            --
#------------------------------------------------------------------------------


import unicornhathd as unicorn
import time


#--------------------------------------
# UnicornHD Display                  --
#--------------------------------------

HatWidth, HatHeight = unicorn.get_shape()
unicorn.set_layout(unicorn.AUTO)
unicorn.rotation(180)
unicorn.brightness(1)



#------------------------------------------------------------------------------
# SPRITES / Classes                                                          --
#------------------------------------------------------------------------------

#This is custom function because UnicornHatHD does not have one !
def setpixels(TheBuffer):
  x = 0
  y = 0

  for y in range (HatWidth):
    for x in range (HatWidth):
      r,g,b = TheBuffer[abs(15-x)][y]
      setpixel(x,y,r,g,b)

      
def setpixelsWithClock(TheBuffer,ClockSprite,h,v):
  x = 0
  y = 0

  for y in range (HatWidth):
    for x in range (HatWidth):
      if (x >= h and x <= h+ClockSprite.width) and (y >= v and y <= v+ClockSprite.height):
        r = ClockSprite.r
        g = ClockSprite.g
        b = ClockSprite.b
      else:
        r,g,b = TheBuffer[abs(15-x)][y]
      setpixel(x,y,r,g,b)



      
      
#Bug fix because my HD is inverted horizontally
def setpixel(x, y, r, g, b):
  if (CheckBoundary(x,y) == 0):
    unicorn.set_pixel(abs(15-x), y, r, g, b)

#Bug fix because my HD is inverted horizontally
def getpixel(h,v):
  r = 0
  g = 0
  b = 0
  r,g,b = unicorn.get_pixel(abs(15-h),v)
  return r,g,b      


  
  
def ClockTimer(seconds):
  global start_time
  elapsed_time = time.time() - start_time
  elapsed_hours, rem = divmod(elapsed_time, 3600)
  elapsed_minutes, elapsed_seconds = divmod(rem, 60)
  #print("Elapsed Time: {:0>2}:{:0>2}:{:05.2f}".format(int(elapsed_hours),int(elapsed_minutes),elapsed_seconds),end="\r")

  if (elapsed_seconds >= seconds ):
    start_time = time.time()
    return 1
  else:
    return 0
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
class Sprite(object):
  def __init__(self,width,height,r,g,b,grid):
    self.width  = width
    self.height = height
    self.r      = r
    self.g      = g
    self.b      = b
    self.grid   = grid

  
  #This version will also draw black parts of the sprite
  def DisplayIncludeBlack(self,h1,v1):
    x = 0,
    y = 0
    for count in range (0,(self.width * self.height)):
      y,x = divmod(count,self.width)
      
      if self.grid[count] == 1:
        if (CheckBoundary(x+h1,y+v1) == 0):
          setpixel(x+h1,y+v1,self.r,self.g,self.b)
      elif self.grid[count] == 0:
        if (CheckBoundary(x+h1,y+v1) == 0):
          setpixel(x+h1,y+v1,0,0,0)
    unicorn.show()


  def Display(self,h1,v1):
    x = 0,
    y = 0
    #print ("Display:",self.width, self.height, self.r, self.g, self.b,v1,h1)
    for count in range (0,(self.width * self.height)):
      y,x = divmod(count,self.width)
      #print("Count:",count,"xy",x,y)
      if self.grid[count] == 1:
        if (CheckBoundary(x+h1,y+v1) == 0):
          setpixel(x+h1,y+v1,self.r,self.g,self.b)
    #unicorn.show()


  def CopySpriteToBuffer(self,h1,v1):
    #Does the same as Display, but does not call show(), allowing calling function to further modify the Buffer
    #before displaying
    x = 0,
    y = 0
    for count in range (0,(self.width * self.height)):
      y,x = divmod(count,self.width)
      #print("Count:",count,"xy",x,y)
      if self.grid[count] == 1:
        if (CheckBoundary(x+h1,y+v1) == 0):
          setpixel(x+h1,y+v1,self.r,self.g,self.b)
      elif self.grid[count] == 0:
        if (CheckBoundary(x+h1,y+v1) == 0):
          setpixel(x+h1,y+v1,0,0,0)
    #unicorn.show()
    
    
    
  def Erase(self,h1,v1):
    #This function draws a black sprite, erasing the sprite.  This may be useful for
    #a future "floating over the screen" type of sprite motion
    #It is pretty fast now, seems just as fast as blanking whole screen using off() or clear()
    x = 0
    y = 0
    #print ("Erase:",self.width, self.height, self.r, self.g, self.b,v1,h1)
    for count in range (0,(self.width * self.height)):
      y,x = divmod(count,self.width)
      #print("Count:",count,"xy",x,y)
      if self.grid[count] == 1:
        if (CheckBoundary(x+h1,y+v1) == 0):
          #setpixel(x+h1,y+v1,0,0,0)
          setpixel(x+h1,y+v1,0,0,0)
    unicorn.show()

  def HorizontalFlip(self):
    x = 0
    y = 0
    flipgrid = []
    
    print ("flip:",self.width, self.height)
    for count in range (0,(self.width * self.height)):
      y,x = divmod(count,self.width)
      #print("Count:",count,"xy",x,y)
      #print("Calculations: ",(y*self.height)+ self.height-x-1)  
      flipgrid.append(self.grid[(y*self.height)+ self.height-x-1])  
    print("Original:", str(self.grid))
    print("Flipped :", str(flipgrid))
    self.grid = flipgrid      

    
  def Scroll(self,h,v,direction,moves,delay):
    #print("Entering Scroll")
    x = 0
    oldh = 0
    #Buffer = copy.deepcopy(unicorn.get_pixels())
    
    #modifier is used to increment or decrement the location
    if direction == "right" or direction == "down":
      modifier = 1
    else: 
      modifier = -1
    
    #print("Modifier:",modifier)
    
    if direction == "left" or direction == "right":
      #print ("Direction: ",direction)  
      for count in range (0,moves):
        h = h + (modifier)
        #erase old sprite
        if count >= 1:
          oldh = h - modifier
          #print ("Scroll:",self.width, self.height, self.r, self.g, self.b,h,v)
          unicorn.clear()

        #draw new sprite
        self.Display(h,v)
        unicorn.show()
        time.sleep(delay)


        


  def ScrollIncludeBlack(self,h,v,direction,moves,delay):
    #print("Entering Scroll")
    x = 0
    oldh = 0
    #Buffer = copy.deepcopy(unicorn.get_pixels())
    
    #modifier is used to increment or decrement the location
    if direction == "right" or direction == "down":
      modifier = 1
    else: 
      modifier = -1
    
    #print("Modifier:",modifier)
    
    if direction == "left" or direction == "right":
      #print ("Direction: ",direction)  
      for count in range (0,moves):
        h = h + (modifier)
        #erase old sprite
        if count >= 1:
          oldh = h - modifier
          #print ("Scroll:",self.width, self.height, self.r, self.g, self.b,h,v)
          

        #draw new sprite
        self.DisplayIncludeBlack(h,v)
        time.sleep(delay)



    if direction == "up" or direction == "down":
      for count in range (0,moves):
        v = v + (modifier)
        #erase old sprite
        if count >= 1:
          oldv = v - modifier
          #self.Erase(h,oldv)
          setpixels(Buffer)
            
        #draw new sprite
        self.Display(h,v)
        time.sleep(delay)
  

        
  
  def ScrollAcrossScreen(self,h,v,direction,ScrollSleep):
    #print ("--ScrollAcrossScreen--")
    #print ("width height",self.width,self.height)
    if (direction == "right"):
      self.Scroll((0- self.width),v,"right",(HatWidth + self.width),ScrollSleep)
    elif (direction == "left"):
      self.Scroll(HatWidth-1,v,"left",(HatWidth + self.width),ScrollSleep)
    elif (direction == "up"):
      self.Scroll(h,HatWidth-1,"left",(HatWidth + self.height),ScrollSleep)




def JoinSprite(Sprite1, Sprite2, Buffer):
  #This function takes two sprites, and joins them together horizontally
  #The color of the second sprite is used for the new sprite
  height = Sprite1.height
  width  = Sprite1.width + Buffer + Sprite2.width
  elements = height * width
  x = 0
  y = 0
  
 
  TempSprite = Sprite(
  width,
  height,
  Sprite2.r,
  Sprite2.g,
  Sprite2.b,
  [0]*elements
  )
  for i in range (0,elements):
    y,x = divmod(i,width)
    
    #copy elements of first sprite
    if (x >= 0 and x< Sprite1.width):
      TempSprite.grid[i] = Sprite1.grid[x + (y * Sprite1.width)]
    
    if (x >= (Sprite1.width + Buffer) and x< (Sprite1.width + Buffer + Sprite2.width)):
      TempSprite.grid[i] = Sprite2.grid[(x - (Sprite1.width + Buffer)) + (y * Sprite2.width)]

  
  return TempSprite    




 
  
def CreateBannerSprite(TheMessage):
  #We need to dissect the message and build our banner sprite one letter at a time
  #We need to initialize the banner sprite object first, so we pick the first letter
  x = -1
  
  BannerSprite = Sprite(1,5,0,0,0,[0,0,0,0,0])
  
  #Iterate through the message, decoding each characater
  for i,c, in enumerate(TheMessage):
    x = ord(c) -65
    if (c == '?'):
      BannerSprite = JoinSprite(BannerSprite, QuestionMarkSprite,0)
    elif (c == '#'):
      BannerSprite = JoinSprite(BannerSprite, PoundSignSprite,0)
    elif (c == '.'):
      BannerSprite = JoinSprite(BannerSprite, PeriodSprite,0)
    elif (c == ':'):
      BannerSprite = JoinSprite(BannerSprite, ColonSprite,0)
    elif (c == '!'):
      BannerSprite = JoinSprite(BannerSprite, ExclamationSprite,0)
    elif (c == ' '):
      BannerSprite = JoinSprite(BannerSprite, SpaceSprite,0)
    elif (ord(c) >= 48 and ord(c)<= 57):
      BannerSprite = JoinSprite(BannerSprite, DigitSpriteList[int(c)],1)
    else:
      BannerSprite = JoinSprite(BannerSprite, TrimSprite(AlphaSpriteList[x]),1)
  return BannerSprite


def CheckBoundary(h,v):
  BoundaryHit = 0
  if v < 0 or v > HatWidth-1 or h < 0 or h > HatWidth-1:
    BoundaryHit = 1
  return BoundaryHit;



def ShowScrollingBanner(TheMessage,r,g,b,ScrollSpeed):
  TheMessage = TheMessage.upper()
  TheBanner = CreateBannerSprite(TheMessage)
  TheBanner.r = r 
  TheBanner.g = g 
  TheBanner.b = b 
  TheBanner.ScrollAcrossScreen(HatWidth-1,1,"left",ScrollSpeed)



DigitList = []
#0
DigitList.append([1,1,1, 
                  1,0,1,
                  1,0,1,
                  1,0,1,
                  1,1,1])
#1
DigitList.append([0,0,1, 
                  0,0,1,
                  0,0,1,
                  0,0,1,
                  0,0,1])
#2
DigitList.append([1,1,1, 
                  0,0,1,
                  1,1,1,
                  1,0,0,
                  1,1,1])
#3
DigitList.append([1,1,1, 
                  0,0,1,
                  0,1,1,
                  0,0,1,
                  1,1,1])
#4
DigitList.append([1,0,1, 
                  1,0,1,
                  1,1,1,
                  0,0,1,
                  0,0,1])
               
#5  
DigitList.append([1,1,1, 
                  1,0,0,
                  1,1,1,
                  0,0,1,
                  1,1,1])
#6
DigitList.append([1,1,1, 
                  1,0,0,
                  1,1,1,
                  1,0,1,
                  1,1,1])
#7
DigitList.append([1,1,1, 
                  0,0,1,
                  0,1,0,
                  1,0,0,
                  1,0,0])
#8  
DigitList.append([1,1,1, 
                  1,0,1,
                  1,1,1,
                  1,0,1,
                  1,1,1])
#9  
DigitList.append([1,1,1, 
                  1,0,1,
                  1,1,1,
                  0,0,1,
                  0,0,1])
                    

# List of Digit sprites
DigitSpriteList = [Sprite(3,5,100,0,0,DigitList[i]) for i in range(0,10)]


AlphaList = []
#A
AlphaList.append([0,1,1,0,0,
                  1,0,0,1,0,
                  1,1,1,1,0,
                  1,0,0,1,0,
                  1,0,0,1,0])

#B
AlphaList.append([1,1,1,0,0,
                  1,0,0,1,0,
                  1,1,1,0,0,
                  1,0,0,1,0,
                  1,1,1,0,0])
#c
AlphaList.append([0,1,1,1,0,
                  1,0,0,0,0,
                  1,0,0,0,0,
                  1,0,0,0,0,
                  0,1,1,1,0])

#D
AlphaList.append([1,1,1,0,0,
                  1,0,0,1,0,
                  1,0,0,1,0,
                  1,0,0,1,0,
                  1,1,1,0,0])

#E
AlphaList.append([1,1,1,1,0,
                  1,0,0,0,0,
                  1,1,1,0,0,
                  1,0,0,0,0,
                  1,1,1,1,0])
                  
#F
AlphaList.append([1,1,1,1,0,
                  1,0,0,0,0,
                  1,1,1,0,0,
                  1,0,0,0,0,
                  1,0,0,0,0])

#G
AlphaList.append([0,1,1,1,0,
                  1,0,0,0,0,
                  1,0,1,1,0,
                  1,0,0,1,0,
                  0,1,1,1,0])

#H
AlphaList.append([1,0,0,1,0,
                  1,0,0,1,0,
                  1,1,1,1,0,
                  1,0,0,1,0,
                  1,0,0,1,0])
#I
AlphaList.append([0,1,1,1,0,
                  0,0,1,0,0,
                  0,0,1,0,0,
                  0,0,1,0,0,
                  0,1,1,1,0])
#J
AlphaList.append([0,1,1,1,0,
                  0,0,1,0,0,
                  0,0,1,0,0,
                  1,0,1,0,0,
                  0,1,0,0,0])
                  
#K
AlphaList.append([1,0,0,1,0,
                  1,0,1,0,0,
                  1,1,0,0,0,
                  1,0,1,0,0,
                  1,0,0,1,0])
#L
AlphaList.append([0,1,0,0,0,
                  0,1,0,0,0,
                  0,1,0,0,0,
                  0,1,0,0,0,
                  0,1,1,1,0])

#M
AlphaList.append([1,0,0,0,1,
                  1,1,0,1,1,
                  1,0,1,0,1,
                  1,0,0,0,1,
                  1,0,0,0,1])

#N
AlphaList.append([1,0,0,0,1,
                  1,1,0,0,1,
                  1,0,1,0,1,
                  1,0,0,1,1,
                  1,0,0,0,1])
#O
AlphaList.append([0,1,1,0,0,
                  1,0,0,1,0,
                  1,0,0,1,0,
                  1,0,0,1,0,
                  0,1,1,0,0])
#P
AlphaList.append([1,1,1,0,0,
                  1,0,0,1,0,
                  1,1,1,0,0,
                  1,0,0,0,0,
                  1,0,0,0,0])
#Q
AlphaList.append([0,1,1,1,0,
                  1,0,0,0,1,
                  1,0,0,0,1,
                  1,0,0,1,0,
                  0,1,1,0,1])
#R 
AlphaList.append([1,1,1,0,0,
                  1,0,0,1,0,
                  1,1,1,0,0,
                  1,0,1,0,0,
                  1,0,0,1,0])
#S
AlphaList.append([0,1,1,1,0,
                  1,0,0,0,0,
                  0,1,1,0,0,
                  0,0,0,1,0,
                  1,1,1,0,0])
#T
AlphaList.append([0,1,1,1,0,
                  0,0,1,0,0,
                  0,0,1,0,0,
                  0,0,1,0,0,
                  0,0,1,0,0])
#U
AlphaList.append([1,0,0,1,0,
                  1,0,0,1,0,
                  1,0,0,1,0,
                  1,0,0,1,0,
                  0,1,1,0,0])
#V
AlphaList.append([1,0,0,0,1,
                  1,0,0,0,1,
                  0,1,0,1,0,
                  0,1,0,1,0,
                  0,0,1,0,0])
#W
AlphaList.append([1,0,0,0,1,
                  1,0,0,0,1,
                  1,0,1,0,1,
                  0,1,0,1,0,
                  0,1,0,1,0])
#X
AlphaList.append([1,0,0,0,1,
                  0,1,0,1,0,
                  0,0,1,0,0,
                  0,1,0,1,0,
                  1,0,0,0,1])
#Y
AlphaList.append([0,1,0,1,0,
                  0,1,0,1,0,
                  0,0,1,0,0,
                  0,0,1,0,0,
                  0,0,1,0,0])
#Z
AlphaList.append([1,1,1,1,0,
                  0,0,0,1,0,
                  0,0,1,0,0,
                  0,1,0,0,0,
                  1,1,1,1,0])


                  
                  
# List of Alpha sprites
AlphaSpriteList = [Sprite(5,5,100,100,100,AlphaList[i]) for i in range(0,26)]



                  
                  
#space                  
SpaceSprite = Sprite(
  3,
  5,
  0,
  0,
  0,
  [0,0,0,
   0,0,0,
   0,0,0,
   0,0,0,
   0,0,0]
)

#Exclamation
ExclamationSprite = Sprite(
  3,
  5,
  0,
  0,
  0,
  [0,1,0,
   0,1,0,
   0,1,0,
   0,0,0,
   0,1,0]
)

#Period
PeriodSprite = Sprite(
  3,
  5,
  0,
  0,
  0,
  [0,0,0,
   0,0,0,
   0,0,0,
   0,0,0,
   0,1,0]
)




#QuestionMark
QuestionMarkSprite = Sprite(
  5,
  5,
  0,
  0,
  0,
  [0,0,1,1,0,
   0,0,0,1,0,
   0,0,1,1,0,
   0,0,0,0,0,
   0,0,1,0,0]
)


#PoundSignSprite
PoundSignSprite = Sprite(
  5,
  5,
  0,
  0,
  0,
  [0,1,0,1,0,
   1,1,1,1,1,
   0,1,0,1,0,
   1,1,1,1,1,
   0,1,0,1,0]
)



def TrimSprite(Sprite1):
  height       = Sprite1.height
  width        = Sprite1.width
  newwidth     = 0
  elements     = height * width
  Empty        = 1
  Skipped      = 0
  EmptyColumns = []
  EmptyCount   = 0
  BufferX      = 0
  BufferColumn = [(0) for i in range(height)]
  
  i = 0
  x = 0
  y = 0

  
  for x in range (0,width):
    
    #Find empty columns, add them to a list
    Empty = 1  
    for y in range (0,height):
      i = x + (y * width)
      
      BufferColumn[y] = Sprite1.grid[i]
      if (Sprite1.grid[i] <> 0):
        Empty = 0
    
    if (Empty == 0):
      newwidth =  newwidth + 1
    
    elif (Empty == 1):
      #print ("Found empty column: ",x)
      EmptyColumns.append(x)
      EmptyCount = EmptyCount +1

      
  BufferSprite = Sprite(
    newwidth,
    height,
    Sprite1.r,
    Sprite1.g,
    Sprite1.b,
    [0]*(newwidth*height)
    )
      
  #Now that we identified the empty columns, copy data and skip those columns
  for x in range (0,width):
    Skipped = 0
    
    for y in range (0,height):
      i = x + (y * width)
      b = BufferX + (y * newwidth)
      if (x in EmptyColumns):
        Skipped = 1
      else:
        BufferSprite.grid[b] = Sprite1.grid[i]
    
    
    #advance our Buffer column counter only if we skipped a column
    if (Skipped == 0):
      BufferX = BufferX + 1
    
    
  
  BufferSprite.width = newwidth
  
  
  
  #print (BufferSprite.grid)
  return BufferSprite



def LeftTrimSprite(Sprite1,Columns):
  height       = Sprite1.height
  width        = Sprite1.width
  newwidth     = 0
  elements     = height * width
  Empty        = 1
  Skipped      = 0
  EmptyColumns = []
  EmptyCount   = 0
  BufferX      = 0
  BufferColumn = [(0) for i in range(height)]
  
  i = 0
  x = 0
  y = 0

  
  for x in range (0,width):
    
    #Find empty columns, add them to a list
    Empty = 1  
    for y in range (0,height):
      i = x + (y * width)
      
      BufferColumn[y] = Sprite1.grid[i]
      if (Sprite1.grid[i] <> 0):
        Empty = 0
    
    if (Empty == 0 or EmptyCount > Columns):
      newwidth =  newwidth + 1
    
    elif (Empty == 1):
      #print ("Found empty column: ",x)
      EmptyColumns.append(x)
      EmptyCount = EmptyCount +1

      
  BufferSprite = Sprite(
    newwidth,
    height,
    Sprite1.r,
    Sprite1.g,
    Sprite1.b,
    [0]*(newwidth*height)
    )
      
  #Now that we identified the empty columns, copy data and skip those columns
  for x in range (0,width):
    Skipped = 0
    
    for y in range (0,height):
      i = x + (y * width)
      b = BufferX + (y * newwidth)
      if (x in EmptyColumns):
        Skipped = 1
      else:
        BufferSprite.grid[b] = Sprite1.grid[i]
    
    
    #advance our Buffer column counter only if we skipped a column
    if (Skipped == 0):
      BufferX = BufferX + 1
    
    
  
  BufferSprite.width = newwidth
  
  
  
  #print (BufferSprite.grid)
  return BufferSprite
    
    
    
    

  
  
def CreateShortWordSprite(ShortWord):   

  ShortWord = ShortWord.upper()
  TheBanner = CreateBannerSprite(ShortWord)
      

  TheBanner.r = SDMedRedR
  TheBanner.g = SDMedRedG
  TheBanner.b = SDMedRedB
  
  
  #add variables to the object (python allows this, very cool!)
  TheBanner.h = (HatWidth - TheBanner.width) / 2
  TheBanner.v = -4
  TheBanner.rgb = (SDMedGreenR,SDMedGreenG,SDMedGreenB)

  #used for displaying clock
  TheBanner.StartTime = time.time()

  #used for scrolling clock
  TheBanner.PauseStartTime = time.time()
  TheBanner.IsScrolling     = 0
  TheBanner.Delay           = 2
  TheBanner.PausePositionV  = 1
  TheBanner.PauseTimerOn    = 0
  
  TheBanner.on = 1
  TheBanner.DirectionIncrement = 1

  
  return TheBanner 



def ShowShortMessage(RaceWorld,PlayerCar,ShortMessage):
  moves = 1
  ShortMessageSprite    = CreateShortMessageSprite(ShortMessage)
  ShortMessageSprite.on = 1
  while (ShortMessageSprite.on == 1):
    RaceWorld.DisplayWindowWithSprite(PlayerCar.h-7,PlayerCar.v-7,ShortMessageSprite)
    MoveMessageSprite(moves,ShortMessageSprite)
    moves = moves + 1
    print ("Message On")
    
  ShortMessageSprite.on = 0








#------------------------------------------------------------------------------
# COLORS                                                                     --
#------------------------------------------------------------------------------


#Custom Colors because we will be running at full brightness

#HighRed
SDHighRedR = 255
SDHighRedG = 0
SDHighRedB = 0

#MedRed
SDMedRedR = 175
SDMedRedG = 0
SDMedRedB = 0

#LowRed
SDLowRedR = 100
SDLowRedG = 0
SDLowRedB = 0

#DarkRed
SDDarkRedR = 45
SDDarkRedG = 0
SDDarkRedB = 0


#HighOrange
SDHighOrangeR = 255
SDHighOrangeG = 128
SDHighOrangeB = 0

#MedOrange
SDMedOrangeR = 200
SDMedOrangeG = 100
SDMedOrangeB = 0

#LowOrange
SDLowOrangeR = 155
SDLowOrangeG = 75
SDLowOrangeB = 0

#DarkOrange
SDDarkOrangeR = 100
SDDarkOrangeG = 45
SDDarkOrangeB = 0



#SDHighPurple
SDHighPurpleR = 230
SDHighPurpleG = 0
SDHighPurpleB = 255

#MedPurple
SDMedPurpleR = 105
SDMedPurpleG = 0
SDMedPurpleB = 155

#SDLowPurple
SDLowPurpleR = 75
SDLowPurpleG = 0
SDLowPurpleB = 120


#SDDarkPurple
SDDarkPurpleR = 45
SDDarkPurpleG = 0
SDDarkPurpleB = 45



#HighGreen
SDHighGreenR = 0
SDHighGreenG = 255
SDHighGreenB = 0

#MedGreen
SDMedGreenR = 0
SDMedGreenG = 200
SDMedGreenB = 0

#LowGreen
SDLowGreenR = 0
SDLowGreenG = 100
SDLowGreenB = 0

#DarkGreen
SDDarkGreenR = 0
SDDarkGreenG = 45
SDDarkGreenB = 0


#HighBlue
SDHighBlueR = 0
SDHighBlueG = 0
SDHighBlueB = 255


#MedBlue
SDMedBlueR = 0
SDMedBlueG = 0
SDMedBlueB = 175

#LowBlue
SDLowBlueR = 0
SDLowBlueG = 0
SDLowBlueB = 100

#DarkBlue
SDDarkBlueR = 0
SDDarkBlueG = 0
SDDarkBlueB = 45


#WhiteMax
SDMaxWhiteR = 255
SDMaxWhiteG = 255
SDMaxWhiteB = 255

#WhiteHigh
SDHighWhiteR = 255
SDHighWhiteG = 255
SDHighWhiteB = 255

#WhiteMed
SDMedWhiteR = 150
SDMedWhiteG = 150
SDMedWhiteB = 150

#WhiteLow
SDLowWhiteR = 100
SDLowWhiteG = 100
SDLowWhiteB = 100

#WhiteDark
SDDarkWhiteR = 45
SDDarkWhiteG = 45
SDDarkWhiteB = 45



#YellowMax
SDMaxYellowR = 255
SDMaxYellowG = 255
SDMaxYellowB = 0


#YellowHigh
SDHighYellowR = 200
SDHighYellowG = 200
SDHighYellowB = 0

#YellowMed
SDMedYellowR = 150
SDMedYellowG = 150
SDMedYellowB = 0

#YellowLow
SDLowYellowR = 100
SDLowYellowG = 100
SDLowYellowB = 0


#YellowDark
SDDarkYellowR = 55
SDDarkYellowG = 55
SDDarkYellowB = 0


#Pink
SDMaxPinkR = 155
SDMaxPinkG = 0
SDMaxPinkB = 130

SDHighPinkR = 130
SDHighPinkG = 0
SDHighPinkB = 105

SDMedPinkR = 100
SDMedPinkG = 0
SDMedPinkB = 75

SDLowPinkR = 75
SDLowPinkG = 0
SDLowPinkB = 50

SDDarkPinkR = 45
SDDarkPinkG = 0
SDDarkPinkB = 50




ColorList = []
ColorList.append((0,0,0))
# 1 2 3 4
ColorList.append((SDDarkWhiteR,SDDarkWhiteG,SDDarkWhiteB))
ColorList.append((SDLowWhiteR,SDLowWhiteG,SDLowWhiteB))
ColorList.append((SDMedWhiteR,SDMedWhiteG,SDMedWhiteB))
ColorList.append((SDHighWhiteR,SDHighWhiteG,SDHighWhiteB))

# 5 6 7 8
ColorList.append((SDDarkRedR,SDDarkRedG,SDDarkRedB))
ColorList.append((SDLowRedR,SDLowRedG,SDLowRedB))
ColorList.append((SDMedRedR,SDMedRedG,SDMedRedB))
ColorList.append((SDHighRedR,SDHighRedG,SDHighRedB))

# 9 10 11 12
ColorList.append((SDDarkGreenR,SDDarkGreenG,SDDarkGreenB))
ColorList.append((SDLowGreenR,SDLowGreenG,SDLowGreenB))
ColorList.append((SDMedGreenR,SDMedGreenG,SDMedGreenB))
ColorList.append((SDHighGreenR,SDHighGreenG,SDHighGreenB))

# 13 14 15 16
ColorList.append((SDDarkBlueR,SDDarkBlueG,SDDarkBlueB))
ColorList.append((SDLowBlueR,SDLowBlueG,SDLowBlueB))
ColorList.append((SDMedBlueR,SDMedBlueG,SDMedBlueB))
ColorList.append((SDHighBlueR,SDHighBlueG,SDHighBlueB))

# 17 18 19 20
ColorList.append((SDDarkOrangeR,SDDarkOrangeG,SDDarkOrangeB))
ColorList.append((SDLowOrangeR,SDLowOrangeG,SDLowOrangeB))
ColorList.append((SDMedOrangeR,SDMedOrangeG,SDMedOrangeB))
ColorList.append((SDHighOrangeR,SDHighOrangeG,SDHighOrangeB))

# 21 22 23 24
ColorList.append((SDDarkYellowR,SDDarkYellowG,SDDarkYellowB))
ColorList.append((SDLowYellowR,SDLowYellowG,SDLowYellowB))
ColorList.append((SDMedYellowR,SDMedYellowG,SDMedYellowB))
ColorList.append((SDHighYellowR,SDHighYellowG,SDHighYellowB))

# 25 26 27 28
ColorList.append((SDDarkPurpleR,SDDarkPurpleG,SDDarkPurpleB))
ColorList.append((SDLowPurpleR,SDLowPurpleG,SDLowPurpleB))
ColorList.append((SDMedPurpleR,SDMedPurpleG,SDMedPurpleB))
ColorList.append((SDHighPurpleR,SDHighPurpleG,SDHighPurpleB))

# 29 30 31 32 33
ColorList.append((SDDarkPinkR,SDDarkPinkG,SDDarkPinkB))
ColorList.append((SDLowPinkR,SDLowPinkG,SDLowPinkB))
ColorList.append((SDMedPinkR,SDMedPinkG,SDMedPinkB))
ColorList.append((SDHighPinkR,SDHighPinkG,SDHighPinkB))
ColorList.append((SDMaxPinkR,SDMaxPinkG,SDMaxPinkB))


#ColorList.append((SDDarkR,SDDarkG,SDDarkB))
#ColorList.append((SDLowR,SDLowG,SDLowB))
#ColorList.append((SDMedR,SDMedG,SDMedB))
#ColorList.append((SDHighR,SDHighG,SDHighB))









