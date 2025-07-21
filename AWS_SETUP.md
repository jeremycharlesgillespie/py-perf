# AWS DynamoDB Setup for PyPerf

## Installation with AWS Support

First, ensure you have the necessary dependencies:

```bash
# Install py-perf with AWS dependencies
pip install py-perf-jg boto3

# Or install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ py-perf-jg boto3
```

## Required AWS Role/Policy

To allow PyPerf to upload timing data to DynamoDB, you need to create an IAM role or user with the following permissions:

### IAM Policy JSON

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:DescribeTable",
                "dynamodb:CreateTable"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:*:table/py-perf-data"
            ]
        }
    ]
}
```

### Setup Options

#### Option 1: IAM User (Recommended for development)

1. Create an IAM user in AWS Console
2. Attach the policy above to the user
3. Create access keys for the user
4. Configure AWS credentials locally:

```bash
# Option A: AWS CLI
aws configure
# Enter your Access Key ID, Secret Access Key, and region (us-east-1)

# Option B: Environment variables
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key
export AWS_DEFAULT_REGION=us-east-1

# Option C: AWS credentials file
# Create ~/.aws/credentials with:
[default]
aws_access_key_id = your_access_key_id
aws_secret_access_key = your_secret_access_key
region = us-east-1
```

#### Option 2: IAM Role (Recommended for production/EC2)

1. Create an IAM role in AWS Console
2. Attach the policy above to the role
3. Attach the role to your EC2 instance or application

### DynamoDB Table Structure

The `py-perf-data` table stores the following data:

- **id** (Number, Primary Key): Unique microsecond timestamp
- **session_id** (String): UUID for each PyPerf session
- **timestamp** (Number): Unix timestamp when data was uploaded
- **hostname** (String): Machine hostname
- **data** (String): Complete JSON timing results
- **total_calls** (Number): Total function calls in session
- **total_wall_time** (Number): Total wall time in seconds
- **total_cpu_time** (Number): Total CPU time in seconds

### Configuration Options

Configure PyPerf's DynamoDB behavior using a `.py-perf.yaml` configuration file:

```yaml
py_perf:
  enabled: true

# For local development (no AWS required)
local:
  enabled: true  # This disables AWS uploads
  data_dir: "./perf_data"
  format: "json"

# For production with AWS DynamoDB
# local:
#   enabled: false

aws:
  region: "us-east-1"
  table_name: "py-perf-data"
  auto_create_table: true
  read_capacity: 5
  write_capacity: 5
```

You can also configure PyPerf programmatically:

```python
from py_perf import PyPerf

# Default configuration (loads .py-perf.yaml automatically)
perf = PyPerf()

# Override with custom AWS settings
perf = PyPerf({
    "aws": {
        "region": "us-east-1",
        "table_name": "my-custom-table"
    },
    "local": {"enabled": False}
})
```
