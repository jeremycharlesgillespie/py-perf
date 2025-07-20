# Python Library PyPI Boilerplate

## Project Structure

## Building and Publishing

```bash
# Build the package
python -m build

# Upload to PyPI (requires twine and PyPI account)
pip install twine
twine upload dist/*


# Py-Perf

This library is used to track and represent the performance of Python code that is executed via an easy to install and configure Python library.

## Installation

```bash
pip install py-perf
```

## Quick Start

### 1. Create Configuration File

Create a `.py-perf.yaml` file in your project directory:

```yaml
py_perf:
  enabled: true
  min_execution_time: 0.001

local:
  enabled: true
  data_dir: "./perf_data"
  format: "json"

filters:
  exclude_modules:
    - "requests"
    - "boto3"
```

### 2. Use in Your Code

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

# Method 2: Use as decorator with arguments
@perf.time_it(store_args=True)
def process_data(data, multiplier=2):
    return [x * multiplier for x in data]

# Call your functions
result1 = slow_function(1000)
result2 = process_data([1, 2, 3, 4, 5])

# Performance data is automatically collected and uploaded
# - Local mode: Saved to ./perf_data/ as JSON files
# - AWS mode: Uploaded to DynamoDB on program exit
# - View data using the web dashboard at http://localhost:8000

# Optional: Get timing results programmatically
summary = perf.get_summary()
print(f"Tracked {summary['call_count']} function calls")
```

### 3. View Results

**Automatic Data Collection:**
- **Local Mode**: Performance data is automatically saved to `./perf_data/` as JSON files
- **AWS Mode**: Data is automatically uploaded to DynamoDB when your program exits

**Web Dashboard:**
Start the included web dashboard to visualize your performance data:

```bash
# Start the web dashboard
python manage.py runserver 8000
```

Then visit http://localhost:8000 to see:
- Performance overview and metrics
- Function-by-function analysis  
- Historical trends and comparisons
- Advanced filtering and search

For AWS integration and production setup, see the Configuration section below.

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/jeremycharlesgillespie/py-perf.git
cd py-perf

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt

# For development (includes testing tools)
pip install -r requirements-dev.txt

# Install pre-commit hooks (optional)
pre-commit install
```

## Configuration

PyPerf uses YAML configuration files for flexible and easy setup. Configuration sources are loaded in priority order:

1. **Default configuration** (built-in defaults)
2. **User configuration files** (`.py-perf.yaml`, `py-perf.yaml`)
3. **Runtime overrides** (passed to PyPerf constructor)

### Quick Start - Local Mode (No AWS Required)

Create a `.py-perf.yaml` file in your project directory:

```yaml
py_perf:
  enabled: true
  debug: false
  min_execution_time: 0.001

local:
  enabled: true  # Use local storage, no AWS required
  data_dir: "./perf_data"
  format: "json"
  max_records: 1000

filters:
  exclude_modules:
    - "boto3"
    - "requests"
    - "urllib3"
  track_arguments: false
```

### AWS DynamoDB Mode

For production AWS usage:

```yaml
py_perf:
  enabled: true
  min_execution_time: 0.001

aws:
  region: "us-east-1"
  table_name: "py-perf-data"
  auto_create_table: true

upload:
  strategy: "on_exit"  # on_exit, real_time, batch, manual

local:
  enabled: false  # Disable local storage
```

### Advanced Configuration

See `.py-perf.yaml.example` for all configuration options including:

- **Performance filtering** (modules, functions, execution time thresholds)
- **Upload strategies** (real-time, batch, manual)
- **Logging configuration**
- **Dashboard settings**

### Runtime Configuration

You can also configure PyPerf programmatically:

```python
from py_perf import PyPerf

# Local-only mode
perf = PyPerf({
    "local": {"enabled": True},
    "py_perf": {"debug": True}
})

# AWS mode with custom settings
perf = PyPerf({
    "aws": {
        "region": "us-east-1",
        "table_name": "my-perf-data"
    },
    "local": {"enabled": False}
})
```

### Configuration File Locations

PyPerf searches for configuration files in this order:

1. `./py-perf.yaml` (current directory)
2. `./.py-perf.yaml` (current directory, hidden file)
3. `~/.py-perf.yaml` (home directory)
4. `~/.config/py-perf/config.yaml` (XDG config directory)

### AWS Setup

For AWS mode:
1. Configure AWS CLI: `aws configure`
2. Create your `.py-perf.yaml` with AWS settings
3. PyPerf will automatically create DynamoDB tables if needed

See `AWS_SETUP.md` for detailed AWS configuration instructions.

### Virtual Environment Usage

Always activate the virtual environment before running PyPerf:

```bash
# Activate virtual environment
source venv/bin/activate

# Run your PyPerf application
python3 tester.py

# Deactivate when done
deactivate
```

## Web Dashboard

PyPerf includes a Django web dashboard for visualizing and analyzing performance data from DynamoDB.

### Starting the Web Dashboard

```bash
# Activate virtual environment
source venv/bin/activate

# Run database migrations (first time only)
python manage.py migrate

# Start the Django development server
python manage.py runserver 8000
```

The dashboard will be available at: http://127.0.0.1:8000

### Web Dashboard Features

- **Performance Overview**: Key metrics, slowest functions, most active hosts
- **Advanced Filtering**: Filter by hostname, date range, function name, session ID
- **Sorting**: Sort records by timestamp, hostname, total calls, wall time, etc.
- **Function Analysis**: Detailed performance analysis for specific functions
- **REST API**: Programmatic access to performance data
- **Real-time Data**: Automatically displays latest performance data from DynamoDB

### Testing

PyPerf includes two comprehensive test suites for the web dashboard:

#### 1. Integration Tests (Requires DynamoDB Connection)

Run the full integration test suite that tests with a real Django server and DynamoDB:

```bash
# Activate virtual environment
source venv/bin/activate

# Run integration test suite
python test_django_server.py
```

The integration test suite will:
- Automatically start/stop the Django server
- Test all web pages and API endpoints with real data
- Verify response times and error handling
- Test function analysis and record detail pages
- Report detailed results with 100% automation

#### 2. Unit Tests (Offline, No External Dependencies)

Run the offline unit test suite with mocked dependencies:

```bash
# Activate virtual environment
source venv/bin/activate

# Run offline unit tests
python manage.py test pyperfweb.dashboard.tests

# Run with verbose output
python manage.py test pyperfweb.dashboard.tests -v 2
```

The unit test suite will:
- Test all 7 view functions with mocked data
- Verify error handling and edge cases
- Test API endpoints with JSON validation
- Work completely offline without DynamoDB
- Cover comprehensive scenarios including empty databases and malformed inputs

#### Test Coverage Summary

- **Integration Tests**: 25 tests covering real server functionality
- **Unit Tests**: 18 tests covering all views with mocked dependencies
- **Combined Coverage**: All views, error scenarios, and edge cases tested
- **Offline Capability**: Unit tests run without internet or AWS connection

### Running PyPerf Library Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run PyPerf library tests
python tester.py
```

### Code Formatting

```bash
# Activate virtual environment
source venv/bin/activate

# Format code (if dev dependencies installed)
black src tests
isort src tests
flake8 src tests
mypy src
```

## License

MIT License - see LICENSE file for details.
