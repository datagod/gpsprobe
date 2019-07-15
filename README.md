<PRE>
   ____ ____  ____  ____  ____   ___  ____  _____                 
  / ___|  _ \/ ___||  _ \|  _ \ / _ \| __ )| ____|                          
 | |  _| |_) \___ \| |_) | |_) | | | |  _ \|  _|                            
 | |_| |  __/ ___) |  __/|  _ <| |_| | |_) | |___                           
  \____|_|   |____/|_|   |_| \_\\___/|____/|_____|                          
 </PRE>                                                                            



![Raspberry Pi Buildout](https://github.com/datagod/gpsprobe/blob/master/GPSProbe%20Pi3.jpg)

An example of GPSProbe running on a Raspberry Pi3 with an external Wifi antenna, GPS, and a Unicornhat HD display.

  A passive surveillance tool that tracks wifi enabled devices nearby,      
  GPSProbe records the MAC addresses, GPS co-ordinates and other pertinent  
  information.  This tool pairs nicely with security cameras to provide     
  evidence of who or what was visiting your property uninvited.             
                                                                            
  Features:                                                                 
  - record MAC address, time of day, signal strength, vendor, etc.           
  - can assign a friendly name to previously recognized MAC addresses        
  - optional tracking of GPS co-ordinates                                   
  - tracks routers as well as mobile devices                                
                                                                            
  Optional Unicorn hat HD display                                          
  - leverages code from Arcade Retro Clock to display device counts,        
    signal counts, and packet counts                                        
                                                                            
                                                                            
  Special Thanks:                                                           
  - This project started off as a fork of probemon.  I added the ability    
    to capture GPS co-ordinates to the capture file.                        
    https://github.com/nikharris0/probemon                                  
                                                                            
  - Arcade Retro Clock HD has not been released as of July 2019 but I have  
    included some functions and objects required to display scrolling       
    alphanumerics and strength bars.                                        
    https://github.com/datagod/Arcade-Retro-Clock                                                                      
                                                                            
  - GPS polling code and thread spawning code was borrowed from another     
    project that I have since lost track.  I will certainly give them       
    full credit when I track them down                                     

