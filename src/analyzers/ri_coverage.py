"""
EC2 Reserved Instance Coverage Analyzer

This module analyzes EC2 Reserved Instance (RI) coverage across AWS accounts
and generates reports on instance coverage status.
"""

import logging
from datetime import datetime, timedelta
from collections import defaultdict

from ..utils import aws_utils, report_utils

logger = logging.getLogger(__name__)

class RICoverageAnalyzer:
    """Analyzes EC2 Reserved Instance coverage and provides statistics."""
    
    def __init__(self, config):
        """
        Initialize the RI coverage analyzer.
        
        Args:
            config (dict): Configuration parameters from settings.yaml
        """
        self.config = config
        self.regions = config.get('regions', ['us-east-1'])
        self.lookback_days = config.get('lookback_days', 30)
        self.aws_config = config.get('aws', {})
        self.profile = self.aws_config.get('profile')
    
    def get_running_instances(self, region):
        """
        Get current running EC2 instances in the specified region.
        
        Args:
            region (str): AWS region name
            
        Returns:
            dict: Running EC2 instances grouped by instance type
        """
        ec2_client = aws_utils.get_aws_client('ec2', region=region, profile=self.profile)
        logger.info(f"Fetching running instances in region {region}")
        
        return aws_utils.get_running_ec2_instances(ec2_client)
    
    def get_reserved_instances(self, region):
        """
        Get active Reserved Instances in the specified region.
        
        Args:
            region (str): AWS region name
            
        Returns:
            dict: Active reserved instances grouped by instance type
        """
        ec2_client = aws_utils.get_aws_client('ec2', region=region, profile=self.profile)
        logger.info(f"Fetching reserved instances in region {region}")
        
        return aws_utils.get_reserved_ec2_instances(ec2_client)
    
    def calculate_coverage(self, running_instances, reserved_instances):
        """
        Calculate instance coverage by RI.
        
        Args:
            running_instances (dict): Running instances grouped by instance type
            reserved_instances (dict): Reserved instances grouped by instance type
            
        Returns:
            dict: Coverage statistics
        """
        # Get the count of RIs by instance type
        ri_counts = reserved_instances['count_by_type']
        ri_details = reserved_instances['details']
        
        # Find the soonest expiring RI
        soonest_expiry = None
        if ri_details:
            # Sort by end_date and get the first one
            sorted_ris = sorted(ri_details, key=lambda x: x.get('end_date', '9999-12-31'))
            if sorted_ris:
                soonest_expiry = {
                    'type': sorted_ris[0].get('type'),
                    'date': sorted_ris[0].get('end_date'),
                    'id': sorted_ris[0].get('id')
                }
        
        # Count running instances by type
        running_counts = {instance_type: len(instances) for instance_type, instances in running_instances.items()}
        
        # Calculate total counts
        total_running = sum(running_counts.values())
        total_reserved = sum(ri_counts.values())
        
        # Calculate covered and uncovered instances
        covered_counts = {}
        uncovered_counts = {}
        uncovered_instances = {}
        
        for instance_type, count in running_counts.items():
            ri_available = ri_counts.get(instance_type, 0)
            covered = min(count, ri_available)
            uncovered = count - covered
            
            covered_counts[instance_type] = covered
            
            if uncovered > 0:
                uncovered_counts[instance_type] = uncovered
                uncovered_instances[instance_type] = uncovered
        
        # Calculate total covered and uncovered
        total_covered = sum(covered_counts.values())
        total_uncovered = sum(uncovered_counts.values())
        
        # Calculate coverage percentage
        coverage_percentage = (total_covered / total_running * 100) if total_running > 0 else 0
        
        return {
            'total_instances': total_running,
            'total_reserved_instances': total_reserved,
            'covered_instances': total_covered,
            'uncovered_instances': total_uncovered,
            'coverage_percentage': coverage_percentage,
            'running_counts_by_type': running_counts,
            'ri_counts_by_type': ri_counts,
            'uncovered_by_type': uncovered_instances,
            'ri_details': ri_details,
            'soonest_expiring_ri': soonest_expiry  # Add the soonest expiring RI
        }
    
    def analyze_region(self, region):
        """
        Analyze RI coverage for a specific region.
        
        Args:
            region (str): AWS region name
            
        Returns:
            dict: Region coverage data
        """
        logger.info(f"Analyzing RI coverage for region: {region}")
        
        running_instances = self.get_running_instances(region)
        reserved_instances = self.get_reserved_instances(region)
        coverage = self.calculate_coverage(running_instances, reserved_instances)
        
        # Map AWS region code to user-friendly name
        region_name_map = {
            # 美洲
            'us-east-1': 'US East (N. Virginia)',
            'us-east-2': 'US East (Ohio)',
            'us-west-1': 'US West (N. California)',
            'us-west-2': 'US West (Oregon)',
            'ca-central-1': 'Canada (Central)',
            'ca-west-1': 'Canada West (Calgary)',
            'sa-east-1': 'South America (São Paulo)',
            
            # 欧洲
            'eu-north-1': 'Europe (Stockholm)',
            'eu-west-1': 'Europe (Ireland)',
            'eu-west-2': 'Europe (London)',
            'eu-west-3': 'Europe (Paris)',
            'eu-central-1': 'Europe (Frankfurt)',
            'eu-central-2': 'Europe (Zurich)',
            'eu-south-1': 'Europe (Milan)',
            'eu-south-2': 'Europe (Spain)',
            
            # 亚太地区
            'ap-east-1': 'Asia Pacific (Hong Kong)',
            'ap-south-1': 'Asia Pacific (Mumbai)',
            'ap-south-2': 'Asia Pacific (Hyderabad)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)',
            'ap-northeast-2': 'Asia Pacific (Seoul)',
            'ap-northeast-3': 'Asia Pacific (Osaka)',
            'ap-southeast-1': 'Asia Pacific (Singapore)',
            'ap-southeast-2': 'Asia Pacific (Sydney)',
            'ap-southeast-3': 'Asia Pacific (Jakarta)',
            'ap-southeast-4': 'Asia Pacific (Melbourne)',
            
            # 中东和非洲
            'me-south-1': 'Middle East (Bahrain)',
            'me-central-1': 'Middle East (UAE)',
            'af-south-1': 'Africa (Cape Town)',
            
            # 中国
            'cn-north-1': 'China (Beijing)',
            'cn-northwest-1': 'China (Ningxia)',
            
            # AWS GovCloud
            'us-gov-east-1': 'AWS GovCloud (US-East)',
            'us-gov-west-1': 'AWS GovCloud (US-West)',
            
            # 以色列
            'il-central-1': 'Israel (Tel Aviv)'
        }
        
        return {
            'region': region,
            'region_name': region_name_map.get(region, region),
            **coverage
        }
    
    def generate_coverage_report(self):
        """
        Generate a comprehensive report on RI coverage across all regions.
        
        Returns:
            dict: Report data containing coverage stats by region
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'regions_data': [],
            'summary': {
                'total_instances': 0,
                'total_reserved_instances': 0,
                'total_uncovered_instances': 0,
                'soonest_expiring_ri': None  # Add field for soonest expiring RI
            }
        }
        
        for region in self.regions:
            region_data = self.analyze_region(region)
            report['regions_data'].append(region_data)
            
            # Update summary
            report['summary']['total_instances'] += region_data['total_instances']
            report['summary']['total_reserved_instances'] += region_data['total_reserved_instances']
            report['summary']['total_uncovered_instances'] += region_data['uncovered_instances']
            
            # Keep track of the soonest expiring RI across all regions
            if region_data.get('soonest_expiring_ri') and (
                not report['summary']['soonest_expiring_ri'] or 
                region_data['soonest_expiring_ri']['date'] < report['summary']['soonest_expiring_ri']['date']):
                report['summary']['soonest_expiring_ri'] = {
                    **region_data['soonest_expiring_ri'],
                    'region': region,
                    'region_name': region_data['region_name']
                }
        
        # Calculate overall coverage percentage
        total_instances = report['summary']['total_instances']
        if total_instances > 0:
            covered_instances = total_instances - report['summary']['total_uncovered_instances']
            report['summary']['overall_coverage_percentage'] = (covered_instances / total_instances * 100)
        else:
            report['summary']['overall_coverage_percentage'] = 0
            
        logger.info("Generated RI coverage report")
        return report
    
    def run_analysis(self):
        """
        Execute the full RI coverage analysis workflow.
        
        Returns:
            dict: Analysis results and coverage statistics
        """
        logger.info("Starting RI coverage analysis")
        
        # Generate coverage report for all regions
        report = self.generate_coverage_report()
        
        logger.info("RI coverage analysis completed")
        return report
