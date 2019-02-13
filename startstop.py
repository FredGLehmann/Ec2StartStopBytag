#############################################################################
#
# StartAndStopInstancesByTagReview
# Start or stop EC2 and RDS instances regarding the StatrDailyTime/StopDailyTime
# and OpeningDays tags
#
#############################################################################
#
# Version 5
#
#############################################################################

import os
import time
import stdexplib

region=os.getenv('REGION','eu-west-1')

#
# Principal function
# As the start and stop commands take in option a list of instances ID
# we are working to build a complete instances ID list, beginnning with all
# runnig instances and remove from the list the instances ID which the stop time is not past
#
def checkthem(actiontime):

    myec2instanceslist = []
    instancesdata = []

    taglist = ["Name","StartDailyTime","StopDailyTime","OpeningDays"]

    # First step : list the running servers and see if we must stop them
    #
    print ("Get Running EC2 Instances and stop them if necessary....")
    myec2instanceslist = stdexplib.get_ec2instanceid_by_state("running",region)
    instancesdata = stdexplib.get_ec2tagsvalues(region,myec2instanceslist,taglist)
    actionlist = get_check_actions(instancesdata,myec2instanceslist,"running",actiontime)
    if len(actionlist) > 0:
        print (len(actionlist),"running instance(s) to stop")
        stdexplib.ec2instances_action(actionlist,"stop",region)
    else:
        print ("0","running instance to stop")

    myec2instanceslist = []
    instancesdata = []

    # Second step : list the stopped servers and see if we must start them
    #
    print ("Get Stopped EC2 Instances and start them if necessary....")
    myec2instanceslist = stdexplib.get_ec2instanceid_by_state("stopped",region)
    instancesdata = stdexplib.get_ec2tagsvalues(region,myec2instanceslist,taglist)
    actionlist = get_check_actions(instancesdata,myec2instanceslist,"stopped",actiontime)
    if len(actionlist) > 0:
        print (len(actionlist),"stopped instance(s) to start")
        stdexplib.ec2instances_action(actionlist,"start",region)
    else:
        print ("0","stopped instance to start")

    # Third step : list the stopped RDS instances and see if we must start them
    #
    print ("Get Stopped RDS Instances and start them if necessary....")
    myrdsinstanceslist = stdexplib.get_ec2instanceid_by_state("stopped",region)
    instancesdata = stdexplib.get_rdstagsvalues(region,myrdsinstanceslist,taglist)
    actionlist = get_check_actions(instancesdata,myrdsinstanceslist,"stopped",actiontime)
    if len(actionlist) > 0:
        print (len(actionlist),"stopped instance(s) to start")
        stdexplib.rdsinstances_action(actionlist,"start",region)
    else:
        print ("0","stopped instance to start")

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
def get_check_actions(instancesdata,instanceslist,state,actiontime):

    idtodel = []
    
#    taglist = [tag1,tag2,tag3,tag4]
#    instancesdata = stdexplib.get_ec2tagsvalues(region,instanceslist,[tag1,tag2,tag3,tag4])

    for index in range(0, len(instancesdata), 1):
        # print (instancesdata[index])
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
            if state == "running":
                if stdexplib.check_slot2(StartTime,StopTime,actiontime,OpDays) == 0:
                    print (InstanceName+" - "+state+" - To Stop")
                elif stdexplib.check_slot2(StartTime,StopTime,actiontime,OpDays) == 1:
                    print (InstanceName+" - "+state+" - State OK")
                    idtodel.append(instanceid)
                elif stdexplib.check_slot2(StartTime,StopTime,actiontime,OpDays) == 2:
                    print (InstanceName+" - "+state+" - Manual Start and Stop")
                    idtodel.append(instanceid)
                elif stdexplib.check_slot2(StartTime,StopTime,actiontime,OpDays) == 3:
                    print (InstanceName+" - "+state+" - State Ok")
                    idtodel.append(instanceid)
                elif stdexplib.check_slot2(StartTime,StopTime,actiontime,OpDays) == 4:
                    print (InstanceName+" : WARNING - Do not know which action to take : leaving in the actual state")
                    idtodel.append(instanceid)
            elif state == "stopped":
                if stdexplib.check_slot2(StartTime,StopTime,actiontime,OpDays) == 0:
                    print (InstanceName+" - "+state+" - State OK")
                    idtodel.append(instanceid)
                elif stdexplib.check_slot2(StartTime,StopTime,actiontime,OpDays) == 1:
                    print (InstanceName+" - "+state+" - To Start")
                elif stdexplib.check_slot2(StartTime,StopTime,actiontime,OpDays) == 2:
                    print (InstanceName+" - "+state+" - Manual Start and Stop")
                    idtodel.append(instanceid)
                elif stdexplib.check_slot2(StartTime,StopTime,actiontime,OpDays) == 3:
                    print (InstanceName+" - "+state+" - State Ok")
                    idtodel.append(instanceid)
                elif stdexplib.check_slot2(StartTime,StopTime,actiontime,OpDays) == 4:
                    print (InstanceName+" : WARNING - Do not know which action to take : leaving in the actual state")
                    idtodel.append(instanceid)
            # Fall back
            else:
                print (InstanceName+" : WARNING - Do not know which action to take : leaving in the actual state")
                idtodel.append(instanceid)

    for id in idtodel:
        instanceslist.remove(id)

    return instanceslist


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
