"""
Mattermost Notification Handler

This module handles sending notifications to Mattermost channels
through webhook integrations.
"""

import json
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class MattermostNotifier:
    """Sends notifications to Mattermost channels."""
    
    def __init__(self, config):
        """
        Initialize the Mattermost notifier.
        
        Args:
            config (dict): Mattermost configuration from settings.yaml
        """
        self.config = config
        self.webhook_url = config['webhook_url']
        self.channel = config.get('channel')
        self.username = config.get('username', 'AWS Resource Optimizer')
        self.icon_emoji = config.get('icon_emoji', ':money_with_wings:')
        self.enabled = config.get('enabled', True)
    
    def format_ri_coverage_message(self, report_data):
        """
        Format RI coverage analysis data into a Mattermost message.
        Only include summary information.
        
        Args:
            report_data (dict): The RI coverage report data
            
        Returns:
            str: Formatted text message
        """
        # Convert timestamp to readable format
        timestamp = datetime.fromisoformat(report_data['timestamp']).strftime('%Y-%m-%d %H:%M UTC')
        
        # Get summary data
        summary = report_data.get('summary', {})
        total_instances = summary.get('total_instances', 0)
        total_ris = summary.get('total_reserved_instances', 0)
        total_uncovered = summary.get('total_uncovered_instances', 0)
        overall_coverage = summary.get('overall_coverage_percentage', 0)
        
        # Get soonest expiring RI info
        soonest_ri = summary.get('soonest_expiring_ri')
        
        # Determine status icon based on coverage percentage
        status_icon = "✅" if overall_coverage >= 80 else "⚠️" if overall_coverage >= 50 else "❌"
        
        # Build a nicely formatted message
        text = "### EC2 Reserved Instance Coverage Report\n\n"
        text += f"**Date:** {timestamp}\n\n"
        
        # Summary section with highlighting
        text += "#### Summary\n"
        text += f"| Metric | Value |\n"
        text += f"|--------|-------|\n"
        text += f"| Running EC2 Instances | **{total_instances}** |\n"
        text += f"| Active Reserved Instances | **{total_ris}** |\n"
        text += f"| Uncovered Instances | **{total_uncovered}** |\n"
        text += f"| Overall Coverage | {status_icon} **{overall_coverage:.1f}%** |\n"
        
        # Add soonest expiring RI if available
        if soonest_ri:
            text += f"| Next RI Expiry | ⏰ **{soonest_ri['type']}** in **{soonest_ri['region_name']}** on **{soonest_ri['date']}** |\n\n"
        else:
            text += f"| Next RI Expiry | No active RIs |\n\n"
        
        # Add region details in a table format
        text += "#### Region Details\n"
        text += "| Region | Running | RIs | Uncovered | Coverage |\n"
        text += "|--------|---------|-----|-----------|----------|\n"
        
        for region_data in report_data.get('regions_data', []):
            region_name = region_data.get('region_name', region_data.get('region'))
            region_instances = region_data.get('total_instances', 0)
            region_ris = region_data.get('total_reserved_instances', 0)
            region_uncovered = region_data.get('uncovered_instances', 0)
            region_coverage = region_data.get('coverage_percentage', 0)
            
            # Only include regions with instances
            if region_instances > 0:
                region_status = "✅" if region_coverage >= 80 else "⚠️" if region_coverage >= 50 else "❌"
                text += f"| {region_name} | {region_instances} | {region_ris} | {region_uncovered} | {region_status} {region_coverage:.1f}% |\n"
        
        # Add additional info from configuration if available
        if self.config.get('additional_info'):
            text += f"\n\n{self.config['additional_info']}\n"
        
        logger.debug("Formatted enhanced message for Mattermost")
        return text
    
    def send_notification(self, message_text):
        """
        Send a notification to the configured Mattermost channel.
        
        Args:
            message_text (str): Text message content to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            logger.info("Mattermost notifications are disabled in configuration")
            return False
            
        logger.info(f"Sending notification to Mattermost channel: {self.channel}")
        
        try:
            # Try the absolute simplest approach - plain text message
            payload = {"text": message_text}
            
            # Log what we're sending
            logger.debug("Sending simple text message to Mattermost webhook")
            
            # Make direct POST with minimal formatting
            response = requests.post(self.webhook_url, 
                                    data=json.dumps(payload),
                                    headers={'Content-Type': 'application/json'})
            
            # Check response
            if response.status_code == 200:
                logger.info("Successfully sent notification to Mattermost")
                return True
            else:
                logger.error(f"Failed to send notification to Mattermost: {response.status_code} {response.text}")
                
                # Try curl equivalent approach as last resort
                logger.debug("Trying curl equivalent approach")
                
                # Create a completely minimal payload string
                curl_payload = '{"text":"' + message_text.replace('\n', '\\n').replace('"', '\\"') + '"}'
                
                curl_response = requests.post(
                    self.webhook_url,
                    data=curl_payload,
                    headers={'Content-Type': 'application/json'}
                )
                
                if curl_response.status_code == 200:
                    logger.info("Successfully sent notification using curl equivalent")
                    return True
                else:
                    logger.error(f"All methods failed: {curl_response.status_code} {curl_response.text}")
                    return False
                
        except Exception as e:
            logger.error(f"Error sending notification to Mattermost: {str(e)}")
            return False
        
    def send_ri_report(self, report_data):
        """
        Create and send an RI coverage report notification.
        
        Args:
            report_data (dict): The RI coverage report data
            
        Returns:
            bool: True if successfully sent, False otherwise
        """
        message_text = self.format_ri_coverage_message(report_data)
        return self.send_notification(message_text)
