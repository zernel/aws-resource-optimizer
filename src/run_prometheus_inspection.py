"""
Prometheus System Inspection Runner

This is the main entry point for running Prometheus system inspections.
It collects metrics over the past 7 days, generates AI-powered reports, 
and sends notifications. Designed to run weekly.
"""

import os
import sys
import yaml
import logging
from datetime import datetime

# Add the parent directory to sys.path to allow imports from the src directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Define base directory and ensure log directory exists
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

from src.analyzers.prometheus_inspector import PrometheusInspector
from src.notifiers.mattermost import MattermostNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "prometheus_inspection.log")),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def load_config(config_path="config/settings.yaml"):
    """
    Load configuration from YAML file.
    
    Args:
        config_path (str): Path to configuration file
        
    Returns:
        dict: Configuration data
    """
    # Use absolute path for configuration file
    if not os.path.isabs(config_path):
        config_path = os.path.join(BASE_DIR, config_path)
        
    try:
        with open(config_path, 'r') as config_file:
            config = yaml.safe_load(config_file)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        sys.exit(1)

def main():
    """Main execution function."""
    logger.info("Starting Prometheus System Inspection")
    
    # Load configuration
    config = load_config()
    
    try:
        # Initialize the Prometheus inspector
        inspector = PrometheusInspector(config['prometheus_inspection'])
        
        # Run the inspection
        report_data = inspector.run_inspection()
        
        # Print summary to console
        print("\n=== Prometheus Inspection Report ===")
        print(f"Metrics collected: {report_data['metrics_count']}")
        print(f"\n{report_data['ai_summary']}\n")
        
        # Send notification if enabled
        if config['notifications'].get('mattermost', {}).get('enabled', False):
            notifier = MattermostNotifier(config['notifications']['mattermost'])
            
            # Format message for Mattermost
            message = "## 🛡️ Infrastructure Daily Report\n---\n"
            message += report_data['ai_summary']
            
            # Send the notification
            success = notifier.send_notification(message)
            
            if success:
                logger.info("Successfully sent notification to Mattermost")
            else:
                logger.warning("Failed to send notification to Mattermost")
        else:
            logger.info("Mattermost notifications are disabled")
            
        logger.info("Inspection completed successfully")
        
    except Exception as e:
        logger.error(f"Inspection failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

