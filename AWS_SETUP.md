# AWS DynamoDB Setup for PyPerf

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
                "dynamodb:DescribeTable"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:760761025470:table/py-perf-data"
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

You can configure PyPerf's DynamoDB behavior:

```python
from py_perf import PyPerf

# Default configuration (uploads to DynamoDB)
perf = PyPerf()

# Disable DynamoDB uploads
perf = PyPerf(config={'use_dynamodb': False})

# Custom table and region
perf = PyPerf(config={
    'dynamodb_table': 'my-custom-table',
    'aws_region': 'us-west-2'
})
```

### Testing the Setup

Run your PyPerf application. You should see either:
- `✓ Successfully uploaded timing data to DynamoDB (ID: xxxxx)` on success
- `✗ DynamoDB upload failed: [error message]` on failure

The application will still print JSON results to console as a backup regardless of upload status.