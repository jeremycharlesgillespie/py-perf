# py-perf-daemon Installation and Setup Guide

This guide covers installing and configuring the py-perf-daemon for continuous system monitoring.

## Overview

The py-perf-daemon is a background service that continuously collects system metrics (CPU, memory, network) and makes them available for correlation with py-perf function timing data. This enables you to understand how system load affects your application performance.

## Quick Start

### 1. Install py-perf with daemon support

```bash
cd py-perf
pip3 install -r requirements.txt
pip3 install psutil  # Required for system monitoring
```

### 2. Test the daemon locally

```bash
# Start daemon in foreground for testing
python3 py-perf-daemon start

# In another terminal, check status
python3 py-perf-daemon status

# Stop the daemon
python3 py-perf-daemon stop
```

## Production Installation

### Linux (systemd)

#### 1. Install the daemon

```bash
# Copy daemon executable
sudo cp py-perf-daemon /usr/local/bin/
sudo chmod +x /usr/local/bin/py-perf-daemon

# Copy systemd service file
sudo cp scripts/py-perf-daemon.service /etc/systemd/system/

# Create user and directories
sudo useradd -r -s /bin/false py-perf
sudo mkdir -p /var/lib/py-perf /var/log/py-perf
sudo chown py-perf:py-perf /var/lib/py-perf /var/log/py-perf

# Copy configuration
sudo mkdir -p /etc/py-perf
sudo cp config/daemon.yaml.example /etc/py-perf/daemon.yaml
sudo chown py-perf:py-perf /etc/py-perf/daemon.yaml
```

#### 2. Configure the daemon

Edit `/etc/py-perf/daemon.yaml`:

```yaml
daemon:
  # Use system paths
  pid_file: /var/run/py-perf-daemon.pid
  log_file: /var/log/py-perf/daemon.log
  data_dir: /var/lib/py-perf
  sample_interval: 1.0
  data_retention_hours: 168  # 1 week
  enable_network_monitoring: true

monitoring:
  auto_track_python: true
  cpu_alert_threshold: 90
  memory_alert_threshold: 85
```

#### 3. Start and enable the service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Start the service
sudo systemctl start py-perf-daemon

# Enable auto-start on boot
sudo systemctl enable py-perf-daemon

# Check status
sudo systemctl status py-perf-daemon

# View logs
sudo journalctl -u py-perf-daemon -f
```

### macOS (launchd)

#### 1. Install the daemon

```bash
# Copy daemon executable
sudo cp py-perf-daemon /usr/local/bin/
sudo chmod +x /usr/local/bin/py-perf-daemon

# Create directories
sudo mkdir -p /var/lib/py-perf /var/log/py-perf
```

#### 2. Install launchd service

```bash
# Copy plist file
sudo cp scripts/com.pyperf.daemon.plist /Library/LaunchDaemons/

# Load the service
sudo launchctl load /Library/LaunchDaemons/com.pyperf.daemon.plist

# Start the service
sudo launchctl start com.pyperf.daemon
```

#### 3. Check status

```bash
# Check if running
python3 /usr/local/bin/py-perf-daemon status

# View logs
tail -f /var/log/py-perf/daemon.log
```

## User Installation (Non-root)

For development or single-user installations:

### 1. Setup directories

```bash
mkdir -p ~/.py-perf/data ~/.py-perf/logs
```

### 2. Copy configuration

```bash
cp config/daemon.yaml.example ~/.py-perf/daemon.yaml
```

### 3. Edit configuration for user paths

```yaml
daemon:
  pid_file: ~/.py-perf/daemon.pid
  log_file: ~/.py-perf/logs/daemon.log
  data_dir: ~/.py-perf/data
  sample_interval: 1.0
  data_retention_hours: 24
```

### 4. Start daemon

```bash
# Start with custom config
./py-perf-daemon -c ~/.py-perf/daemon.yaml start

# Check status
./py-perf-daemon -c ~/.py-perf/daemon.yaml status
```

## Verifying Installation

### 1. Check daemon is running

```bash
# Using the daemon command
py-perf-daemon status

# Or check process list
ps aux | grep py-perf-daemon
```

### 2. Verify data collection

```bash
# Check data directory
ls -la /var/lib/py-perf/  # or ~/.py-perf/data/

# Look for metrics files
find /var/lib/py-perf -name "metrics_*.json" -mtime -1
```

### 3. Test PyPerf integration

```python
from py_perf import PyPerf
import time

# Initialize PyPerf
perf = PyPerf()

# Check daemon connection
config_info = perf.get_config_info()
print("Daemon status:", config_info.get('daemon'))

@perf.time_it
def test_function():
    time.sleep(0.1)
    return "test"

# Run function
result = test_function()

# Get enhanced summary with system context
summary = perf.get_enhanced_summary()
print("System monitoring enabled:", summary.get('system_monitoring_enabled'))

# Get system correlation report
correlation = perf.get_system_correlation_report()
print("Correlation report:", correlation)
```

## Configuration Options

### Daemon Configuration (`/etc/py-perf/daemon.yaml`)

```yaml
daemon:
  sample_interval: 1.0           # Sampling frequency (seconds)
  max_samples: 3600              # Memory buffer size
  data_retention_hours: 168      # How long to keep data files
  enable_network_monitoring: true # Include network metrics

monitoring:
  auto_track_python: true        # Auto-track Python processes
  track_processes:               # Additional processes to monitor
    - node
    - java
  cpu_alert_threshold: 90        # Log warnings above this CPU %
  memory_alert_threshold: 85     # Log warnings above this memory %

export:
  format: json                   # Export format
  compress: true                 # Compress exported files
  batch_size: 1000              # Samples per file
```

### PyPerf Configuration (`.py-perf.yaml`)

```yaml
py_perf:
  enabled: true
  enable_system_monitoring: true  # Enable daemon integration

local:
  enabled: true
  data_dir: "./perf_data"
```

## Troubleshooting

### Daemon not starting

1. **Check permissions**:
   ```bash
   sudo chown py-perf:py-perf /var/lib/py-perf /var/log/py-perf
   ```

2. **Check Python dependencies**:
   ```bash
   python3 -c "import psutil; print('psutil OK')"
   ```

3. **Run in foreground for debugging**:
   ```bash
   # Skip daemonization for debugging
   python3 py-perf-daemon start --no-daemon
   ```

### PyPerf not connecting to daemon

1. **Check daemon is running**:
   ```bash
   py-perf-daemon status
   ```

2. **Check data directory permissions**:
   ```bash
   ls -la /var/lib/py-perf/
   ```

3. **Enable debug logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   
   from py_perf import PyPerf
   perf = PyPerf()
   ```

### High resource usage

1. **Increase sample interval**:
   ```yaml
   daemon:
     sample_interval: 5.0  # Sample every 5 seconds instead of 1
   ```

2. **Disable network monitoring**:
   ```yaml
   daemon:
     enable_network_monitoring: false
   ```

3. **Reduce data retention**:
   ```yaml
   daemon:
     data_retention_hours: 24  # Keep only 1 day of data
   ```

## Uninstallation

### Linux (systemd)

```bash
# Stop and disable service
sudo systemctl stop py-perf-daemon
sudo systemctl disable py-perf-daemon

# Remove files
sudo rm /etc/systemd/system/py-perf-daemon.service
sudo rm /usr/local/bin/py-perf-daemon
sudo rm -rf /etc/py-perf
sudo rm -rf /var/lib/py-perf
sudo rm -rf /var/log/py-perf

# Remove user
sudo userdel py-perf

# Reload systemd
sudo systemctl daemon-reload
```

### macOS (launchd)

```bash
# Stop and unload service
sudo launchctl stop com.pyperf.daemon
sudo launchctl unload /Library/LaunchDaemons/com.pyperf.daemon.plist

# Remove files
sudo rm /Library/LaunchDaemons/com.pyperf.daemon.plist
sudo rm /usr/local/bin/py-perf-daemon
sudo rm -rf /var/lib/py-perf
sudo rm -rf /var/log/py-perf
```

## Security Considerations

1. **File Permissions**: Daemon runs as dedicated user with minimal permissions
2. **Network Access**: Only local system monitoring, no external connections
3. **Data Privacy**: Only system metrics collected, no application data
4. **Resource Limits**: Configured CPU and memory limits via systemd/launchd

## Performance Impact

- **CPU Usage**: ~0.1-0.5% with 1-second sampling
- **Memory Usage**: ~10-50MB depending on buffer size
- **Disk I/O**: Minimal, periodic batch writes
- **Network**: No network usage for monitoring