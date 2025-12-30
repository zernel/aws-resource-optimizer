# AWS Resource Optimizer

Automate the management of AWS resources for cost efficiency and optimization.

## Overview

AWS Resource Optimizer is a tool designed to help DevOps teams monitor, analyze, and optimize AWS resource utilization and costs. This project aims to provide automated solutions for common cost optimization challenges in AWS environments.

## Features

### EC2 Reserved Instance Coverage Analysis
- Scheduled analysis of EC2 Reserved Instance coverage across your AWS accounts
- Detailed reports showing running instances and RI coverage by region
- Automated notifications to Mattermost channels
- Simple overview of uncovered instances that could benefit from RI purchases

### Prometheus System Inspection (AI-Powered)
- Automated daily system health checks using Prometheus metrics
- AI-powered analysis of infrastructure performance over 24-hour periods
- Monitors CPU usage, memory consumption, and disk space
- Generates intelligent summaries with actionable recommendations
- Automated notifications to Mattermost channels

## Setup

### Prerequisites
- Python 3.8+
- AWS CLI configured with appropriate permissions (for RI analysis)
- Prometheus server (for system inspection)
- OpenAI API key (for AI-powered analysis)
- Server with crontab access
- Network access to Mattermost servers

### Installation
1. Clone this repository to your server
2. Install required dependencies: `pip install -r requirements.txt`
3. Configure AWS credentials and settings in `config/settings.yaml` (see `config/settings.yaml.sample`)
4. Set up crontab job to run the analyzer scripts

Example crontab configuration:
```
# Run EC2 RI coverage analysis every month
0 8 1 * * cd /path/to/aws-resource-optimizer && python src/run_ri_analysis.py 2>&1

# Run Prometheus system inspection daily at 9 AM
0 9 * * * cd /path/to/aws-resource-optimizer && python src/run_prometheus_inspection.py 2>&1
```

## Project Structure
```
aws-resource-optimizer/
├── src/
│   ├── analyzers/                      # Analysis modules
│   │   ├── ri_coverage.py              # RI coverage analyzer
│   │   └── prometheus_inspector.py     # Prometheus system inspector
│   ├── notifiers/
│   │   └── mattermost.py               # Mattermost notification handler
│   ├── utils/                          # Utility functions
│   │   ├── aws_utils.py                # AWS API helpers
│   │   └── report_utils.py             # Reporting helpers
│   ├── run_ri_analysis.py              # Main entry point for RI analysis
│   └── run_prometheus_inspection.py    # Main entry point for Prometheus inspection
├── config/
│   └── settings.yaml                   # Configuration file
├── reports/                            # Directory for generated reports
├── logs/                               # Log files
├── requirements.txt                    # Python dependencies
└── README.md
```

## Technologies

- Python with Boto3 (AWS SDK) for AWS resource management
- Prometheus for infrastructure metrics collection
- OpenAI GPT models for intelligent analysis
- Local file system for storing reports and logs
- Crontab for task scheduling
- Mattermost webhooks for notifications
- Pandas for data analysis and report generation

## License

[License information to be determined]
