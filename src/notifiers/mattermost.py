"""
Mattermost Notification Handler

This module handles sending notifications to Mattermost channels
through webhook integrations.
"""

import json
import logging
import requests
from ..utils import report_utils

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
        
        Args:
            report_data (dict): The RI coverage report data
            
        Returns:
            dict: Formatted message object
        """
        # Generate markdown report
        markdown_content = report_utils.generate_markdown_report(report_data)
        
        # Create message payload for Mattermost
        message = {
            'text': markdown_content,
            'username': self.username,
            'icon_emoji': self.icon_emoji
        }
        
        if self.channel:
            message['channel'] = self.channel
        
        logger.debug("Formatted Mattermost message for RI coverage report")
        return message
    
    def send_notification(self, message):
        """
        Send a notification to the configured Mattermost channel.
        
        Args:
            message (dict or str): Message content to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            logger.info("Mattermost notifications are disabled in configuration")
            return False
            
        logger.info(f"Sending notification to Mattermost channel: {self.channel}")
        
        try:
            # Simplify message format to ensure it only contains fields supported by Mattermost
            simplified_message = {
                'text': message['text']
            }
            
            # Optional fields
            if 'username' in message:
                simplified_message['username'] = message['username']
            if 'icon_emoji' in message:
                simplified_message['icon_emoji'] = message['icon_emoji']
            if 'channel' in message:
                simplified_message['channel'] = message['channel']
            
            response = requests.post(
                self.webhook_url,
                json=simplified_message,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.info("Successfully sent notification to Mattermost")
                return True
            else:
                logger.error(f"Failed to send notification to Mattermost: {response.status_code} {response.text}")
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
        message = self.format_ri_coverage_message(report_data)
        return self.send_notification(message)
