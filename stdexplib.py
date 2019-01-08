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
# Verify if in the parameter data, we can find a day similar to today
#
# Input1 : data to analyse (some days in three digit format, enclosed by "'")
# Output : True (today is integrated in data) or False (today is not integrated in data)
#
def check_day(data):

    from time import strftime
    n = 0

    actualday = strftime("%a").upper()

    datasplit=data.split(",")
    for day in datasplit:
        if day == actualday:
            n=1

    if n == 1:
        return True
    else:
        return False

#####################################################################################################################
#
#####################################################################################################################
#
# Verify if in the parameter data, we can find a day similar to today
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

    # If StartTime = 99
    #   If StopTime=99 => do nothing
    #   Else
    #       If state=running and StopTime<ActualTime => stop server
    #       Else
    #       Do nothing
    # And If StopTime = 99
    #   If StartTime=99 => Do nothing
    #   Else
    #       If State=stopped and StartTime<ActualTime => Start Server
    #       Else
    #       Do nothing
    # And If StartTime<>99 and StopTime<>99 and StartTime=StopTime => 2
    # Else
    #   If State=stopped
    #       If StartTime<Actualtime and StopTime>ActualTime => Start Server
    #       Else => Do nothing
    #   Else If State=running
    #       If StartTime<ActualTime and StopTime>ActualTime or StartTime>ActuelTime and StopTime> ActualTime => Stop Server
    #       Else => Do nothing
    #   Else
    #       => Do nothing

    if int(tagvalue1[:2]) == 99:
        if int(tagvalue2[:2]) == 99:
            return 0
        else:
            if state == "running" and check_time(tagvalue2,actiontime) == 1:
                return 1
            else:
                return 0
    elif int(tagvalue2[:2]) == 99:
        if int(tagvalue1[:2]) == 99:
            return 0
        else:
            if state == "stopped" and check_time(tagvalue1,actiontime) == 1:
                return 1
            else:
                return 0
    elif (int(tagvalue1[:2]) != 99) and (int(tagvalue2[:2]) != 99) and (tagvalue1 == tagvalue2):
        return 2
    else:
        if state == "stopped":
            if check_time(tagvalue1,actiontime) == 1 and check_time(tagvalue2,actiontime) == 0:
                return 1
            else:
                return 0
        elif state == "running":
            if (check_time(tagvalue1,actiontime) == 1 and check_time(tagvalue2,actiontime) == 1) or (check_time(tagvalue1,actiontime) == 0 and check_time(tagvalue2,actiontime) == 0):
                return 1
            else:
                return 0
        else:
            return 0

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
def ec2instances_action(instanceslist,action):

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
