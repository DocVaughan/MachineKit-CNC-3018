#! /usr/bin/env python

###############################################################################
# linuxcnc_testing.py
#
# Testing linuxcnc commands for control of the CNC 3018 mill 
# MachineKit setup. The intention is to test commands here before integration 
# with the Flask-socketio-based interface. 
#
# NOTE: As of 08/03/20, his is not intended to be run as a script. It's more of
#       a holder for the code pieces we'll need in a complete script.
#
# See this link for more information:
#  http://www.machinekit.io/docs/common/python-interface/
#
#
# Created: 07/24/20
#   - Joshua Vaughan
#   - joshua.vaughan@louisiana.edu
#   - @doc_vaughan
#   - http://www.ucs.louisiana.edu/~jev9637
#
# Modified:
#   * 08/03/20 - JEV - Added g-code loading and running
#
# TODO:
#   * Update to Python 3
###############################################################################

import time
import sys

import linuxcnc

try:
    # create a connection to the status channel
    status = linuxcnc.stat() 
    
    # Get current values
    status.poll()
    
    # Create a connection to the command channel
    command = linuxcnc.command()
    
except linuxcnc.error, detail:
    print "error", detail
    sys.exit(1)

for x in dir(status):
    if not x.startswith('_'):
        print x, getattr(status, x)


# Rest the e-stop and enable the axes
command.state(linuxcnc.STATE_ESTOP_RESET)
command.state(linuxcnc.STATE_ON)

# Switch to manual mode
command.mode(linuxcnc.MODE_MANUAL)

# Home the axes at their current positions
command.home(0)  # Home the x-axis
command.home(1)  # Home the y-axis
command.home(2)  # Home the z-axis

# Jog the x-axis 1-inch
JOG_SPEED = 0.1     # in/s
JOG_DISTANCE = 0.25  # inches
command.jog(linuxcnc.JOG_INCREMENT, 2, JOG_SPEED, JOG_DISTANCE)


# While we're moving poll the status and print out 
# the desired and actual positions
status.poll()  # Get the current status

while status.axis[0]['velocity'] != 0.0:
    print('Desired:     {:8.6f}'.format(status.axis[0]['output']))
    print('Actual:      {:8.6f}'.format(status.position[0]))
    print('Velocity:    {:8.6f}'.format(status.axis[0]['velocity']))
    print('')
    status.poll()
    time.sleep(0.1)
    


def ok_for_mdi():
    status.poll()
    return not status.estop and status.enabled and status.homed and (status.interp_state == linuxcnc.INTERP_IDLE)

def ok_for_auto():
    status.poll()
    return not status.estop and status.enabled and status.homed and (status.interp_state == linuxcnc.INTERP_IDLE)


if ok_for_mdi():
   command.mode(linuxcnc.MODE_MDI)
   command.wait_complete()  # wait until mode switch executed
   command.mdi("G0 X0.0 Y0.0 Z0.0")
else:
    print("Was not able to switch to MDI mode")



# To load the G-code file and step through it
# First, reset the interpreter. You will need to be 
command.reset_interpreter()
command.wait_complete()

gcode_filename = '/home/machinekit/Documents/nc_files/MachineKit.ngc'  # Use the full path
command.program_open(gcode_filename)

status.poll()
if status.file != gcode_filename:
    print('Current file is not the same as the desired')
    
# We can create a string of g-code commands from the file too.
# This might be useful for displaying the currently running line
with open(gcode_filename) as gcode_file:
    # split each line into a list entry
    gcode_stringArray = gcode_file.read().split('\n')
    
    # Then remove any blank/empty lines
    gcode_stringArray = [elem for elem in gcode_stringArray if (not elem.startswith('('))]# and elem != '')]


if ok_for_auto():
    command.mode(linuxcnc.MODE_AUTO)
    command.wait_complete()

    # Now, we could step though the G-code one line at a time.
    # command.auto(linuxcnc.AUTO_STEP)
    
    # Or, we can run the entire file, starting at line number START_LINE (zero indexed)
    START_LINE = 0
    command.auto(linuxcnc.AUTO_RUN, START_LINE)
    command.wait_complete()

    # Pause immediately after starting, if you want to step through the file 
    # manually.
    #command.auto(linuxcnc.AUTO_PAUSE)

    status.poll()  # Get the current status

    # The positions in this loop will update, but the g-code gets processed
    # in advance of the move, so we won't be able to see the commands as they
    # are run unless with manually 
    #     command.auto(linuxcnc.AUTO_PAUSE) as above
    # Then step through the g-code file in the loop
    while (True):
        # Uncomment pause above and the step here to step through the g-code
        # manually or at a slower rate. To require a user command you can 
        # uncomment the raw_input() command below
        #command.auto(linuxcnc.AUTO_STEP) 
        print('Desired:     {:8.6f}, {:8.6f}, {:8.6f}'.format(status.axis[0]['output'],
                                                              status.axis[1]['output'],
                                                              status.axis[2]['output']))
        print('Actual:      {:8.6f}, {:8.6f}, {:8.6f}'.format(status.position[0],
                                                              status.position[1],
                                                              status.position[2]))
        print('Velocity:    {:8.6f}, {:8.6f}, {:8.6f}'.format(status.axis[0]['velocity'],
                                                              status.axis[1]['velocity'],
                                                              status.axis[2]['velocity']))
        print('Line Num:    {:d}'.format(status.motion_line))
        
        # TODO: 08/03/20 - JEV - Figure out how MachineKit parses comments and empty line
        print('Command:     {}'.format(gcode_stringArray[status.motion_line+1]))
        print('')
    
        if gcode_stringArray[status.motion_line] == 'M2':
            break
        status.poll()

        # Uncomment to wait for a user return key to continue
        # raw_input()

        time.sleep(0.1)

else:
    print("Was not able to switch to auto mode")



    
# Abort any running commands
command.abort()

# Finally, turn the axis off and put back into ESTOP
command.state(linuxcnc.STATE_OFF)
command.wait_complete()
command.state(linuxcnc.STATE_ESTOP)