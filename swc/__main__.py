#Code to import packages
import sys
import os
from dotenv import load_dotenv
from pathlib import Path  # python3 only
env_path = Path('..') / '.env'
load_dotenv(dotenv_path=env_path)

ROOT = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, ROOT)

