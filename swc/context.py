import os
import sys
import pprint
from pathlib import Path

script_path = os.path.dirname(__file__)
parent_path = os.path.dirname(os.path.dirname(__file__))
data_path = Path('data/')
output_path = Path('data/clean/')
output_path.mkdir(parents=True, exist_ok=True)
pp = pprint.PrettyPrinter(indent=4, width=1)

if __name__ == "__main__":
    print (parent_path, data_path)
