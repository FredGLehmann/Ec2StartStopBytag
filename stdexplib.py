#####################################################################################################################
#
# Library for all standard function in infrastructure exploitation
#
# frederic.lehmann@transdev.com
#
#####################################################################################################################
#
# Functions Summary
#
#	- get_instanceid_by_state(state) / get all the Running or Stoped instances ID
#       - get_ec2tagsvalues(region,instanceslist,tagslist) / get some tags values from an instances ID list
#       - verify_time_format(data) / check data format for time rekognition
#       - verify_days_format(data) / check data format for days rekognition
#       - check_slot(starttime,stoptime,state,actiontime) / 
#       - check_time(data,actiontime) / comprare time in data to actual time
#       - ec2instances_action(instanceslist,action) /  start or stop instances, based on ID instances list
#
#####################################################################################################################


#####################################################################################################################
#
# Get all the EC2 instances ID by state
#
# Input1 : running / stopped
# Input2 : AWS region
# Output : list of running or stopped instances ID
#
def get_instanceid_by_state(state,region):

    import boto3

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

#####################################################################################################################
#
#####################################################################################################################
#
# Get an EC2 tag value
#
# Input1 : instance ID
# Input2 : tags name
# Input3 : AWS region
# Output : list
# Output Format : [instanceid1,instance1tag1,instance1tag2,....],[instanceid2,instance2tag1,instance2tag2,...],....
#
def get_ec2tagsvalues(region,instanceslist,tagslist):

    import boto3
    returnlist = []
    tempodata = []

    ec2 = boto3.resource(
        'ec2',
        region_name=region
    )
    print ("list :",len(instanceslist))
    for index1 in range(0, len(instanceslist), 1):
        myinstance = ec2.Instance(instanceslist[index1])
        tempodata.append(instanceslist[index1])
        if myinstance.tags:
            if myinstance.tags == "":
                tagvalue = ""
            else:
                for index2 in range(0, len(tagslist), 1):
                    for tags in myinstance.tags:
                        if tags["Key"] == tagslist[index2]:
                            tempodata.append(tags["Value"])
                            find = 1
                    if not(find == 1):
                        tempodata.append("NO TAG")
                    find = 0
        else:
            tempodata.append("NO TAG")
            tempodata.append("NO TAG")
            tempodata.append("NO TAG")
            tempodata.append("NO TAG")

        returnlist.append(tempodata)
        tempodata = []

    return returnlist

#####################################################################################################################
#
#####################################################################################################################
#
# Get RDS tag value
#
# Input1 : instance List
# Input2 : tags name
# Input3 : AWS region
# Output : list
# Output Format : [instanceid1,instance1tag1,instance1tag2,....],[instanceid2,instance2tag1,instance2tag2,...],....
#
def get_rdstagsvalues(region,instanceslist,tagslist):

#####################################################################################################################
#
# Verify if the parameter is well formated for time rekognition (HH:MM:SS+HH:MM:SS)
#
# Input1 : data to analyse
# Output : True (format ok) or False (format ko)
#
def verify_time_format(data):

    import re

    if re.match('^[0-9]{2}\:[0-9]{2}\:[0-9]{2}\+[0-9]{2}\:[0-9]{2}$',data):
        if int(data[:2])==99:
            return True
        if (int(data[:2])>23) or (int(data[3:5])>59) or (int(data[6:8])>59):
            print (data+" : Time Format OK - Data KO")
            return False
        else:
            return True
    else:
        # print (data+" : Time Format KO")
        return False

#####################################################################################################################
#
#####################################################################################################################
#
# Verify if the parameter is well formated for date rekognition (MON,TUE,....)
#
# Input1 : data to analyse
# Output : True (format ok) or False (format ko)
#
def verify_days_format(data):

    import re

    if re.match('^[aA-zZ]{3}(,[aA-zZ]{3})*$',data):
        return True
        print (data + " : OpeningDays Format KO")
    else:
        return False

#####################################################################################################################
#
#####################################################################################################################
#
# Verify if today and tomorrow is a working day
#
# Input1 : data to analyse (some days in three digit format, enclosed by "'")
# Output : 
#       0 => today and yesterday are not working days
#       1 => today is a working day but not yesterady
#       2 => only yesterday is a working day
#       3 => today and yesterday are working days
#       4 => Fall back
#
def check_day(data):

    from time import strftime
    td = 0
    ye = 0

    fullweek = ["SUN","MON","TUE","WED","THU","FRI","SAT"]
    today = strftime("%a").upper()
    weekindex = strftime("%w")

    if int(weekindex) == 0:
        yesterday = fullweek[6]
    else:
        yesterday = fullweek[int(weekindex)-1]

    datasplit=data.split(",")
    for day in datasplit:
        if day == today:
            td=1
        elif day == yesterday:
            ye=1

    if td == 0 and ye == 0:
        return 0                # Today and yesterday are not working days
    elif td == 1 and ye == 0:
        return 1                # Today is a working day but not yesterday
    elif td == 0 and ye == 1:
        return 2                # only yesterday was a working day
    elif td == 1 and ye == 1:
        return 3                # Today and yesterday are working days
    else:
        return 4

#####################################################################################################################
#
#####################################################################################################################
#
# Verify if is the timeslot is the good one
#
# Input1 : starttime of the AWS object
# Input2 : stoptime of the AWS object
# Input3 : actual state of the AWS object (running/stopped)
# Output :  0 => do nothing
#           1 => action
#           2 => starttime and stoptime are the same but not 99
#
def check_slot(starttime,stoptime,state,actiontime):

    #print ("StartTime : "+tagvalue1)
    #print ("StopTime : "+tagvalue2)

    # If StartTime = 99                                                 (Manual start)
    #   If StopTime=99 => do nothing                                    (manual start and manual stop)
    #   Else
    #       If state=running and StopTime<ActualTime => stop server     (server running and stop time is past)
    #       Else
    #       Do nothing
    # AndIf StopTime = 99
    #   If StartTime=99 => Do nothing                                   (manual start and stop)
    #   Else
    #       If State=stopped and StartTime<ActualTime => Start Server   (server stopped and start time past)
    #       Else
    #       Do nothing
    # And If StartTime<>99 and StopTime<>99 and StartTime=StopTime => 2 (start and stop are equal, referencing to workdays only)
    # Else
    #   If State=stopped
    #       If StartTime<Actualtime and StopTime>ActualTime => Start Server
    #       Else => Do nothing
    #   Else If State=running
    #       If StartTime<ActualTime and StopTime>ActualTime or StartTime>ActuelTime and StopTime> ActualTime => Stop Server
    #       Else => Do nothing
    #   Else
    #       => Do nothing
    #
    #
    # AndIf StartTime<Stoptime                                               (timeslot based on a week day )
    #   If State=stopped
    #       If StartTime<Actualtime and StopTime>ActualTime => Start Server
    #       Else => Do nothing
    #   Else If State=running
    #       If StartTime<ActualTime and StopTime>ActualTime or StartTime>ActuelTime and StopTime> ActualTime => Stop Server
    #       Else => Do nothing
    #   Else
    #       => Do nothing

    # AndIf StartTime>StopTime                                              (timeslot based on a night work)
    #   If State=stopped
    #       If StartTime<Actualtime and StopTime<ActualTime or StartTime>ActualTime and StopTime>ActualTime => Start Server (before or after the stop slot of the day)
    #       Else => Do nothing
    #   Else If State=running
    #       If StartTime>ActualTime and StopTime<ActualTime => Stop Server      (in the stop slot)
    #       Else => Do nothing
    #   Else
    #       => Do nothing
    # Else
    #   => Do Nothing

    if int(starttime[:2]) == 99:
        if int(stoptime[:2]) == 99:
            return 0
        else:
            if state == "running" and check_time(tagvalue2,actiontime) == 1:
                return 1
            else:
                return 0
    elif int(stoptime[:2]) == 99:
        if int(starttime[:2]) == 99:
            return 0
        else:
            if state == "stopped" and check_time(tagvalue1,actiontime) == 1:
                return 1
            else:
                return 0
    elif (int(starttime[:2]) != 99) and (int(stoptime[:2]) != 99) and (starttime == stoptime):
        return 2
    elif (starttime < stoptime):
        if state == "stopped":
            if check_time(starttime,actiontime) == 1 and check_time(stoptime,actiontime) == 0:
                return 1
            else:
                return 0
        elif state == "running":
            if (check_time(starttime,actiontime) == 1 and check_time(stoptime,actiontime) == 1) or (check_time(starttime,actiontime) == 0 and check_time(stoptime,actiontime) == 0):
                return 1
            else:
                return 0
        else:
            return 0
    elif (starttime > stoptime):
        if state == "stopped":
            if (check_time(starttime,actiontime) == 1 and check_time(stoptime,actiontime) == 1) or (check_time(starttime,actiontime) == 0 and check_time(stoptime,actiontime) == 0):
                return 1
            else:
                return 0
        elif state == "running":
            if check_time(starttime,actiontime) == 0 and check_time(stoptime,actiontime) == 1:
                return 1
            else:
                return 0
        else:
            return 0

#####################################################################################################################
#
#####################################################################################################################
#
# Check if we are or not in a running slot
#
# Input1 : starttime of the AWS object
# Input2 : stoptime of the AWS object
# Input3 : openingsdays
# Output :  0 => Not a running slot
#           1 => Running Slot
#           2 => manual start and stop
#           3 => cannot determine
#
def check_slot2(starttime,stoptime,actiontime,actionday):

    # check if one of the data time is 99
    if int(starttime[:2]) == 99:
        if int(stoptime[:2]) == 99:
            return 2
        else:
            if check_time(stoptime,actiontime) == 1:
                return 0
            else:
                return 1
    elif int(stoptime[:2]) == 99:
        if int(starttime[:2]) == 99:
            return 2
        else:
            if check_time(starttime,actiontime) == 1:
                return 1
            else:
                return 0

    # check if we are on a day slot or a night slot
    if (starttime < stoptime):              # We are in a day slot
        if check_time(starttime,actiontime) == 1 and check_time(stoptime,actiontime) == 0 and check_day(actionday):
            return 1
        else:
            return 0
    elif (starttime > stoptime):            # We are in a night slot
        if check_time(starttime,actualtime) == 1 and check_time(starttime,"23:59:59") == 0 and (check_day(actionday) == 1 or check_day(actionday) == 3):
            return 1
        elif check_time(starttime,"23:59:59") == 1 and check_time(stoptime,actualtime) and (check_day(actionday) == 1 or check_day(actionday) == 2 or check_day(actionday) == 3):
            return 1
        else:
            return 0
    elif (int(starttime[:2]) != 99) and (int(stoptime[:2]) != 99) and (starttime == stoptime):      # we are in a 24/24 slot
        if check_day(actionday) == 1 or check_day(actionday) == 3:
            return 1
        else:
            return 0

    else:
        return 3

#####################################################################################################################
#
#####################################################################################################################
#
# Verify if time in parameter is in advance or late compared to the actual time
#
# Input1 : time
# Output :  0 => time in parameter is greater than actual time
#           1 => time in parameter is less or equal than actual time
#
def check_time(data,actiontime):

    from datetime import time

    actualtime = time(int(actiontime[:2]), int(actiontime[3:5]), int(actiontime[6:8]))
    idgmttime = time(int(data[:2]), int(data[3:5]), int(data[6:8]))

    if idgmttime <= actualtime:
        return 1
    else:
        return 0

#####################################################################################################################
#
#####################################################################################################################
#
# Action for Ec2 Instances
#
# Input1 : ID list of instances
# Output : Nothing
#
def ec2instances_action(instanceslist,action,region):

    import boto3

    ec2 = boto3.client('ec2', region_name=region)

    if action == "start":
        for id in instanceslist:
            print (id+" starting")
        #ec2.start_instances(InstanceIds=instanceslist)
    else:
        for id in instanceslist:
            print (id+" stopping")
        #ec2.stop_instances(InstanceIds=instanceslist)

#####################################################################################################################
# The End
#####################################################################################################################
