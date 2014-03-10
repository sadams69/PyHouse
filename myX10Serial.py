from time import localtime,strftime, sleep
import serial, math
import thread
#import MySQLdb
import sys
from string import Template

HouseControlDatabase = 'Test.HouseControl'
DebugFlag = 1

HouseCodes = \
	{'A':		0b01100000,\
	 'B':		0b11100000,\
	 'C':		0b00100000,\
	 'D':		0b10100000,\
	 'E':		0b00010000,\
	 'F':		0b10010000,\
	 'G':		0b01010000,\
	 'H':		0b11010000,\
	 'I':		0b01110000,\
	 'J':		0b11110000,\
	 'K':		0b00110000,\
	 'L':		0b10110000,\
	 'M':		0b00000000,\
	 'N':		0b10000000,\
	 'O':		0b01000000,\
	 'P':		0b11000000}

DeviceCodes = \
	{'1'	:	0b00000110,\
	 '2'	:	0b00001110,\
	 '3'	:	0b00000010,\
	 '4'	:	0b00001010,\
	 '5'	:	0b00000001,\
	 '6'	:	0b00001001,\
	 '7'	:	0b00000101,\
	 '8'	:	0b00001101,\
	 '9'	:	0b00000111,\
	 '10'   :	0b00001111,\
	 '11'   :	0b00000011,\
	 '12'   :	0b00001011,\
	 '13'   :	0b00000000,\
	 '14'   :	0b00001000,\
	 '15'   :	0b00000100,\
	 '16'   :	0b00001100}

FunctionCodes = { \
  'All Units Off'			:	0b00000000, \
	'All Lights On'			:	0b00000001, \
	'On'					:	0b00000010, \
	'Off'					:	0b00000011, \
	'Dim'					:	0b00000100, \
	'Bright'				:	0b00000101, \
	'All Lights Off'		:	0b00000110, \
	'Extended Code'			:	0b00000111, \
	'Hail Request'			:	0b00001000, \
	'Hail Acknowledge'		:	0b00001001, \
	'Pre-set Dim (1)'		:	0b00001010, \
	'Pre-set Dim (2)'		:	0b00001011, \
	'Extended Data Transfer' :	0b00001100, \
	'Status On'				:	0b00001101, \
	'Status Off'			:	0b00001110, \
	'Status Request'		:	0b00001111  \
    }

MiscCodes = { \
	'PollAcknowledge': 		0xc3, \
	'DataPoll':				0x5a, \
	'PowerFailPoll':		0xa5, \
	'PCStopPoll' : 			0xfb \
    }

class X10():
    def __init__(self, House = 'A', Unit = 1, Command = 'On'):            
        self.House      = House
        self.Unit       = Unit
        self.Type       = 'Null'
        self.Command    = Command
        self.Raw        = ''
        self.Error      = 0
        return

    def Send(self, serial):
        global HouseCodes, DeviceCodes, FunctionCodes
        #Define the house and unit
        #print 'Inside Send'
        Command = chr(0x02)
        Command = Command + chr(0x63)
        #print 'Part way' + self.House + self.Unit
        Command = Command + chr(HouseCodes[self.House] + DeviceCodes[self.Unit])
        #print 'Doubt it'
        Command = Command + chr(0x00) # Indicates Unit Code
        #print 'half way'
        serial.write(Command)
        sleep(0.5) # This is needed or the modem does not seem to acknowledge properly
        
        #Define the command
        Command = chr(0x02)
        Command = Command + chr(0x63)   # X10 Send
        Command = Command + chr(HouseCodes[self.House] + FunctionCodes[self.Command])
        Command = Command + chr(0x80)    # Command code
        serial.write(Command)
        #LogHouseCommand(self)


def GetDataBuffer(Serial):
    NBytes = int(serial.read(1))
    FA = serial.read(1)
    DataOut = serial.read(NBytes)
    return [NBytes, FA, DataOut]

def HeaderCode(DimCode,FAi,ESi):
    FA = {'Function':'1', 'Address':'0'}
    ES = {'Extended':'1', 'Standard':'0'}
    DimCode = 22 # Number between 0 and 22 for the dimming light parameter
    DimCode = bin(DimCode)
    code = DimCode + '1' + FA[FAi] + ES[ESi]
    return code

def PrepareSerial():
    # Opening the serial connection
    ser=serial.Serial("/dev/ttyUSB0", baudrate=19200, timeout = 3.0)
   # ser.baudrate=19200
   # ser.port=0
    return ser

def SerialRead(ser):
# Read all of the data in the output buffer. Return the last none empty result
    temp = ser.read()
    output = temp
    while temp != "":
        print hex(ord(output))
        temp = ser.read()
        if temp != "":
            output = temp
    return output

def SerialOut(Serial, List):
    for i in List:
        print "{}".format(i)
        Serial.write('{}'.format(i))

def DecodeChunk(Chunk, ChunkType):
    global HouseCodes, DeviceCodes, FunctionCodes

    for i in HouseCodes:
        Value = HouseCodes[i]
        if Chunk & 0b11110000 == Value & 0b11110000:
            #print "Chunk {0:b}, {0}: HouseCode {1:b}, {2}".format(Chunk, Value, i)
            AHouse = i

    if ChunkType == 'UnitCode':
        Code = None
        for i in DeviceCodes:
            Value = DeviceCodes[i]
            if Chunk & 0b00001111 == Value & 0b00001111:
                #print "Chunk {0:b}, {0}: HouseCode {1:b}, {2}".format(Chunk, Value, i)
                Code = i
        return (AHouse,Code)

    elif ChunkType == 'Command':
        Code = None
        for i in FunctionCodes:
            Value = FunctionCodes[i]
            if Chunk & 0b00001111 == Value & 0b00001111:
                #print "Chunk {0:b}, {0}: HouseCode {1:b}, {2}".format(Chunk, Value, i)
                Code = i
        return (AHouse,Code)

def ParseSensors(Sensors):
    '''
    Sensors contains information pulled from the serial bus. The assumption is that it contains
    X10 Commands. The commands have two parts, the unit and the command. Once a pair has been
    received, they are sent to the database. 
    '''
    
    global X, RawString
    Status = None
    dbOutFlag = 1
    RawString = ''
    for i in [ord(x) for x in Sensors]:
        if Status is None:
            if i == 0x02:
                Status = 'X10'
                X.Command = ''
                X.Type = ''
                X.Raw = ''
                Chunk = None
            elif i == 0x15:
                Status = 'Failed'
                X.Command = Status
                DBOut(X)
                Chunk = None
        elif Status == 'X10':
            if i == 0x52:
                Status = Status + ':' + 'Received'
                X.Type = 'Received'
            elif i == 0x53:
                Status = Status + ':' + 'Sent'
                X.Type = 'Sent'
        elif (Status == 'X10:Received' or Status == 'X10:Sent'):
            if Chunk is None:
                Chunk = i
            elif i == 0x00:
                Status = Status + ':' + 'UnitCode'
                X.House, X.Unit = DecodeChunk(Chunk, 'UnitCode')
                DBOut(X)
                Status = None
                Chunk = None
            elif i == 0x80:
                Status = Status + ':' + 'Command'
                X.House, X.Command = DecodeChunk(Chunk, 'Command')
                dbOutFlag = 1
                Status = None
                Chunk = None
        RawString = RawString + " {0:X}".format(i)
        if dbOutFlag:
            X.Raw = RawString
            DBOut(X)
            RawString = ''
            dbOutFlag = 0
    #X.Command = 'Repeat'
    
    #DBOut(X)

def SingleSerialScan(ser):
    global X
    #print 'Checking inside offender: ' + repr(ser.isOpen())

    aFlag = 0
    myTime = 0
    myTime2 = 0
    siW = 0
    siW0 = 0
    
    Sensors = None
    while ser.inWaiting:
        siW = ser.inWaiting()
        LocalTime   = localtime()
        Hour        = LocalTime[3]
        Minute      = LocalTime[4]
        Second =   LocalTime[5]
        myTime2    = Minute*60+Second

        # if this is the first time data is recognized in the buffer
        # start the timer and record the number of pieces of data
        if siW and not aFlag:
            myTime = myTime2
            aFlag = 1
            siW0 = siW
            print "Waiting for serial data. Starting with ", siW, " bytes."
        elif siW != siW0:
            print "New Data: ", myTime2-myTime, ":", siW
            siW0 = siW

        # Exit criteria
        if siW>7 and (myTime2 - myTime) > 2:
            print "Reading data from buffer"
            Sensors = ser.read(ser.inWaiting())
            break
        sleep(0.1)
        
    print "Serial String"
    print Sensors
    #my_hex = Sensors.decode("hex")
    print " ".join(hex(ord(n)) for n in Sensors)
    if len(Sensors) > 0:
        ParseSensors(Sensors)
        print "House ", X.House, " Unit ", X.Unit, " Command ", X.Command
        
def SerialScan():
    ser=PrepareSerial()
    ser.open()

    for ifor in range(0,20):
        if ifor % 10 == 0:
            print "Checking for sensor input"
        Sensors = ser.read(1000)
        if len(Sensors) > 0:
            ParseSensors(Sensors)
            ASensors = Sensors
        #sleep(1)

    print "closing serial port"
    ser.close()

def DBOut(X):
    query = Template('''
    insert into
        Test.SensorLog
        (House, Unit, Command, Type, Raw, DTime)
    values
        ("$myHouse","$myUnit","$myCommand","$myType", "$myRaw", now())
    ''').substitute(dict(myHouse = X.House,
                         myUnit = X.Unit,
                         myCommand = X.Command,
                         myType     = X.Type,
                         myRaw    = X.Raw))
    #MyUpdate(query)
    pout = Template('''$myHouse:$myUnit->$myCommand,$myType:$myRaw''').substitute(dict(myHouse = X.House,
                         myUnit = X.Unit,
                         myCommand = X.Command,
                         myType     = X.Type,
                         myRaw    = X.Raw))
    print pout

if __name__ == '__main__':
    print "New Run"
    X = X10()
    RawString = ''
    ser = PrepareSerial()
    ser.open()

    Activate = X10(House = 'A', Unit = '1', Command = 'On')
    Deactivate = X10(House = 'A', Unit = '1', Command = 'Off')
    Activate.Send(ser)
    sleep(1)
    Deactivate.Send(ser)
    sleep(1)


