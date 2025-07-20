#!/usr/bin/env python3
"""Test file for PyPerf timing functionality."""

import time
import random
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'py-perf'))
from core import PyPerf


# Initialize the performance tracker
perf = PyPerf()


@perf.time_it
def fast_calculation():
    """Quick calculation - should show minimal CPU time."""
    return sum(range(1000))


@perf.time_it
def slow_io_operation():
    """Simulates I/O with sleep - wall time > CPU time."""
    time.sleep(0.1)
    return "I/O operation complete"


@perf.time_it(store_args=True)
def cpu_intensive_task(iterations=100000):
    """CPU-heavy task - CPU time should be significant."""
    result = 0
    for i in range(iterations):
        result += i ** 2
    return result


@perf.time_it
def mixed_workload():
    """Mix of CPU work and I/O."""
    # Some CPU work
    data = [random.random() for _ in range(5000)]
    # Some I/O simulation
    time.sleep(0.05)
    # More CPU work
    return sum(x * 2 for x in data)


@perf.time_it(store_args=True)
def variable_duration(sleep_time=0.02, work_amount=1000):
    """Function with variable execution time based on parameters."""
    time.sleep(sleep_time)
    return sum(range(work_amount))


def my_app():
    """This simulates a normal app using the library."""
    print("Running PyPerf Tests...")
    print("=" * 50)
    
    # Run each function multiple times
    print("1. Fast calculation (3 runs)")
    for _ in range(3):
        result = fast_calculation()
        print(f"   Result: {result}")
    
    print("\n2. Slow I/O operation (2 runs)")
    for _ in range(2):
        result = slow_io_operation()
        print(f"   Result: {result}")
    
    print("\n3. CPU intensive task (2 runs with different iterations)")
    cpu_intensive_task(50000)
    cpu_intensive_task(100000)
    
    print("\n4. Mixed workload (3 runs)")
    for _ in range(3):
        result = mixed_workload()
        print(f"   Result sum: {result:.2f}")
    
    print("\n5. Variable duration (3 runs with different parameters)")
    variable_duration(0.01, 500)
    variable_duration(0.03, 1500)
    variable_duration(0.05, 2000)


if __name__ == "__main__":
    my_app()
    # Timing results will be automatically output at program exit