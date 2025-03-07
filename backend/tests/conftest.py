"""
This file is automatically loaded by pytest and sets up the environment for all tests.
"""
import os
import sys

# Add the src directory to the path if not already there
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path) 