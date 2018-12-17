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
# Output : value of the tag 
#
def get_ec2tagvalue(instanceid,tagname,region):

    import boto3
    tagvalue = ""

    myec2 = boto3.resource(
        'ec2',
        region_name=region
    )

    myinstance = myec2.Instance(instanceid)

    if myinstance.tags:
        if myinstance.tags == "":
            tagvalue = ""
        else:
            for tags in myinstance.tags:
                if tags["Key"] == tagname:
                    tagvalue = tags["Value"]
    else:
        tagvalue = ""

    return tagvalue

#####################################################################################################################
