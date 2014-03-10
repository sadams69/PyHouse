

import HouseDefinition3 as HD
from HousePi3 import CurrentTime

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

def CheckEvents(Events):
    # 
x = EventList()
