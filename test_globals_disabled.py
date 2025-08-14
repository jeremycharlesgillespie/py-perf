#!/usr/bin/env python3
"""
Test script showing how to disable global variables in exception traces.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from py_perf.core import PyPerf

# Global variables that won't be shown
CONFIG = {"setting": "value"}
API_URL = "https://api.example.com"

def test_function():
    """Function that will cause an exception."""
    local_var = "local value"
    return local_var / CONFIG  # Type error

def main():
    """Test with globals disabled."""
    print("Testing with global variables disabled...")
    
    # Initialize PyPerf with globals disabled
    perf = PyPerf({
        'py_perf': {
            'exception_show_globals': False
        }
    })
    
    test_function()

if __name__ == "__main__":
    main()