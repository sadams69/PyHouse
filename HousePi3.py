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
import myX10Serial
import ic
import HouseDefinition3 as HouseDefinition
import SendGmail
#from code import interact; interact()


# Define Globals
__version__ = '0.2'

DebugFlag = HouseDefinition.DebugFlag
TestTime = 0

# Class deinitions

class Event():
    def __init__(self,
                Type = 'Timer',
                 Source = '',
                Persistence = True,
                 Who = '',
                 TurnOn = 0,
                 TurnOff = 0,
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

def EventList(Timers = HouseDefinition.Timers):
    Events = []
    Index = 0
    for ii in range(len(Timers)):
        aTimer = Timers[ii]
        Events.append(Event(**aTimer))

    return(Events)

def EventsLog(Events, comm):

    ct = CurrentTime()
    print 'Current Time: %6.3f' % ct
    textout = '\nType\tSource\tPersist\tWho\t\tt1\tt2\tAck'
    comm.logger(textout)
    print '%s' % textout
    
    for ii in range(len(Events)):
        aEvent = Events[ii]
        textout = '%s\t%s\t%d\t%s\t%5.2f\t%5.2f\t%s\n' % (aEvent.Type,
                                                          aEvent.Source,
                                                          aEvent.Persistence,
                                                          aEvent.Who,
                                                          aEvent.TurnOn,
                                                          aEvent.TurnOff,
                                                          aEvent.Ack)
        comm.logger(textout)
        print '%s' % textout
    
    return(Events)

def CheckEvents(Events, L, comm, LightLookUp):
    ''' Mark all of the lights that are on as "marked"
    Scan through the events to acknowledge and events within the on/off times.
    Turning on a light does something if it is off.
    Turning on a marked light will just reset the status to on
    '''

    for Li in L:
        if (Li.Status == 'On'):
            Li.Status = 'Marked'
            
    for aEvent in Events:
        CT = CurrentTime()
        if (aEvent.TurnOn<= CT and CT <= aEvent.TurnOff):
            if (aEvent.Type == 'Timer'):
                aEvent.Ack = 'Ack'
                L[LightLookUp[aEvent.Who]].SetMood(aEvent.Style)
                L[LightLookUp[aEvent.Who]].LightOn(comm)
            elif (aEvent.Type == 'SensorAction' or aEvent.Type == 'DoorAction'):
                aEvent.Ack = 'Ack'
                L[LightLookUp[aEvent.Who]].SetMood(aEvent.Style)
                L[LightLookUp[aEvent.Who]].LightOn(comm)
            elif (aEvent.Type == 'Off' and aEvent.Ack == 'NAK'):
                aEvent.Ack = 'Ack'
                L[LightLookUp[aEvent.Who]].SetMood(aEvent.Style)
                L[LightLookUp[aEvent.Who]].LightOff(comm, True) # force == True
            elif (aEvent.Type == 'Blink' and aEvent.Ack == 'NAK'):
                aEvent.Ack = 'Ack'
                if (L[LightLookUp[aEvent.Who]].Status == 'On'):
                    L[LightLookUp[aEvent.Who]].SetMood(aEvent.Style)
                    L[LightLookUp[aEvent.Who]].LightOff(comm)
                    sleep(0.5)
                    L[LightLookUp[aEvent.Who]].LightOn(comm)
                else:
                    L[LightLookUp[aEvent.Who]].SetMood(aEvent.Style)
                    L[LightLookUp[aEvent.Who]].LightOn(comm)
                    sleep(0.5)
                    L[LightLookUp[aEvent.Who]].LightOff(comm)
        elif (CT > aEvent.TurnOff or CT < aEvent.TurnOn): 
            if (aEvent.Persistence == True):
                aEvent.Ack = 'NAK' # NAK any timers that are out of the on/off time

    # Has the temporary event expired?
    for i in range(len(Events)-1,-1,-1):
        if (Events[i].Persistence == False and Events[i].Ack == 'Ack' and (CT > Events[i].TurnOff or CT < Events[i].TurnOn)):
            Events.pop(i)

    # Turn off all of the lights that were marked and on, but no event continued that on status
    for Li in L:
        if (Li.Status == 'Marked'):
            EventsLog(Events, comm)
            Li.LightOff(comm)

        
        
class Light():
    def __init__(self,
                 Name           = 'A1',
                 LightType      = 'Insteon',
                 X10Light       = [],
                 InstLight      = []):
        #         X10Light       = myX10Serial.X10(),
        #         InstLight      = ic.InsteonLight()):
        self.Alias          = Name
        self.LightType      = LightType
        self.X10Light       = X10Light
        self.InstLight      = InstLight
        self.Status         = 'Off' # (On, Off, Marked - to be turned off if no event sustains the On)

                      
    def LightStatus(self, comm):
        to_poll = [comm.parse_addr(self.InstLight.Address)]
        print to_poll
        
        failed = False
        for addr in to_poll:
            result = comm.send_insteon_direct(addr, 0x19, 0x00, 
                                              error_ok=True, ack_data=True)
            if result is None:
                failed = True
                result_s = 'TIMEOUT'
            elif result is False:
                failed = True
                result_s = 'NAK'
            else:
                self.InstLight.Intensity = result[1]
                result_s = "%1.f%% (0x%02X)" % (
                    result[1] * 100.0 / 255, result[1])

    def SetMood(self, NewMood):
        if (NewMood==[]):
            NewMood = ['OnFast',0,0]
            
        self.InstLight.Style = NewMood
        
    def LightMood(self, comm, intensity):

        if (self.InstLight.Intensity > intensity):
            command = 'dim'
        else:
            command = 'brighten'
        
        args = ['repsend',
                self.InstLight.Address,
                command,
                abs(int((self.InstLight.Intensity - intensity)/8))+1,
                self.InstLight.Style[2]]
        addr = comm.parse_addr(args[1])       
        cmd = comm.parse_bytes(ic.ALIASES_COMMAND.get(args[2], args[2]), 2,
                               what='command')
        
        count = int(args[3])
        print "Intensity %d" % self.InstLight.Intensity
        print "Intensity Target %d" % intensity
        print "count: %d" % count
        
        if len(args) > 4:
            delay = float(args[4])
        else:
            delay = 0.5
        
        for step in range(1, count+1):
            res = comm.send_insteon_direct(addr, cmd[0], cmd[1], 
                                           error_ok=True, ack_data=True)
            if res is None:
                print 'Step %d: NO-RESPONSE' % step
                #return 1
            elif res is False:
                print 'Step %d: NAK' % step
                #return 2
            else:
                print 'Step %d: ACK %s' % (step, comm.format_bytes(res))
            comm.listen_for(delay)
            
    def LightOn(self, comm, force = False):
        if (self.Status == 'Off' or force): 
            if (self.LightType == 'X10'):
                textout =  Template('''Turn on $Alias: $House$Unit'''
                               ).substitute(dict(Alias = self.Alias, House = self.X10Light.House, Unit = self.X10Light.Unit))
                print textout
                comm.logger(textout)
                
                self.X10Light.Command = 'On'
                self.X10Light.Send(comm.ser)
                msg = comm._read_packet(timeout=5)
                if msg != []:
                    print comm.format_rxpacket(msg)
                sleep(0.5)
                self.X10Light.Send(comm.ser)
                msg = comm._read_packet(timeout=5)
                if msg != []:
                    print comm.format_rxpacket(msg)
                #sleep(1)
                
            elif (self.LightType == 'Insteon'):
                if (self.InstLight.Style[0] == 'Mood'):
                    self.LightStatus(comm)
                    if (self.InstLight.Intensity):
                        textout = "Leaving alone: Light Status: %d" % self.InstLight.Intensity
                        print textout
                        comm.logger(textout)
                        
                    else: #If off, set to the appropriate level
                        intensity = self.InstLight.Style[1]
                        self.LightMood(comm,intensity)
                else:
                    args = ['isend', self.InstLight.Address,'on-fast']
                    addr = comm.parse_addr(args[1])
                    cmd = comm.parse_bytes(ic.ALIASES_COMMAND.get(args[2], args[2]), 2,
                                       what='command')
                    res = comm.send_insteon_direct(addr, cmd[0], cmd[1], 
                                               error_ok=True, ack_data=True)
                    if res is None:
                        print 'NO-RESPONSE'
                        return 1
                    elif res is False:
                        print 'NAK'
                        return 2
                    else:
                        print 'ACK %s' % comm.format_bytes(res)

                    print "turn insteon light on"
            self.Status = 'On'
        elif (self.Status == 'Marked'):
            self.Status = 'On'
            
    def LightOff(self, comm, force=False):
        if (self.Status == 'On' or self.Status == 'Marked' or force):
            if (self.LightType == 'X10'):
                textout =  Template('''Turn off $Alias: $House$Unit'''
                           ).substitute(dict(Alias = self.Alias, House = self.X10Light.House, Unit = self.X10Light.Unit))
                print textout
                comm.logger(textout)

                self.X10Light.Command = 'Off'
                self.X10Light.Send(comm.ser)
                msg = comm._read_packet(timeout=5)
                if msg != []:
                    print comm.format_rxpacket(msg)
                sleep(0.5)
                self.X10Light.Send(comm.ser)
                msg = comm._read_packet(timeout=5)
                if msg != []:
                    print comm.format_rxpacket(msg)
                #sleep(1)
                
            elif (self.LightType == 'Insteon'):
                if (self.InstLight.Style[0] == 'Mood'):
                    self.LightStatus(comm)
                    if (not self.InstLight.Intensity):
                        print "Leaving alone: Light Status: %d" % self.InstLight.Intensity
                        textout = "Leaving alone: Light Status: %d" % self.InstLight.Intensity
                        print textout
                    else: #If on, set to zero
                        intensity = 0
                        self.LightMood(comm,intensity)
                else:
                    args = ['isend', self.InstLight.Address, 'off-fast']
                    addr = comm.parse_addr(args[1])
                    cmd = comm.parse_bytes(ic.ALIASES_COMMAND.get(args[2], args[2]), 2,
                                       what='command')
                    res = comm.send_insteon_direct(addr, cmd[0], cmd[1], 
                                               error_ok=True, ack_data=True)
                    if res is None:
                        print 'NO-RESPONSE'
                        return 1
                    elif res is False:
                        print 'NAK'
                        return 2
                    else:
                        print 'ACK %s' % comm.format_bytes(res)

                print "turn insteon light off"

            self.Status = 'Off'
        
          

# Procedures
def StringOfLights(Aliases, LightType, Lights = []):
    
    for alias in Aliases.keys():
        Parms = Aliases[alias]
        X10Light       = myX10Serial.X10()
        InstLight      = ic.InsteonLight()

        if (LightType == 'X10'):
            #X10Light.update(Aliases[alias])
            X10Light.House = Aliases[alias]['House']
            X10Light.Unit = Aliases[alias]['Unit']
            
        elif (LightType == 'Insteon'):
            #InstLight.update(Aliases[alias])
            InstLight.Address = Aliases[alias]
            
        Lights.append(Light(Name = alias,
                            X10Light = X10Light,
                            InstLight = InstLight,
                            LightType = LightType))
    return Lights

def CycleLights(Lights, comm):
    for L in Lights:
        print "cycling: %s" % L.Alias
        L.LightOn(comm)
        sleep(0.5)
        L.LightOff(comm)
        sleep(0.5)

def CurrentTime():
    global DebugFlag, TestTime

    if DebugFlag:
        myTime = TestTime
    else:
        LocalTime   = localtime()
        Hour        = LocalTime[3]*1.0
        Minute      = LocalTime[4]*1.0
        Second      = LocalTime[5]*1.0
        myTime    = Hour+Minute/60.0+Second/(60*60)
    return myTime

def SensorWatch(L, comm, LightLookUp):
    SensorEvents = []
    sensor_watch_timeout = 4
    msg = comm._read_packet(timeout=sensor_watch_timeout)
    if msg != []:
        print comm.format_rxpacket(msg)
        msg = comm._read_packet(timeout=sensor_watch_timeout)
        if msg != []:
            print comm.format_rxpacket(msg)
    if (comm.X10.Command == 'on'):
        textout= "Sensor: %c-%d -> on" % (comm.X10.House, comm.X10.Unit)
        print textout
        comm.logger(textout)
        # Find the sensor that the X10 command signifies
        for sa in HouseDefinition.SensorAliases:
            print sa, comm.X10.House, comm.X10.Unit,HouseDefinition.SensorAliases[sa]['House'], HouseDefinition.SensorAliases[sa]['Unit']
            if (comm.X10.House == HouseDefinition.SensorAliases[sa]['House'] and
                comm.X10.Unit == HouseDefinition.SensorAliases[sa]['Unit']):
                ct = CurrentTime()
                print "Found action definition for ", sa
                # Once you have the sensor alias, scan through the sensors and the lights to act on
                
                for SensorInfo in HouseDefinition.Sensors:
                    if (SensorInfo['Source'] == sa):
                        for Whoi in SensorInfo['Who']: # May be multiple outputs
                            SensorEvents.append(Event(Type = 'SensorAction',
                                                Source = sa,
                                                Persistence = False,
                                                Who = Whoi,
                                                TurnOn = ct-0.01,
                                                TurnOff = ct + SensorInfo['When'][2],
                                                Style = SensorInfo['Style']))
                        textout = "Creating Sensor Events %s, %f, %f" % (SensorInfo['Who'], ct, ct + SensorInfo['When'][2] )
                        print textout
                        comm.logger(textout)
                                            
        comm.X10.Command = 'Ack'
    return SensorEvents

def SwitchCondense(SwitchEvents):
    condensed = [SwitchEvents[0]]
    for i in range(1,len(SwitchEvents)):
        if (condensed[-1].Address == SwitchEvents[i].Address and
            condensed[-1].Command == SwitchEvents[i].Command):
            pass
        else:
            condensed.append(SwitchEvents[i])

    return condensed
            
def SwitchWatch(comm):
    SensorEvents = []
    # Append comm.SwitchEvents
    if (len(comm.SwitchEvents) > 0):
        print 'Found some events: %d' % len(comm.SwitchEvents)
        condensed = SwitchCondense(comm.SwitchEvents)
        print 'Found some events: %d' % len(condensed)
        
        for sEvent in condensed:
            if (sEvent.Command == 'Open'):
                sa = sEvent.Address

                # Take care of any light timmer events
                for SensorInfo in HouseDefinition.Sensors:
                    if (SensorInfo['Source'] == sa):
                        for Whoi in SensorInfo['Who']: # May be multiple outputs
                            ct = CurrentTime()
                            SensorEvents.append(Event(Type = 'DoorAction',
                                                Source = sa,
                                                Persistence = False,
                                                Who = Whoi,
                                                TurnOn = ct-0.01,
                                                TurnOff = ct + SensorInfo['When'][2],
                                                Style = SensorInfo['Style']))
                        textout = "Creating Sensor Events %s, %f, %f" % (SensorInfo['Who'], ct, ct + SensorInfo['When'][2] )
                        print textout
                        comm.logger(textout)


                # Take care of any email events
                for SensorInfo in HouseDefinition.EmailAlerts:
                    if (SensorInfo['Source'] == sa):
                        for Whoi in SensorInfo['Who']: # May be multiple outputs
                            ct = CurrentTime()
                            textout = "Email alert %s: Opened, %5.2f" % (sa, ct)
                            try:
                                SendGmail.Send(textout, Whoi)
                            except:
                                comm.logger('Problem sending email.')
                                
                        print textout
                        comm.logger(textout)
               
        comm.SwitchEvents = []

    return SensorEvents

def SensorLightLookUp(L):
    LookUp = {}
    for x in range(0,len(L)):
        print L[x].Alias, x
        LookUp[L[x].Alias] = x
    return LookUp

def main():
    global DebugFlag, TestTime
    parser = optparse.OptionParser(
        usage='%prog [options] command [args]',
        description=__doc__, version=__version__)
    parser.format_description = lambda _: parser.description.lstrip()

    parser.add_option('-D', '--device', metavar='FNAME',
                      help='Serial port to use')
    parser.add_option('--lock-port', metavar='NUM', type='int',
                      help='TCP port used to make sure only once instance'
                      'of this programm is running. 0 to disable.')
    parser.add_option('-x', '--xsend', action='store_true',
                      help='Send x10 command')
    parser.add_option('-t', '--test', action='store_true',
                      help='Print more info')
    parser.add_option('-o', '--operate', action='store_true',
                      help='Print more info')
    parser.add_option('-v', '--verbose', action='store_true',
                      help='Print more info')
    parser.add_option('-r', '--retry', metavar='N', type='int', 
                      default=ic.InsteonComm.INSTEON_RETRIES,
                      help='If insteon device does not respond, retry that'
                      ' many times (default %default)')

    opts, args = parser.parse_args()

    print sys.argv
    
    if (len(sys.argv) == 1):
        args = ['operate']
        
    def make_comm():
        comm = ic.InsteonComm(device=opts.device,
                           verbose=opts.verbose,
                           lock_port=opts.lock_port)
        comm.INSTEON_RETRIES = opts.retry
        return comm
    
    comm = make_comm()

    if False:
        print "printing input arguments"
        for i in args:
            print i

    Activate    = myX10Serial.X10(House = 'A', Unit = '3', Command = 'On')
    Activate2    = myX10Serial.X10(House = 'A', Unit = '4', Command = 'On')
    Deactivate  = myX10Serial.X10(House = 'A', Unit = '3', Command = 'Off')
    L2 = [Light(LightType = 'X10', Name = 'Front', X10Light = Activate)]
    L2.append(Light(LightType = 'Insteon', Name = 'Front', InstLight = ic.InsteonLight()))
    
    
    if args[0] == 'test':
        comm.logger('Starting HousePi (test mode)')

        L = StringOfLights(HouseDefinition.InsteonAliases, 'Insteon')
        L = StringOfLights(HouseDefinition.X10Aliases, 'X10', L)
        LightLookUp = SensorLightLookUp(L)
        Events = EventList()                                            # Generate the event list frotm the HouseDefinition module      
        CycleLights(L,comm)

        TotalTime = 8.0
        while True:
            TotalTime = TotalTime + 0.5
            TestTime = TotalTime % 24
            Events.extend(SensorWatch(L, comm, LightLookUp)) # New module should append new events to the list as determined by the sensors
            CheckEvents(Events, L, comm, LightLookUp)               
            if (TotalTime>28):
                break

    if args[0] == 'operate':
        DebugFlag = False
        comm.logger('Starting HousePi')

        # Generating the light string structure
        L = StringOfLights(HouseDefinition.InsteonAliases, 'Insteon')   # Form the string of lights based on te insteon aliases
        L = StringOfLights(HouseDefinition.X10Aliases, 'X10', L)        # Append the X10Aliased lights to L
        LightLookUp = SensorLightLookUp(L)                              # Make a lookup dictionary { Alias : LightIndex for L}
        Events = EventList()
        EventsLog(Events, comm)
        #import pdb; pdb.set_trace()

        # Generate the event list frotm the HouseDefinition module
        CycleLights(L,comm)

        counter = 0
        while True:
            counter+=1
            LenEvents = len(Events)
            Events.extend(SensorWatch(L, comm, LightLookUp)) # New module should append new events to the list as determined by the sensors
            Events.extend(SwitchWatch(comm))                # New module should append new events to the list as determined by the switches
            if (counter > 100 or LenEvents <> len(Events)):
                EventsLog(Events, comm)
                counter = 0
            CheckEvents(Events, L, comm, LightLookUp)
                
    elif args[0] == 'xsend':
        Activate.Send(comm.ser)
        sleep(1)
        Deactivate.Send(comm.ser)

    elif args[0] == 'isend':
        addr = comm.parse_addr(args[1])
        cmd = comm.parse_bytes(ic.ALIASES_COMMAND.get(args[2], args[2]), 2,
                               what='command')
        res = comm.send_insteon_direct(addr, cmd[0], cmd[1], 
                                       error_ok=True, ack_data=True)
        if res is None:
            print 'NO-RESPONSE'
            return 1
        elif res is False:
            print 'NAK'
            return 2
        else:
            print 'ACK %s' % comm.format_bytes(res)

    elif args[0] == 'repsend':
        if len(args) not in [4, 5]:
            parser.error('Wrong number of arguments')

        addr = comm.parse_addr(args[1])       
        cmd = comm.parse_bytes(ic.ALIASES_COMMAND.get(args[2], args[2]), 2,
                               what='command')
        
        count = int(args[3])
        if len(args) > 4:
            delay = float(args[4])
        else:
            delay = 0.5
        
        for step in range(1, count+1):
            res = comm.send_insteon_direct(addr, cmd[0], cmd[1], 
                                           error_ok=True, ack_data=True)
            if res is None:
                print 'Step %d: NO-RESPONSE' % step
                return 1
            elif res is False:
                print 'Step %d: NAK' % step
                return 2
            else:
                print 'Step %d: ACK %s' % (step, comm.format_bytes(res))
            comm.listen_for(delay)        

    elif args[0] == 'status':
        to_poll = [ comm.parse_addr(a)
                    for a in args[1:] ]
        if len(to_poll) == 0:
            devs = comm.get_linked_devices()
            to_poll = [dev['addr'] for dev in devs]

        print to_poll[0]
        failed = False
        for addr in to_poll:
            result = comm.send_insteon_direct(addr, 0x19, 0x00, 
                                              error_ok=True, ack_data=True)
            if result is None:
                failed = True
                result_s = 'TIMEOUT'
            elif result is False:
                failed = True
                result_s = 'NAK'
            else:
                comm.ILight.Address = addr
                comm.ILight.Status = result[1]
                result_s = "%1.f%% (0x%02X)" % (
                    result[1] * 100.0 / 255, result[1])
            if len(args) == 2:
                # only one device, explicitly specified
                print result_s
            else:
                print 'status of %r: %s' % (
                    comm.format_addr(addr), result_s)

        if failed:
            return 1

    elif args[0] == 'watch':
        if len(args) != 1:
            parser.error('Too many arguments')
        msg = comm._read_packet(timeout=5)
        if msg != []:
            print comm.format_rxpacket(msg)
        msg = comm._read_packet(timeout=5)
        if msg != []:
            print comm.format_rxpacket(msg)


    print "All done!"

if __name__ == '__main__':
    try:
        sys.exit(main())
    except ic.UserError as e:
        print >>sys.stderr, 'FATAL ERROR: %s' % e
        
        comm.Logfile.close()
        sys.exit(99)
