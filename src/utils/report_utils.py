"""
Reporting Utilities

This module provides helper functions for generating and formatting reports.
"""

import os
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

def ensure_report_directory(config):
    """
    Ensure the report directory exists.
    
    Args:
        config (dict): Report configuration
        
    Returns:
        str: Path to the report directory
    """
    output_dir = config.get('output_dir', 'reports')
    logger.debug(f"Ensuring report directory exists: {output_dir}")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

def generate_report_filename(report_type, file_format):
    """
    Generate a standardized report filename with timestamp.
    
    Args:
        report_type (str): Type of report (e.g., 'ri_coverage')
        file_format (str): File format extension (e.g., 'csv')
        
    Returns:
        str: Generated filename
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{report_type}_{timestamp}.{file_format}"
    logger.debug(f"Generated report filename: {filename}")
    return filename

def format_ri_coverage_data(report_data):
    """
    Format RI coverage data into a pandas DataFrame.
    
    Args:
        report_data (dict): Raw RI coverage report data
        
    Returns:
        pd.DataFrame: Formatted report data
    """
    logger.debug("Formatting RI coverage data into DataFrame")
    
    # Create rows for each region
    rows = []
    for region_data in report_data.get('regions_data', []):
        row = {
            'Region': region_data.get('region', 'Unknown'),
            'Running Instances': region_data.get('total_instances', 0),
            'Reserved Instances': region_data.get('total_reserved_instances', 0),
            'Uncovered Instances': region_data.get('uncovered_instances', 0),
            'Coverage Percentage': region_data.get('coverage_percentage', 0),
            'Timestamp': report_data.get('timestamp', datetime.now().isoformat())
        }
        rows.append(row)
    
    # Add summary row
    summary = report_data.get('summary', {})
    summary_row = {
        'Region': 'TOTAL (All Regions)',
        'Running Instances': summary.get('total_instances', 0),
        'Reserved Instances': summary.get('total_reserved_instances', 0),
        'Uncovered Instances': summary.get('total_uncovered_instances', 0),
        'Coverage Percentage': summary.get('overall_coverage_percentage', 0),
        'Timestamp': report_data.get('timestamp', datetime.now().isoformat())
    }
    rows.append(summary_row)
    
    return pd.DataFrame(rows)

def save_report_to_csv(df, filename, config):
    """
    Save a DataFrame to a CSV file.
    
    Args:
        df (pd.DataFrame): Data to save
        filename (str): Filename to save as
        config (dict): Report configuration
        
    Returns:
        str: Path to saved file
    """
    report_dir = ensure_report_directory(config)
    filepath = os.path.join(report_dir, filename)
    logger.info(f"Saving report to CSV: {filepath}")
    df.to_csv(filepath, index=False)
    return filepath

def save_report_to_html(df, filename, config):
    """
    Save a DataFrame to an HTML file with styling.
    
    Args:
        df (pd.DataFrame): Data to save
        filename (str): Filename to save as
        config (dict): Report configuration
        
    Returns:
        str: Path to saved file
    """
    report_dir = ensure_report_directory(config)
    filepath = os.path.join(report_dir, filename)
    logger.info(f"Saving report to HTML: {filepath}")
    
    # Add styling to the HTML report
    styled_df = df.style.set_properties(**{
        'border': '1px solid gray',
        'padding': '5px',
    })
    
    styled_df.to_html(filepath)
    return filepath

def save_report_to_json(df, filename, config):
    """
    Save a DataFrame to a JSON file.
    
    Args:
        df (pd.DataFrame): Data to save
        filename (str): Filename to save as
        config (dict): Report configuration
        
    Returns:
        str: Path to saved file
    """
    report_dir = ensure_report_directory(config)
    filepath = os.path.join(report_dir, filename)
    logger.info(f"Saving report to JSON: {filepath}")
    df.to_json(filepath, orient='records')
    return filepath

def generate_markdown_report(report_data):
    """
    Generate a markdown report from the RI coverage data.
    
    Args:
        report_data (dict): The RI coverage report data
    
    Returns:
        str: Markdown formatted report
    """
    logger.debug("Generating markdown report for RI coverage")
    
    # Convert UTC timestamp to readable format
    timestamp = datetime.fromisoformat(report_data['timestamp']).strftime('%Y-%m-%d %H:%M UTC')
    
    # Start the markdown report
    markdown = f"# EC2 Reserved Instance Coverage Report\n\n"
    markdown += f"Inspection Time: {timestamp}\n\n"
    
    # Get soonest expiring RI info
    summary = report_data.get('summary', {})
    soonest_ri = summary.get('soonest_expiring_ri')
    
    if soonest_ri:
        markdown += f"**Next RI Expiration:** {soonest_ri['type']} in {soonest_ri['region_name']} will expire on {soonest_ri['date']}\n\n"
    
    # Add region sections
    for region_data in report_data.get('regions_data', []):
        region_name = region_data.get('region_name', region_data.get('region', 'Unknown Region'))
        total_instances = region_data.get('total_instances', 0)
        covered_instances = region_data.get('covered_instances', 0)
        
        # Skip regions with no instances
        if total_instances == 0:
            markdown += f"## {region_name}\n"
            markdown += "No running EC2 instances in this region.\n\n"
            continue
        
        markdown += f"## {region_name}\n"
        
        coverage_ratio = f"{covered_instances}/{total_instances}"
        markdown += f"Currently running {total_instances} EC2 instances, with {coverage_ratio} instances covered by RIs"
        
        # Add uncovered instances by type if any
        uncovered_by_type = region_data.get('uncovered_by_type', {})
        if uncovered_by_type:
            markdown += ", remaining:\n"
            for instance_type, count in uncovered_by_type.items():
                markdown += f" - {count} x '{instance_type}' instances\n"
        else:
            markdown += ". All instances are covered by RIs.\n"
        
        # Add RI details if available
        ri_details = region_data.get('ri_details', [])
        if ri_details:
            markdown += "\n### Currently Active Reserved Instances\n"
            markdown += "| Instance Type | Count | Expiration Date |\n"
            markdown += "|---------|------|--------|\n"
            
            # Sort RIs by expiration date
            sorted_ris = sorted(ri_details, key=lambda x: x.get('end_date', '9999-12-31'))
            
            for ri in sorted_ris:
                instance_type = ri.get('type', 'Unknown')
                count = ri.get('count', 0)
                end_date = ri.get('end_date', 'Unknown')
                
                markdown += f"| {instance_type} | {count} | {end_date} |\n"
        
        markdown += "\n"
    
    # Add summary section
    total_instances = summary.get('total_instances', 0)
    total_ris = summary.get('total_reserved_instances', 0)
    overall_coverage = summary.get('overall_coverage_percentage', 0)
    
    markdown += "## Summary\n"
    markdown += f"- Total Running EC2 Instances: {total_instances}\n"
    markdown += f"- Total Reserved Instances (RI): {total_ris}\n"
    markdown += f"- Overall Coverage: {overall_coverage:.2f}%\n"
    
    return markdown

def save_markdown_report(markdown_content, filename, config):
    """
    Save markdown content to a file.
    
    Args:
        markdown_content (str): Markdown content to save
        filename (str): Filename to save as
        config (dict): Report configuration
        
    Returns:
        str: Path to saved file
    """
    report_dir = ensure_report_directory(config)
    filepath = os.path.join(report_dir, filename)
    logger.info(f"Saving markdown report: {filepath}")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
        
    return filepath
