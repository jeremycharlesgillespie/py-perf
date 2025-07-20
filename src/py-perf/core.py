import time
import functools
import json
import atexit
import uuid
import os
from typing import Any, Optional, Dict, List, Callable

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


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
    """Performance tracking library for Python functions."""
    
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        """Initialize the PyPerf instance.
        
        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        self.timing_results: List[TimingResult] = []
        self.enabled = self.config.get('enabled', True)
        self.auto_output = self.config.get('auto_output', True)
        self._output_on_exit = self.config.get('output_on_exit', True)
        
        # DynamoDB configuration
        self.use_dynamodb = self.config.get('use_dynamodb', True)
        self.dynamodb_table = self.config.get('dynamodb_table', 'py-perf-data')
        self.aws_region = self.config.get('aws_region', 'us-east-1')
        self.session_id = str(uuid.uuid4())
        
        # Initialize DynamoDB client if available
        self.dynamodb_client = None
        if BOTO3_AVAILABLE and self.use_dynamodb:
            try:
                self.dynamodb_client = boto3.client('dynamodb', region_name=self.aws_region)
            except Exception as e:
                print(f"Warning: Could not initialize DynamoDB client: {e}")
                self.use_dynamodb = False
        
        # Register exit handler for automatic output
        if self._output_on_exit:
            atexit.register(self._output_results)
    
    def time_it(self, func: Callable = None, *, store_args: bool = False) -> Callable:
        """Decorator to time function execution.
        
        Args:
            func: Function to decorate (when used as @time_it)
            store_args: Whether to store function arguments in results
            
        Returns:
            Decorated function or decorator
        """
        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return f(*args, **kwargs)
                
                wall_start = time.perf_counter()
                cpu_start = time.process_time()
                
                try:
                    result = f(*args, **kwargs)
                    return result
                finally:
                    wall_time = time.perf_counter() - wall_start
                    cpu_time = time.process_time() - cpu_start
                    
                    timing_result = TimingResult(
                        function_name=f.__name__,
                        wall_time=wall_time,
                        cpu_time=cpu_time,
                        args=args if store_args else (),
                        kwargs=kwargs if store_args else {}
                    )
                    self.timing_results.append(timing_result)
            
            return wrapper
        
        if func is None:
            return decorator
        else:
            return decorator(func)
    
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
        self.enabled = True
    
    def disable(self) -> None:
        """Disable timing collection."""
        self.enabled = False
    
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
            return False
            
        try:
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
            self.dynamodb_client.put_item(
                TableName=self.dynamodb_table,
                Item=item
            )
            
            print(f"✓ Successfully uploaded timing data to DynamoDB (ID: {record_id})")
            return True
            
        except ClientError as e:
            print(f"✗ DynamoDB upload failed: {e.response['Error']['Message']}")
            return False
        except NoCredentialsError:
            print("✗ DynamoDB upload failed: AWS credentials not found")
            return False
        except Exception as e:
            print(f"✗ DynamoDB upload failed: {e}")
            return False
    
    def _output_results(self) -> None:
        """Internal method to output results automatically."""
        if not self.auto_output or not self.timing_results:
            return
            
        results = self.build_json_results()
        
        # Try to upload to DynamoDB first
        uploaded = False
        if self.use_dynamodb:
            uploaded = self._upload_to_dynamodb(results)
        
        # Always print results as backup/verification
        print("\n" + "=" * 50)
        print("PY-PERF TIMING RESULTS")
        if uploaded:
            print("(Also uploaded to DynamoDB)")
        print("=" * 50)
        print(json.dumps(results, indent=2))
    
    def output_results(self) -> None:
        """Manually output results in JSON format."""
        self._output_results()
    
    def upload_to_dynamodb(self) -> bool:
        """Manually upload current results to DynamoDB."""
        if not self.timing_results:
            print("No timing data to upload")
            return False
            
        results = self.build_json_results()
        return self._upload_to_dynamodb(results)