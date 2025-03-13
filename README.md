# AWS Resource Optimizer

Automate the management of AWS resources for cost efficiency and optimization.

## Overview

AWS Resource Optimizer is a tool designed to help DevOps teams monitor, analyze, and optimize AWS resource utilization and costs. This project aims to provide automated solutions for common cost optimization challenges in AWS environments.

## Features

### EC2 Reserved Instance Coverage Analysis
- Scheduled analysis of EC2 Reserved Instance coverage across your AWS accounts
- Detailed reports showing potential savings opportunities
- Automated notifications to Mattermost channels
- Historical trend analysis to track optimization progress
- Recommendations for new Reserved Instance purchases

## Planned Features (in future releases)

### Automated Instance Management
- Smart scheduling for non-production environments
- Automatic shutdown of development and testing instances during off-hours
- Customizable schedules based on team working hours
- Override mechanisms for special cases

### Storage Optimization
- Detection and cleanup of orphaned EBS volumes
- Identification of unused snapshots and AMIs
- Automated lifecycle policies for resource management
- Cost impact reports for storage resources

## Setup

### Prerequisites
- Python 3.8+
- AWS CLI configured with appropriate permissions
- Server with crontab access
- Network access to Mattermost servers

### Installation
1. Clone this repository to your server
2. Install required dependencies: `pip install -r requirements.txt`
3. Configure AWS credentials and settings in `config/settings.yaml`
4. Set up crontab job to run the analyzer scripts

Example crontab configuration:
```
# Run EC2 RI coverage analysis every Monday at 8 AM
0 8 * * 1 cd /path/to/aws-resource-optimizer && python src/run_ri_analysis.py >> /var/log/aws-optimizer/ri-analysis.log 2>&1
```

## Project Structure
```
aws-resource-optimizer/
├── src/
│   ├── analyzers/              # Analysis modules
│   │   └── ri_coverage.py      # RI coverage analyzer
│   ├── notifiers/
│   │   └── mattermost.py       # Mattermost notification handler
│   ├── utils/                  # Utility functions
│   │   ├── aws_utils.py        # AWS API helpers
│   │   └── report_utils.py     # Reporting helpers
│   └── run_ri_analysis.py      # Main entry point for RI analysis
├── config/
│   └── settings.yaml           # Configuration file
├── reports/                    # Directory for generated reports
├── logs/                       # Log files
├── requirements.txt            # Python dependencies
└── README.md
```

## Technologies

- Python with Boto3 (AWS SDK)
- Local file system for storing reports and logs
- Crontab for task scheduling
- Mattermost webhooks for notifications
- Pandas for data analysis and report generation

## License

[License information to be determined]
