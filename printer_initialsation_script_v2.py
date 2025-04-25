"""
v1 -> v2:
- added checkSubstrateLevel() function
- moved flush step to before alignment to allow flushing into waste container
- edited flush() function to instruct user to position nozzle above waste container, and for user to select which pump to flush
- fixed bug in moveTogether() function that caused velocity to be set to ~40mph lmao

this script requires the following packages:
general:
traceback (for printing error messages to the terminal)
time

for translation stages:
pylablib (which has dependency on numba, whose 0.60 version isn't compatible with Python 3.13 therefore 3.12.7 should be used for this script)
pythonnet (which has dependecy on clr)

for pumps:
serial
"""

###FUNCTIONS ZONE 

def genericError(exc):
    print(
            CRED,
            "\nPROCESS FAILED",
            CEND
            )
    print(CRED,
        "\nError Message:",
        exc,
        '\n\n',
        traceback.format_exc(),
        CEND
        )
    holdTerminal()


#a function to keep the terminal open while I read the error message
def holdTerminal():
     while True:
        entry = input("Press x to exit: ")
        if entry == 'x':
            exit()
        else:
            continue

def isBlank (myString):
    return not (myString and myString.strip())

def getPumpResponse(pump_number):
    try:
        pumps = {
            1 : pump1,
            2 : pump2
        }
        b = bytearray() #b will store the pump's respose as it read
        while True:
            #using read(number of bytes) to read the pump's response one byte at a time
            next_byte = pumps[pump_number].read(1)
            for byte in bytearray(next_byte):
                b.append(byte)

            #next_byte.decode('utf-8') converts a byte type variable to a string
            if next_byte.decode('utf-8') == ':': #':' for pump stopped 
                break
            elif next_byte.decode('utf-8') == '>': #'>' for pump running
                break
            else:
                continue
        
        response = b.decode('utf-8')[:-1].strip()
        return response


    except Exception as exc:
        genericError(exc)

# a function that move the stages at certain velocities such that they arrive at the given position at the same time
def moveTogether(new_position, velocity):

    # position (tuple) is the desired final position of the nozzle in absolute coords IN MM!!!
    # velocity (float) of the substrate velocity IN MM/S!!!

    current_position = (X_stage.get_position()/multi, Y_stage.get_position()/multi)

    relative = (abs(current_position[0] - new_position[0]), abs(current_position[1] - new_position[1])) # distances in X and Y between current and new positions

    print(relative)

    try:
        v_X = velocity * (relative[0])/(max(relative))
    except ZeroDivisionError:
        v_X = velocity
    
    try:
        v_Y = velocity * (relative[1])/(max(relative))
    except ZeroDivisionError:
        v_Y = velocity
    
    print("\nV_x = ", str(v_X))
    print("\nV_y = ", str(v_Y))

    # setting temporary max velocities for the syncronised move
    X_stage.setup_velocity(max_velocity=v_X*multi, scale=True)
    Y_stage.setup_velocity(max_velocity=v_Y*multi, scale=True)

    X_stage.move_to(new_position[0]*multi)
    Y_stage.move_to(new_position[1]*multi)

    time.sleep(0.2)

    X_stage.wait_for_stop()
    Y_stage.wait_for_stop()

    # setting velocities back to their normal value
    X_stage.setup_velocity(max_velocity=velocity*multi, scale=True)
    Y_stage.setup_velocity(max_velocity=velocity*multi, scale=True)

    time.sleep(0.1) # delay to allow stages to settle before reporting position    

    print("\nNew position:",
          "\nX: " + str(X_stage.get_position()/multi) + 'mm',
          "\nY: " + str(Y_stage.get_position()/multi) + 'mm',
          "\n"
    )

def moveToAtVelocity(new_position, velocity):

    # position (tuple) is the desired final position of the nozzle in absolute coords IN MM!!!
    # velocity (float) of the substrate velocity IN MM/S!!!

    # setting velocities to given values
    X_stage.setup_velocity(max_velocity=velocity*multi, scale=True)
    Y_stage.setup_velocity(max_velocity=velocity*multi, scale=True)

    # moving
    X_stage.move_to(new_position[0]*multi)
    Y_stage.move_to(new_position[1]*multi)

    time.sleep(0.2)

    X_stage.wait_for_stop()
    Y_stage.wait_for_stop()

    print("\nNew position:",
          "\nX: " + str(X_stage.get_position()/multi) + 'mm',
          "\nY: " + str(Y_stage.get_position()/multi) + 'mm',
          "\n"
    )

def moveByAtVelocity(relative_position, velocity):

    # position (tuple) is the desired final position of the nozzle in absolute coords IN MM!!!
    # velocity (float) of the substrate velocity IN MM/S!!!

    # setting velocities to given values
    X_stage.setup_velocity(max_velocity=velocity*multi, scale=True)
    Y_stage.setup_velocity(max_velocity=velocity*multi, scale=True)

    # moving
    X_stage.move_by(relative_position[0]*multi)
    Y_stage.move_by(relative_position[1]*multi)

    time.sleep(0.2)

    X_stage.wait_for_stop()
    Y_stage.wait_for_stop()

    print("\nNew position:",
          "\nX: " + str(X_stage.get_position()/multi) + 'mm',
          "\nY: " + str(Y_stage.get_position()/multi) + 'mm',
          "\n"
    )

def flush():
    try:
        print('Position the nozzle above a waste container.')
        entry = input("\nPress enter when ready to flush: ")

        pump1.write(bytes(f'ULM{Q_flush}\r\n', encoding='utf-8'))
        pump2.write(bytes(f'ULM{Q_flush}\r\n', encoding='utf-8'))

        while True:
            which_pump = input("\nWhich pumps should be flushed? Enter '1', '2', or 'b' for both: ")
            if which_pump == '1': # flush only pump1
                pump1.write(b'RUN\r\n')
                entry = input("\nPress enter to end flush: ")
                pump1.write(b'STP\r\n')
                break
            elif which_pump == '2': # flush only pump2
                pump2.write(b'RUN\r\n')
                entry = input("\nPress enter to end flush: ")
                pump2.write(b'STP\r\n')
                break
            elif which_pump == 'b' or which_pump =='B': # flush both pump1 and pump2
                pump1.write(b'RUN\r\n')
                pump2.write(b'RUN\r\n')

                entry = input("\nPress enter to end flush: ")

                pump1.write(b'STP\r\n')
                pump2.write(b'STP\r\n')
                break
            else:
                print("\nInvalid input, please enter '1', '2', or 'b'")
                continue

    except Exception as exc:
        genericError(exc)

def checkSubstrateLevel(substrate_dimensions):

    # this function scans the nozzle over the surface so that the user can use the microscope to check that the substrate is level
    # this is to ensure that the z-height of the nozzle above the substrate remains constant
    try:
        print("\nChecking substrate for level...")

        # moving the nozzle to each substate corner

        moveTogether((2, 2), v_travel)

        moveTogether((substrate_dimensions[0] - 2, 2), v_travel)

        moveTogether((substrate_dimensions[0] - 2, substrate_dimensions[1] - 2), v_travel)

        moveTogether((2, substrate_dimensions[1] - 2), v_travel)

        moveTogether((2, 2), v_travel)

    except Exception as exc:
        genericError(exc)


















#defining some string to use to print coloured text to the terminal
#see link for details (https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal?page=2&tab=modifieddesc#tab-top)
#to get colours to display on 32-bit versions of windows, you have to edit the registry
#see link for details (https://superuser.com/questions/413073/windows-console-with-ansi-colors-handling/1050078)
CRED = '\033[91m'
CGREEN = '\033[92m'
CEND = '\033[0m'

print("\nImporting packages...")
try:
    from pylablib.devices import Thorlabs

    import time

    import clr

    import serial

    import numpy as np

    import traceback

    print("Packages imported")
except ModuleNotFoundError as exc:
    print(
        CRED,
        "\nFAILED TO IMPORT PACKAGES",
        "\nCheck that the following packages are installed:",
        "\npylablib"\
        "\npythonnet",
        "\nserial",
        CEND
        )
    print(CRED,
        "\nError Message:",
        exc,
        CEND
        )
    holdTerminal()
    



#Connecting to and starting the translation stages

print("\nAccessing Thorlabs DLLs..")
try:
    # addings the dynamic link libraries (DLLs) that come with Kinesis
    # DLLs are like small programs that can be called upon by other programs

    clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll.")
    clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll.")
    clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.KCube.BrushlessMotorCLI.dll.")

    # importing the functionality of the Thorlabs DLLs into python
    from Thorlabs.MotionControl.DeviceManagerCLI import *
    from Thorlabs.MotionControl.GenericMotorCLI import *
    from Thorlabs.MotionControl.KCube.BrushlessMotorCLI import *

    print("DLL references added")
except Exception as exc:
    print(
        CRED,
        "\nUNABLE TO LOCATE THORLABS DLLS",
        "\nEnsure Kinesis software is installed - expected path for DLLs is:",
        "\nC:\\Program Files\\Thorlabs\\Kinesis",
        CEND
        )
    print(CRED,
        "\nError Message:",
        exc,
        CEND
        )
    holdTerminal()

# inputting KBD-101 device serial numbers
SN_Y = "28000262"
SN_X = "28250342"

multi = 2000 # used to convert from internal steps to mm 

# I'm only using the Thorlabs DLLs to enable controllers, since I can't seem to do that with pylablib
print("\nConnecting to motor controllers via Thorlabs DLLs...")
try:
    DeviceManagerCLI.BuildDeviceList()

    #creating a new device for the X axis controller
    X_controller = KCubeBrushlessMotor.CreateKCubeBrushlessMotor(SN_X)

    #creating a new device for the Y axis controller
    Y_controller = KCubeBrushlessMotor.CreateKCubeBrushlessMotor(SN_Y)

    # calling for the device X_controller to connect to the KBD101 with serial number SN_X
    X_controller.Connect(SN_X)

    # calling for the device Y_controller to connect to the KBD101 with serial number SN_Y
    Y_controller.Connect(SN_Y)

    print("Motor controllers connected")
except Exception as exc:
    print(
        CRED,
        "\nCONNECTION FAILED",
        "\nEnsure motor controllers are connected",
        CEND
        )
    print(CRED,
        "\nError Message:",
        exc,
        CEND
        )
    holdTerminal()

print("\nEnabling stages...")
try:
    time.sleep(0.5)

    # polling refers to the KBD101 sending updates about the state of the motor to the PC (takes the number of MILLISECONDS between updates as the arguement)
    X_controller.StartPolling(250)
    Y_controller.StartPolling(250)
    time.sleep(0.5)  # wait statements are important to allow settings to be sent to the device (time.sleep() takes number of SECONDS as an arguement)

    # enabling the device
    X_controller.EnableDevice()
    Y_controller.EnableDevice()

    print("Stages enabled")

    # Stop polling and close device
    X_controller.StopPolling()
    X_controller.Disconnect(True)

    # Stop polling and close device
    Y_controller.StopPolling()
    Y_controller.Disconnect(True)

    print("Disconnected from control via Thorlabs DLLs\n")

    time.sleep(0.5)  # Wait for device to enable
except Exception as exc:
    genericError(exc)


try:
    #connect to the devices for motion control using pylablib
    #pylablib will be used for all motion control
    X_stage = Thorlabs.KinesisMotor(SN_X)
    Y_stage = Thorlabs.KinesisMotor(SN_Y)
except Exception as exc:
    genericError(exc)

print("\nHoming stages...")
try:
    X_stage.home(sync=False, force=True) # setting sync=False means the script doesn't wait until the homing finishes to continue sending commands - i.e., simultaneous movement of X and Y
    Y_stage.home(sync=False, force=True)

    #loop that checks to see if stages have homed
    homing_timeout = 10 #no. of seconds allowed before homing timeout error
    check_rate = 0.5 #no. of seconds between checks for homing
    max_checks = homing_timeout/check_rate #maximum number of times the program will check whether homing is complete before raising homing timeout error

    print("max check = " + str(max_checks))
    checks = 0
    while X_stage.is_homed() == False or Y_stage.is_homed() == False:

        time.sleep(check_rate)

        if checks == max_checks:
            raise TimeoutError("Failed to home stages within time limit")

        if X_stage.is_homing() == True and Y_stage.is_homing() == True:
            print("\nX stage: Homing...\nY stage: Homing...")
        elif X_stage.is_homed() == True and Y_stage.is_homing() == True:
            print("\nX stage: Homed\nY stage: Homing...")

        elif X_stage.is_homing() == True and Y_stage.is_homed() == True:
            print("\nX stage: Homing...\nY stage: Homed")
        
        checks+=1
    
    if X_stage.is_homed() == True and Y_stage.is_homed() == True:
        print("\nStages homed")
    else:
        raise Exception("Stages have not homed correctly")      
except Exception as exc:
    genericError(exc)




#connecting to pumps
print('Opening ports...')
try:
    pump1 = serial.Serial(
        port='COM11',
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_TWO,
        bytesize=serial.EIGHTBITS
    )
except serial.SerialException as exc:
    print(
        CRED,
        "\nUNABLE TO OPEN PORT COM 11",
        "\nCheck serial connection between PC and pump",
        CEND
        )
    print(CRED,
        "\nError Message:",
        exc,
        CEND
        )

try:
    pump2 = serial.Serial(
        port='COM12',
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_TWO,
        bytesize=serial.EIGHTBITS
    )
except serial.SerialException as exc:
    print(
        CRED,
        "\nUNABLE TO OPEN PORT COM 12",
        "\nCheck serial connection between PC and pump",
        CEND
        )
    print(CRED,
        "\nError Message:",
        exc,
        CEND
        )

pump1.isOpen()
pump2.isOpen()
print('Ports opened')

#pump self test will be to query them for their firmware version number and read the response to make sure communication is working
print("\nPerforming pump communication self-test...")
try:
    print("\nTesting Pump 1...")
    pump1.write(b'ver\r\n')

    response = getPumpResponse(1)

    if isBlank(response) == True:
        raise Exception('\nPump 1 response string empty')
    if response == '11.060':
        print("Pump 1 coms self test successful")
    else:
        raise Exception(f"\nPump 1 returned unexpected response string: {response}")
except Exception as exc:
    print(
        CRED,
        "\nPUMP 1 COMS SELF TEST FAILED",
        CEND
        )
    print(CRED,
        "\nError Message:",
        exc,
        CEND
        )
    holdTerminal()

try:
    print("\nTesting Pump 2...")
    pump2.write(b'ver\r\n')
    
    response = getPumpResponse(2)

    if isBlank(response) == True:
        raise Exception('\nPump 2 response string empty')
    if response == '11.062':
        print("Pump 2 coms self test successful")
    else:
        raise Exception(f"\nPump 2 returned unexpected response string: {response}")
except Exception as exc:
    print(
        CRED,
        "\nPUMP 2 COMS SELF TEST FAILED",
        CEND
        )
    print(CRED,
        "\nError Message:",
        exc,
        CEND
        )
    holdTerminal()


### systew initializatin complete
print(
    CGREEN,
    "\n\n*** SYSTEM INITIALIZATION COMPLETE ***\n\n",
    CEND
    )













# enter parameters for the print job here
dead_volume = 500 #uL - this is the volume in the Tygon tubes, the DropChip and the nozzle
Q_flush = 3 #uL/min - pump rate (using same rate for both pumps during flush)
Q_1 = 1.25 #uL/min - pump 1 pump rate (during printing)
Q_2 = 1.25 #uL/min - pump 2 pump rate (during printing)
d_1 = 4.66 #mm - pump 1 syringe diameter
d_2 = 4.66 #mm - pump 2 syringe diameter
v_print = 20 #mm/s substrate velocity
v_travel = 50 #mm/s - velocity when not printing
substrate_dimensions = (45, 45) #mm - the...dimensions of the...substrate
alignment_position = (4, 4) # in coordinates used after homing - i.e., with (0, 0) at the home position
flush_position = (2, substrate_dimensions[0] - 2)


# ask user if a flush of the system is required
try:
    while True:
        query_flush = input('\nFlush required (y/n): ')
        if query_flush == 'y' or query_flush == 'Y':
            flush()
            break
        elif query_flush == 'n' or query_flush == 'N':
            break
        else:
            print("\nInvalid input, please enter 'y' or 'n'") 
except Exception as exc:
    genericError(exc)



# moving stage to a position that allows user to align nozzle with substrate edge
try:
    print("\nMoving to alignment position...")

    moveTogether(alignment_position, velocity=v_travel)

    print("\nPositioned for alignment")
except Exception as exc:
    genericError(exc)



#instructing user to perform nozzle alignment
entry = input("\nCenter the nozzle on the substrate.\nPress enter when done: ")
print('OK')

# prompting user to adjust z height
entry = input("\nAdjust z height to desired value.\nPress enter when done: ")
print('OK')

# setting substrate corner dimensions
try:
    X_stage.set_position_reference(position=alignment_position[0]*multi)
    Y_stage.set_position_reference(position=alignment_position[1]*multi)    
except Exception as exc:
    genericError(exc)


# setting pump diameters
try:
            pump1.write(bytes(f'MMD{d_1}\r\n', encoding='utf-8'))
            getPumpResponse(1)
            pump2.write(bytes(f'MMD{d_2}\r\n', encoding='utf-8'))
            getPumpResponse(2)

            time.sleep(0.5) # time must be allowed after writing pump diameters (to allow time forpumps to access their internal memory?
except Exception as exc:
    genericError(exc)



### systew initializatin complete
print(
    CGREEN,
    "\n\n*** PRINTER SET-UP COMPLETE ***\n\n",
    CEND
    )

# ask uset if they want to execute a substrate level check
try:
    while True:
        level_query = input("\nRun substrate level check? (y/n): ")
        if level_query == 'y' or level_query == 'Y':
            checkSubstrateLevel(substrate_dimensions)
            continue
        elif level_query == 'n' or level_query == 'N':
            break
        else:
            print("\nInvalid input, please enter 'y' or 'n'")
except Exception as exc:
    genericError(exc)














entry = input("\nPress enter to begin print: ")














# print test
try:
    print('\nPrinting...')

   # print job goes here

    print('Print complete') 


except Exception as exc:
    genericError(exc)




holdTerminal()    