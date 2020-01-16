import configparser
import boto3
import sys
import boto_calls as bc


def get_config_parser(ini_filename):
    # ConfigParser to read config.ini
    Config = configparser.ConfigParser()
    Config.read(ini_filename)
    return Config


CredentialsConfig = get_config_parser("config.ini")


AWS_ACCESS_KEY_ID = CredentialsConfig.get("aws_credentials", "aws_access_key_id")
AWS_SECRET_ACCESS_KEY = CredentialsConfig.get("aws_credentials", "aws_secret_access_key")
TAG_ROOT = CredentialsConfig.get("general_config","tag_root")
REGION = CredentialsConfig.get("network_config","region")
INSTANCE_ACCESS_PORT = CredentialsConfig.get("network_config","instance_access_port")
VPC_CIDR_BLOCK = CredentialsConfig.get("network_config","vpc_cidr_block")
SUBNET_CIDR_BLOCK = CredentialsConfig.get("network_config","subnet_cidr_block")
INSTANCE_AMI = CredentialsConfig.get("instance_config","instance_ami")
INSTANCE_TYPE = CredentialsConfig.get("instance_config","instance_type")
USER_DATA = open("instance_startup_script").read()


client = bc.get_ec2_client(REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
vpc_id = bc.build_vpc(client,VPC_CIDR_BLOCK, TAG_ROOT)
igw_id = bc.build_igw(client, vpc_id , TAG_ROOT)
keypair_name = bc.build_keypair(client, TAG_ROOT)
subnet_id = bc.build_subnet(client, vpc_id, SUBNET_CIDR_BLOCK, TAG_ROOT)
route_table_id = bc.build_route_table(client, vpc_id, subnet_id, igw_id, TAG_ROOT)
security_group_id = bc.build_security_group(client, vpc_id, INSTANCE_ACCESS_PORT, TAG_ROOT)
ec2_instance_id = bc.build_ec2_instance(client, INSTANCE_AMI, security_group_id, subnet_id, keypair_name, INSTANCE_TYPE, USER_DATA, TAG_ROOT)
public_ip, allocation_id = bc.allocate_public_ip(client)
bc.associate_public_ip(client, ec2_instance_id, allocation_id)

print(f"{public_ip}:{INSTANCE_ACCESS_PORT}")

