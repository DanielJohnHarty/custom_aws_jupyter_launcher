import boto3
import os
import time

def get_ec2_client(region, aws_access_key_id, aws_secret_access_key):

    try:
        ec2 = boto3.client(
            "ec2",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region,
        )

    except Exception as e:
        print(f"Unable to create client object. Error:\n{e}\nExiting...")

    try:
        _ = ec2.describe_account_attributes()
    except Exception as e:
        print(f"Unable to validate client object. Error:\n{e}")

    return ec2

def build_vpc(ec2_client, VPC_CIDR_BLOCK, TAG_ROOT):
    try:
        vpc_data = ec2_client.create_vpc(CidrBlock=VPC_CIDR_BLOCK)

        VpcId = vpc_data["Vpc"]["VpcId"]
        vpc_waiter = ec2_client.get_waiter("vpc_exists")
        vpc_waiter.wait(VpcIds=[VpcId])

        ec2_client.create_tags(
            Resources=[VpcId],
            Tags=[{"Key": "Name", "Value": TAG_ROOT + "_VPC"}],
        )
        print(VpcId)
        result = VpcId

    except Exception as e:
        print(e)
        sys.exit()

    return result

def build_subnet(ec2_client, VpcId, PUBLIC_SUBNET_CIDR_BLOCK, TAG_ROOT):

    try:
        subnet_data = ec2_client.create_subnet(
            VpcId=VpcId, CidrBlock=PUBLIC_SUBNET_CIDR_BLOCK
        )
        subnet_id = subnet_data["Subnet"]["SubnetId"]
        ec2_client.create_tags(
            Resources=[subnet_id],
            Tags=[{"Key": "Name", "Value": TAG_ROOT + "_Public_Subnet"}],
        )

    except Exception as e:
        print(e)

    return subnet_id

def build_igw(ec2_client, VpcId, TAG_ROOT):

    try:
        igw_data = ec2_client.create_internet_gateway()
        igw_id = igw_data["InternetGateway"]["InternetGatewayId"]
        ec2_client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=VpcId)
        ec2_client.create_tags(
            Resources=[igw_id],
            Tags=[{"Key": "Name", "Value": TAG_ROOT + "_IGW"}],
        )

    except Exception as e:
        print(e)
        sys.exit()

    return igw_id

def build_route_table(ec2_client, VpcId, subnet_id, igw_id, TAG_ROOT):

    try:
        route_table_data = ec2_client.create_route_table(VpcId=VpcId)
        route_tbl_id = route_table_data["RouteTable"]["RouteTableId"]
        ec2_client.create_tags(
            Resources=[route_tbl_id],
            Tags=[{"Key": "Name", "Value": TAG_ROOT + "_RouteTable"}],
        )
        ec2_client.create_route(
            RouteTableId=route_tbl_id,
            DestinationCidrBlock="0.0.0.0/0",
            GatewayId=igw_id,
        )

        ec2_client.associate_route_table(RouteTableId=route_tbl_id, SubnetId=subnet_id)

    except Exception as e:
        print(e)
        sys.exit()

    return route_tbl_id

def build_keypair(ec2_client, TAG_ROOT):
    key_pair_name = TAG_ROOT + "_KEY_PAIR"

    try:
        kp = ec2_client.create_key_pair(KeyName=key_pair_name)

        # Write keypair to a local file
        privatekey = kp["KeyMaterial"]
        filename = key_pair_name + ".pem"
        write_keypair_to_file(filename, privatekey)

    except Exception as e:
        print(e)
        print("Looks like that keypair_name already exists. So you already have it.")
        pass

    return key_pair_name

def write_keypair_to_file(filename, key_material):
    """
    Writes the creted keypair to a local file.
    """
    if os.path.exists(filename):
        os.remove(filename)

    with open(filename, "w") as file:
        file.write(key_material)

def add_security_group_rule(ec2_client, security_group_id, INSTANCE_ACCESS_PORT):
    ec2_client.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": int(INSTANCE_ACCESS_PORT),
                "ToPort": int(INSTANCE_ACCESS_PORT),
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            }
        ],
    )

def build_security_group(ec2_client, VpcId, INSTANCE_ACCESS_PORT, TAG_ROOT):

    try:
        security_group_response_data = ec2_client.create_security_group(
            GroupName=TAG_ROOT + "_SECURITY_GROUP",
            Description=TAG_ROOT + "_SECURITY_GROUP",
            VpcId=VpcId,
        )

        ec2_client.get_waiter("security_group_exists").wait()
        security_group_id = security_group_response_data["GroupId"]
        ec2_client.create_tags(
            Resources=[security_group_id],
            Tags=[{"Key": "Name", "Value": TAG_ROOT + "_SECURITY_GROUP"}],
        )
    except Exception as e:
        print("Couldn't create security group. Error:")
        print(e)
        pass

    try:
        add_security_group_rule(ec2_client, security_group_id, INSTANCE_ACCESS_PORT)
        print("Added rule to security group")

    except Exception as e:
        print("Couldn't add rule to security group. Error:")
        print(e)
        pass

    return security_group_id

def allocate_public_ip(ec2_client):

    try:
        allocated_ip_data = ec2_client.allocate_address()
        allocation_id = allocated_ip_data["AllocationId"]
        public_ip = allocated_ip_data["PublicIp"]
        result = (public_ip, allocation_id)
    except Exception as e:
        print("Unable to allocate public IP. Error:")
        print(e)
        result = "e", "e"

    return result

def associate_public_ip(ec2_client, instance_id, allocation_id):

    print(f"""Just wait a few seconds before asociating a public IP please..""")
    while True:
        try:
            ec2_client.associate_address(
                InstanceId=instance_id, AllocationId=allocation_id
            )
            break
        except Exception as e:
            print(f"Error associating public IP. Error:\n{e}")
            print(f"""Retrying in 10 seconds...""")
            time.sleep(10)

def build_ec2_instance(ec2_client, instance_ami, security_group_id, subnet_id, key_pair_name, instance_type, userdata, TAG_ROOT):
    try:
        instance_data = ec2_client.run_instances(
            ImageId=instance_ami,
            KeyName=key_pair_name,
            MinCount=1,
            MaxCount=1,
            SecurityGroupIds=[security_group_id],
            SubnetId=subnet_id,
            UserData=userdata,
            InstanceType=instance_type,
        )

        instance_id = instance_data["Instances"][0]["InstanceId"]
        ec2_client.create_tags(
            Resources=[instance_id],
            Tags=[{"Key": "Name", "Value": TAG_ROOT + "_Instance"}],
        )

    except Exception as e:
        print("Error creating EC2 instance. Error:")
        print(e)
        instance_id = e
        pass

    return instance_id
