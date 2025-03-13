"""
AWS API Utilities

This module provides helper functions for interacting with AWS services.
"""

import logging
import boto3
import botocore.exceptions
from collections import defaultdict

logger = logging.getLogger(__name__)

def get_aws_client(service_name, region=None, profile=None, role_arn=None):
    """
    Get an AWS service client with optional configuration.
    
    Args:
        service_name (str): AWS service name (e.g., 'ec2', 'ce')
        region (str, optional): AWS region name
        profile (str, optional): AWS profile name
        role_arn (str, optional): IAM role ARN to assume
        
    Returns:
        boto3.client: Configured AWS service client
    """
    session_kwargs = {}
    client_kwargs = {}
    
    if profile:
        session_kwargs['profile_name'] = profile
        
    session = boto3.Session(**session_kwargs)
    
    # Handle role assumption if provided
    if role_arn:
        sts_client = session.client('sts')
        assumed_role = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName='AWSResourceOptimizer'
        )
        credentials = assumed_role['Credentials']
        
        client_kwargs['aws_access_key_id'] = credentials['AccessKeyId']
        client_kwargs['aws_secret_access_key'] = credentials['SecretAccessKey']
        client_kwargs['aws_session_token'] = credentials['SessionToken']
    
    if region:
        client_kwargs['region_name'] = region
    
    try:
        client = session.client(service_name, **client_kwargs)
        logger.debug(f"Created AWS client for service: {service_name}")
        return client
    except botocore.exceptions.ClientError as e:
        logger.error(f"Failed to create AWS client for {service_name}: {str(e)}")
        raise

def get_aws_accounts():
    """
    Get a list of all accessible AWS accounts.
    
    Returns:
        list: List of account dictionaries with id and name
    """
    # This would implement logic to list AWS accounts
    logger.debug("Retrieving list of accessible AWS accounts")
    return []

def get_running_ec2_instances(client):
    """
    Get all running EC2 instances using the provided client.
    
    Args:
        client (boto3.client): EC2 client
        
    Returns:
        dict: Running EC2 instances grouped by instance type
    """
    try:
        paginator = client.get_paginator('describe_instances')
        instance_type_count = defaultdict(list)
        
        for page in paginator.paginate(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]):
            for reservation in page['Reservations']:
                for instance in reservation['Instances']:
                    instance_type = instance['InstanceType']
                    instance_id = instance['InstanceId']
                    platform = instance.get('Platform', 'Linux/UNIX')  # Default to Linux/UNIX if not specified
                    
                    instance_type_count[instance_type].append({
                        'instance_id': instance_id, 
                        'platform': platform
                    })
        
        total_instances = sum(len(instances) for instances in instance_type_count.values())
        logger.debug(f"Found {total_instances} running EC2 instances across {len(instance_type_count)} instance types")
        return instance_type_count
    except botocore.exceptions.ClientError as e:
        logger.error(f"Failed to get running EC2 instances: {str(e)}")
        return {}

def get_reserved_ec2_instances(client):
    """
    Get all active EC2 Reserved Instances using the provided client.
    
    Args:
        client (boto3.client): EC2 client
        
    Returns:
        dict: Active reserved instances grouped by instance type
    """
    try:
        response = client.describe_reserved_instances(
            Filters=[{'Name': 'state', 'Values': ['active']}]
        )
        
        ri_type_count = defaultdict(int)
        ri_details = []
        
        for ri in response['ReservedInstances']:
            instance_type = ri['InstanceType']
            instance_count = ri['InstanceCount']
            ri_type_count[instance_type] += instance_count
            
            ri_details.append({
                'id': ri['ReservedInstancesId'],
                'type': instance_type,
                'count': instance_count,
                'platform': ri.get('ProductDescription', 'Linux/UNIX'),
                'end_date': ri['End'].strftime('%Y-%m-%d')
            })
        
        total_ris = sum(ri_type_count.values())
        logger.debug(f"Found {total_ris} active Reserved Instances across {len(ri_type_count)} instance types")
        return {'count_by_type': ri_type_count, 'details': ri_details}
    except botocore.exceptions.ClientError as e:
        logger.error(f"Failed to get Reserved Instances: {str(e)}")
        return {'count_by_type': {}, 'details': []}

def get_ec2_reserved_instances(region=None):
    """
    Get all active EC2 Reserved Instances in the specified region.
    
    Args:
        region (str, optional): AWS region name
        
    Returns:
        list: Active reserved instances
    """
    # This would implement logic to list EC2 Reserved Instances
    logger.debug(f"Retrieving active EC2 Reserved Instances in region: {region}")
    return []