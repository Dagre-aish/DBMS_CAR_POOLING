import os
import sys

# Ensure app directory is in Python path
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app'))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from app import app
