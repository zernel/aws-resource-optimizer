"""
Prometheus System Metrics Inspector

This module collects system metrics from Prometheus and uses AI to generate
daily inspection reports.
"""

import logging
import subprocess
import requests
from openai import OpenAI

logger = logging.getLogger(__name__)

class PrometheusInspector:
    """Collects metrics from Prometheus and generates AI-powered inspection reports."""
    
    # Default queries for system metrics (7-day analysis window)
    DEFAULT_QUERIES = {
        "cpu_usage": 'avg by (instance) (1 - rate(node_cpu_seconds_total{mode="idle"}[7d])) * 100',
        "mem_usage": 'max by (instance) (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100',
        "disk_free": 'min by (instance, mountpoint) (node_filesystem_avail_bytes{fstype=~"ext4|xfs"} / node_filesystem_size_bytes{fstype=~"ext4|xfs"}) * 100'
    }
    
    def __init__(self, config):
        """
        Initialize the Prometheus inspector.
        
        Args:
            config (dict): Configuration from settings.yaml
        """
        self.config = config
        self.prometheus_url = config.get('prometheus_url')
        self.container_name = config.get('container_name')
        self.openai_api_key = config.get('openai_api_key')
        self.model = config.get('model', 'gpt-4o')
        self.queries = config.get('queries', self.DEFAULT_QUERIES)
        self.thresholds = config.get('thresholds', {
            'cpu_warning': 80,
            'mem_warning': 90,
            'disk_warning': 15
        })
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required for Prometheus inspection")
        
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
    def get_container_ip(self, container_name):
        """
        Get Docker container IP address dynamically.
        
        Args:
            container_name (str): Docker container name
            
        Returns:
            str: Prometheus URL with container IP
        """
        try:
            cmd = f"docker inspect -f '{{{{range .NetworkSettings.Networks}}}}{{{{.IPAddress}}}}{{{{end}}}}' {container_name}"
            ip = subprocess.check_output(cmd, shell=True).decode().strip()
            if not ip:
                raise ValueError(f"Could not find IP for container: {container_name}")
            prometheus_url = f"http://{ip}:9090"
            logger.info(f"Found Prometheus container at {prometheus_url}")
            return prometheus_url
        except Exception as e:
            logger.error(f"Error getting container IP: {e}")
            return None
    
    def get_prometheus_url(self):
        """
        Get Prometheus URL from configuration or by detecting container.
        
        Returns:
            str: Prometheus URL
        """
        if self.prometheus_url:
            return self.prometheus_url
        elif self.container_name:
            return self.get_container_ip(self.container_name)
        else:
            raise ValueError("Either prometheus_url or container_name must be specified in configuration")
    
    def fetch_prometheus_data(self, prometheus_url):
        """
        Fetch metrics data from Prometheus API.
        
        Args:
            prometheus_url (str): Base URL of Prometheus server
            
        Returns:
            list: List of metric data strings
        """
        report_data = []
        
        for metric_name, query in self.queries.items():
            try:
                url = f"{prometheus_url}/api/v1/query"
                response = requests.get(url, params={'query': query}, timeout=10)
                response.raise_for_status()
                
                results = response.json().get('data', {}).get('result', [])
                
                for res in results:
                    instance = res['metric'].get('instance', 'unknown')
                    value = float(res['value'][1])
                    
                    if metric_name == "cpu_usage":
                        val_str = f"Avg CPU Usage: {value:.2f}%"
                    elif metric_name == "mem_usage":
                        val_str = f"Max Mem Usage: {value:.2f}%"
                    elif metric_name == "disk_free":
                        mount = res['metric'].get('mountpoint', '/')
                        val_str = f"Min Disk Free ({mount}): {value:.2f}%"
                    else:
                        val_str = f"{metric_name}: {value:.2f}"
                    
                    report_data.append({
                        'instance': instance,
                        'metric': metric_name,
                        'value': value,
                        'display': f"[{instance}] {val_str}"
                    })
                    
                logger.info(f"Fetched {len(results)} results for metric: {metric_name}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching {metric_name} from Prometheus: {e}")
            except Exception as e:
                logger.error(f"Unexpected error processing {metric_name}: {e}")
        
        return report_data
    
    def format_data_for_ai(self, raw_data):
        """
        Format raw metric data for AI consumption.
        
        Args:
            raw_data (list): List of metric data dictionaries
            
        Returns:
            str: Formatted text for AI prompt
        """
        if not raw_data:
            return "No data collected from Prometheus."
        
        lines = [item['display'] for item in raw_data]
        return "\n".join(lines)
    
    def get_ai_summary(self, raw_data_text):
        """
        Generate AI summary of system metrics.
        
        Args:
            raw_data_text (str): Formatted metric data text
            
        Returns:
            str: AI-generated inspection report
        """
        if not raw_data_text or raw_data_text == "No data collected from Prometheus.":
            return "No data collected from Prometheus. Please check container status and configuration."
        
        thresholds = self.thresholds
        prompt = f"""
You are an expert SRE. Below is the system performance data for the past 7 days:

{raw_data_text}

Please provide a concise weekly inspection report in English with factual analysis only:
1. Overall system health status (Normal/Warning/Critical).
2. Highlight any instances with potential risks:
   - CPU > {thresholds['cpu_warning']}%
   - Memory > {thresholds['mem_warning']}%
   - Disk free space < {thresholds['disk_warning']}%
3. Identify instances with potential resource waste:
   - List each server only once, with all its resource waste indicators on the same line
   - Format: Server name — CPU usage: X%, Memory usage: Y% (indicate if very low)
   - Focus on servers with very low average CPU usage (< 10-15%) and/or very low memory usage (< 20-30%)
   - Do not create separate categories for the same server; combine all observations for each server into a single entry

Use Markdown formatting with bullet points. Keep it professional and concise.
This is a factual analysis report only - provide observations and data analysis, but do not include actionable suggestions or recommendations. Do not offer to generate additional documents or rulesets.
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            summary = response.choices[0].message.content
            logger.info("Successfully generated AI summary")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating AI summary: {e}")
            return f"Error generating AI summary: {str(e)}"
    
    def run_inspection(self):
        """
        Run the complete inspection process.
        
        Returns:
            dict: Inspection report data
        """
        logger.info("Starting Prometheus system inspection")
        
        try:
            # Get Prometheus URL
            prometheus_url = self.get_prometheus_url()
            if not prometheus_url:
                raise ValueError("Could not determine Prometheus URL")
            
            # Fetch metrics data
            logger.info(f"Fetching data from {prometheus_url}")
            raw_data = self.fetch_prometheus_data(prometheus_url)
            
            # Format data for AI
            formatted_data = self.format_data_for_ai(raw_data)
            
            # Generate AI summary
            logger.info("Generating AI summary")
            ai_summary = self.get_ai_summary(formatted_data)
            
            # Prepare report data
            report_data = {
                'prometheus_url': prometheus_url,
                'metrics_count': len(raw_data),
                'raw_metrics': raw_data,
                'formatted_data': formatted_data,
                'ai_summary': ai_summary
            }
            
            logger.info("Inspection completed successfully")
            return report_data
            
        except Exception as e:
            logger.error(f"Inspection failed: {e}", exc_info=True)
            raise

