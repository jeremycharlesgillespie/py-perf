#!/usr/bin/env python3
"""
Simple test showing that just importing py-perf enables enhanced exceptions.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Just import py-perf - this should automatically enable enhanced exception handling
from py_perf import PyPerf

# Create a simple problematic scenario
def divide_by_zero():
    numbers = [1, 2, 3, 0, 5]
    total = 100
    
    for num in numbers:
        result = total / num  # Will fail when num=0
        print(f"{total} / {num} = {result}")

# This should show enhanced exception output
print("Testing enhanced exceptions by just importing py-perf...")
perf = PyPerf()  # Initialize PyPerf
divide_by_zero()  # This will trigger the enhanced exception handler