# py-perf-jg

A lightweight Python performance tracking library with automatic data collection and visualization.

## Quick Start

### Installation

```bash
# Install from PyPI
pip install py-perf-jg

# For test installations from Test PyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ py-perf-jg
```

### Basic Usage

```python
from py_perf import PyPerf
import time

# Initialize the performance tracker (loads .py-perf.yaml automatically)
perf = PyPerf()

# Method 1: Use as decorator
@perf.time_it
def slow_function(n):
    time.sleep(0.1)
    return sum(range(n))

# Method 2: Use as decorator with argument tracking
@perf.time_it(store_args=True)
def process_data(data, multiplier=2):
    return [x * multiplier for x in data]

# Call your functions
result1 = slow_function(1000)
result2 = process_data([1, 2, 3, 4, 5])

# Performance data is automatically collected and saved:
# - Local mode: Saved to ./perf_data/ as JSON files
# - AWS mode: Uploaded to DynamoDB on program exit

# Optional: Get timing results programmatically
summary = perf.get_summary()
print(f"Tracked {summary['call_count']} function calls")
```

### Configuration

Create a `.py-perf.yaml` file in your project directory:

```yaml
py_perf:
  enabled: true
  min_execution_time: 0.001

# For local development (no AWS required)
local:
  enabled: true
  data_dir: "./perf_data"
  format: "json"

# For production with AWS DynamoDB
# aws:
#   region: "us-east-1"
#   table_name: "py-perf-data"

filters:
  exclude_modules:
    - "boto3"
    - "requests"
    - "urllib3"
  track_arguments: false
```

## Features

- **Zero-configuration**: Works out of the box with sensible defaults
- **Flexible storage**: Local JSON files or AWS DynamoDB
- **Smart filtering**: Exclude libraries and focus on your code
- **Automatic collection**: Data is saved automatically when your program exits
- **Lightweight**: Minimal performance overhead
- **Easy configuration**: YAML-based configuration files
- **Web dashboard support**: Integrates with [py-perf-viewer](https://github.com/jeremycharlesgillespie/py-perf-viewer) for data visualization

## Storage Options

### Local Storage (Default)
Perfect for development and testing:
- No external dependencies
- Human-readable JSON format
- Automatic cleanup of old files

### AWS DynamoDB
For production environments:
- Scalable cloud storage
- Real-time data access
- Built-in redundancy

Configure AWS mode in your `.py-perf.yaml`:

```yaml
py_perf:
  enabled: true

aws:
  region: "us-east-1"
  table_name: "py-perf-data"
  auto_create_table: true

local:
  enabled: false  # Disable local storage when using AWS
```

## Configuration File Locations

PyPerf searches for configuration files in this order:

1. `./py-perf.yaml` (current directory)
2. `./.py-perf.yaml` (current directory, hidden file)
3. `~/.py-perf.yaml` (home directory)
4. `~/.config/py-perf/config.yaml` (XDG config directory)

## API Reference

### PyPerf Class

```python
from py_perf import PyPerf

# Initialize with default configuration
perf = PyPerf()

# Initialize with custom configuration
perf = PyPerf({
    "local": {"enabled": True},
    "py_perf": {"debug": True}
})
```

### Decorators and Context Managers

```python
# As decorator
@perf.time_it
def my_function():
    pass

# As decorator with argument tracking
@perf.time_it(store_args=True)
def my_function_with_args(x, y):
    pass

# As context manager
with perf.time_it():
    # code to time
    pass
```

### Data Access

```python
# Get all results
results = perf.get_results()

# Get results for specific function
results = perf.get_results("my_function")

# Get summary statistics
summary = perf.get_summary()
summary = perf.get_summary("my_function")

# Manual data export
perf.save_to_local_storage()  # Force save to local files
perf.upload_to_dynamodb()    # Force upload to AWS
```

## License

MIT License - see LICENSE file for details.

## Web Dashboard

For visualizing and analyzing performance data, use the companion [py-perf-viewer](https://github.com/jeremycharlesgillespie/py-perf-viewer) Django dashboard:

```bash
# Install the viewer dashboard
pip install py-perf-viewer

# Or run the standalone project
git clone https://github.com/jeremycharlesgillespie/py-perf-viewer
cd py-perf-viewer
pip install -r requirements.txt
python start_viewer.py
```

The dashboard provides:
- **Performance Overview**: Key metrics, slowest functions, most active hosts
- **Advanced Filtering**: Filter by hostname, date range, function name, session ID
- **Function Analysis**: Detailed performance analysis for specific functions
- **REST API**: Programmatic access to performance data
- **Real-time Data**: Automatically displays latest performance data

## Package Development

### Building and Publishing

This package uses automated version management:

```bash
# Build and upload to PyPI (increments version automatically)
./upload_package.sh

# Build only (increments version)
python build_package.py

# Check current version
python -c "from version_manager import get_current_version; print(get_current_version())"
```

### Related Projects

- **[py-perf-viewer](https://github.com/jeremycharlesgillespie/py-perf-viewer)** - Django web dashboard for data visualization
- **[py-perf on PyPI](https://pypi.org/project/py-perf-jg/)** - Published package on PyPI

## Contributing

This is a standalone PyPI package. For development setup and contribution guidelines, see the main repository at [github.com/jeremycharlesgillespie/py-perf](https://github.com/jeremycharlesgillespie/py-perf).