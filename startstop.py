#############################################################################
#
# StartAndStopInstancesByTagReview
# Start or stop EC2 instances regarding the StatrDailyTime or StopDailyTime Tags
#
#############################################################################
#
# Version 3
#
#############################################################################

import boto3
import os
import time

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
    myec2instanceslist = get_instanceid_by_state("running")
    get_check_actions("Name","StartDailyTime","StopDailyTime","OpeningDays",myec2instanceslist,"stop",actiontime)

    myec2instanceslist = []

    #Second step : demarrage des serveurs arretes
    print ("Get Stopped EC2 Instances and start them if necessary....")
    myec2instanceslist = get_instanceid_by_state("stopped")
    get_check_actions("Name","StartDailyTime","StopDailyTime","OpeningDays",myec2instanceslist,"start",actiontime)

#
# Get all the EC2 instances ID by state
# Input : running / stopped
# Output : list of running or stopped instances ID
def get_instanceid_by_state(state):

    instanceslist = []

    ec2 = boto3.client(
        'ec2',
        region_name=region
    )

    ec2instances = ec2.describe_instances(
        Filters=[
            {
                'Name': 'instance-state-name', 'Values': [state]
            }
        ]
    )

    for reservation in (ec2instances["Reservations"]):
        for instance in reservation["Instances"]:
            instanceslist.append(instance["InstanceId"])

    return instanceslist

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
def get_check_actions(tag1,tag2,tag3,tag4,instanceslist,action,actiontime):

    idtodel = []

    myec2 = boto3.resource(
        'ec2',
        region_name=region
    )

    # For each instance in instancelist, get the tags values
    for instanceid in instanceslist:
        myinstance=myec2.Instance(instanceid)
        InstanceName = ""
        StartTime = ""
        StopTime = ""
        OpDays = ""
        for tags in myinstance.tags:
            if tags["Key"] == tag1:
                InstanceName = tags["Value"]
            elif tags["Key"] == tag2:
                StartTime = tags["Value"]
            elif tags["Key"] == tag3:
                StopTime = tags["Value"]
            elif tags["Key"] == tag4:
                OpDays = tags["Value"]

        # check the consistency of the values
        if not(verify_time_format(StartTime)) or not(verify_time_format(StopTime)) or not(verify_days_format(OpDays)):
            print (InstanceName+" : Tags missing or format ko")
            idtodel.append(instanceid)
        # Check if we have something todo regarding the different values
        else:
                # if it's a working day
            if check_day(OpDays):
                if check_slot(StartTime,StopTime,action,actiontime) == 0:
                    print (InstanceName+" : State OK")
                    idtodel.append(instanceid)
                elif check_slot(StartTime,StopTime,action,actiontime) == 1:
                    print (InstanceName+" : To "+action)
                elif check_slot(StartTime,StopTime,action,actiontime) == 2:
                    if action == "start":
                        print (InstanceName+" : To Start")
            elif (not(check_day(OpDays))) and (check_slot(StartTime,StopTime,action,actiontime) == 2) and (action == "stop"):
                print (InstanceName+" : To Stop")

    for id in idtodel:
        instanceslist.remove(id)

    if len(instanceslist) > 0:
        ec2instances_action(instanceslist,action)

#
# Check the correct configuration of a time data based on REGEXP
# Input : StartDailyTime or StopDailyTime tag value
# Output :
#   True if formzt is ok
#   False if format is ko
#
def verify_time_format(tagvalue):

    import re

    if re.match('^[0-9]{2}\:[0-9]{2}\:[0-9]{2}\+[0-9]{2}\:[0-9]{2}$',tagvalue):
        if int(tagvalue[:2])==99:
            return True
        if (int(tagvalue[:2])>23) or (int(tagvalue[3:5])>59) or (int(tagvalue[6:8])>59):
            print (tagvalue+" : Time Format OK - Data KO")
            return False
        else:
            return True
    else:
        # print (tagvalue+" : Time Format KO")
        return False

#
# Check the correct configuration of a day data based on REGEXP
# Input : Openingays tag value
# Output :
#   True if formzt is ok
#   False if format is ko
#
def verify_days_format(tagvalue):

    import re

    if re.match('^[aA-zZ]{3}(,[aA-zZ]{3})*$',tagvalue):
        return True
        print (tagvalue + " : OpeningDays Format KO")
    else:
        return False

#
# Check if today we must start the instances
# Input : Openingays tag value
# Output :
#   True if it's a working day
#   False if it's not a working day
#
def check_day(tagvalue):

    from time import strftime
    n = 0

    actualday = strftime("%a").upper()

    tagsplit=tagvalue.split(",")
    for day in tagsplit:
        if day == actualday:
            n=1

    if n == 1:
        return True
    else:
        return False


#
# Check if it is the good time to do something
# Input :
#   StartTime
#   StopTime
#   State of the instance
#
# Output
#   0 : do nothing
#   1 : start or stop the instance
#   2 : start and stop time are the same (but not 99)
#
def check_slot(tagvalue1,tagvalue2,state,actiontime):

    #print ("StartTime : "+tagvalue1)
    #print ("StopTime : "+tagvalue2)

    if int(tagvalue1[:2]) == 99:
        if int(tagvalue2[:2]) == 99:
            return 0
        else:
            if state == "stop" and check_time(tagvalue2,actiontime) == 1:
                return 1
            else:
                return 0
    elif int(tagvalue2[:2]) == 99:
        if int(tagvalue1[:2]) == 99:
            return 0
        else:
            if state == "start" and check_time(tagvalue1,actiontime) == 1:
                return 1
            else:
                return 0
    elif (int(tagvalue1[:2]) != 99) and (int(tagvalue2[:2]) != 99) and (tagvalue1 == tagvalue2):
        return 2
    else:
        if state == "start":
            if check_time(tagvalue1,actiontime) == 1 and check_time(tagvalue2,actiontime) == 0:
                return 1
            else:
                return 0
        elif state == "stop":
            if (check_time(tagvalue1,actiontime) == 1 and check_time(tagvalue2,actiontime) == 1) or (check_time(tagvalue1,actiontime) == 0 and check_time(tagvalue2,actiontime) ==
 0):
                return 1
            else:
                return 0
        else:
            return 0

#
# Check if it is the good time to do something
# Input : StartDailyTime or StopDailyTime tag value
# Output : 0 if ok / 1 if ko / 2 if 99
#
def check_time(tagvalue,actiontime):

    from datetime import time
    
    actualtime = time(int(actiontime[:2]), int(actiontime[3:5]), int(actiontime[6:8]))
    idgmttime = time(int(tagvalue[:2]), int(tagvalue[3:5]), int(tagvalue[6:8]))
    
    #now = datetime.now()
    #actualtime = now.time()
    #if tagvalue[8:9] == "+":
    #    idgmttime = time(int(tagvalue[:2])-int(tagvalue[9:11]), int(tagvalue[3:5]), int(tagvalue[6:8]))
    #else:
    #    idgmttime = time(int(tagvalue[:2])+int(tagvalue[9:11]), int(tagvalue[3:5]), int(tagvalue[6:8]))

    if idgmttime <= actualtime:
        return 1
    else:
        return 0

#
# Start or Stop EC2 instances
# Input :
#   instanceslist => list of EC2 instances ID
#   action => action to perform on the instances in the list
# Output : Nothing
#
def ec2instances_action(instanceslist,action):

    ec2 = boto3.client('ec2', region_name=region)

    print("Action : "+ action)

    #if action == "start":
    #    ec2.start_instances(InstanceIds=instanceslist)
    #else:
    #    ec2.stop_instances(InstanceIds=instanceslist)

#
# Main
#
def lambda_handler(event, context):
    
    from time import strftime
    
    # Print default lambda time
    print ("Lambda default time : " + os.environ['TZ'])
    
    # Get the MYTIMEZONE environment variable, if not exist set it to Paris timezone
    myTZ=os.getenv('MYTIMEZONE','Europe/Paris')
    # Set the lambda local TZ
    os.environ['TZ'] = myTZ
    time.tzset()
    lambdatime=strftime("%H:%M:%S").upper()
    print ("Right local time : "+ lambdatime)
    
    # go 
    checkthem(lambdatime)

