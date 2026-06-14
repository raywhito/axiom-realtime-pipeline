import os
import sys

# Make the pipeline's python/ package importable from the tests.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
