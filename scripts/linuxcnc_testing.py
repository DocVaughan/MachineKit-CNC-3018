#! /usr/bin/env python

###############################################################################
# linuxcnc_testing.py
#
# Script for testing linuxcnc commands for control of the CNC 3018 mill 
# MachineKit setup. The intention is to test commands here before integration 
# with the Flask-socketio-based interface. 
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
#   * 
#
# TODO:
#   * Update to Python 3
###############################################################################

import linuxcnc
import time

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

for x in dir(s):
    if not x.startswith('_'):
        print x, getattr(s,x)


# Rest the e-stop and enable the axes
command.state(linuxcnc.STATE_ESTOP_RESET)
command.state(linuxcnc.STATE_ON)

# Switch to manual mode
command.mode(linuxcnc.MODE_MDI)

# Home the axes at their current positions
command.home(0)  # Home the x-axis
command.home(1)  # Home the y-axis
command.home(2)  # Home the z-axis

# Jog the x-axis 1-inch
JOG_SPEED = 0.1
JOG_DISTANCE = 1.0
command.jog(linuxcnc.JOG_INCREMENT, 0, JOG_SPEED, JOG_DISTANCE)

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

if ok_for_mdi():
   command.mode(linuxcnc.MODE_MDI)
   command.wait_complete()  # wait until mode switch executed
   command.mdi("G0 X1.0 Y1.0 Z0.1")