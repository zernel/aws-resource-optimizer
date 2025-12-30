# Prometheus System Inspection Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd /path/to/aws-resource-optimizer
pip install -r requirements.txt
```

### 2. Configure Settings

Copy and edit the configuration file:

```bash
cp config/settings.yaml.sample config/settings.yaml
```

Edit `config/settings.yaml` and update the `prometheus_inspection` section:

```yaml
prometheus_inspection:
  # Option 1: Direct URL to Prometheus server
  prometheus_url: "http://your-prometheus-server:9090"
  
  # Option 2: Docker container name (will auto-detect IP)
  # Uncomment if Prometheus runs in Docker
  # container_name: "prometheus"
  
  # OpenAI Configuration
  openai_api_key: "sk-your-actual-openai-api-key"
  model: "gpt-4o"
  
  # Default queries are already configured for 7-day analysis, modify if needed
  queries:
    cpu_usage: 'avg by (instance) (1 - rate(node_cpu_seconds_total{mode="idle"}[7d])) * 100'
    mem_usage: 'max by (instance) (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
    disk_free: 'min by (instance, mountpoint) (node_filesystem_avail_bytes{fstype=~"ext4|xfs"} / node_filesystem_size_bytes{fstype=~"ext4|xfs"}) * 100'
  
  # Alert thresholds
  thresholds:
    cpu_warning: 80
    mem_warning: 90
    disk_warning: 15
```

### 3. Test the Script

Run manually to test:

```bash
python src/run_prometheus_inspection.py
```

Expected output:
```
Starting Prometheus System Inspection
Configuration loaded from /path/to/config/settings.yaml
...
=== Prometheus Inspection Report ===
Metrics collected: X

## Overall System Health: Normal

...

Done!
```

### 4. Set Up Cron Job

Add to your crontab:

```bash
crontab -e
```

Add this line for weekly execution (every Monday at 9 AM):

```
0 9 * * 1 cd /path/to/aws-resource-optimizer && /path/to/venv/bin/python src/run_prometheus_inspection.py 2>&1
```

## Configuration Options

### Prometheus Connection

**Option 1: Direct URL** (Recommended for production)
```yaml
prometheus_url: "http://prometheus.example.com:9090"
```

**Option 2: Docker Container** (Useful for local development)
```yaml
container_name: "prometheus"
```

### Custom Queries

Add your own Prometheus queries:

```yaml
queries:
  cpu_usage: 'your_custom_query'
  custom_metric: 'rate(custom_metric[24h])'
```

### Threshold Customization

Adjust warning thresholds based on your infrastructure:

```yaml
thresholds:
  cpu_warning: 70    # Lower threshold for stricter monitoring
  mem_warning: 85
  disk_warning: 20   # Higher threshold if you have large disks
```

## Troubleshooting

### Issue: "Could not find IP for container"

**Solution:** Make sure the container name is correct and the container is running:
```bash
docker ps | grep prometheus
```

### Issue: "OpenAI API error"

**Solution:** Verify your API key is correct and has available credits:
- Check at: https://platform.openai.com/api-keys
- Ensure billing is set up

### Issue: "No data collected from Prometheus"

**Solution:** 
1. Verify Prometheus is accessible:
   ```bash
   curl http://your-prometheus:9090/api/v1/query?query=up
   ```
2. Check if node_exporter is running and exposing metrics
3. Verify your Prometheus queries are correct

### Issue: "Mattermost notification failed"

**Solution:**
1. Test webhook manually:
   ```bash
   curl -X POST -H 'Content-Type: application/json' \
     -d '{"text":"Test message"}' \
     https://your-mattermost/hooks/your-webhook
   ```
2. Verify webhook URL in config is correct
3. Check network connectivity to Mattermost server

## Log Files

Check logs for debugging:

```bash
tail -f logs/prometheus_inspection.log
```

## Integration with Existing RI Analysis

Both scripts can run independently:

```bash
# RI Analysis (monthly)
0 8 1 * * cd /path/to/aws-resource-optimizer && python src/run_ri_analysis.py

# System Inspection (weekly, every Monday)
0 9 * * 1 cd /path/to/aws-resource-optimizer && python src/run_prometheus_inspection.py
```

They share the same Mattermost configuration and can post to the same or different channels.

