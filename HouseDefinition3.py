
#InsteonAliases = {'dimmer': {'Address' : '1D-D9-3D'}}
import time
try:
    from PrivateHouse import PrivateHouseEmail
    print "Email Alerts from: ",PrivateHouseEmail['from']
except:
    print '*'*100
    print "You need to create PrivateHouse.py that includes one dictionary called PrivateHouseEmail with 'to', 'from', 'username', and 'password' fields"
    print '*'*100
    raise error("Stopping.")

x = time.localtime()

Logfile = './logs/HousePi.%d.%d.%d.%d.txt' % (x.tm_year, x.tm_mon, x.tm_mday, x.tm_hour)
Testing = False
DebugFlag = Testing

USB = {'Mac' : "/dev/tty.usbserial", 'Rpi': "/dev/ttyUSB0", 'win': "USB0"}
if (Testing):
    InsteonAliases = {'dimmer': '1D-D9-3D'}

    X10Aliases = {          'Garage Front'      :   { 'House' : 'A', 'Unit' : '1'},
                            'Living Room'       :   { 'House' : 'B', 'Unit' : '3'}
                 }

    SensorAliases = {   'Porch'             : {'House' : 'A', 'Unit' : 9},
                        'Inside Roaming'    : {'House' : 'A', 'Unit' : 9}
                    }

    # Can have two timers for each alias, one for am and one for pm
    Timers  =       {         'Living Room'       :   { 'TurnOn' : 12+0, 'TurnOff' : 12+2},
                               'dimmer'       :   { 'TurnOn' : 12+5, 'TurnOff' : 12+7}
                      }


    Sensors = { 'Porch' :               [     {'Who'   :'Living Room', 'When' :  [1,24,75./60], 'Style' : []} ],
                'Inside Roaming'    :   [   {'Who'   :'dimmer', 'When' :  [12,24,75./60], 'Style' : ['Mood',90,.1]}]}
                    
else:
    InsteonAliases = {'dimmer': '1D-D9-3D',
                      'DownstairsBathroom' : '25-3E-EA',
                      'BackPorchLight' : '25-42-27'}

    InsteonSwitchAliases = {'SideDoor': '28-11-80',
                      'BasementDoor' : '28-13-15',
                      'FrontDoor' : '28-13-18',
                      'GarageSideDoor' : '28-0A-62'}

    X10Aliases = {          'Garage Front'      :   { 'House' : 'B', 'Unit' : '1'},
                            'Living Room'       :   { 'House' : 'B', 'Unit' : '3'},
                            'Upstairs Hall'     :   { 'House' : 'B', 'Unit' : '4'},
                            'Garage Back'       :   { 'House' : 'B', 'Unit' : '2'}
                      }

    SensorAliases = {   'Front'             : {'House' : 'A', 'Unit' : 1},
                        'Porch'             : {'House' : 'A', 'Unit' : 2},
                        'Cellar'             : {'House' : 'A', 'Unit' : 4},
                        'Inside Roaming'    : {'House' : 'A', 'Unit' : 3},
                        'DownstairsBathroomSensor'    : {'House' : 'A', 'Unit' : 5},
                        'BackPorchSensor'    : {'House' : 'A', 'Unit' : 6}
                    }

    Timers  =       [    { 'Who' : 'Garage Front'      ,    'TurnOn' : 12+4, 'TurnOff' : 12+10, 'Style' : []},
                          { 'Who' : 'Garage Front'      ,    'TurnOn' : 5.5, 'TurnOff' : 6.25, 'Style' : []},
                          {  'Who' :'Living Room'       , 'TurnOn' : 12+4, 'TurnOff' : 12+9, 'Style' : []},
                          {  'Who' :'Upstairs Hall'     , 'TurnOn' : 12+5, 'TurnOff' : 12+9, 'Style' : []},
                          # { 'Who' :'DownstairsBathroom'       , 'TurnOn' : 12+5.5, 'TurnOff' : 12+12, 'Style' : []},
                           { 'Who' :'Garage Back'       , 'TurnOn' : 12+5.5, 'TurnOff' : 12+7, 'Style' : []},
                           { 'Who' :'Garage Back'       , 'TurnOn' : 5, 'TurnOff' : 7, 'Style' : []},
                             { 'Who' :'BackPorchLight'       , 'TurnOn' : 12+5, 'TurnOff' : 12+8, 'Style' : []}
                      ]
   

    Sensors = [ {'Source' : 'Porch'     , 'Who'   :['Garage Front', 'Living Room']   , 'When' :  [22,24,15./60]  , 'Style' : []}, 
                {'Source' : 'Porch'     , 'Who'   :['Living Room']   , 'When' :  [0,8,45./60]   , 'Style' : []},
                {'Source' :'Front'      , 'Who'   :['Garage Front', 'Living Room']   , 'When' :  [20,24,15./60]  , 'Style' : []}, 
                {'Source' :'Front'      ,'Who'   :['Living Room']    , 'When' :  [0,8,45./60]   , 'Style' : []},
                {'Source' :'Cellar'     , 'Who'   :['Living Room', 'dimmer']  , 'When' :  [20,24,30./60]  , 'Style' : []}, 
                {'Source' :'GarageSideDoor'     , 'Who'   :['Living Room']  , 'When' :  [0,24,1./60]  , 'Style' : []}, 
                {'Source' : 'Cellar'    ,'Who'   :['Living Room', 'dimmer']    , 'When' :  [0,8,30./60]   , 'Style' : []},
                #{'Source' :'DownstairsBathroomSensor', 'Who'   :['DownstairsBathroom']      , 'When' :  [4,24,1./60]  , 'Style' : ['Mood',250,.1]},
                 {'Source' :'DownstairsBathroomSensor', 'Who'   :['DownstairsBathroom']      , 'When' :  [10,24,10./60]  , 'Style' : []},
                {'Source' :'DownstairsBathroomSensor', 'Who'   :['DownstairsBathroom']      , 'When' :  [0,5,10./60]  , 'Style' : ['Mood',90,.1]},
                {'Source' :'DownstairsBathroomSensor', 'Who'   :['DownstairsBathroom']      , 'When' :  [5,10,10./60]  , 'Style' : ['Mood',90,.1]},
                {'Source' :'Inside Roaming', 'Who'   :['dimmer', 'Living Room']      , 'When' :  [1,24,1./60]  , 'Style' : []}]

    EmailAlerts = [  {'Source' :'FrontDoor'     , 'Who'   :[PrivateHouseEmail['to']]  , 'HouseState' : 'Ready'},
                     {'Source' :'SideDoor'     , 'Who'   :[PrivateHouseEmail['to']]  , 'HouseState' : 'Ready'},
                     {'Source' :'GarageSideDoor'     , 'Who'   :[PrivateHouseEmail['to']]  , 'HouseState' : 'Ready'},
                     {'Source' :'BasementDoor'     , 'Who'   :[PrivateHouseEmail['to']]  , 'HouseState' : 'Ready'}]
                    

