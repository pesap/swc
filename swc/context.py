""" Contextualize scrips

This scrip contextualize and add some standard functions and variables to all other
scripts.
"""

# Standard packages
import os
import sys
import pprint
from pathlib import Path

# Third-party packages
from dotenv import load_dotenv
from loguru import logger


# Load .env variables
load_dotenv()

script_path = os.path.dirname(__file__)
parent_path = os.path.dirname(os.path.dirname(__file__))

data_path = Path("data/")
data_path.mkdir(exist_ok=True, parents=True)
output_path = Path("data/clean/")
output_path.mkdir(parents=True, exist_ok=True)

pp = pprint.PrettyPrinter(indent=4, width=1)

logger.remove(0)
logger.add(sys.stderr, level="INFO")
logger.add("sam.log")

if __name__ == "__main__":
    print(parent_path, data_path)
