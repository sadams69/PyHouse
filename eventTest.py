#!/usr/bin/env python
#
# 
#
"""
HousePi automation program.

Program intended for use with the Raspberry pi computer.

Commands
    xsend A-1-On                -- Send X10 Command
    isend 29-9E-2D off-fast     -- Send Insteon Command
    listen N                    -- Listen for sensors for X seconds  
"""
import errno
import glob
import optparse
import os
import serial
import socket
import sys
import time
from time import localtime,strftime, sleep
from string import Template
#from code import interact; interact()


# Define Globals
__version__ = '0.2'


AllTimers  =       [    { 'Who' : 'Garage Front'      ,    'TurnOn' : 12+4, 'TurnOff' : 12+10, 'Style' : []},
                          { 'Who' : 'Garage Front'      ,    'TurnOn' : 5.5, 'TurnOff' : 6.25, 'Style' : []},
                          {  'Who' :'Living Room'       , 'TurnOn' : 12+4, 'TurnOff' : 12+9, 'Style' : []}
                      ]

# Class deinitions
class Light():
    def __init__(self, name = 'bob', address = '123'):
        self.address = address
        self.name = name
        self.intensity = 0
    
    def LightOn(self):
        self.intensity = 100
        print "Light: %s, on, %d" % (self.name, self.intensity)
        
    def LightOff(self):
        self.intensity = 0
        print "Light: %s, off, %d" % (self.name, self.intensity)

    def LightDim(self):
        self.intensity -= 10
        if (self.intensity<0):
            self.intensity = 0
        print "Light: %s, off, %d" % (self.name, self.intensity)

    def LightBright(self):
        self.intensity += 10
        if (self.intensity>100):
            self.intensity = 100
        print "Light: %s, off, %d" % (self.name, self.intensity)
    
    
    
class Event():
    def __init__(self, ain):
        
        if (ain['Type']=='Timer'):
            aLight = ain['LightLookup'][ain['
                Type = 'Timer',
                 Source = '',
                 Persistence = True,
                 TerminationCriteria = False,
                 ActionCriteria = 'Between',
                 CloseCriteria = True,
                 TurnOn = 0,
                 TurnOff = 0,
                 CloseAction = [],
                 Action = [], 
                 ActionArgs = [],
                 Style = [],
                 Ack = 'NAK'):
        self.Type = Type
        self.Source = Source
        self.Persistence = Persistence
        self.Who = Who
        self.TurnOn = TurnOn
        self.TurnOff = TurnOff
        self.Style = Style
        self.Ack = Ack

        self.counter = 0
    
    def Between(self):
        tc = current_time()
        if (self.t1 < tc and self.t2 > tc):
            return True
        else:
            return False
                
    def terminate(self):
        if (self.counter>8):
            self.Ack = 'Ack'
            return(True)
        else:
            return(False)
    
    def increment(self):
        self.counter+=1
    
    def onclose(self):
        print "Closing up shop"
        #print "Length Eventlist: ", len(Events)
        self.children = Event()
        
    def action(self):
        self.increment()
        print "Acting: ",self.counter

    def done(self):
        if (self.counter>4):
            return(True)
        else:
            return(False)
            
def EventList(Timers = AllTimers):
    Events = []
    Index = 0
    for ii in range(len(Timers)):
        aTimer = Timers[ii]
        Events.append(Event(**aTimer))

    return(Events)


def main():
                                                # Generate the event list frotm the HouseDefinition module      
    Events = EventList()
    L1 = Light(name = 'fred', address = '456')
    L2 = Light(name = 'jane', address = '987')
    L = [L1, L2]
    
    print "Length Eventlist: ", len(Events)
    
    E = Event()
    while(True):
        if(E.terminate()):
            break
        else:
            E.action()
            if (E.done()):
                print "Call closing action"
                E.onclose()
                break
    E.Ack = 'Ack'
    print "All done"
    
    Events.append(E.children)
    print "Length Eventlist: ", len(Events)
            
    
  
if __name__ == '__main__':
    try:
        main()
    except:
        print 'FATAL ERROR: ' 
        sys.exit(99)
