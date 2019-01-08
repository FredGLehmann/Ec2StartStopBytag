#############################################################################
#
# StartAndStopInstancesByTagReview
# Start or stop EC2 instances regarding the StatrDailyTime or StopDailyTime Tags
#
#############################################################################
#
# Version 5
#
#############################################################################

import os
import time
import stdexplib

region = 'eu-west-1'

#
# Principal function
# As the start and stop commands take in option a list of instances ID
# we are working to build a complete instances ID list, beginnning with all
# runnig instances and remove from the list the instances ID which the stop time is not past
#
def checkthem(actiontime):

    myec2instanceslist = []

    #First step : arret des serveurs qui tournent
    print ("Get Running EC2 Instances and stop them if necessary....")
    myec2instanceslist = stdexplib.get_instanceid_by_state("running",region)
    get_check_actions("Name","StartDailyTime","StopDailyTime","OpeningDays",["i-01a9be017b577d7f8"],"running",actiontime)

    myec2instanceslist = []

    #Second step : demarrage des serveurs arretes
#    print ("Get Stopped EC2 Instances and start them if necessary....")
#    myec2instanceslist = stdexplib.get_instanceid_by_state("stopped",region)
#█  get_check_actions("Name","StartDailyTime","StopDailyTime","OpeningDays",myec2instanceslist,"start",actiontime)

#
# Get some tags values, and ask some other function to check the values
# Input :
#   tag1 => Name
#   tag2 => StartDailyTime
#   tag3 => StopDailyHour
#   tag4 => OpeningDays
#   instanceslist => EC2 instances list to check
#   action => start or stop
# Output : Nothing
def get_check_actions(tag1,tag2,tag3,tag4,instanceslist,state,actiontime):

    idtodel = []
    
    taglist = [tag1,tag2,tag3,tag4]
    instancesdata = stdexplib.get_ec2tagsvalues(region,instanceslist,[tag1,tag2,tag3,tag4])

    for index in range(0, len(instancesdata), 1):
        print (instancesdata[index])
        instanceid = instancesdata[index][0]
        if instancesdata[index][1] == "NO TAG":
            InstanceName = instanceid
        else:
            InstanceName = instancesdata[index][1]

        if instancesdata[index][2] == "NO TAG":
            StartTime = ""
        else:
            StartTime = instancesdata[index][2]

        if instancesdata[index][3] == "NO TAG":
            Stoptime = ""
        else:
            StopTime = instancesdata[index][3]
    
        if instancesdata[index][4] == "NO TAG":
            OpDays = ""
        else:
            OpDays = instancesdata[index][4]
        
        # check the consistency of the values
        if not(stdexplib.verify_time_format(StartTime)) or not(stdexplib.verify_time_format(StopTime)) or not(stdexplib.verify_days_format(OpDays)):
            print (InstanceName+" - "+state+" - Tags missing or format ko : leaving in the actual state")
            idtodel.append(instanceid)
        # Check if we have something todo regarding the different values
        else:
            # if it's a working day
            if stdexplib.check_day(OpDays):
                if stdexploib.check_slot(StartTime,StopTime,state,actiontime) == 0:
                    print (InstanceName+" - "+state+" - State OK")
                    idtodel.append(instanceid)
                elif stdexploib.check_slot(StartTime,StopTime,state,actiontime) == 1:
                    if state == "Running":
                        print (InstanceName+" - "+state+" - To Stop")
                    else:
                        print (InstanceName+" - "+state+" - To Start")
                elif stdexploib.check_slot(StartTime,StopTime,state,actiontime) == 2:
                    if state == "stopped":
                        print (InstanceName+" - "+state+" - To Start")
            # If it's not a working day
            elif (not(stdexplib.check_day(OpDays))):
                if state == "running":
                    print (InstanceName+" - "+state+" - To Stop")
                elif state == "stopped":
                    print (InstanceName+" - "+state+" - State OK")
                    idtodel.append(instanceid)
            # Fall back
            else:
                print (InstanceName+" : WARNING - Do not know which action to take : leaving in the actual state")
                idtodel.append(instanceid)

    for id in idtodel:
        instanceslist.remove(id)

    if len(instanceslist) > 0:
        print (len(instanceslist)," instance(s) to ",action)
        stdexplib.ec2instances_action(instanceslist,action)
    else:
        print ("0 instance to ",action)

#
# Main for Lambda
#
def lambda_handler(event, context):
    
    from time import strftime
    
    # Print default lambda time
    print ("Lambda default TimeZone : " + os.environ['TZ'])
    
    # Get the MYTIMEZONE environment variable, if not exist set it to Paris timezone
    myTZ=os.getenv('MYTIMEZONE','Europe/Paris')
    # Set the lambda local TZ
    os.environ['TZ'] = myTZ
    time.tzset()
    lambdatime=strftime("%H:%M:%S").upper()
    print ("Right local TimeZone/Time : "+myTZ+"/"+ lambdatime)
    
    # go 
    checkthem(lambdatime)

#
# Main for Python Origin
#
#print ("Gooooo !!!!")
#lambda_handler("","")
