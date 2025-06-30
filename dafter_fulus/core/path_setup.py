"""
This module adds the parent directory to the Python path.
This allows the Django app to import the money_tracker module.
"""

import os
import sys

# Get the parent directory of the Django project
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add the parent directory to the Python path
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)