import configparser
import time
import os
import datetime
import sys
import pickle
import boto3
import gui_elements

class Instance:
    def log_warnings(func, *args, **kwargs):
        """
        On failure prints exception plus warning to 
        check everything on AWS console
        """

        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(
                    f"""Error during self_destruct. Loging to your AWS console
                      to be sure that all the instances pieces have been removed.
                      incurr charges whether you are using them or not, so be diligent and
                      check manually that nothing has been left behind in the auto-destruct sequence.
                      The error details are as follows:\n{e}"""
                )
                sys.exit()

        return wrapper

    def __init__(self):
        self.region = None
        self.vpc_id = None
        self.igw_id = None
        self.keypair_name = None
        self.subnet_id = None
        self.route_table_id = None
        self.security_group_id = None
        self.ec2_instance_id = None
        self.public_ip = None
        self.allocation_id = None

    def __str__(self):
        s = ""
        for att in vars(self):
            value = self.__getattribute__(att)
            s += f"{att} -> {value}\n"
        return s

    def __repr__(self):
        return self.__str__()


    def self_destruct(self, client):
        """
        Order of destroy methods matters
        """

        if self.ec2_instance_id:
            self.destroy_ec2_instance(client)

        if self.keypair_name:
            self.destroy_keypair(client)
            self.destroy_keypair_file()

        if self.public_ip:
            self.destroy_elastic_ip(client)

        if self.igw_id:
            self.destroy_internet_gateway(client)

        if self.subnet_id:
            self.destroy_subnet(client)

        if self.route_table_id:
            self.destroy_route_table(client)

        if self.security_group_id:
            self.destroy_security_group(client)

        if self.vpc_id:
            self.destroy_vpc(client)

        self.vpc_id = None
        self.igw_id = None
        self.keypair_name = None
        self.subnet_id = None
        self.route_table_id = None
        self.security_group_id = None
        self.ec2_instance_id = None
        self.public_ip = None
        self.allocation_id = None

    @log_warnings
    def destroy_ec2_instance(self, client):
        print("Terminating EC2 Instance. This can take a few minutes...")
        client.terminate_instances(InstanceIds=[self.ec2_instance_id])
        ec2_waiter = client.get_waiter("instance_terminated")
        ec2_waiter.wait(InstanceIds=[self.ec2_instance_id])
        print("EC2 instance terminated...")

    @log_warnings
    def destroy_keypair(self, client):
        client.delete_key_pair(KeyName=self.keypair_name)
        print("Keypair deleted...")

    @log_warnings
    def destroy_keypair_file(self):
        print("Deleting loc keypair file")
        keypair_filename = self.keypair_name + ".pem"
        if os.path.exists(keypair_filename):
            os.remove(keypair_filename)
        print("File deleted")

    @log_warnings
    def destroy_elastic_ip(self, client):
        print("Releasing elastic ip...")
        client.release_address(AllocationId=self.allocation_id)
        print("Elastic ip released...")

    @log_warnings
    def destroy_internet_gateway(self, client):
        print("Detatching Internet gateway...")
        client.detach_internet_gateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_id)
        print("Destroying Internet gateway...")
        client.delete_internet_gateway(InternetGatewayId=self.igw_id)
        print("Internet gateway deleted.")

    @log_warnings
    def destroy_subnet(self, client):
        print("Destroying subnet...")
        client.delete_subnet(SubnetId=self.subnet_id)
        print("Subnet destroyed...")

    @log_warnings
    def destroy_route_table(self, client):
        print("Destroying routetable...")
        client.delete_route_table(RouteTableId=self.route_table_id)
        print("Routetable destroyed...")

    @log_warnings
    def destroy_security_group(self, client):
        print("Destroying security group...")
        client.delete_security_group(GroupId=self.security_group_id)
        print("Security group destroyed...")

    @log_warnings
    def destroy_vpc(self, client):
        print("Destroying security group...")
        client.delete_vpc(VpcId=self.vpc_id)
        print("Security group destroyed...")


class InstanceFactory:
    def __init__(self, config_ini_filename):

        config = configparser.ConfigParser()
        config.read(config_ini_filename)

        self.AWS_ACCESS_KEY_ID = config.get("aws_credentials", "aws_access_key_id")
        self.AWS_SECRET_ACCESS_KEY = config.get(
            "aws_credentials", "aws_secret_access_key"
        )
        self.TAG_ROOT = config.get("general_config", "tag_root")
        self.REGION = config.get("network_config", "region")
        self.INSTANCE_ACCESS_PORT = config.get(
            "instance_config", "instance_access_port"
        )
        self.VPC_CIDR_BLOCK = config.get("network_config", "vpc_cidr_block")
        self.SUBNET_CIDR_BLOCK = config.get("network_config", "subnet_cidr_block")
        self.INSTANCE_AMI = config.get("instance_config", "ami")
        self.INSTANCE_TYPE = config.get("instance_config", "instance_type")
        self.USER_DATA = open("instance_startup_script").read()

    def get_client(self):

        try:
            client = boto3.client(
                "ec2",
                aws_access_key_id=self.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY,
                region_name=self.REGION,
            )

        except Exception as e:
            print(f"Unable to create client object. Error:\n{e}\nExiting...")

        try:
            _ = client.describe_account_attributes()
        except Exception as e:
            print(f"Unable to validate client object. Error:\n{e}")

        return client

    def get_blank_instance(self):
        return Instance()

    def __str__(self):
        s = ""
        for att in vars(self):

            secret = att == "AWS_SECRET_ACCESS_KEY"
            value = self.__getattribute__(att)
            if secret and value:
                s += f"{att} -> ****************\n"
            elif secret and not value:
                s += f"{att} -> missing\n"
            else:
                s += f"{att} -> {value}\n"
        return s

    def __repr__(self):
        return self.__str__()

    def save_instance_to_file(self, instance:Instance):
        filename = gui_elements.get_save_as_filepath()
        pickle.dump(instance, open(filename, "wb"))

    def load_instance_from_savefile(self)->Instance:

        # Load pickled data to dict
        filename = gui_elements.get_saved_file_filepath()
        fe = gui_elements.SAVED_FILE_EXTENTION
        
        # End procedure if the file type looks wrong
        if not filename.endswith(fe):
            print(f"Are you sure about that file? It should be a {fe} file...")
            return

        instance = pickle.load(open(filename, "rb"))

        return instance

    def launch_instance(self):

        try:
            instance = self.get_blank_instance()
            instance.region = self.REGION
            client = self.get_client()
            self.build_vpc(client, instance)
            self.build_igw(client, instance)
            self.build_keypair(client, instance)
            self.build_subnet(client, instance)
            self.build_route_table(client, instance)
            self.build_security_group(client, instance)
            self.build_ec2_instance(client, instance)
            self.allocate_public_ip(client, instance)
            self.associate_public_ip(client, instance)

            print("Instance created!")

            if gui_elements.confirm_save():
                print("Save Instance?")
                self.save_instance_to_file(instance)

            
        except Exception as e:
            print(f"An error occured\n{e}")
            print(f"Would you like me to remove the parts which were created?")
            if input().lower() in ["yes", "y"]:
                instance.self_destruct(client)

        
        return instance

    def build_vpc(self, client, instance):
        try:
            vpc_data = client.create_vpc(CidrBlock=self.VPC_CIDR_BLOCK)

            VpcId = vpc_data["Vpc"]["VpcId"]
            vpc_waiter = client.get_waiter("vpc_exists")
            vpc_waiter.wait(VpcIds=[VpcId])

            client.create_tags(
                Resources=[VpcId],
                Tags=[{"Key": "Name", "Value": self.TAG_ROOT + "_VPC"}],
            )

        except Exception as e:
            print(e)
        print("VPC built...")
        instance.vpc_id = VpcId

    def build_subnet(self, client, instance):

        try:
            subnet_data = client.create_subnet(
                VpcId=instance.vpc_id, CidrBlock=self.SUBNET_CIDR_BLOCK
            )
            subnet_id = subnet_data["Subnet"]["SubnetId"]

            subnet_waiter = client.get_waiter('subnet_available')
            subnet_waiter.wait(SubnetIds=[subnet_id])

            client.create_tags(
                Resources=[subnet_id],
                Tags=[{"Key": "Name", "Value": self.TAG_ROOT + "_Public_Subnet"}],
            )

        except Exception as e:
            print(e)

        print("Subnet built...")
        instance.subnet_id = subnet_id

    def build_igw(self, client, instance):

        try:
            igw_data = client.create_internet_gateway()
            igw_id = igw_data["InternetGateway"]["InternetGatewayId"]
            client.attach_internet_gateway(
                InternetGatewayId=igw_id, VpcId=instance.vpc_id
            )
            client.create_tags(
                Resources=[igw_id],
                Tags=[{"Key": "Name", "Value": self.TAG_ROOT + "_IGW"}],
            )

        except Exception as e:
            print(e)

        print("Internet gateway built...")
        instance.igw_id = igw_id

    def build_route_table(self, client, instance):

        try:
            route_table_data = client.create_route_table(VpcId=instance.vpc_id)
            route_tbl_id = route_table_data["RouteTable"]["RouteTableId"]
            client.create_tags(
                Resources=[route_tbl_id],
                Tags=[{"Key": "Name", "Value": self.TAG_ROOT + "_RouteTable"}],
            )
            client.create_route(
                RouteTableId=route_tbl_id,
                DestinationCidrBlock="0.0.0.0/0",
                GatewayId=instance.igw_id,
            )

            client.associate_route_table(
                RouteTableId=route_tbl_id, SubnetId=instance.subnet_id
            )

        except Exception as e:
            print(e)

        print("Route table built...")
        instance.route_table_id = route_tbl_id

    def build_keypair(self, client, instance):
        key_pair_name = self.TAG_ROOT + "_KEY_PAIR"

        try:
            kp = client.create_key_pair(KeyName=key_pair_name)

            # Write keypair to a local file
            privatekey = kp["KeyMaterial"]
            filename = key_pair_name + ".pem"

            self.write_keypair_to_file(filename, privatekey)
            print("Key pair built and saved locally...")

        except Exception as e:
            print(e)
            print(
                "Looks like that keypair_name already exists. So you already have it."
            )
            pass

        instance.keypair_name = key_pair_name

    def write_keypair_to_file(self, key_filename, privatekey):
        """
        Writes the creted keypair to a local file.
        """

        if os.path.exists(key_filename):
            os.remove(key_filename)

        with open(key_filename, "w") as file:
            file.write(privatekey)

    def add_security_group_rule(self, client, instance):
        client.authorize_security_group_ingress(
            GroupId=instance.security_group_id,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": int(self.INSTANCE_ACCESS_PORT),
                    "ToPort": int(self.INSTANCE_ACCESS_PORT),
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                }
            ],
        )

    def build_security_group(self, client, instance):

        try:
            security_group_response_data = client.create_security_group(
                GroupName=self.TAG_ROOT + "_SECURITY_GROUP",
                Description=self.TAG_ROOT + "_SECURITY_GROUP",
                VpcId=instance.vpc_id,
            )

            security_group_id = security_group_response_data["GroupId"]

            subgroup_waiter = client.get_waiter('security_group_exists')
            subgroup_waiter.wait(GroupIds=[security_group_id])

            client.create_tags(
                Resources=[security_group_id],
                Tags=[{"Key": "Name", "Value": self.TAG_ROOT + "_SECURITY_GROUP"}],
            )

            print("Security group built...")
            instance.security_group_id = security_group_id

        except Exception as e:
            print("Couldn't create security group. Error:")
            print(e)

        try:
            self.add_security_group_rule(client, instance)
            print("Added rule to security group")

        except Exception as e:
            print("Couldn't add rule to security group. Error:")
            print(e)

    def allocate_public_ip(self, client, instance):

        try:
            allocated_ip_data = client.allocate_address()
            allocation_id = allocated_ip_data["AllocationId"]
            public_ip = allocated_ip_data["PublicIp"]

            instance.allocation_id = allocation_id
            instance.public_ip = public_ip
            print("IP allocated...")
        except Exception as e:
            print("Unable to allocate public IP. Error:")
            print(e)

    def associate_public_ip(self, client, instance):

        print(f"""Just wait a few seconds before asociating a public IP please..""")

        # These aren't the right waiters...
        # instance_exists_waiter = client.get_waiter('instance_exists')
        # instance_exists_waiter.wait(InstanceIds=[instance.ec2_instance_id])


        for attempt in range(5):
            try:
                client.associate_address(
                    InstanceId=instance.ec2_instance_id,
                    AllocationId=instance.allocation_id,
                )
                print("IP associated...")
                return
            except Exception:
                print(f"Instance not ready for IP association.\n")
                print(f"""Retrying in 15 seconds...""")
                time.sleep(15)

        print("Error: Unusually long time to associate an IP.")
        print("Please review your installation manually via your AWS console.")

    def build_ec2_instance(self, client, instance):

        try:
            instance_data = client.run_instances(
                ImageId=self.INSTANCE_AMI,
                KeyName=instance.keypair_name,
                MinCount=1,
                MaxCount=1,
                SecurityGroupIds=[instance.security_group_id],
                SubnetId=instance.subnet_id,
                UserData=self.USER_DATA,
                InstanceType=self.INSTANCE_TYPE,
            )

            ec2_instance_id = instance_data["Instances"][0]["InstanceId"]
            client.create_tags(
                Resources=[ec2_instance_id],
                Tags=[{"Key": "Name", "Value": self.TAG_ROOT + "_Instance"}],
            )
            print("EC2 instance launched...")

        except Exception as e:
            print("Error creating EC2 instance. Error:")
            print(e)

        instance.ec2_instance_id = ec2_instance_id

