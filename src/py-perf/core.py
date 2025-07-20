import time
import functools
import json
import atexit
import uuid
import os
import re
import logging
from pathlib import Path
from typing import Any, Optional, Dict, List, Callable

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

# Import our configuration system
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "py_perf"))
from config import get_config, PyPerfConfig


class TimingResult:
    """Stores timing information for a function call."""
    
    def __init__(self, function_name: str, wall_time: float, cpu_time: float, 
                 args: tuple = (), kwargs: dict = None):
        self.function_name = function_name
        self.wall_time = wall_time
        self.cpu_time = cpu_time
        self.args = args
        self.kwargs = kwargs or {}
        self.timestamp = time.time()


class PyPerf:
    """Performance tracking library for Python functions with OmegaConf configuration."""
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the PyPerf instance.
        
        Args:
            config_override: Optional configuration overrides (will be merged with default config)
        """
        # Load configuration using OmegaConf
        self.config: PyPerfConfig = get_config(config_override)
        self.logger = logging.getLogger(__name__)
        
        # Initialize core state
        self.timing_results: List[TimingResult] = []
        self.session_id = str(uuid.uuid4())
        
        # Check if PyPerf is enabled
        if not self.config.is_enabled():
            self.logger.info("PyPerf is disabled via configuration")
            return
        
        # Validate configuration
        issues = self.config.validate()
        if issues:
            self.logger.warning(f"Configuration issues found: {issues}")
        
        # Initialize storage backend
        self._init_storage()
        
        # Register exit handler for automatic upload
        upload_strategy = self.config.get("upload.strategy", "on_exit")
        if upload_strategy == "on_exit":
            atexit.register(self._upload_results)
        
        self.logger.debug(f"PyPerf initialized with session_id: {self.session_id}")
    
    def _init_storage(self) -> None:
        """Initialize storage backend (DynamoDB or local)."""
        self.dynamodb_client = None
        self.local_storage = None
        
        if self.config.is_local_only():
            self._init_local_storage()
        else:
            self._init_dynamodb()
    
    def _init_local_storage(self) -> None:
        """Initialize local storage."""
        data_dir = Path(self.config.get("local.data_dir", "./perf_data"))
        data_dir.mkdir(parents=True, exist_ok=True)
        
        storage_format = self.config.get("local.format", "json")
        self.local_storage = {
            "data_dir": data_dir,
            "format": storage_format
        }
        
        self.logger.debug(f"Local storage initialized: {data_dir}")
    
    def _init_dynamodb(self) -> None:
        """Initialize DynamoDB client."""
        if not BOTO3_AVAILABLE:
            self.logger.error("boto3 not available, cannot use DynamoDB. Set PY_PERF_LOCAL_ENABLED=true for local mode")
            return
        
        try:
            aws_config = self.config.get_aws_config()
            region = aws_config.get("region")
            profile = aws_config.get("profile")
            
            session_kwargs = {"region_name": region}
            if profile:
                session_kwargs["profile_name"] = profile
            
            session = boto3.Session(**session_kwargs)
            self.dynamodb_client = session.client('dynamodb')
            
            # Test connection
            self.dynamodb_client.describe_table(TableName=aws_config["table_name"])
            self.logger.debug(f"DynamoDB client initialized for table: {aws_config['table_name']}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                if self.config.get("aws.auto_create_table", True):
                    self._create_dynamodb_table()
                else:
                    self.logger.error(f"DynamoDB table not found: {aws_config['table_name']}")
                    self.dynamodb_client = None
            else:
                self.logger.error(f"DynamoDB connection failed: {e}")
                self.dynamodb_client = None
        except Exception as e:
            self.logger.error(f"Could not initialize DynamoDB client: {e}")
            self.dynamodb_client = None
    
    def _create_dynamodb_table(self) -> None:
        """Create DynamoDB table with proper schema."""
        try:
            aws_config = self.config.get_aws_config()
            table_name = aws_config["table_name"]
            
            self.dynamodb_client.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'id', 'AttributeType': 'N'}
                ],
                BillingMode='PROVISIONED',
                ProvisionedThroughput={
                    'ReadCapacityUnits': aws_config.get("read_capacity", 5),
                    'WriteCapacityUnits': aws_config.get("write_capacity", 5)
                }
            )
            
            # Wait for table to be active
            waiter = self.dynamodb_client.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            self.logger.info(f"Created DynamoDB table: {table_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to create DynamoDB table: {e}")
            self.dynamodb_client = None
    
    def time_it(self, func: Callable = None, *, store_args: bool = None) -> Callable:
        """Decorator to time function execution.
        
        Args:
            func: Function to decorate (when used as @time_it)
            store_args: Whether to store function arguments in results (uses config default if None)
            
        Returns:
            Decorated function or decorator
        """
        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                # Check if PyPerf is enabled
                if not self.config.is_enabled():
                    return f(*args, **kwargs)
                
                # Check if this function should be tracked based on filters
                if not self._should_track_function(f.__name__, f.__module__):
                    return f(*args, **kwargs)
                
                wall_start = time.perf_counter()
                cpu_start = time.process_time()
                
                try:
                    result = f(*args, **kwargs)
                    return result
                finally:
                    wall_time = time.perf_counter() - wall_start
                    cpu_time = time.process_time() - cpu_start
                    
                    # Check minimum execution time threshold
                    min_time = self.config.get("py_perf.min_execution_time", 0.001)
                    if wall_time < min_time:
                        return
                    
                    # Check if we should store arguments
                    should_store_args = store_args
                    if should_store_args is None:
                        should_store_args = self.config.get("filters.track_arguments", False)
                    
                    timing_result = TimingResult(
                        function_name=f.__name__,
                        wall_time=wall_time,
                        cpu_time=cpu_time,
                        args=args if should_store_args else (),
                        kwargs=kwargs if should_store_args else {}
                    )
                    
                    # Check max tracked calls limit
                    max_calls = self.config.get("py_perf.max_tracked_calls", 10000)
                    if len(self.timing_results) < max_calls:
                        self.timing_results.append(timing_result)
                    else:
                        self.logger.warning(f"Max tracked calls limit ({max_calls}) reached")
            
            return wrapper
        
        if func is None:
            return decorator
        else:
            return decorator(func)
    
    def _should_track_function(self, func_name: str, module_name: str) -> bool:
        """Check if function should be tracked based on configuration filters."""
        
        # Check exclude modules
        exclude_modules = self.config.get("filters.exclude_modules", [])
        for pattern in exclude_modules:
            if module_name and pattern in module_name:
                return False
        
        # Check include modules (if specified, only track these)
        include_modules = self.config.get("filters.include_modules", [])
        if include_modules:
            included = False
            for pattern in include_modules:
                if module_name and pattern in module_name:
                    included = True
                    break
            if not included:
                return False
        
        # Check exclude functions
        exclude_functions = self.config.get("filters.exclude_functions", [])
        for pattern in exclude_functions:
            if re.match(pattern, func_name):
                return False
        
        # Check include functions (if specified, only track these)
        include_functions = self.config.get("filters.include_functions", [])
        if include_functions:
            included = False
            for pattern in include_functions:
                if re.match(pattern, func_name):
                    included = True
                    break
            if not included:
                return False
        
        return True
    
    def get_results(self, function_name: Optional[str] = None) -> List[TimingResult]:
        """Get timing results.
        
        Args:
            function_name: Filter by function name, or None for all results
            
        Returns:
            List of timing results
        """
        if function_name:
            return [r for r in self.timing_results if r.function_name == function_name]
        return self.timing_results.copy()
    
    def get_summary(self, function_name: Optional[str] = None) -> Dict[str, Any]:
        """Get summary statistics for timing results.
        
        Args:
            function_name: Filter by function name, or None for all results
            
        Returns:
            Dictionary with summary statistics
        """
        results = self.get_results(function_name)
        if not results:
            return {}
        
        wall_times = [r.wall_time for r in results]
        cpu_times = [r.cpu_time for r in results]
        
        return {
            'function_name': function_name or 'all_functions',
            'call_count': len(results),
            'wall_time': {
                'total': sum(wall_times),
                'average': sum(wall_times) / len(wall_times),
                'min': min(wall_times),
                'max': max(wall_times)
            },
            'cpu_time': {
                'total': sum(cpu_times),
                'average': sum(cpu_times) / len(cpu_times),
                'min': min(cpu_times),
                'max': max(cpu_times)
            }
        }
    
    def clear_results(self) -> None:
        """Clear all timing results."""
        self.timing_results.clear()
    
    def enable(self) -> None:
        """Enable timing collection."""
        self.config.set("py_perf.enabled", True)
    
    def disable(self) -> None:
        """Disable timing collection."""
        self.config.set("py_perf.enabled", False)
    
    def get_unique_function_names(self) -> List[str]:
        """Get list of unique function names that have been timed."""
        return list(set(result.function_name for result in self.timing_results))
    
    def get_functions_with_stored_args(self) -> List[str]:
        """Get list of function names that have stored arguments."""
        functions_with_args = set()
        for result in self.timing_results:
            if result.args or result.kwargs:
                functions_with_args.add(result.function_name)
        return list(functions_with_args)
    
    def build_json_results(self) -> Dict[str, Any]:
        """Build complete JSON results automatically."""
        if not self.timing_results:
            return {
                "message": "No timing data collected",
                "overall_summary": {},
                "function_summaries": {},
                "detailed_results": {}
            }
        
        results = {
            "overall_summary": self.get_summary(),
            "function_summaries": {},
            "detailed_results": {}
        }
        
        # Get summary for each function
        for func_name in self.get_unique_function_names():
            summary = self.get_summary(func_name)
            if summary:
                results["function_summaries"][func_name] = summary
        
        # Get detailed results for functions with stored arguments
        for func_name in self.get_functions_with_stored_args():
            function_results = self.get_results(func_name)
            if function_results:
                results["detailed_results"][func_name] = []
                for result in function_results:
                    results["detailed_results"][func_name].append({
                        "args": result.args,
                        "kwargs": result.kwargs,
                        "wall_time": result.wall_time,
                        "cpu_time": result.cpu_time,
                        "timestamp": result.timestamp
                    })
        
        return results
    
    def _upload_to_dynamodb(self, results: Dict[str, Any]) -> bool:
        """Upload results to DynamoDB table."""
        if not self.dynamodb_client:
            self.logger.error("DynamoDB client not available")
            return False
            
        try:
            aws_config = self.config.get_aws_config()
            table_name = aws_config["table_name"]
            
            # Generate a unique ID for this session's data
            record_id = int(time.time() * 1000000)  # microsecond timestamp as ID
            
            # Prepare the item for DynamoDB
            item = {
                'id': {'N': str(record_id)},
                'session_id': {'S': self.session_id},
                'timestamp': {'N': str(time.time())},
                'hostname': {'S': os.uname().nodename if hasattr(os, 'uname') else 'unknown'},
                'data': {'S': json.dumps(results)}
            }
            
            # Add metadata if available
            if results.get('overall_summary'):
                summary = results['overall_summary']
                item['total_calls'] = {'N': str(summary.get('call_count', 0))}
                item['total_wall_time'] = {'N': str(summary.get('wall_time', {}).get('total', 0))}
                item['total_cpu_time'] = {'N': str(summary.get('cpu_time', {}).get('total', 0))}
            
            # Upload to DynamoDB
            timeout = self.config.get("upload.timeout", 30)
            self.dynamodb_client.put_item(
                TableName=table_name,
                Item=item
            )
            
            self.logger.info(f"Successfully uploaded timing data to DynamoDB (ID: {record_id})")
            return True
            
        except ClientError as e:
            self.logger.error(f"DynamoDB upload failed: {e.response['Error']['Message']}")
            return False
        except NoCredentialsError:
            self.logger.error("DynamoDB upload failed: AWS credentials not found")
            return False
        except Exception as e:
            self.logger.error(f"DynamoDB upload failed: {e}")
            return False
    
    def _save_to_local_storage(self, results: Dict[str, Any]) -> bool:
        """Save results to local storage."""
        if not self.local_storage:
            self.logger.error("Local storage not available")
            return False
        
        try:
            data_dir = self.local_storage["data_dir"]
            storage_format = self.local_storage["format"]
            
            # Generate filename with timestamp and session ID
            timestamp = int(time.time())
            filename = f"perf_data_{timestamp}_{self.session_id[:8]}"
            
            if storage_format == "json":
                filepath = data_dir / f"{filename}.json"
                with open(filepath, 'w') as f:
                    json.dump({
                        "id": timestamp * 1000000,
                        "session_id": self.session_id,
                        "timestamp": time.time(),
                        "hostname": os.uname().nodename if hasattr(os, 'uname') else 'unknown',
                        "data": results
                    }, f, indent=2)
            
            elif storage_format == "csv":
                # TODO: Implement CSV format
                self.logger.warning("CSV format not yet implemented, using JSON")
                return self._save_to_local_storage({**results, "format": "json"})
            
            elif storage_format == "sqlite":
                # TODO: Implement SQLite format
                self.logger.warning("SQLite format not yet implemented, using JSON")
                return self._save_to_local_storage({**results, "format": "json"})
            
            self.logger.info(f"Successfully saved timing data to local storage: {filepath}")
            
            # Clean up old files if needed
            self._cleanup_local_storage()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Local storage save failed: {e}")
            return False
    
    def _cleanup_local_storage(self) -> None:
        """Clean up old local storage files based on max_records setting."""
        try:
            max_records = self.config.get("local.max_records", 1000)
            data_dir = self.local_storage["data_dir"]
            
            # Get all perf data files
            pattern = "perf_data_*.json"
            files = list(data_dir.glob(pattern))
            
            # Sort by modification time (newest first)
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Remove excess files
            if len(files) > max_records:
                for f in files[max_records:]:
                    f.unlink()
                    self.logger.debug(f"Removed old performance data file: {f}")
                    
        except Exception as e:
            self.logger.warning(f"Failed to cleanup local storage: {e}")
    
    def _upload_results(self) -> None:
        """Internal method to upload results automatically based on configuration."""
        if not self.timing_results:
            return
            
        results = self.build_json_results()
        
        # Upload based on configuration
        uploaded = False
        if self.config.is_local_only():
            uploaded = self._save_to_local_storage(results)
        else:
            uploaded = self._upload_to_dynamodb(results)
        
        # Log results if debug mode is enabled
        if self.config.is_debug():
            self.logger.debug(f"Performance results: {json.dumps(results, indent=2)}")
    
    def output_results(self) -> None:
        """Manually output/upload results based on configuration."""
        self._upload_results()
    
    def upload_to_dynamodb(self) -> bool:
        """Manually upload current results to DynamoDB."""
        if not self.timing_results:
            self.logger.info("No timing data to upload")
            return False
            
        results = self.build_json_results()
        return self._upload_to_dynamodb(results)
    
    def save_to_local_storage(self) -> bool:
        """Manually save current results to local storage."""
        if not self.timing_results:
            self.logger.info("No timing data to save")
            return False
            
        results = self.build_json_results()
        return self._save_to_local_storage(results)
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get current configuration information for debugging."""
        return {
            "enabled": self.config.is_enabled(),
            "debug": self.config.is_debug(),
            "local_only": self.config.is_local_only(),
            "upload_strategy": self.config.get("upload.strategy"),
            "min_execution_time": self.config.get("py_perf.min_execution_time"),
            "max_tracked_calls": self.config.get("py_perf.max_tracked_calls"),
            "storage_type": "local" if self.config.is_local_only() else "dynamodb",
            "session_id": self.session_id,
            "current_tracked_calls": len(self.timing_results)
        }