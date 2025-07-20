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

```python
from py_perf import PyPerf
import time

# Initialize the performance tracker
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

# Get timing results
summary = perf.get_summary()
print(f"Total calls: {summary['call_count']}")
print(f"Average wall time: {summary['wall_time']['average']:.4f}s")
print(f"Average CPU time: {summary['cpu_time']['average']:.4f}s")

# Get results for specific function
slow_summary = perf.get_summary('slow_function')
print(f"slow_function called {slow_summary['call_count']} times")
```

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
pip install boto3

# Install in development mode with dev dependencies (optional)
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install
```

### AWS DynamoDB Setup

PyPerf automatically uploads timing data to AWS DynamoDB. See `AWS_SETUP.md` for complete setup instructions.

Quick setup:
1. Configure AWS CLI: `aws configure`
2. Ensure your AWS user has DynamoDB permissions for the `py-perf-data` table
3. PyPerf will automatically upload timing data on program exit

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

### Automated Testing

Run the comprehensive test suite to verify the web dashboard is working correctly:

```bash
# Activate virtual environment
source venv/bin/activate

# Run automated test suite
python test_django_server.py
```

The test suite will:
- Automatically start/stop the Django server
- Test all web pages and API endpoints
- Verify response times and error handling
- Report detailed results with 100% automation

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
