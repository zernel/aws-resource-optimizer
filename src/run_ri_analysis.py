"""
EC2 Reserved Instance Analysis Runner

This is the main entry point for running EC2 Reserved Instance coverage analysis.
It loads configuration, runs the analysis, generates reports, and sends notifications.
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

from src.analyzers.ri_coverage import RICoverageAnalyzer
from src.notifiers.mattermost import MattermostNotifier
from src.utils import report_utils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "ri_analysis.log")),
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
    logger.info("Starting EC2 Reserved Instance Coverage Analysis")
    
    # Load configuration
    config = load_config()
    
    try:
        # Initialize the RI coverage analyzer
        analyzer = RICoverageAnalyzer(config['ri_analysis'])
        
        # Run the analysis
        report_data = analyzer.run_analysis()
        
        # Generate markdown report
        markdown_content = report_utils.generate_markdown_report(report_data)
        
        # Save markdown report
        filename = report_utils.generate_report_filename('ri_coverage', 'md')
        report_file = report_utils.save_markdown_report(markdown_content, filename, config['reporting'])
        
        # Send notification if enabled
        if config['notifications'].get('mattermost', {}).get('enabled', False):
            notifier = MattermostNotifier(config['notifications']['mattermost'])
            notifier.send_ri_report(report_data)
            
        logger.info(f"Analysis complete. Report generated: {report_file}")
        
        # Print report to console for immediate viewing
        print("\n" + markdown_content)
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
