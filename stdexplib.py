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
