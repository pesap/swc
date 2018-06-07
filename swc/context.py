import os
import sys
from pathlib import Path

script_path = os.path.dirname(__file__)
parent_path = os.path.dirname(os.path.dirname(__file__))
data_path = Path('data/')

if __name__ == "__main__":
    print (parent_path, data_path)
